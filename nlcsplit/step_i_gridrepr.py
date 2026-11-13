"""表 1 拆行：把"同一张网格上的算法离散差"与"换到分区网格的表示差"分开量。

三个量，同一份密度、同一个 level：
  V_native  nr_nlc_vxc 在 mf.grids 参照网格上（PySCF 自己的核，含插值）
  V_ref     我们的显式双重和，也放在 mf.grids 参照网格上
            ⇒ V_ref − V_native = 纯算法离散差（同网格、同密度，只剩核的差别）
  V_part    我们的显式双重和，放在 gen_grid.get_partition 的分区网格上
            ⇒ V_part − V_ref = 网格换了以后"同一张网格值函数"的表示差
不报单值：level 0/1/2 各来一遍，看两行各自的收敛趋势。
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pyscf import gto, dft                                    # noqa: E402
from pyscf.dft import numint                                  # noqa: E402
from nlcsplit import geomlib, nlc, partition                  # noqa: E402

KCAL = 627.509474
BETA = (1.0 / 32.0) * (3.0 / 6.0 ** 2) ** nlc.BETA_EXP


def on_grid(mol, mf, coords, weights):
    """在给定网格上算 E_NLC：返回 (原生核@参照网格, 显式双重和+β∫ρ, ρ, wρ)。

    原生核那条只认 mf.grids（nr_nlc_vxc 内部就取它），所以它在两个调用点
    返回同一个数——这正是我们要的：它是"参照网格上的真值"。
    """
    ni = mf._numint
    rho = ni.eval_rho(mol, ni.eval_ao(mol, coords, deriv=1), mf.make_rdm1(), xctype="GGA")
    sigma = rho[1] ** 2 + rho[2] ** 2 + rho[3] ** 2
    b, C = mf._numint.nlc_coeff("wb97x_v")[0][0]
    w0, kap, keep = nlc.vv10_fields(rho[0], sigma, b, C)
    wr = weights * rho[0]
    idx = np.where(keep)[0]
    mine = nlc.local_term(BETA, wr) + nlc.pair_energy(coords, wr, w0, kap, idx, idx)
    _, exc_native, _ = numint.nr_nlc_vxc(ni, mol, mf.grids, "wb97x_v", mf.make_rdm1())
    return float(exc_native), mine, rho[0], wr


def main():
    """只有直接运行才做 SCF 与双重和；import 这个模块不再有副作用。"""
    for level in (0, 1, 2):
        mol = gto.M(atom=geomlib.h2o_dimer(), basis="6-31g*", verbose=0, unit="Angstrom")
        mf = dft.RKS(mol)
        mf.xc = "wb97x_v"
        mf.grids.level = level
        t0 = time.time()
        mf.kernel()
        v_native, mine_ref, rho_ref, wr_ref = on_grid(mol, mf, mf.grids.coords, mf.grids.weights)
        coords_p, w_p, owner = partition.atom_partition(mol, level=level, scheme="becke")
        _, mine_part, rho_p, wr_p = on_grid(mol, mf, coords_p, w_p)

        pop_ref = wr_ref.sum()
        pop_part = wr_p.sum()
        print(f"level {level}  N_ref={len(mf.grids.coords):7d}  N_part={len(coords_p):7d}"
              f"  ({time.time()-t0:.0f}s)")
        print(f"  原生核 E_NLC                = {v_native:.10f} Ha")
        print(f"  显式和 @参照网格            = {mine_ref:.10f} Ha   "
              f"差(同网格) = {(mine_ref-v_native)*KCAL:+.3e} kcal/mol = {(mine_ref-v_native):+.3e} Ha")
        print(f"  显式和 @分区网格            = {mine_part:.10f} Ha   "
              f"差(换网格) = {(mine_part-mine_ref)*KCAL:+.4f} kcal/mol")
        print(f"  ∫ρ 参照/分区 = {pop_ref:.8f} / {pop_part:.8f}  "
              f"(真值 {mol.nelectron})  ⇒ 网格的电子数表示差 {pop_part-pop_ref:+.2e} e"
              f" = β·Δ {(pop_part-pop_ref)*BETA*KCAL:+.2e} kcal/mol")

    print(f"\nβ = {BETA:.6f} Ha/电子 = {BETA*KCAL:.4f} kcal/mol/电子"
          f"  ⇒ 任何 Becke 布居跨度 ΔN_A 直接放大 {BETA*KCAL:.2f} 倍进局域项")


if __name__ == "__main__":
    main()
