"""(c) VV10 对相互作用能的贡献：分成"冻结成对项"与"密度弛豫"两部分。

约定（ωB97X-V 的 E_NLC = β∫ρdr + 1/2∬ρρΦ；β∫ρ 在两种密度下都等于 β·N_e，
所以它在任何相互作用差值里精确抵消，下面只报非局域双重积分部分 E_nl）：

  P_frz  = 2·Σ_{i∈A}Σ_{j∈B} w_iρ_i w_jρ_j Φ_ij |_{ρ=SC}      复合物自洽密度下的片间成对项
  P_sup  = 同上但 ρ = ρ_A + ρ_B（在同一张网格、同一套 AO 上叠加）
  DSUP     = E_nl[ρ_SC] - E_nl[ρ_A] - E_nl[ρ_B]                 超位置差（单体各自网格）。刻意不叫 CP：文献里 CP 默认是 counterpoise
  relax  = E_nl[ρ_SC] - E_nl[ρ_sup]                           纯密度弛豫，无网格重划分假象

先前一版把 P_frz 少乘了 2（pair_energy 返回的是半份交叉块），得到的
"frozen 只是 superposition 的一半"是伪结果，本文件已改正并换成同网格参照。
"""
import sys, os, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pyscf import gto, dft
from nlcsplit import partition, nlc, geomlib

KCAL = 627.509474
BASIS = "6-31g*"
LEVEL = 0
BETA = lambda b: (1.0 / 32.0) * (3.0 / (b * b)) ** 0.75


def _fields(mol, dm, level):
    """在 Becke 分区网格上求 ρ、|∇ρ|²，返回 VV10 场量与网格信息。"""
    tmp = dft.RKS(mol); tmp.xc = "wb97x_v"; tmp.grids.level = level
    b, C = tmp._numint.nlc_coeff("wb97x_v")[0][0]
    X, W, owner = partition.atom_partition(mol, level=level, scheme="becke")
    ni = tmp._numint
    rho = ni.eval_rho(mol, ni.eval_ao(mol, X, deriv=1), dm, xctype="GGA")
    sig = rho[1] ** 2 + rho[2] ** 2 + rho[3] ** 2
    w0, kap, keep = nlc.vv10_fields(rho[0], sig, b, C)
    return dict(X=X, wr=W * rho[0], w0=w0, kap=kap, keep=keep, owner=owner,
                b=b, C=C, ne=float((W * rho[0]).sum()))


def _nl_all(p):
    idx = np.where(p["keep"])[0]
    return nlc.pair_energy(p["X"], p["wr"], p["w0"], p["kap"], idx, idx)


def _cross(p, frags):
    idA = np.where(np.isin(p["owner"], frags[0]) & p["keep"])[0]
    idB = np.where(np.isin(p["owner"], frags[1]) & p["keep"])[0]
    return 2.0 * nlc.pair_energy(p["X"], p["wr"], p["w0"], p["kap"], idA, idB)


def _embed(dm_sub, mol, shells):
    """把单体的 AO 密度矩阵按壳层顺序嵌入复合物 AO 空间。"""
    nao = mol.nao_nr()
    dm = np.zeros((nao, nao))
    idx = np.concatenate([np.arange(mol.ao_loc[sh], mol.ao_loc[sh + 1]) for sh in shells])
    assert len(idx) == dm_sub.shape[0], "单体基组与复合物子空间维数不一致"
    dm[np.ix_(idx, idx)] = dm_sub
    return dm


def _shells_of(mol, atoms):
    atoms = set(atoms)
    return [sh for sh in range(mol.nbas) if mol.bas_atom(sh) in atoms]


def optimize(mol, level=2, maxiter=60):
    """ωB97X-V 解析梯度 + L-BFGS-B 优化（笛卡尔，Bohr）。

    网格必须比分解用的 LEVEL 高：实测 level 0 的核梯度有 7.3e-3 Ha/bohr 的
    假力（D6h 苯 sandwich 本该为零），会把几何带偏。解析梯度本身已用
    有限差分核到 1e-4。不依赖 pyscf.geomopt（本机无 geometric 包）。
    """
    from scipy.optimize import minimize
    box = {}

    def fg(x):
        m = mol.copy()
        m.set_geom_(x.reshape(-1, 3), unit="Bohr")
        r = dft.RKS(m); r.xc = "wb97x_v"; r.grids.level = level
        e = r.kernel()
        g = r.nuc_grad_method().kernel()
        box["m"], box["e"], box["gn"] = m, e, np.abs(g).max()
        return e, g.ravel()

    res = minimize(fg, mol.atom_coords().ravel(), jac=True, method="L-BFGS-B",
                   options=dict(maxiter=maxiter, gtol=1e-6))
    print(f"  优化 {res.nit} 步  E_SCF={box['e']:.10f}  |g|max={box['gn']:.2e}  "
          f"success={res.success}", flush=True)
    return box["m"], box["e"], box["gn"]


def run(tag, mol, frags):
    mf = dft.RKS(mol); mf.xc = "wb97x_v"; mf.grids.level = LEVEL; mf.kernel()
    p_sc = _fields(mol, mf.make_rdm1(), LEVEL)

    # 超位置密度：各单体在自己原子子空间里自洽，再嵌入复合物 AO 空间
    nao = mol.nao_nr()
    dm_sup = np.zeros((nao, nao))
    e_mono_nl = 0.0
    for f in frags:
        shells = _shells_of(mol, f)
        sub = gto.M(atom=[(mol.atom_symbol(i), mol.atom_coord(i)) for i in f],
                    basis=BASIS, verbose=0, unit="Bohr")
        mfs = dft.RKS(sub); mfs.xc = "wb97x_v"; mfs.grids.level = LEVEL; mfs.kernel()
        dm_sup += _embed(mfs.make_rdm1(), mol, shells)
        ps = _fields(sub, mfs.make_rdm1(), LEVEL)
        e_mono_nl += _nl_all(ps)

    p_sup = _fields(mol, dm_sup, LEVEL)

    k = KCAL
    P_frz, P_sup = _cross(p_sc, frags) * k, _cross(p_sup, frags) * k
    E_sc, E_sup = _nl_all(p_sc) * k, _nl_all(p_sup) * k
    DSUP = E_sc - e_mono_nl * k
    print(f"  {tag}")
    print(f"    ∫ρ: SC={p_sc['ne']:.6f}  SUP={p_sup['ne']:.6f}  (N_e={mol.nelectron}) "
          f"→ β∫ρ 项在两密度下相同，相互作用差里精确抵消")
    print(f"    E_nl[SC]={E_sc:+9.4f}  E_nl[ρ_sup]={E_sup:+9.4f}  "
          f"E_nl[A]+E_nl[B]={e_mono_nl*k:+9.4f}   (kcal/mol)")
    print(f"    片间成对项  P_frz={P_frz:+8.4f}   P_sup={P_sup:+8.4f}   "
          f"弛豫对成对项的贡献={P_frz-P_sup:+8.4f}")
    print(f"    超位置差 Δsup={DSUP:+8.4f}   同网格纯弛豫 relax={E_sc-E_sup:+8.4f}   "
          f"P_frz/Δsup={P_frz/DSUP:6.3f}   relax/Δsup={(E_sc-E_sup)/DSUP:6.3f}")
    # 一致性：E_nl[SC] = intra_A + intra_B + P_frz（此处只验证交叉块与总和对得上）
    idA = np.where(np.isin(p_sc["owner"], frags[0]) & p_sc["keep"])[0]
    idB = np.where(np.isin(p_sc["owner"], frags[1]) & p_sc["keep"])[0]
    blk = lambda i, j: nlc.pair_energy(p_sc["X"], p_sc["wr"], p_sc["w0"], p_sc["kap"], i, j)
    recon = blk(idA, idA) + blk(idB, idB) + P_frz / k
    print(f"    可加性校验 |E_nl-Recon|={abs(E_sc/k-recon):.2e}\n")
    return dict(P_frz=P_frz, P_sup=P_sup, DSUP=DSUP, relax=E_sc - E_sup)


def main():
    print("== ωB97X-V/%s，网格 level=%d ==" % (BASIS, LEVEL))
    m0 = gto.M(atom=geomlib.h2o_dimer(), basis=BASIS, verbose=0, unit="Angstrom")
    fr = geomlib.FRAGS["(H2O)2"]
    run("水二聚体 / 初始 S22 结构", m0, fr)

    mb = gto.M(atom=geomlib.benzene_sandwich(), basis=BASIS, verbose=0, unit="Angstrom")
    mfb = dft.RKS(mb); mfb.xc = "wb97x_v"; mfb.grids.level = LEVEL; mfb.kernel()
    gb = mfb.nuc_grad_method().kernel()
    print(f"  苯 sandwich E_SCF={mfb.e_tot:.10f} |g|max={np.abs(gb).max():.3e}"
          f"（D6h 对称，应≈0）")
    if np.abs(gb).max() > 1e-4:
        mb, _, _ = optimize(mb)
    run("苯 sandwich", mb, geomlib.FRAGS["(C6H6)2"])

    # 优化放在最后：它最慢，别让它挡住上面两个体系的数
    mopt, eopt, gn = optimize(m0)
    ang = 1.8897261254
    print(f"  优化后 O..O = {np.linalg.norm(mopt.atom_coord(0)-mopt.atom_coord(3))/ang:.3f} Å")
    run("水二聚体 / 优化后结构", mopt, fr)


if __name__ == "__main__":
    t = time.time(); main(); print(f"总用时 {time.time()-t:.0f}s")
