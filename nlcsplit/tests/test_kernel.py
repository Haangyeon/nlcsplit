"""核与分解的单元测试：不跑自洽场，用合成网格点，秒级完成。

独立性要求：`naive_pair` 用最笨的三重循环直接算 R² 和双重和，
与 `nlc.pair_energy` 的 gemm 化实现结构上无关；两者逐位对照才谈得上验证。
"""
import numpy as np
import pytest

from nlcsplit import nlc


def naive_pair(coords, wr, w0, kap, iA, iB, pairing="same-centre"):
    """朴素双重循环参照实现（O(N_A·N_B) 但走 python 循环，只用于小样本对照）。"""
    s = 0.0
    for i in iA:
        for j in iB:
            r2 = float(np.sum((coords[i] - coords[j]) ** 2))
            if pairing == "same-centre":
                g = w0[i] * r2 + kap[i]
                gp = w0[j] * r2 + kap[j]
            else:
                g = w0[j] * r2 + kap[i]
                gp = w0[i] * r2 + kap[j]
            s += wr[i] * wr[j] * (-1.5 / (g * gp * (g + gp)))
    return 0.5 * s


@pytest.fixture
def toy():
    rng = np.random.default_rng(20260929)
    coords = rng.normal(scale=1.5, size=(9, 3))
    rho = np.abs(rng.normal(scale=0.4, size=9)) + 1e-3
    sigma = np.abs(rng.normal(scale=0.3, size=9))
    w0, kap, keep = nlc.vv10_fields(rho, sigma, b=6.0, C=0.01)
    weights = np.ones(9) / 9
    return coords, weights * rho, w0, kap, keep


def test_fast_matches_naive_bit_for_bit(toy):
    X, wr, w0, kap, _ = toy
    iA, iB = np.arange(0, 5), np.arange(3, 9)
    fast = nlc.pair_energy(X, wr, w0, kap, iA, iB, block=2)
    ref = naive_pair(X, wr, w0, kap, iA, iB)
    assert fast == pytest.approx(ref, rel=1e-13, abs=0.0)


def test_cross_pairing_is_a_different_number(toy):
    """同中心与交叉配对必须给出不同的值——否则这条判别等于没测。"""
    X, wr, w0, kap, _ = toy
    iA, iB = np.arange(0, 5), np.arange(3, 9)
    same = nlc.pair_energy(X, wr, w0, kap, iA, iB, pairing="same-centre")
    cross = nlc.pair_energy(X, wr, w0, kap, iA, iB, pairing="cross")
    assert same != cross and abs(same - cross) / abs(same) > 1e-6


def test_wB_equivalent_to_index_split(toy):
    """wB= 传两套归属权重时应等于按索引切分（软分区靠这条复用同一条 gemm 路径）。

    Φ 在同中心配对下对 (i,j) 对称，而 fA 只在 iA 非零、fB 只在 iB 非零，
    所以全网格和只余下 A×B 这一块 ⇒ 两者应严格相等，不是两倍关系。
    """
    X, wr, w0, kap, _ = toy
    iA, iB = np.arange(0, 5), np.arange(3, 9)
    allr = np.arange(len(X))
    fA = np.zeros(len(X)); fA[iA] = 0.7
    fB = np.zeros(len(X)); fB[iB] = 0.35
    direct = nlc.pair_energy(X, wr * fA, w0, kap, iA, iB, wB=wr * fB)
    full = nlc.pair_energy(X, wr * fA, w0, kap, allr, allr, wB=wr * fB)
    assert full == pytest.approx(direct, rel=1e-12, abs=0.0)


def test_local_term_is_beta_times_nelec(toy):
    X, wr, w0, kap, _ = toy
    beta = (1.0 / 32.0) * (3.0 / 36.0) ** nlc.BETA_EXP
    assert nlc.local_term(beta, wr) == pytest.approx(beta * wr.sum(), rel=1e-15)


def test_rho_floor_drops_low_density_points():
    rho = np.array([1e-20, 1e-3, 5e-1, 1e-20])
    sigma = np.array([1e-8, 1e-3, 1e-2, 1e-8])
    w0, kap, keep = nlc.vv10_fields(rho, sigma, b=6.0, C=0.01, rho_floor=1e-12)
    assert list(keep) == [False, True, True, False]
    assert np.all(np.isfinite(w0)) and np.all(np.isfinite(kap))
