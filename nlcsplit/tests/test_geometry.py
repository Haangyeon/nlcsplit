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


def _ring_metrics(atoms, frags):
    ring = []
    for f in frags:
        pts = [np.array(atoms[i][1]) for i in f if atoms[i][0] == "C"]
        assert len(pts) == 6, f"每片应有 6 个碳，实得 {len(pts)}"
        cen = sum(pts) / 6.0
        X = np.array([p - cen for p in pts])
        # 法向 = 最小奇异值对应的右奇异向量（环是平面的，两弦叉积也够，但 SVD 不依赖选哪两条弦）
        _, sv, vt = np.linalg.svd(X, full_matrices=False)
        n = vt[2] / np.linalg.norm(vt[2])
        # 官方 S22 的碳环不是数值意义上严格平面：实测面外残差 1.63e-3 Å（A）与 5.49e-4 Å（B）。
        # 所以这里用 5e-3 Å 的宽容差——它的任务是"若文件被换成非平面/被改坏就报"，不是重新优化几何。
        assert sv[2] < 5e-3, f"苯环面外残差 {sv[2]:.2e} Å，几何文件不像苯环"
        ring.append((cen, n))
    (c1, n1), (c2, n2) = ring
    cv = c2 - c1
    along = float(cv @ n1)
    lateral = float(np.linalg.norm(cv - along * n1))
    ang = float(np.degrees(np.arccos(min(1.0, abs(float(n1 @ n2))))))
    return float(np.linalg.norm(cv)), ang, abs(along), lateral


def test_benzene_dimer_geometries_are_the_two_named_kinds():
    """正文把 S22 的两个苯二聚体分别叫"平行位移(A)"与"T 型(B)"，这句必须由坐标背书。

    动机（2026-10-05 复查）：§3.2 一度把 (A) 叫 sandwich、(B) 叫 parallel-displaced，
    而量出来 (A) 的环面夹角 0.0 度、平面内滑移 1.698 Å——那是平行位移，不是夹心；
    (B) 夹角 90.0 度——那是 T 型。真正的夹心是我们自己构造的 `benzene_sandwich(d=3.81)`，
    滑移为 0，它是**第三个**几何。名字与几何一旦错位，审稿人只要量一次坐标就能抓住，
    所以这里钉死：换 S22 文件、改索引或改构造参数都会立刻失败。
    """
    import os
    d = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                     "scratch", "lit", "s22")
    if not os.path.isdir(d):
        pytest.skip("S22 官方几何未取回（跑 nlcsplit/tools/get_s22.sh）")
    # (A) = S22_11：面对面、有滑移
    atoms, frags = geomlib.s22_system("苯二聚体(A)", d)
    dist, ang, layer, slip = _ring_metrics(atoms, frags)
    assert ang < 5.0, f"(A) 环面夹角 {ang:.1f} 度，不是面对面堆积"
    assert slip > 1.0, f"(A) 平面内滑移仅 {slip:.3f} Å，那是夹心而不是平行位移"
    assert 2.8 < layer < 4.0, f"(A) 层距 {layer:.3f} Å 不在 π 堆积范围"
    # (B) = S22_20：T 型
    atoms, frags = geomlib.s22_system("苯二聚体(B)", d)
    dist2, ang2, layer2, slip2 = _ring_metrics(atoms, frags)
    assert ang2 > 80.0, f"(B) 环面夹角 {ang2:.1f} 度，不是 T 型"
    # 构造的夹心必须是第三个几何：滑移为 0，不能与前两者混用
    sb = geomlib.benzene_sandwich()
    fr = geomlib.FRAGS["(C6H6)2"]
    d3, ang3, layer3, slip3 = _ring_metrics(sb, fr)
    assert ang3 < 5.0 and slip3 < 1e-6, f"构造夹心滑移 {slip3:.3f} Å，已不是夹心"
    assert abs(layer3 - 3.81) < 1e-6, f"构造夹心层距 {layer3:.3f}，与 d=3.81 不符"


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
