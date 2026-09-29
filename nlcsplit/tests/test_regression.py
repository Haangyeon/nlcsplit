"""回归 + 外部对照测试（需要跑自洽场，标记 slow）。

两类断言的性质不同，别混起来读：
  * 与 PySCF 原生 VV10 核（`numint.nr_nlc_vxc` → libdft.VXC_vv10nlc）对照 = **外部对照**；
    再加 ORCA 6.0.1 的输出（见 README 的 ref/ 说明）才算两个独立程序。
  * 对 P_frz / 五方案跨度的断言 = **回归护栏**，只防改动引入漂移，
    数值本身来自本包自己的计算，不构成独立验证。
"""
import numpy as np
import pytest

from nlcsplit import geomlib, nlc, partition

KCAL = 627.509474
BASIS = "6-31g*"


@pytest.fixture(scope="module")
def dimer():
    gto = pytest.importorskip("pyscf.gto")
    return gto.M(atom=geomlib.h2o_dimer(), basis=BASIS, verbose=0, unit="Angstrom")


def test_geometry_is_physical(dimer):
    """受体 H 必须背向给体：旧坐标把 H..H 压到 1.64 Å，这条防它回潮。"""
    C = dimer.atom_coords()
    dd = np.linalg.norm(C[:, None, :] - C[None, :, :], axis=2) / 1.8897261254
    sym = [dimer.atom_symbol(i) for i in range(dimer.natm)]
    bonds = [dd[i, j] for i in range(6) for j in range(i + 1, 6)
             if dd[i, j] < 1.2 and sym[i] != sym[j]]
    assert len(bonds) == 4 and abs(max(bonds) - 0.9572) < 1e-3, "4 条 O-H 键长不对"
    inter = [dd[i, j] for i in range(3) for j in range(3, 6)]
    assert min(inter) > 1.8, f"片间最短非键 {min(inter):.3f} Å 是非物理塌缩"


@pytest.mark.slow
def test_matches_pyscf_native_kernel(dimer):
    """E_NLC 总量必须落在 PySCF 原生核上；level 0 只允许粗网格表示误差。"""
    from pyscf.dft import numint
    mf, X, W, rho, sig = partition.scf_grid(dimer, xc="wb97x_v", level=0, basis=BASIS)
    b, C = mf._numint.nlc_coeff("wb97x_v")[0][0]
    res = nlc.fragment_decomposition(X, W, rho, sig, geomlib.FRAGS["(H2O)2"],
                                     b=b, C=C, owner=partition.nearest_partition(dimer, X))
    _, e_ref, _ = numint.nr_nlc_vxc(mf._numint, dimer, mf.grids, "wb97x_v",
                                    mf.make_rdm1())
    # 0.10 kcal/mol 是从"当年写测试时没量过残差"来的，实测残差最大 9.672e-06 kcal/mol
    # （`test_tolerance_probe.py`，level 0/1/2 三档），比它紧 1.03e4 倍的界才是有依据的界。
    # 1e-4 留 10 倍余量给浮点与 PySCF 版本差异。**这是同一个库里两套实现的对照**，
    # 不是第二个程序——独立程序的锚点在 ORCA 6.0.1，见 §4 与 logs/orca_anchor.json。
    assert abs((res["E_total"] - e_ref) * KCAL) < 1e-4


@pytest.mark.slow
def test_pair_terms_regression(dimer):
    """冻结密度片间项与方案跨度：数值来自本包，作用是拦住改动引入的漂移。"""
    from pyscf.dft import numint
    mf, X, W, rho, sig = partition.scf_grid(dimer, xc="wb97x_v", level=0, basis=BASIS)
    b, C = mf._numint.nlc_coeff("wb97x_v")[0][0]
    vals = {}
    for scheme in ("becke", "becke-becke-rad", "becke-treutler", "stratmann"):
        co, we, owner = partition.atom_partition(dimer, level=0, scheme=scheme)
        ao = mf._numint.eval_ao(dimer, co, deriv=1)
        r = mf._numint.eval_rho(dimer, ao, mf.make_rdm1(), xctype="GGA")
        s = r[1] ** 2 + r[2] ** 2 + r[3] ** 2
        res = nlc.fragment_decomposition(co, we, r[0], s, geomlib.FRAGS["(H2O)2"],
                                         b=b, C=C, owner=owner)
        vals[scheme] = res["inter"][(0, 1)] * KCAL
        assert abs(res["intra"][0] + res["intra"][1] + res["inter"][(0, 1)]
                   - res["E_nl"]) < 1e-10          # 可加性
    assert vals["becke"] == pytest.approx(-0.5316, abs=0.02)
    span = max(vals.values()) - min(vals.values())
    assert 0.01 < span < 0.10, f"方案跨度 {span:.4f} 出界，归属敏感性需重新评估"
