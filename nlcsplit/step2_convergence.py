"""Step 2：E_AB 随网格 level 与基组的收敛，以及跨归属方案的稳定性。

判据（执行计划 Step 2）：至少一种方案在 level 0→2、STO-3G→6-31G*→aug-cc-pVDZ 下
E_AB 变化 < 0.05 kcal/mol。

几何一律取自 geomlib（单一真值源）。本脚本以前内联过一份不同的水二聚体坐标，
与 geomlib.h2o_dimer() 给出的 P_frz 相差 0.078 kcal/mol —— 比归属方案的全部
跨度还大 14 倍，是"两套几何"这类坑的来源，已删。
E_AB 现在是**整份**交叉项 2·Σ_{i∈A}Σ_{j∈B}。
"""
import sys, os, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pyscf import gto
from pyscf.dft import numint
from nlcsplit import partition, nlc, geomlib

FRAG = geomlib.FRAGS["(H2O)2"]
KCAL = 627.509474

# (基组, 最高 level)。成本随 N^2 增长。6-31g* 跑到 2 是为了给"网格是否收敛"一条
# 独立于 level 0 的证据：V2 核 + 修正几何下实测 E_AB = -0.5316(lvl0) / -0.5237(lvl1) /
# -0.5235(lvl2)，散布 0.008 kcal/mol（1.5%）。旧注释里那两个数是不同年代口径混来的
# （-0.6316 是错核错几何的 lvl0，-0.5537 其实是 aug-cc-pVDZ lvl1），不能当参照。
PLAN = [("sto-3g", (0, 1, 2)), ("6-31g*", (0, 1, 2)), ("aug-cc-pvdz", (0, 1))]


def one(mol, level, basis, scheme="becke"):
    mf, X0, W0, rho0, sig0 = partition.scf_grid(mol, xc="wb97x_v", level=level, basis=basis)
    b, C = mf._numint.nlc_coeff("wb97x_v")[0][0]
    X, W, owner = partition.atom_partition(mol, level=level, scheme=scheme)
    ao = mf._numint.eval_ao(mol, X, deriv=1)
    rho = mf._numint.eval_rho(mol, ao, mf.make_rdm1(), xctype="GGA")
    sig = rho[1] ** 2 + rho[2] ** 2 + rho[3] ** 2
    t0 = time.time()
    res = nlc.fragment_decomposition(X, W, rho[0], sig, FRAG, b=b, C=C, owner=owner)
    _, exc_ref, _ = numint.nr_nlc_vxc(mf._numint, mol, mf.grids, "wb97x_v", mf.make_rdm1())
    return dict(N=len(X), E_AB=res["inter"][(0, 1)], E_nl=res["E_nl"],
                E_tot=res["E_total"], libxc=exc_ref, E_scf=mf.e_tot, sec=time.time() - t0)


def main():
    print(f"{'基组':13s} {'lvl':3s} {'N':>7s} {'E_AB':>10s} {'E_nl':>10s} "
          f"{'E_NLC总':>10s} {'pyscf核':>10s} {'我-参照核':>10s} {'秒':>6s}")
    rows = []
    for basis, levels in PLAN:
        mol = gto.M(atom=geomlib.h2o_dimer(), basis=basis, verbose=0, unit="Angstrom")
        for lv in levels:
            r = one(mol, lv, basis)
            d = (r["E_tot"] - r["libxc"]) * KCAL
            print(f"{basis:13s} {lv:<3d} {r['N']:7d} {r['E_AB']*KCAL:+9.4f} {r['E_nl']*KCAL:+9.4f} "
                  f"{r['E_tot']*KCAL:+9.3f} {r['libxc']*KCAL:+9.3f} {d:+9.3f} {r['sec']:6.1f}")
            rows.append((basis, lv, r["E_AB"] * KCAL))
        # 换方案对照（同基组同 level 中层）
        lv = levels[len(levels) // 2]
        for sch in ("stratmann", "becke-treutler"):
            r = one(mol, lv, basis, scheme=sch)
            print(f"    ^ {sch:16s} lvl={lv} E_AB={r['E_AB']*KCAL:+.4f} kcal/mol")

    ab = np.array([v for _, _, v in rows])
    print(f"\nE_AB 全体跨度 = {ab.max()-ab.min():.4f} kcal/mol  (判据 <0.05)")
    same = {}
    for basis, lv, v in rows:
        same.setdefault(basis, []).append(v)
    for basis, vs in same.items():
        print(f"  {basis:13s} 跨网格散布 = {max(vs)-min(vs):.4f} kcal/mol")
    print("Step 2:", "PASS" if ab.max() - ab.min() < 0.05 else "需复核（见计划回退条件）")


if __name__ == "__main__":
    main()
