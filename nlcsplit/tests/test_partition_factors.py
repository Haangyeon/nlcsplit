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


def test_soft_attribution_owner_masked_matches_analytic_gaussian():
    """base_w 的拼接点表把空间覆盖 natm 次；软归属必须按 owner 掩膜。

    外部锚是解析积分：h =  centre=(0,0,0.2) 的单位高斯，∫h d³r = pi^{3/2}。
    PySCF 自己的权重对同一个 h 给到解析值 1e-6 以内，所以"按 owner 掩膜后对 a
    求和 == PySCF 总权重积分"是可判的；不掩膜（`Σ base_w·S[:,a]·h`）则在 level 1
    偏 7.4%、level 3 偏 -0.3%，说明它连一个常数倍都不是，不能靠除以 natm 修。
    """
    mol = H2O2
    natm = mol.natm
    centre = np.array([0.0, 0.0, 0.2])
    exact = np.pi ** 1.5
    for level in (1, 2, 3):
        coords, base_w, S = partition.partition_factors(mol, level=level, scheme="becke")
        _, w_ref, owner = partition.atom_partition(mol, level=level, scheme="becke")
        h = np.exp(-np.sum((coords - centre) ** 2, axis=1))

        masked = np.array([(base_w[owner == a] * S[owner == a, a] * h[owner == a]).sum()
                           for a in range(natm)])
        assert abs(masked.sum() - exact) / exact < 2e-5, (
            f"level {level}: owner 掩膜软归属按片段加回 {masked.sum():.6f}，"
            f"解析值 {exact:.6f}")
        # 与 PySCF 总权重积分同口径（同一批点、同一个 h）
        assert abs(masked.sum() - (w_ref * h).sum()) / exact < 2e-5

        naive = ((base_w[:, None] * S) * h[:, None]).sum(axis=0)
        assert abs(naive.sum() / (natm * (w_ref * h).sum()) - 1.0) < 0.10
        assert abs(naive.sum() / masked.sum() - natm) < 0.10 * natm
        # 逐片段：不掩膜的配方在粗网格上偏到百分之十几，不是"差一个 natm 因子"
        assert np.max(np.abs(naive / natm - masked) / np.maximum(np.abs(masked), 1e-12)) > 0.01


def test_base_w_on_real_density_is_not_a_measure_at_all():
    """把上一条的光滑函数换成真实密度 ρ：多算的倍率根本不是一个常数。

    锚同样是外部的：Σ w_pyscf·ρ 必须回到电子数（PySCF 自己的权重做这件事），而
    Σ base_w·ρ 在水二聚体 level 0/1/2/3 上实测是 100.19 / 690.26 / 279.08 / 94.75
    个"电子"（ne=20），即隐含倍率 5.01 / 34.5 / 14.0 / 4.74 —— 非单调、也不收敛到
    natm=6。所以"除以原子数"这类补丁在这里错得更远（6 倍 vs 34.5 倍）。
    这条测试存在的意义：光滑高斯上的 7% 偏差会让人误以为找到了规律。
    """
    pytest.importorskip("pyscf")
    from pyscf import gto
    mol = gto.M(atom=geomlib.h2o_dimer(), basis="6-31g*", unit="Angstrom", verbose=0)
    mf, _, _, _, _ = partition.scf_grid(mol, level=1)
    coords, base_w, S = partition.partition_factors(mol, level=1, scheme="becke")
    _, w_ref, owner = partition.atom_partition(mol, level=1, scheme="becke")
    ao = mf._numint.eval_ao(mol, coords, deriv=1)
    rho = mf._numint.eval_rho(mol, ao, mf.make_rdm1(), xctype="GGA")[0]

    ne = mol.nelectron
    assert abs(float((w_ref * rho).sum()) - ne) / ne < 1e-4        # 外部锚：PySCF 权重
    assert abs(float((base_w * rho).sum()) / ne - mol.natm) > 1.0  # 拼接测度：错一个量级
    masked = sum(float((base_w[owner == a] * S[owner == a, a] * rho[owner == a]).sum())
                 for a in range(mol.natm))
    assert abs(masked - ne) / ne < 1e-4                            # 掩膜写法可锚
    assert abs(float((base_w * rho).sum()) / masked - mol.natm) > 1.0


def test_unknown_scheme_raises():
    with pytest.raises(KeyError):
        partition.partition_matrix(H2O2, np.zeros((1, 3)), scheme="nope")
    with pytest.raises(KeyError):
        partition.partition_factors(H2O2, level=0, scheme="nope")
