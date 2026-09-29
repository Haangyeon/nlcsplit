"""partition_factors 的一致性自检：归一性 + 复现 PySCF 自己的 partition 权重。

比对对象是 gen_grid.get_partition 的输出（PySCF 的 C 核 VXCgen_grid），
不是本仓库的任何实现 —— 这是外部锚。
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pyscf import gto                          # noqa: E402
from nlcsplit import geomlib, partition        # noqa: E402

H2O2 = gto.M(atom=geomlib.h2o_dimer(), basis="6-31g*", unit="Angstrom", verbose=0)
BENZ = gto.M(atom=geomlib.benzene_sandwich(), basis="6-31g*", unit="Angstrom", verbose=0)
SCHEMES = sorted(partition.SCHEMES)


@pytest.mark.parametrize("mol", [H2O2, BENZ], ids=["h2o2", "benzene"])
@pytest.mark.parametrize("scheme", SCHEMES)
def test_level0_factors_match_pyscf_weights(mol, scheme):
    coords, base_w, S = partition.partition_factors(mol, level=0, scheme=scheme)
    c_ref, w_ref, owner = partition.atom_partition(mol, level=0, scheme=scheme)

    assert np.array_equal(coords, c_ref)
    assert S.shape == (len(coords), mol.natm)
    assert np.abs(S.sum(axis=1) - 1.0).max() < 1e-12
    assert np.all(S >= -1e-14)
    # owner 那一列乘回原始体积元，必须逐点等于 PySCF 给 get_partition 的权重
    soft = base_w * S[np.arange(len(owner)), owner]
    assert np.abs(soft - w_ref).max() < 1e-11
    assert np.abs(soft - w_ref).sum() / base_w.sum() < 1e-14


@pytest.mark.slow
@pytest.mark.parametrize("scheme", SCHEMES)
@pytest.mark.parametrize("level", [1, 2])
def test_higher_levels(scheme, level):
    coords, base_w, S = partition.partition_factors(H2O2, level=level, scheme=scheme)
    _, w_ref, owner = partition.atom_partition(H2O2, level=level, scheme=scheme)
    assert np.abs(base_w * S[np.arange(len(owner)), owner] - w_ref).max() < 1e-11


def test_soft_and_hard_are_different_reads():
    """owner 硬指派只是取了 S 的一列；跨片点上的软归属确实非零。
    若这条不成立，local term 就不存在两种口径，API 也白加。"""
    mol = H2O2
    coords, base_w, S = partition.partition_factors(mol, level=0, scheme="becke")
    _, _, owner = partition.atom_partition(mol, level=0, scheme="becke")
    # 网格按原子分块生成，[0,2,3] 是受体那块子网格的点（不是原子序号）
    acceptor = np.isin(owner, [3, 4, 5])
    assert S[acceptor, 0].max() > 1e-6                     # 供体 O 在受体子网格上非零
    assert (base_w[acceptor] * S[acceptor, 0]).sum() > 1e-4
    # 归一性推到积分：Σ_a ∫s_a·1 == Σ_i base_w_i == 全体点权
    assert abs((base_w[:, None] * S).sum() - base_w.sum()) < 1e-9 * abs(base_w.sum())


def test_unknown_scheme_raises():
    with pytest.raises(KeyError):
        partition.partition_matrix(H2O2, np.zeros((1, 3)), scheme="nope")
    with pytest.raises(KeyError):
        partition.partition_factors(H2O2, level=0, scheme="nope")
