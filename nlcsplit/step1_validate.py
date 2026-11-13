"""Step 1 验收：归属分区是否正确、可加性是否精确成立。

判据（来自执行计划）：
  A. 分区网格积分 ∫ρdr == N_elec（相对误差 < 1e-4），且与 PySCF 常规网格一致
  B. |Σ_块 E_XY − E_nl(整体直接双重和)| < 1e-10 Ha
未过 A/B 不得进入 Step 2。
"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pyscf import gto, dft
from pyscf.dft import numint
from nlcsplit import partition, nlc, geomlib

FRAG = geomlib.FRAGS["(H2O)2"]
KCAL = 627.509474


def density_at(mf, coords):
    ni = mf._numint
    ao = ni.eval_ao(mf.mol, coords, deriv=1)
    rho = ni.eval_rho(mf.mol, ao, mf.make_rdm1(), xctype="GGA")
    return rho[0], rho[1] ** 2 + rho[2] ** 2 + rho[3] ** 2


def check(mol, mf, X, W, owner, label, b, C):
    rho, sig = density_at(mf, X)
    nelec = mol.nelectron
    integ = float(np.dot(rho, W))
    ok_int = abs(integ - nelec) / nelec < 1e-4
    w0, kap, keep = nlc.vv10_fields(rho, sig, b, C)
    wr = W * rho
    allr = np.where(keep)[0]
    E_nl_direct = nlc.pair_energy(X, wr, w0, kap, allr, allr)
    res = nlc.fragment_decomposition(X, W, rho, sig, FRAG, b=b, C=C, owner=owner)
    dev = abs(res["E_nl"] - E_nl_direct)
    ok_add = dev < 1e-10
    print(f"  {label:18s} N={len(X):6d} ∫ρ={integ:9.5f}/{nelec} "
          f"[{'OK' if ok_int else 'FAIL'}]  E_nl={E_nl_direct*KCAL:+8.4f}kcal "
          f"分块和差={dev:.2e}Ha [{'OK' if ok_add else 'FAIL'}]  "
          f"E_AB={res['inter'][(0,1)]*KCAL:+7.4f}kcal  内A={res['intra'][0]*KCAL:+7.3f} "
          f"内B={res['intra'][1]*KCAL:+7.3f} 丢点={res['n_dropped']}")
    return ok_int and ok_add, res, E_nl_direct, integ


def main():
    mol = gto.M(atom=geomlib.h2o_dimer(), basis="6-31g*", verbose=0, unit="Angstrom")
    # 几何自检：今天两次误判都源于手打坐标把 O-H 键长写错，先把键长暴露出来
    C = mol.atom_coords()   # 复数形式返回 Bohr（已实测），单数 atom_coord() 的默认单位不同，别混用
    d = [np.linalg.norm(C[i] - C[j]) / 1.8897261254
         for i in range(mol.natm) for j in range(i + 1, mol.natm)]
    oh = [x for x in d if x < 1.5]
    print(f"  几何自检：成键距离 n={len(oh)} 范围 {min(oh):.4f}-{max(oh):.4f} Å"
          f"（两个水共 4 条 O-H ≈0.957 Å）")
    assert len(oh) == 4 and abs(max(oh) - 0.9572) < 0.02, "水二聚体成键数或键长不对"
    mf, X0, W0, rho0, sig0 = partition.scf_grid(mol, xc="wb97x_v", level=1)
    b, C = mf._numint.nlc_coeff("wb97x_v")[0][0]
    print(f"水二聚体 6-31g* ωB97X-V  E_SCF={mf.e_tot:.8f}  b={b} C={C}")

    nelec_ref = float(np.dot(rho0, W0))
    print(f"常规网格 N={len(X0)} ∫ρ={nelec_ref:.6f} (应 {mol.nelectron})")
    nelec_ref2, exc_ref, _ = numint.nr_nlc_vxc(mf._numint, mol, mf.grids, "wb97x_v", mf.make_rdm1())
    print(f"[PySCF 原生 _vv10nlc 核] E_NLC(总) = {exc_ref*KCAL:+.4f} kcal/mol\n")

    allok = True
    for scheme in partition.SCHEMES:
        X, W, owner = partition.atom_partition(mol, level=1, scheme=scheme)
        ok, *_ = check(mol, mf, X, W, owner, f"scheme={scheme}", b, C)
        allok &= ok

    # 对照：同一批公共点上按最近原子硬指派
    owner_hard = partition.nearest_partition(mol, X0)
    ok, *_ = check(mol, mf, X0, W0, owner_hard, "nearest(公共网格)", b, C)
    allok &= ok

    print("\n== 自洽性交叉核对 ==")
    Xb, Wb, ob = partition.atom_partition(mol, level=1, scheme="becke")
    _, resb, _, ib = check(mol, mf, Xb, Wb, ob, "(重复 Becke)", b, C)
    Xs, Ws, os_ = partition.atom_partition(mol, level=1, scheme="stratmann")
    _, ress, _, is_ = check(mol, mf, Xs, Ws, os_, "(重复 Stratmann)", b, C)
    print(f"Becke 与 Stratmann 的 E_AB 之差 = "
          f"{abs(resb['inter'][(0,1)] - ress['inter'][(0,1)])*KCAL:.4f} kcal/mol")
    print(f"∫ρ 差异 = {abs(ib-is_):.6f} 电子")
    print("\nStep 1 验收:", "PASS" if allok else "FAIL")
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())
