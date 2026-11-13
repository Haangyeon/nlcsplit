"""家族外归属构造（Voronoi / Hirshfeld）的自检。

这些函数是 `scheme_factors()` 这一个入口下最后两个分支（家族内四个 + 家族外两个 = 六个），
也是正文跨构造那一列的包内路径，所以它们必须被随包发布的那套测试覆盖
—— 否则 wheel 里装的是一个没人跑过的新分支。

判据一律不拿本仓自己的实现当锚：Voronoi 对 `nearest_partition`（PySCF 之外的几何事实），
Hirshfeld 对"权重退化 = 1/natm"这个已知错误指纹的反面（有一版把全部自由原子建在原点，
权重退化成均匀，片间块恰好等于总量的一半 —— 那是构造错的指纹不是物理结果）。
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pyscf import gto                          # noqa: E402
from nlcsplit import partition                 # noqa: E402

# 异核双原子：两个元素的自由原子基态多重度都在 FREE_ATOM_MULT 表里，
# 而且同核会把"权重接反"这类错误变成不可见（对称时 A 与 B 无法区分）。
DIATOMIC = gto.M(atom="C 0 0 0; O 0 0 1.128", basis="6-31g*", unit="Angstrom", verbose=0)
NORM_TOL = 1e-12       # 与 partition._NORM_TOL 同值：判据必须与实现里那条是同一个数
DEGENERATE = 1.0 / DIATOMIC.natm               # 自由原子建错位置时的退化值

CO, _BASE_W, _S0 = partition.partition_factors(DIATOMIC, level=0, scheme="becke")
OWNER = partition.nearest_partition(DIATOMIC, CO)
IDX = np.arange(len(CO))


def test_scheme_table_splits_into_family_and_cross_family():
    assert partition.CROSS_FAMILY_SCHEMES == ("voronoi", "hirshfeld")
    assert set(partition.CROSS_FAMILY_SCHEMES).isdisjoint(partition.SCHEMES)
    assert list(partition.ALL_SCHEMES) == list(partition.SCHEMES) + list(
        partition.CROSS_FAMILY_SCHEMES)


def test_voronoi_is_hard_assignment_not_a_soft_one():
    S = partition.voronoi_factors(DIATOMIC, CO)
    assert S.shape == (DIATOMIC.natm, len(CO))
    assert np.abs(S.sum(axis=0) - 1.0).max() < NORM_TOL
    assert set(np.unique(S)) <= {0.0, 1.0}
    # 外部锚：one-hot 的 argmax 必须逐点等于最近原子硬指派
    assert np.array_equal(S.argmax(axis=0), OWNER)


def test_hirshfeld_is_normalized_and_not_degenerate():
    S, S_alt, n_zero = partition.hirshfeld_factors(DIATOMIC, CO)
    assert S.shape == (DIATOMIC.natm, len(CO))
    assert np.abs(S.sum(axis=0) - 1.0).max() < NORM_TOL
    assert S.min() >= -1e-14 and S.max() <= 1.0 + 1e-14
    assert n_zero == 0 and S_alt is None
    own = S[OWNER, IDX]
    # 退化指纹是逐点恰好 1/natm；真把自由原子放回自己中心上，owner 那一列在大多数点上占优。
    assert own.mean() > DEGENERATE + 0.15
    assert (own >= 0.9).mean() > 0.5
    assert (own >= 0.5).mean() > 0.8


def test_dispatcher_actually_routes_cross_family_schemes():
    """`scheme_factors` 若把 scheme 参数吃掉、退回家族内默认，读数照样归一、照样能跑，
    只有拿另一种构造去比才看得出它是同一个东西 —— 所以这条比对是必须的。"""
    becke = partition.scheme_factors(DIATOMIC, CO, scheme="becke")
    voro = partition.scheme_factors(DIATOMIC, CO, scheme="voronoi")
    hirs = partition.scheme_factors(DIATOMIC, CO, scheme="hirshfeld")
    for name, S in (("voronoi", voro), ("hirshfeld", hirs)):
        assert np.abs(S.sum(axis=0) - 1.0).max() < NORM_TOL, name
    assert np.abs(voro - becke).max() > 1e-3
    assert np.abs(hirs - becke).max() > 1e-3
    assert np.abs(hirs - voro).max() > 1e-3
    # Voronoi 经 dispatcher 与直接调用必须逐位相同（分派没插第二道归一化）
    assert np.array_equal(voro, partition.voronoi_factors(DIATOMIC, CO))


def test_unknown_scheme_lists_all_six_names():
    with pytest.raises(KeyError) as exc:
        partition.scheme_factors(DIATOMIC, CO, scheme="nope")
    msg = str(exc.value)
    for s in partition.ALL_SCHEMES:
        assert s in msg
