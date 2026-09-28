"""Step D：密度下限 rho_floor 这一**人为参数**到底影响结果多少。

背景：nlc.vv10_fields() 用 keep = rho > rho_floor 把远区低密度点整批剔除，
否则 |grad rho|^4/rho^4 会 0/0 或下溢（实测 sto-3g level2 出 NaN）。
模块默认 RHO_FLOOR = 1.0e-12。这个数是为了数值稳健而选的，**不是物理量**，
所以必须回答：把它挪几档，报出来的 P_frz 挪多少。

测量设计（严格单一变量）：
  - 同一个体系（geomlib 水二聚体，S22 初始结构）、同一个基组 6-31g*、同一个泛函
  - 对每个 level 只跑**一次** SCF，dm 固定不动 ⇒ 密度与 floor 无关
  - 对每个 level 只建**一张** Becke 分区网格（scheme='becke'），rho/|grad rho|^2
    都在同一张网格上由同一个 dm 求出 ⇒ floor 是唯一的自变量
  - floor 只进入 vv10_fields(rho, sigma, b, C, rho_floor=floor) 的 keep 掩码
  level 0 不跑：PROGRESS 2026-09-28 22:35 [retract] 已判定它 ∫ρ 少 0.015 个电子、不可信。

量的定义（单位 kcal/mol，系数 KCAL=627.509474）：
  E_nl   = pair_energy(idx, idx)              整份非局域双重积分（对角自作用即全和）
  P_frz  = 2 * pair_energy(idA, idB)          整份片间成对项。**必须乘 2**：
                                                pair_energy 返回 0.5*Σ_A*Σ_B，是半份
  E_loc  = beta * Σ_i w_i rho_i               beta = (1/32)(3/b^2)^(3/4)，走全网格
  int_rho= E_loc / beta                       用来显示 floor 有没有改变电子数积分

判读（不美化）：若 1e-10..1e-14 档内 P_frz 跨度 < 0.005 kcal/mol ⇒ floor 不敏感，
可当实现细节；否则如实报跨度，并跟 P_frz 本身（本体系 ~ -0.63，量级 ~0.55）比大小。

交叉核对：floor=1e-12（即 RHO_FLOOR 默认值）这一档必须复现
nlcsplit/logs/20260928T142013Z_step2.out 里 6-31g* lvl1/lvl2 的 E_AB 与 E_nl
（同几何、同基组、同 level、同 scheme、同默认 floor）；对不上就说明本脚本的调用方式有误。

本文件不改动 nlc.py / partition.py / geomlib.py / step1..step_c / run_all.sh。

跑后补记（22:5x，只改本 docstring，未动计算路径）：本次运行期间另一 agent 给
nlc.pair_energy 加了可选关键字 wB（默认 None）。已用独立朴素双重和复核当前源：
wB=None 与显式 wB=wr 逐位相同（差 0.00e+00）、block 无关（差 0.00e+00）、物理远区
关系 σ=(2β)²ρ² 下 self/cross 相对差 1.4e-15 / 0.0，可加性 E_all=(A,A)+(B,B)+2(A,B)
成立（5.8e-28 Ha）⇒ 上面日志里的数字对当前 nlc.py 依然成立。
（注：若把 σ/ρ⁴ 造得病态大，w0 会到 1e10，此时 gemm 对角项 R²≈0 与 R²=0 有 1e-6
相对差——那是合成数据的产物，不是真实密度下的行为。）
"""
import os
# 必须在 import numpy 之前设：这台机器只有 8 核且另有任务在跑。
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"

import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pyscf import gto, dft  # noqa: E402
from nlcsplit import geomlib, nlc, partition  # noqa: E402

KCAL = 627.509474
XC = "wb97x_v"
BASIS = "6-31g*"
SCHEME = "becke"
SYSTEM = "(H2O)2  geomlib.h2o_dimer()  S22 初始结构  O..O=2.983 A"
FRAGS = geomlib.FRAGS["(H2O)2"]
LEVELS = (1, 2)
FLOORS = (1.0e-8, 1.0e-10, 1.0e-12, 1.0e-14, 1.0e-16)
REF_FLOOR = 1.0e-12
BAND = (1.0e-10, 1.0e-12, 1.0e-14)   # 验收区间
TOL = 0.005                          # kcal/mol
# 存档参照 (E_AB, E_nl) kcal/mol，6-31g* lvl1/lvl2，默认 floor 1e-12，构造几何
# ⚠ 2026-09-29 换版：旧值 (-0.6333,-7.6804)/(-0.6335,-7.6817) 是**错核(交叉配对) +
#   错几何(受体 H 朝向给体、H..H 塌到 1.64 Å)** 两重错误下的数，留着会把正确实现
#   误判成"回归"。现值来源：logs/20260929T010500Z_step1_geomfix.out (lvl1) 与
#   CentOS logs/20260928T165857Z_centos-step2.out (lvl2)，均为 V2 核 + 修正几何。
ARCHIVED = {1: (-0.5237, -7.8130), 2: (-0.5235, -7.8137)}


def beta_of(b):
    return (1.0 / 32.0) * (3.0 / (b * b)) ** nlc.BETA_EXP


def state(level):
    """一个 level 建一次：SCF(dm) + Becke 分区网格 + 该网格上的 rho/|grad rho|^2。

    floor 不出现在这里 —— 这就是"floor 是唯一自变量"的保证。
    """
    mol = gto.M(atom=geomlib.h2o_dimer(), basis=BASIS, verbose=0, unit="Angstrom")
    t0 = time.time()
    mf = dft.RKS(mol)
    mf.xc = XC
    mf.grids.level = level
    mf.kernel()
    dm = mf.make_rdm1()
    b, C = mf._numint.nlc_coeff(XC)[0][0]

    X, W, owner = partition.atom_partition(mol, level=level, scheme=SCHEME)
    ao = mf._numint.eval_ao(mol, X, deriv=1)
    rho = mf._numint.eval_rho(mol, ao, dm, xctype="GGA")
    sig = rho[1] ** 2 + rho[2] ** 2 + rho[3] ** 2

    st = dict(level=level, mol=mol, mf=mf, dm=dm, b=b, C=C, X=X, W=W, owner=owner,
              rho=rho[0], sig=sig, wr=W * rho[0])
    # 常规（非分区）网格上的 ∫ρ 一并存档，用来看两张网格的电子数
    ni = mf._numint
    rg_w = mf.grids.weights
    rrho = ni.eval_rho(mol, ni.eval_ao(mol, mf.grids.coords, deriv=1), dm, xctype="GGA")
    st["reg_grid"] = dict(N=len(mf.grids.coords), int_rho=float(np.dot(rrho[0], rg_w)))
    print(f"  [level {level}] SCF {time.time()-t0:.1f}s  E_SCF={mf.e_tot:.10f}  "
          f"N_e={mol.nelectron}  nao={mol.nao_nr()}", flush=True)
    print(f"  [level {level}] b={b} C={C}  beta={beta_of(b):.10e} Ha/el  "
          f"dm 指纹={abs(dm).sum():.10f}", flush=True)
    print(f"  [level {level}] Becke 网格 N={len(X)}  ∫ρ(全点,与 floor 无关)="
          f"{st['wr'].sum():.6f}   常规网格 N={st['reg_grid']['N']} "
          f"∫ρ={st['reg_grid']['int_rho']:.6f}", flush=True)
    return st


def one_level(st, floor):
    """给定 (固定网格, 固定 dm) 与一个 floor，算全部上报量。"""
    X, wr, owner = st["X"], st["wr"], st["owner"]
    w0, kap, keep = nlc.vv10_fields(st["rho"], st["sig"], st["b"], st["C"],
                                    rho_floor=floor)
    idx = np.where(keep)[0]
    idA = np.where(np.isin(owner, FRAGS[0]) & keep)[0]
    idB = np.where(np.isin(owner, FRAGS[1]) & keep)[0]

    beta = beta_of(st["b"])
    t0 = time.time()
    E_nl = nlc.pair_energy(X, wr, w0, kap, idx, idx)          # 整份
    t1 = time.time()
    P_frz = 2.0 * nlc.pair_energy(X, wr, w0, kap, idA, idB)   # 半份 ×2
    t2 = time.time()
    E_loc = nlc.local_term(beta, wr)                            # 全网格，不受 floor 影响
    intra = (nlc.pair_energy(X, wr, w0, kap, idA, idA),
             nlc.pair_energy(X, wr, w0, kap, idB, idB)) if floor == REF_FLOOR else None

    bad = int((~np.isfinite(w0[idx])).sum() + (~np.isfinite(kap[idx])).sum())
    r = dict(level=st["level"], floor=floor, N=len(X), N_used=int(idx.size),
             N_drop=int((~keep).sum()), E_nl=E_nl, P_frz=P_frz, E_loc=E_loc,
             int_rho=E_loc / beta, int_rho_used=float(wr[idx].sum()),
             rho_max_dropped=float(st["rho"][~keep].max()) if (~keep).any() else float("nan"),
             rho_min_kept=float(st["rho"][idx].min()) if idx.size else float("nan"),
             n_nonfinite=bad, t_nl=t1 - t0, t_cross=t2 - t1, t_tot=t2 - t0,
             intra=intra, nA=int(idA.size), nB=int(idB.size))
    print(f"    floor={floor:.0e}  N_used={r['N_used']:6d} N_drop={r['N_drop']:6d} "
          f"(A={r['nA']} B={r['nB']})  E_nl={E_nl*KCAL:+9.4f}  P_frz={P_frz*KCAL:+9.5f}  "
          f"E_loc={E_loc*KCAL:+9.4f}  ∫ρ={r['int_rho']:.6f}  "
          f"∫ρ_used={r['int_rho_used']:.9f}  非有限场量点={bad}  "
          f"[{t2-t0:.1f}s]  ({r['t_nl']:.1f}+{r['t_cross']:.1f})", flush=True)
    print(f"      边界证据: 被丢点的最大 ρ={r['rho_max_dropped']:.3e} < "
          f"{floor:.0e} ≤ 保留点的最小 ρ={r['rho_min_kept']:.3e}"
          f"   (丢点 {100*r['N_drop']/r['N']:.1f}% 的网格点 / "
          f"带走 {r['int_rho']-r['int_rho_used']:.3e} 个电子，共 {r['int_rho']:.6f})", flush=True)
    return r


def main():
    t_all = time.time()
    print("=" * 108)
    print("Step D · rho_floor 敏感性")
    print(f"  体系   : {SYSTEM}")
    print(f"  片段   : {FRAGS}  (geomlib.FRAGS['(H2O)2'])")
    print(f"  基组   : {BASIS}      泛函: {XC}      能量单位 kcal/mol (×{KCAL})")
    print(f"  网格   : partition.atom_partition(scheme='{SCHEME}')，level ∈ {LEVELS}（不跑 level 0）")
    print(f"  floor  : {FLOORS}   参照档 = {REF_FLOOR:g}（= nlc.RHO_FLOOR 默认值）")
    print(f"  nlc.RHO_FLOOR 默认 = {nlc.RHO_FLOOR:g}；本脚本只显式传参，不改常量")
    print(f"  OMP_NUM_THREADS = {os.environ['OMP_NUM_THREADS']}")
    print("=" * 108, flush=True)

    rows = []
    for level in LEVELS:
        print(f"\n### level = {level}   体系/基组/泛函见抬头；每档 floor 共用同一 dm 同一网格", flush=True)
        st = state(level)
        # 只读校验：vv10_fields 的 keep 是否恰为 rho > floor（掩码语义必须确认，别猜）
        for f in FLOORS:
            _, _, kp = nlc.vv10_fields(st["rho"], st["sig"], st["b"], st["C"], rho_floor=f)
            assert np.array_equal(kp, st["rho"] > f), "keep 掩码语义与 rho>floor 不一致"
        for f in FLOORS:
            rows.append(one_level(st, f))
        locs = [r["E_loc"] for r in rows[-len(FLOORS):]]
        print(f"  [level {level}] E_loc 跨 {len(FLOORS)} 档 floor 的最大变化 = "
              f"{max(locs)-min(locs):.3e} Ha（按构造应为 0：local_term 不接 keep 掩码）",
              flush=True)
        del st

    print("\n" + "=" * 108)
    print("汇总表  每行 = (体系=水二聚体 geomlib, 基组=6-31g*, 泛函=wb97x_v, 网格=scheme becke, level, floor)")
    print("-" * 108)
    hdr = (f"{'lvl':>3s} {'floor':>7s} {'N_used':>7s} {'N_drop':>7s} "
           f"{'E_nl':>10s} {'P_frz':>10s} {'dP_frz vs 1e-12':>18s} {'E_loc':>10s} {'∫ρ':>10s}")
    print(hdr)
    print("-" * 108)
    ref_p = {r["level"]: r["P_frz"] * KCAL for r in rows if r["floor"] == REF_FLOOR}
    for r in rows:
        pk = r["P_frz"] * KCAL
        print(f"{r['level']:3d} {r['floor']:7.0e} {r['N_used']:7d} {r['N_drop']:7d} "
              f"{r['E_nl']*KCAL:+10.4f} {pk:+10.5f} {pk-ref_p[r['level']]:+18.8f} "
              f"{r['E_loc']*KCAL:+10.4f} {r['int_rho']:10.6f}")
    print("-" * 108)

    print("\nP_frz 矩阵（kcal/mol，行=level，列=floor；8 位小数以便看清亚 µkcal 变化）")
    print("  lvl " + "".join(f"{f:>14.0e}" for f in FLOORS))
    for level in LEVELS:
        v = {r["floor"]: r["P_frz"] * KCAL for r in rows if r["level"] == level}
        print(f"  {level:>3d} " + "".join(f"{v[f]:>+14.8f}" for f in FLOORS))
    print("\nE_nl 矩阵（kcal/mol，同上）")
    print("  lvl " + "".join(f"{f:>14.0e}" for f in FLOORS))
    for level in LEVELS:
        v = {r["floor"]: r["E_nl"] * KCAL for r in rows if r["level"] == level}
        print(f"  {level:>3d} " + "".join(f"{v[f]:>+14.8f}" for f in FLOORS))

    print("\n== 一致性校验 ==")
    for r in rows:
        if r["floor"] != REF_FLOOR:
            continue
        recon = r["intra"][0] + r["intra"][1] + r["P_frz"]
        print(f"  level {r['level']} floor 1e-12: 可加性 |E_nl-(intraA+intraB+P_frz)| = "
              f"{abs(recon-r['E_nl']):.2e} Ha   "
              f"(intraA={r['intra'][0]*KCAL:+.4f} intraB={r['intra'][1]*KCAL:+.4f} "
              f"P_frz={r['P_frz']*KCAL:+.4f})")
        if r["level"] in ARCHIVED:
            ae, an = ARCHIVED[r["level"]]
            print(f"  level {r['level']} vs 存档 step2(6-31g*, 默认 floor): "
                  f"dE_AB={r['P_frz']*KCAL-ae:+.5f}  dE_nl={r['E_nl']*KCAL-an:+.5f} kcal/mol")

    print("\n== 判读 ==")
    print(f"  验收区间 = floor ∈ {BAND}，判据 = P_frz 跨度 < {TOL} kcal/mol")
    for level in LEVELS:
        v = {r["floor"]: r["P_frz"] * KCAL for r in rows if r["level"] == level}
        bs = [f for f in BAND if f in v]
        if len(bs) < len(BAND):
            print(f"  [警告] level {level} 缺档 {sorted(set(BAND)-set(bs))}，"
                  f"区间跨度按现有 {bs} 计算")
        sp = max(v[f] for f in bs) - min(v[f] for f in bs)
        sp_all = max(v.values()) - min(v.values())
        base = abs(v[REF_FLOOR])
        verdict = ("不敏感 —— floor 在 1e-10..1e-14 之间可当实现细节"
                   if sp < TOL else
                   f"敏感 —— 需要交代 floor 的取值")
        print(f"  level {level}: 区间 1e-10..1e-14 跨度 = {sp:.6f} kcal/mol "
              f"({sp:.3e})  (判据 <{TOL}) → {verdict}")
        print(f"             全 {len(FLOORS)} 档跨度 = {sp_all:.6f}；"
              f"相对 |P_frz(1e-12)|={base:.4f} "
              f"即 {100*sp/base:.4f}%（区间内）/ {100*sp_all/base:.4f}%（含 1e-8 与 1e-16）")
        if sp_all >= TOL:
            worst = max(FLOORS, key=lambda f: abs(v[f] - v[REF_FLOOR]))
            print(f"             偏移最大的档 = {worst:.0e}，"
                  f"相对 1e-12 偏 {v[worst]-v[REF_FLOOR]:+.6f} kcal/mol")
    print(f"\n总用时 {time.time()-t_all:.0f}s")


if __name__ == "__main__":
    main()
