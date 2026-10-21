"""归属证书的自检：退化判据必须**真的会响**，界必须与逐方案读数自洽。

为什么着重负控：一个坏构造（权重退化成 1/natm，或某个片段独占全部测度）在数值上不留痕迹——
每点求和仍是 1，`fragment_decomposition` 的归一化门也照过，界照样印得出来。
所以"证书"这个交付物的全部风险都在**它会不会把坏构造洗白**，
这条测试存在的意义就是让"洗白"变成一次失败。
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pyscf import gto                              # noqa: E402
import nlcsplit                                    # noqa: E402
from nlcsplit import certificate, geomlib, partition   # noqa: E402

NATM, NPTS = 4, 50


def _kinds(S, name="x", seen=None):
    flags, _fp = certificate.degeneracy_flags(S, name, seen)
    return [f["kind"] for f in flags]


def test_good_localized_matrix_is_not_flagged():
    """先证明判据不是一见就响的摆设：一个正常的软归属必须零标记。"""
    S = np.full((NATM, NPTS), 0.25)
    S[0] += 0.35
    S[1] += 0.20
    S[2] -= 0.30
    S[3] -= 0.45
    S = np.clip(S, 0.0, None)
    S /= S.sum(axis=0)
    flags, fp = certificate.degeneracy_flags(S, "ok")
    assert flags == []
    assert fp


def test_uniform_matrix_is_caught():
    """历史缺陷指纹：自由原子全建在原点 ⇒ 逐点恰好 1/natm，每点和仍是 1。"""
    S = np.full((NATM, NPTS), 1.0 / NATM)
    assert "uniform-degenerate" in _kinds(S)


def test_single_fragment_capture_is_caught():
    S = np.zeros((NATM, NPTS))
    S[0] = 1.0
    assert "single-fragment-capture" in _kinds(S)


def test_unnormalized_matrix_is_caught():
    S = np.full((NATM, NPTS), 0.5 / NATM)
    assert "not-normalized" in _kinds(S)


def test_two_names_with_identical_matrix_are_caught():
    """分派参数被吃掉时，两个不同名构造会给出逐位相同的矩阵。"""
    S = np.tile(np.array([[0.7], [0.3], [0.0], [0.0]]), (1, NPTS))
    seen = {}
    f1, fp1 = certificate.degeneracy_flags(S, "becke", seen)
    seen["becke"] = fp1
    f2, fp2 = certificate.degeneracy_flags(S * 1.0, "voronoi", seen)
    assert [f["kind"] for f in f1] == []
    assert any(f["kind"] == "identical-to-other-scheme" for f in f2)


def test_matrix_shape_is_enforced():
    with pytest.raises(ValueError):
        certificate.degeneracy_flags(np.ones(NPTS), "flat")


def test_certify_rejects_sets_that_cannot_form_a_contrast():
    mol = gto.M(atom=geomlib.h2o_dimer(), basis="6-31g*", unit="Angstrom", verbose=0)
    frags = [[0, 1, 2], [3, 4, 5]]
    with pytest.raises(ValueError):
        certificate.certify(mol, frags, schemes=["becke"])          # 一个方案不配叫上下界
    with pytest.raises(ValueError):
        certificate.certify(mol, [[0, 1, 2, 3, 4, 5]])              # 单片段没有片间项
    with pytest.raises(ValueError):
        certificate.certify(mol, [[0, 1, 2], []])                   # 空片段
    with pytest.raises(KeyError):
        certificate.certify(mol, frags, schemes=["becke", "nope"])  # 未知且没给自定义矩阵


def test_entry_point_is_callable_from_package_root():
    assert nlcsplit.certify is certificate.certify
    assert "certify" in nlcsplit.__all__


@pytest.mark.slow
def test_certificate_on_water_dimer_level0():
    """端到端：六个构造在同一批点上各给一个 E_AB，界取最值，且总 NLC 不随归属变。

    最后那条是本件唯一的外部锚：`fragment_decomposition` 的分块按定义覆盖全域且互不重叠，
    所以 E_nl 必须逐方案相同（实测差异在机器精度上）。如果某个方案的权重没有真正归一，
    变的是总量而不是分块 —— 只看 E_AB 是看不出来的。
    """
    mol = gto.M(atom=geomlib.h2o_dimer(), basis="6-31g*", unit="Angstrom", verbose=0)
    frags = [[0, 1, 2], [3, 4, 5]]
    schemes = ["becke", "becke-treutler", "stratmann", "voronoi"]
    r = certificate.certify(mol, frags, level=0, schemes=schemes)
    assert r["flagged"] == []
    assert r["usable"] == schemes
    enl = [r["per_scheme"][s]["E_nl"] for s in schemes]
    assert abs(max(enl) - min(enl)) / abs(enl[0]) < 1e-12
    eab = {s: r["per_scheme"][s]["E_ab"][(0, 1)] for s in schemes}
    b = r["bounds"][(0, 1)]
    assert b["lo"] == min(eab.values()) and b["hi"] == max(eab.values())
    assert b["span"] == pytest.approx(b["hi"] - b["lo"], rel=1e-12)
    assert b["argmin"] in schemes and b["argmax"] in schemes
    assert b["span"] > 1e-4                       # 界若为 0，说明分派根本没生效


@pytest.mark.slow
def test_negative_control_uniform_construction_gets_no_certificate():
    """故意把一个退化构造混进方案集：它必须被标记、不进界，而且**不能**让界退化成 0。

    如果实现只是"把退化方案的值也纳入 min/max"，那证书会因为均匀权重那个数恰好居中
    而照发不误；更糟的是可用方案被剔到只剩一个时若给 span=0，会被读成"没有归属歧义"。
    """
    mol = gto.M(atom=geomlib.h2o_dimer(), basis="6-31g*", unit="Angstrom", verbose=0)
    frags = [[0, 1, 2], [3, 4, 5]]
    # 网格点数只有跑过才知道，所以先拿一次正常证书取 npts，再用它造退化矩阵。
    base = certificate.certify(mol, frags, level=0, schemes=["becke", "voronoi"])
    npts = base["meta"]["npts"]
    unif = np.full((mol.natm, npts), 1.0 / mol.natm)
    r = certificate.certify(mol, frags, level=0, schemes=["becke", "uniform"],
                            extra_soft={"uniform": unif})
    kinds = {(f["scheme"], f["kind"]) for f in r["flagged"]}
    assert ("uniform", "uniform-degenerate") in kinds
    assert r["usable"] == ["becke"]
    b = r["bounds"][(0, 1)]
    assert b["span"] is None and b["lo"] is None
    assert "少于两个" in b["detail"]
