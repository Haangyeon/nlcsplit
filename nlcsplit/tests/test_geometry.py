"""几何真值源的内部坐标回归测试。

动机：本项目已发生两次"半角当极角"的构造错（水二聚体受体 H 朝向、NH3 的 ∠HNH
实测 88.06 度而标称 106.7 度），两次都是事后对文献才发现，代价是整批数值作废。
能闭嘴检验的量必须在构造时就验掉——这里把每个单体的键长与键角钉死。
"""
import numpy as np
import pytest

from nlcsplit import geomlib


def _d(pts, i, j):
    return float(np.linalg.norm(np.array(pts[i][1]) - np.array(pts[j][1])))


def _ang(pts, i, j, k):
    v1 = np.array(pts[i][1]) - np.array(pts[j][1])
    v2 = np.array(pts[k][1]) - np.array(pts[j][1])
    return float(np.degrees(np.arccos(v1 @ v2 / np.linalg.norm(v1) / np.linalg.norm(v2))))


def test_h2o_internal():
    p = geomlib.h2o()
    assert _d(p, 0, 1) == pytest.approx(0.9572, abs=1e-6)
    assert _d(p, 0, 2) == pytest.approx(0.9572, abs=1e-6)
    assert _ang(p, 1, 0, 2) == pytest.approx(104.52, abs=1e-3)


def test_nh3_internal():
    """三 H 方位互差 120 度时 cos∠HNH=(3cos²θ−1)/2，极角不是半角。"""
    p = geomlib.nh3()
    for k in (1, 2, 3):
        assert _d(p, 0, k) == pytest.approx(1.012, abs=1e-6)
    assert _ang(p, 1, 0, 2) == pytest.approx(106.7, abs=1e-3)
    assert _ang(p, 2, 0, 3) == pytest.approx(106.7, abs=1e-3)


def test_ch4_internal():
    p = geomlib.ch4()
    for k in (1, 2, 3, 4):
        assert _d(p, 0, k) == pytest.approx(1.087, abs=1e-6)
    assert _ang(p, 1, 0, 2) == pytest.approx(109.4712, abs=1e-3)


def test_benzene_internal():
    p = geomlib.benzene()
    assert _d(p, 0, 2) == pytest.approx(1.397, abs=1e-9)     # C–C
    assert _d(p, 0, 1) == pytest.approx(1.084, abs=1e-9)     # C–H
    assert _ang(p, 2, 0, 10) == pytest.approx(120.0, abs=1e-6)


def test_h2o_dimer_is_physical():
    """受体 H 必须背向给体：旧坐标 H···H 塌到 1.64 Å，受体角被夹成 106.4 度。"""
    p = geomlib.h2o_dimer()
    C = np.array([c for _, c in p])
    d = lambda i, j: float(np.linalg.norm(C[i] - C[j]))
    assert d(0, 3) == pytest.approx(2.983, abs=1e-6)
    assert d(3, 4) == pytest.approx(0.9572, abs=1e-6)
    assert _ang(p, 3, 4, 0) == pytest.approx(180.0, abs=1e-6)     # 线性氢键
    assert _ang(p, 1, 0, 2) == pytest.approx(104.52, abs=1e-3)    # 受体单体角没被夹
    inter = min(d(i, j) for i in (0, 1, 2) for j in (3, 4, 5))
    assert inter > 1.9, f"片间最短非键 {inter:.3f} Å，出现非物理塌缩"


def test_s22_split_is_not_contiguous():
    """官方 S22 文件原子顺序是交错的：硬写 [0,1,2],[3,4,5] 会切错片段。"""
    import os
    d = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                     "scratch", "lit", "s22")
    if not os.path.isdir(d):
        pytest.skip("S22 官方几何未取回（跑 nlcsplit/tools/get_s22.sh）")
    atoms, frags = geomlib.s22_system("水二聚体", d)
    assert frags == [[0, 2, 3], [1, 4, 5]]
    assert [s for s, _ in atoms] == ["O", "O", "H", "H", "H", "H"]
