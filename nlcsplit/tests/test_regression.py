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
                                         b=b, C=C, owner=owner, closure_check=True)
        vals[scheme] = res["inter"][(0, 1)] * KCAL
        # 这里的参照是"同一批保留点不切片段一次算完"，不是分块和的别名：
        # 早先那条断言拿 E_nl 比它自己的定义式，恒真、永不触发。
        assert res["E_nl"] == pytest.approx(res["E_nl_ref"], rel=1e-12, abs=0.0)
    assert vals["becke"] == pytest.approx(-0.5316, abs=0.02)
    span = max(vals.values()) - min(vals.values())
    assert 0.01 < span < 0.10, f"方案跨度 {span:.4f} 出界，归属敏感性需重新评估"


def test_counterpoise_honours_the_callers_basis(monkeypatch):
    """反泊松的鬼单体必须建在**传进来的那个复合物**的基组上。

    2026-10-03 的真实失败：调用方用 aug-cc-pvdz 建复合物，`counterpoise()` 却按模块默认
    BASIS(=NCBAS=6-31g*) 搭鬼单体，函数自己那句维数断言当场把 <CLUSTER> 作业打死。这里复合物
    故意用比模块默认更大的基组：修复前它抛 AssertionError，修复后走通且基组确实传下去了。
    """
    from pyscf import gto
    from nlcsplit import step_h_s22 as H

    monkeypatch.setattr(H, "BASIS", "6-31g*")            # 模块默认，与复合物故意不同
    atom = ("O 0 0 0.66; H 0 0.77 -0.16; H 0 -0.77 -0.16; "
            "O 0 2.98 0.0; H 0 3.3 0.89; H 0.94 3.3 -0.4")
    mol = gto.M(atom=atom, basis="aug-cc-pvdz", unit="Angstrom", verbose=0)

    asked = []
    real_M = gto.M

    def spy(*a, **kw):
        asked.append(kw.get("basis"))
        return real_M(*a, **kw)

    class FakeMF:
        class _G:
            level = 0

        def __init__(self, sub):
            self.sub, self.converged, self.e_tot, self.xc = sub, True, -76.4, ""
            self.grids = self._G()

        def kernel(self):
            return self.e_tot

    monkeypatch.setattr(H.gto, "M", spy)
    monkeypatch.setattr(H.dft, "RKS", FakeMF)
    monkeypatch.setattr(H, "terms", lambda m, lv, tag: {"e_tot": -152.9})
    H.counterpoise(mol, [[0, 1, 2], [3, 4, 5]], 0)
    assert mol.nao_nr() == 82, "前提变了：aug-cc-pVDZ 的水二聚体不再是 82 AO"
    assert set(asked) == {"aug-cc-pvdz"}, f"鬼单体拿到基组 {set(asked)}，复合物基组没传下去"
