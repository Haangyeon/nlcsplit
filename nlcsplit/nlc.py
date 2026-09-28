"""VV10 / rVV10 非局域关联能的显式双重积分与片断-成对分解。

核定义（参照 = PySCF 原生 C 核 `libdft.VXC_vv10nlc`，不是 libxc；见下方"裁判是谁"）：
    w0(r)  = sqrt( C |grad rho|^4 / rho^4 + (4 pi / 3) rho )
    kappa(r) = b (3 pi / 2) (rho / 9 pi)^(1/6)
    g  = w0(r) R^2 + kappa(r),  g' = w0(r') R^2 + kappa(r')   # 同中心配对
    Phi = -3 / (2 g g' (g + g'))
    E_NL  = 1/2 sum_i sum_j w_i rho_i w_j rho_j Phi_ij
    E_loc = beta int rho dr,   beta = (1/32)(3/b^2)^(3/4)
    E_NLC = E_loc + E_NL

这里是 O(N^2) 的显式实现：价值不在"真值"，在于把核折叠成点值后再摊回 (i,j) 对，
从而可按片段归属；对表用两个独立程序（见 step_e_kernel.py）。

**裁判是谁**（2026-09-29 读源码纠正，此前一律误标为 "libxc"）：
`pyscf.dft.numint.nr_nlc_vxc` 内部调的是 PySCF 自己的 `_vv10nlc`，**不经过 libxc**
（libxc 只负责半局域那部分）。所以本项目实际的对照是
  (1) PySCF 原生 VV10 核（同一程序库的另一套实现，逐点差 ≤3e-5 kcal/mol）
  (2) ORCA 6.0.1（`ref/h2o_wb97xv.out`，真正独立程序，差 6e-4 kcal/mol）
论文与日志里凡"与 libxc 一致"的说法都要按此改写；若要引入 libxc 本尊的 VV10
作第三方裁判，得直接调 libxc 的 `xc_nlc_vxc`，PySCF 这条路径给不了。
"""
import numpy as np

PI = np.pi
BETA_EXP = 0.75
RHO_FLOOR = 1.0e-12   # 远区 rho->0 时 |grad rho|^4/rho^4 会 0/0 或下溢（实测 sto-3g level2 出 NaN）


def vv10_fields(rho, sigma, b, C, rho_floor=RHO_FLOOR):
    """由密度与其梯度模方给出 w0、kappa。

    返回 (w0, kappa, keep)，keep 是布尔掩码：密度低于 rho_floor 的点不参与双重积分。
    """
    rho = np.asarray(rho)
    sigma = np.asarray(sigma)
    keep = rho > rho_floor
    rho_safe = np.where(keep, rho, rho_floor)
    w0 = np.sqrt(C * sigma ** 2 / rho_safe ** 4 + (4.0 / 3.0) * PI * rho_safe)
    kap = b * (1.5 * PI) * (rho_safe / (9.0 * PI)) ** (1.0 / 6.0)
    return w0, kap, keep


def local_term(beta, wr):
    """E_loc = beta * integral(rho dr)，wr 为 weight*rho。"""
    return beta * wr.sum()


def pair_energy(coords, wr, w0, kap, iA, iB, block=256, wB=None, pairing="same-centre"):
    """0.5 * sum_{i in A} sum_{j in B} wr_i wr_j Phi_ij

    传同一个索引集合即得该子块的自身项；A != B 时给的是"半份"成对项，
    因此总和有 E = sum_A E_AA + 2 sum_{A<B} E_AB 的关系（可加性可校验）。
    wB 给定时，B 侧用 wB 而 A 侧用 wr —— 软分区要靠它传两套归属权重。

    pairing 决定 g/g' 怎么配对（`step_e_kernel.py` 用 PySCF 原生核判别，kcal/mol 偏差）：
      "same-centre"  g = w0_i R² + κ_i , g' = w0_j R² + κ_j   → 与 PySCF 原生核、ORCA 6.0.1 一致（0.0000）
      "cross"        g = w0_j R² + κ_i , g' = w0_i R² + κ_j   → 高 +0.13(水)/+0.42(Ar)，是错的
    默认取 same-centre；cross 留着做"定义敏感性"的可审计对照。

    R² 用极化恒等式 |a-b|² = |a|²+|b|²-2a·b 走一次 gemm，而不是先做
    (block,n,3) 的位移张量：后者在水苯二聚体尺度上要多占 5 倍内存。
    """
    if pairing not in ("same-centre", "cross"):
        raise ValueError(f"未知 pairing {pairing!r}，可选 'same-centre' / 'cross'")
    iA = np.asarray(iA)
    iB = np.asarray(iB)
    cA = coords[iA]
    cB = coords[iB]
    if len(iA) == 0 or len(iB) == 0:
        return 0.0
    wb = wr if wB is None else wB
    r2B = np.einsum("ij,ij->i", cB, cB)
    w0B, kapB, wrB = w0[iB], kap[iB], wb[iB]
    w0A, kA, wrA = w0[iA], kap[iA], wr[iA]
    s = 0.0
    for p0 in range(0, len(iA), block):
        sl = slice(p0, min(p0 + block, len(iA)))
        A = cA[sl]
        R2 = np.einsum("ij,ij->i", A, A)[:, None] + r2B[None, :] - 2.0 * (A @ cB.T)
        np.maximum(R2, 0.0, out=R2)
        if pairing == "same-centre":
            g = R2 * w0A[sl][:, None] + kA[sl][:, None]
            gp = R2 * w0B[None, :] + kapB[None, :]
        else:
            g = R2 * w0B[None, :] + kA[sl][:, None]
            gp = R2 * w0A[sl][:, None] + kapB[None, :]
        phi = -1.5 / (g * gp * (g + gp))
        phi *= wrB[None, :]
        s += float(np.dot(phi.sum(axis=1), wrA[sl]))
    return 0.5 * s


def fragment_decomposition(coords, weights, rho, sigma, fragments,
                           b=6.0, C=0.01, owner=None, soft=None, rho_floor=RHO_FLOOR):
    """按片段归属给出 E_NLC 的分块分解。

    参数
      fragments : list[list[int]]  原子序号分组（片段定义）
      owner     : (N,) int         每个网格点归属的原子序号；None 时按最近原子硬指派
      soft      : (natm, N) 或 None  逐点归属权重（例如 Becke 分区因子）；
                                   给了它就做软分区，此时要求 sum_a soft[a] == 1
      rho_floor : 密度下限，低于它的网格点不参与双重积分（远区 0/0 与下溢）

    返回 dict：{'E_loc', 'E_nl', 'E_total', 'intra': {k:..}, 'inter': {(k,l):..}}
    inter[(A,B)] 是**整份**交叉贡献（不是半份），故 E_nl = Σ intra + Σ inter。
    """
    coords = np.asarray(coords)
    weights = np.asarray(weights)
    w0, kap, keep = vv10_fields(rho, sigma, b, C, rho_floor)
    wr = weights * rho
    beta = (1.0 / 32.0) * (3.0 / (b * b)) ** BETA_EXP
    npts = len(coords)
    nf = len(fragments)

    if soft is not None:
        soft = np.asarray(soft)
        dev = np.abs(soft.sum(axis=0) - 1.0).max()
        if dev > 1e-8:
            raise ValueError(f"软分区权重每点之和偏离 1 达 {dev:.3e}，不可用")
        keepf = keep.astype(float)
        fw = [sum(soft[a] for a in fragments[k]) * keepf for k in range(nf)]
        def blk(A, B):
            return _soft_pair(coords, wr, w0, kap, fw[A], fw[B])
    else:
        if owner is None:
            raise ValueError("需要 owner（硬分区）或 soft（软分区权重）之一")
        idx_of = {k: np.where(np.isin(owner, fragments[k]) & keep)[0] for k in range(nf)}
        def blk(A, B):
            return pair_energy(coords, wr, w0, kap, idx_of[A], idx_of[B])

    out = {"E_loc": local_term(beta, wr), "n_dropped": int((~keep).sum()),
           "intra": {}, "inter": {}}
    for A in range(nf):
        out["intra"][A] = blk(A, A)
        for B in range(A + 1, nf):
            out["inter"][(A, B)] = 2.0 * blk(A, B)
    out["E_nl"] = sum(out["intra"].values()) + sum(out["inter"].values())
    out["E_total"] = out["E_loc"] + out["E_nl"]
    return out


def _soft_pair(coords, wr, w0, kap, fA, fB):
    """软分区块：0.5·ΣΣ (wρf^A)_i (wρf^B)_j Φ_ij。

    直接复用 pair_energy 的 gemm 路径：把逐点归属权重折进 wr，全点求和。
    f 里已乘过 keep，被丢掉的点权重为 0，不必再传索引。
    """
    n = len(coords)
    allr = np.arange(n)
    return pair_energy(coords, wr * fA, w0, kap, allr, allr, wB=wr * fB)
