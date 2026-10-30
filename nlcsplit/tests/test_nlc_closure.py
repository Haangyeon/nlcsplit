"""分块和 vs 一次算完：这条闭包检查必须**能**失败。

来历（2026-10-06，外部评审组方法论席 C2，我逐条开文件核实后成立）：
`nlc.fragment_decomposition` 里 `E_nl` 按定义就是 `sum(intra) + sum(inter)`，
而 `step_h_s22.py`、`step_d_floor.py`、`tests/test_regression.py` 三处断言比的正是
"这个和 减 它自己"，恒等于零、永不触发。真正独立的那次比对只在 fastpair 的通路上，
没覆盖本函数。这里补上，并且按本仓规矩配一个**必须失败**的负控——
没有负控的 PASS 不算 PASS。

用解析密度而不是跑一次 SCF：这条性质只关乎索引划分与因子 2 的记账，
与密度从哪来无关，所以合成网格更快也更可控。
"""
import numpy as np
import pytest

from nlcsplit import nlc

A = np.array([-1.6, 0.0, 0.0])
B = np.array([1.6, 0.0, 0.0])
EXPO = 1.4


def grid(n=13, step=0.55):
    k = np.arange(n) - (n - 1) / 2.0
    g = step * np.stack(np.meshgrid(k, k, k, indexing="ij"), -1).reshape(-1, 3)
    return g + np.array([0.11, -0.07, 0.05])            # 偏心，避免对称性掩盖错位


def density(g):
    ra, rb = g - A, g - B
    d2a, d2b = np.einsum("ij,ij->i", ra, ra), np.einsum("ij,ij->i", rb, rb)
    rhoa, rhob = np.exp(-EXPO * d2a), np.exp(-EXPO * d2b)
    gv = -2.0 * EXPO * (ra * rhoa[:, None] + rb * rhob[:, None])
    rho = rhoa + rhob
    sigma = np.einsum("ij,ij->i", gv, gv)
    return rho, sigma


def owner_of(g):
    return (np.linalg.norm(g - B, axis=1) < np.linalg.norm(g - A, axis=1)).astype(int)


@pytest.fixture(scope="module")
def case():
    g = grid()
    rho, sigma = density(g)
    return g, rho, sigma, owner_of(g)


def _run(owner, frags, **kw):
    g = grid()
    rho, sigma = density(g)
    w = np.full(len(g), 0.37)                            # 非均匀权重，权重漏乘会暴露
    return nlc.fragment_decomposition(g, w, rho, sigma, frags, owner=owner, **kw)


def test_closure_holds_on_a_real_partition(case):
    g, rho, sigma, owner = case
    res = _run(owner, [[0], [1]], closure_check=True)
    assert "E_nl_ref" in res, "闭包参照没算出来"
    assert res["E_nl"] == pytest.approx(res["E_nl_ref"], rel=1e-12, abs=0.0), \
        f"分块和 {res['E_nl']!r} 与一次算完 {res['E_nl_ref']!r} 不符"


def test_default_off_costs_nothing(case):
    g, rho, sigma, owner = case
    res = _run(owner, [[0], [1]])
    assert "E_nl_ref" not in res, "默认路径不该付这次双份求和的钱"


def test_negative_control_dropped_fragment_must_raise(case):
    """把第二个片段整个扔掉：块和少了一整块，闭包检查必须当场炸。

    这条是整个测试的意义所在。若它不抛，说明检查还是恒真的，上面那个 PASS 一文不值。
    """
    g, rho, sigma, owner = case
    with pytest.raises(AssertionError, match="片段索引或因子"):
        _run(owner, [[0]], closure_check=True)


def test_negative_control_regroupings_must_differ_from_reference(case):
    """漏计与重计交叉项，都必须与独立参照对不上。

    上一版这里写的是 `intra[0] + inter` 再求和，代数上恒等于 E_nl，比的是同一个量的
    两种求和顺序——那是一条永远不会失败的检查，恰好是本文件要消灭的东西。
    现在以 E_nl_ref 为准绳，把交叉项加两次、或干脆不加。
    """
    g, rho, sigma, owner = case
    res = _run(owner, [[0], [1]], closure_check=True)
    ref = res["E_nl_ref"]
    inter = res["inter"][(0, 1)]
    over = sum(res["intra"].values()) + 2.0 * inter      # 交叉项重复计一份
    under = sum(res["intra"].values())                   # 交叉项整个漏掉
    assert abs(over - ref) > 1e-9 * abs(ref), "重复计交叉项没看出来"
    assert abs(under - ref) > 1e-9 * abs(ref), "漏计交叉项没看出来"
    assert abs(sum(res["intra"].values()) + inter - ref) < 1e-9 * abs(ref), \
        "正确的那个分组反而对不上参照了"


def test_soft_partition_closures_too(case):
    g, rho, sigma, owner = case
    n = len(g)
    s0 = 1.0 / (1.0 + np.exp(-2.0 * (g[:, 0] - 0.0)))
    soft = np.vstack([s0, 1.0 - s0])
    assert abs(soft.sum(axis=0) - 1.0).max() < 1e-12
    w = np.full(n, 0.37)
    r1, r2 = density(g)
    res = nlc.fragment_decomposition(g, w, r1, r2, [[0], [1]], soft=soft,
                                     closure_check=True)
    assert res["E_nl"] == pytest.approx(res["E_nl_ref"], rel=1e-11, abs=0.0)
