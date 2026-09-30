"""A2a 的独立验算：界真的是界（L1）、细化不毁掉接受判据（MAC 的全部依据）、
τ→0 回到精确值（L4）、同网格一次性求和恒等式、以及 ×2 只施加一次。

裁判是外部锚点。本文件**不 import** ide-qoder 的 `fastpair_ide.py`。

⚠ 锚点必须同网格：`partition.scf_grid(level=1)` 与 `partition.atom_partition(level=1)`
在水平二聚体上给的是**不同点数**（实测 18368 vs 19936），所以 `step_f.terms()` 那条路
不能拿来当逐位对照 —— 差的是网格，不是算法。这里用同样架在 atom_partition 网格上的
`nlc.pair_energy(idx, idx)` / `nlc.fragment_decomposition` 作锚。

前四条不需要 SCF（合成夹具），因为它们测的是**定理本身**：界不成立时不该等到
几分钟的 SCF 之后才炸。需要 SCF 的一律 `@pytest.mark.slow`，且共用一个模块级
fixture —— 水二聚体 lvl1 的 SCF 一次 57 s，原来那版每条测试各跑一次，光这点就
白花十分钟。

跑法：在仓库根执行 `python3 -m pytest nlcsplit/tests/test_fastpair.py -q -s`
"""
import os
import sys

import numpy as np
import pytest
from pyscf import gto

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from nlcsplit import fastpair, geomlib, nlc, partition        # noqa: E402
from nlcsplit.step_f_dispersion import BASIS                  # noqa: E402

KCAL = 627.50947400
BOHR = 1.8897261254


# ---------------------------------------------------------------- 合成夹具
def _synthetic(npts=400, seed=0, natm=3):
    """一套满足 same-centre 核口径的随机场：rho>0、sigma>=0、求积权重>0。

    界的成立与否只依赖这三条符号条件和 |Phi| 对 g、g' 的单调性，不依赖密度是从
    哪个波函数来的——所以这里可以不调 PySCF 就把定理本身打一遍。
    """
    rng = np.random.default_rng(seed)
    coords = rng.normal(scale=4.0, size=(npts, 3))
    rho = np.exp(rng.normal(scale=1.5, size=npts)) * 1e-3
    sig = np.abs(rng.normal(size=npts)) * 1e-2
    weights = rng.uniform(1e-4, 1e-3, size=npts)
    w0, kap, keep = nlc.vv10_fields(rho, sig, b=6.0, C=0.01)
    idx = np.flatnonzero(keep)
    owner = rng.integers(0, natm, size=npts)
    return coords, weights * rho, w0, kap, idx, owner


def test_node_bound_dominates_pair_energy_on_synthetic_fields():
    """L1 的内核：任意两个子集上，证得界 ≥ |pair_energy| 的实际值。随机 200 组。"""
    coords, wr, w0, kap, idx, _ = _synthetic()
    worst = 0.0
    rng = np.random.default_rng(1)
    for trial in range(200):
        nA = int(rng.integers(3, idx.size // 2))
        nB = int(rng.integers(3, idx.size // 2))
        A = fastpair._node(coords, wr, w0, kap, rng.choice(idx, nA, replace=False))
        B = fastpair._node(coords, wr, w0, kap, rng.choice(idx, nB, replace=False))
        actual = abs(float(nlc.pair_energy(coords, wr, w0, kap, A.idx, B.idx)))
        bound = fastpair.node_bound(A, B)
        assert bound >= actual - 1e-18, f"trial {trial}: 界 {bound:.3e} < 实际 {actual:.3e}"
        worst = max(worst, bound / max(actual, 1e-300))
    print(f"\n  合成场：界/实际 最坏比值 {worst:.1f}x（200 组随机子集，全部成立）")


def test_ball_bound_can_lose_monotonicity_under_refinement():
    """为什么 D 必须来自**盒**：质心+最大半径的球在细化下可以给出更大的界。

    构造是可手算的。A = 四个等质量点在 (0,0),(10,0),(0,10),(10,10)：质心 (5,5)、
    半径 sqrt(50)=7.071，球伸到 x=12.07。B = 单点在 (20,5)。
        球版父对 D = 15 - 7.071 = 7.929
    取子块 {(10,0),(10,10)}：质心 (10,5)、半径 5，球伸到 x=15 —— **伸出父球之外**，
    于是子对 D = 10 - 5 = 5.0 < 7.929。界随细化变大 ⇒ 自顶向下的"父块够小就整块跳"
    会漏掉大的部分，球判据不能用来做 MAC。
    盒版：父盒 x<=10、子盒 x=10，两者对 B 的间距都是 10.0，单调。
    """
    pts = np.array([[0., 0., 0.], [10., 0., 0.], [0., 10., 0.], [10., 10., 0.]])
    w = np.ones(4)
    A = fastpair._node(pts, w, np.full(4, 1.0), np.full(4, 1.0), np.arange(4))
    child = fastpair._node(pts, w, np.full(4, 1.0), np.full(4, 1.0), np.array([1, 3]))
    B = fastpair._node(np.array([[20., 5., 0.]]), np.ones(1),
                       np.ones(1), np.ones(1), np.array([0]))
    assert child.radius == pytest.approx(5.0)
    assert A.radius == pytest.approx(np.sqrt(50.0))
    assert fastpair.ball_sep(child, B) < fastpair.ball_sep(A, B), \
        "夹具失效：球版这里应当违反单调，否则本条测的是恒真式"
    assert fastpair.box_sep(child, B) >= fastpair.box_sep(A, B)


def test_box_separation_is_never_increased_by_refinement():
    """盒间距在细化下单调不降 —— MAC 正确性的唯一几何前提。随机 4000 组。

    界随细化不增还需要另外三条，都在这里一起打：质量不增、w0min 不减、κmin 不减。
    """
    rng = np.random.default_rng(7)

    def node(pts):
        w = np.ones(len(pts))
        return fastpair._node(pts, w, np.full(len(pts), 1.0),
                              np.full(len(pts), 1.0), np.arange(len(pts)))

    for trial in range(4000):
        nA = int(rng.integers(2, 8))
        A = rng.normal(size=(nA, 3)) * rng.uniform(0.2, 4.0)
        k = int(rng.integers(1, nA))
        B = (rng.normal(size=(int(rng.integers(2, 8)), 3)) * rng.uniform(0.2, 4.0)
             + np.array([rng.uniform(2.0, 15.0), 0.0, 0.0]))
        P, Q = node(A), node(B)
        for child in (node(A[:k]), node(A[k:])):
            assert fastpair.box_sep(child, Q) >= fastpair.box_sep(P, Q) - 1e-12, trial
            assert child.mass <= P.mass + 1e-15 and child.w0min >= P.w0min - 1e-15
            assert child.kmin >= P.kmin - 1e-15
            assert fastpair.node_bound(child, Q) <= fastpair.node_bound(P, Q) + 1e-15


# ---------------------------------------------------------------- 需要 SCF
@pytest.fixture(scope="module")
def h2o2_lvl1():
    mol = gto.M(atom=geomlib.h2o_dimer(), basis=BASIS, verbose=0, unit="Angstrom")
    mf = partition.scf_grid(mol, xc="wb97x_v", level=1, basis=BASIS)[0]
    assert mf.converged, "SCF 未收敛，后面的比较无意义"
    return mol, mf


def _same_grid_full(mol, mf, level, scheme="becke"):
    """在 atom_partition 的同一张网格上，一次算完全量 E_nl（不分级、不切块）。"""
    X, W, owner = partition.atom_partition(mol, level=level, scheme=scheme)
    ni = mf._numint
    b, C = ni.nlc_coeff(mf.xc)[0][0]
    rf = ni.eval_rho(mol, ni.eval_ao(mol, X, deriv=1), mf.make_rdm1(), xctype="GGA")
    w0, kap, keep = nlc.vv10_fields(rf[0], rf[1] ** 2 + rf[2] ** 2 + rf[3] ** 2, b=b, C=C)
    wr = W * rf[0]
    idx = np.flatnonzero(keep)
    beta = (1.0 / 32.0) * (3.0 / (b * b)) ** nlc.BETA_EXP
    return float(nlc.pair_energy(X, wr, w0, kap, idx, idx) + nlc.local_term(beta, wr))


@pytest.mark.slow
def test_tree_partitions_the_block(h2o2_lvl1):
    """切树必须不重不漏，并且叶对之间**真的出现正间距** —— 屏蔽的可能性只来自这里。

    "不重不漏"是可加性由构造保证的前提：`_mac` 把 P×Q 切成"接受集 + 求和集"，
    靠的就是叶子是块的一个划分。

    后半截原来断言的是"最大叶盒对角 < 原子球半径"，实测立不住：水二聚体 lvl1 的
    atom 1 有 86 片叶，最大叶盒对角 14.25 bohr，而原子球半径 13.99 bohr。原因写在
    `build_tree` 的终止条件里 —— `idx.size <= min_pts`（默认 32）一到就停手，所以
    尾巴上那几片叶可以**既只有 32 个点又在空间上摊得很开**；盒对角量的是叶内点的
    空间摊布，实现从没打算把它压到原子球半径以下，把这条写成断言等于断言一个设计
    根本够不到的数。
    真正决定屏蔽可不可能的是**跨原子的叶对里有没有 box_sep > 0**：整原子球判据对这个
    数恒给 0（`test_ball_control_drops_nothing` 把那条负结果钉住了），只要叶对里出现
    一个正间距，三角不等式就第一次给出与距离有关的界，`_mac` 才有东西可跳。
    所以断言它 > 0；最大叶半径、最大叶盒对角、非零间距叶对占比一律只 print 当诊断。
    """
    mol, mf = h2o2_lvl1
    s = fastpair.screened_decomposition(mol, mf, level=1, screen=None, bound="tree")
    live = [P for P in s["blocks"] if P is not None]
    cross_pos = cross_all = 0
    for P in live:
        lv = fastpair.leaves(P.tree)
        assert sum(c.mass for c in lv) == pytest.approx(P.mass, rel=1e-12, abs=1e-14)
        allidx = np.concatenate([c.idx for c in lv])
        assert allidx.size == P.idx.size
        assert set(allidx.tolist()) == set(P.idx.tolist())
        assert len(set(allidx.tolist())) == allidx.size, "叶子重叠：划分不成立"
        worst_r = max(c.radius for c in lv)
        worst_box = max(float(np.linalg.norm(c.hi - c.lo)) for c in lv)
        gap = min(fastpair.box_sep(a, b) for a in lv for b in lv if a is not b)
        pos = tot = 0
        for Q in live:
            if Q is P:
                continue
            lvq = fastpair.leaves(Q.tree)
            for a in lv:
                for b in lvq:
                    tot += 1
                    if fastpair.box_sep(a, b) > 0.0:
                        pos += 1
        cross_pos += pos
        cross_all += tot
        print(f"  atom {P.atom}: nleaf={len(lv):4d} mass={P.mass:.3f}"
              f"  原子球半径={P.radius:5.2f}  最大叶半径={worst_r:5.2f}"
              f"  最大叶盒对角={worst_box:5.2f}  最小盒间距={gap:5.2f}"
              f"  跨原子非零间距叶对={pos}/{tot} ({(pos / tot if tot else 0.0):5.1%})")
        assert len(lv) > 1, "没真的切开"
    assert cross_all > 0
    print(f"  跨原子叶对合计（有序）：{cross_pos}/{cross_all} 有正盒间距"
          f"  —— 整原子球判据给不出任何一个")
    assert cross_pos > 0, \
        "叶对之间一个正间距都没有 ⇒ 盒判据退化回恒 0，屏蔽仍然不可能"
    assert s["n_leafpairs_total"] > 0


@pytest.mark.slow
def test_L1_certified_bound_dominates_actual(h2o2_lvl1):
    """每个阈值下都必须有 界 ≥ 实际被丢掉的量，且**至少真的丢掉过东西**。

    只断言 `cert >= actual` 是恒真的：原来那版界松到任何 ε 都一个原子对都不跳
    （实测苯夹心 300 个块对里 0 个可跳），于是"界成立"完全没内容。
    """
    mol, mf = h2o2_lvl1
    full = fastpair.screened_decomposition(mol, mf, level=1, screen=None)
    assert full["n_accepted"] == 0 and full["cert_err"] == 0.0
    dropped_any, ratios = False, []
    for thresh in (1e-4, 1e-6, 1e-8, 1e-10, 1e-12):
        s = fastpair.screened_decomposition(mol, mf, level=1, screen=thresh)
        actual = abs(s["E_nl"] - full["E_nl"])
        assert s["cert_err"] >= actual - 1e-18, (
            f"h2o2 lvl1 τ={thresh:g}: 界 {s['cert_err']:.3e} Ha < 实际 {actual:.3e} Ha")
        assert s["n_accepted"] + s["n_leafpairs_evaluated"] <= s["n_leafpairs_total"]
        print(f"\n  h2o2 lvl1 τ={thresh:g}: 接受 {s['n_accepted']:6d}"
              f"/{s['n_leafpairs_total']} 叶对  省下的点对占比"
              f" {1 - s['total_frac']:6.2%}  实际差 {actual*KCAL:.3e}"
              f"  界 {s['cert_err']*KCAL:.3e} kcal/mol")
        if actual > 1e-16:
            dropped_any = True
            ratios.append(s["cert_err"] / actual)
    assert dropped_any, "所有阈值都没丢掉任何东西 ⇒ 这组 τ 对该体系无意义"
    print(f"  h2o2: 界/实际 最坏比值 {max(ratios):.1f}x")


@pytest.mark.slow
def test_L4_zero_budget_reproduces_the_exact_value(h2o2_lvl1):
    """τ→0 必须回到精确值，且接受集+求和集真的铺满 P×Q。

    逐位相同只在 `bound="ball"`（走原子块路径，求和顺序不变）下要求；树路径把一个
    原子对拆成许多叶对再相加，**顺序**变了，所以那里按重排噪声判（计划书 L4 原话：
    差值等于浮点重排噪声 ~1e-14 相对）。
    """
    mol, mf = h2o2_lvl1
    a = fastpair.screened_decomposition(mol, mf, level=1, screen=None)
    b = fastpair.screened_decomposition(mol, mf, level=1, screen=1e-30, bound="ball")
    assert b["n_atom_pairs"] == a["n_atom_pairs"]
    assert a["E_nl"] == b["E_nl"], "bound='ball' 且 τ→0 时求和顺序不变，不该改变任何一个数"
    # 粗粒度建树：τ=1e-30 时接受数为 0 ⇒ 每条叶对都算过 ⇒ 点对数必须**恰好**等于
    # 远程块对的总点对数。这就是"接受集与求和集构成划分"的机器可验形式。
    c = fastpair.screened_decomposition(mol, mf, level=1, screen=1e-30, min_pts=4096)
    assert c["n_accepted"] == 0 and c["cert_err"] == 0.0
    assert c["pointpairs_evaluated"] == c["pointpairs_far"], \
        f"点对记账不闭合：{c['pointpairs_evaluated']} vs {c['pointpairs_far']}"
    assert c["E_nl"] == pytest.approx(a["E_nl"], rel=1e-13, abs=1e-16), (
        f"树路径重排噪声过大: {c['E_nl']!r} vs {a['E_nl']!r}")
    print(f"\n  L4: 原子路径逐位相同；树路径({c['n_leaves']} 叶)相对差"
          f" {abs(c['E_nl']-a['E_nl'])/abs(a['E_nl']):.2e}，点对记账闭合")


@pytest.mark.slow
def test_screen_off_equals_one_shot_same_grid(h2o2_lvl1):
    """屏蔽关闭时，按原子分块求和必须等于**同一张网格上**一次算完的全量。

    片段级的对照不在这里做：`test_regression.py::test_matches_pyscf_native_kernel`
    已经在管这件事，我不用猜来的接口去重复它、更不在这里混用 scf_grid 的网格。
    """
    mol, mf = h2o2_lvl1
    one_shot = _same_grid_full(mol, mf, 1)
    s = fastpair.screened_decomposition(mol, mf, level=1, screen=None)
    assert s["E_nl"] == pytest.approx(one_shot, rel=1e-12, abs=1e-12), \
        f"原子分块和 {s['E_nl']!r} vs 一次算完 {one_shot!r}"
    assert abs(s["E_nl"] - one_shot) < 1e-11, "分块和与一次算完差得超过了重排噪声"


@pytest.mark.slow
def test_x2_not_applied_twice(h2o2_lvl1):
    """×2 只在块级别施加一次：对角 + 2·非对角 == E_pair，屏蔽开也成立。"""
    mol, mf = h2o2_lvl1
    for thresh in (None, 1e-8):
        s = fastpair.screened_decomposition(mol, mf, level=1, screen=thresh)
        diag = sum(v for (a, q), v in s["pairs"].items() if a == q)
        off = sum(v for (a, q), v in s["pairs"].items() if a != q)
        assert s["E_pair"] == pytest.approx(diag + 2.0 * off, rel=0, abs=1e-14), thresh
        assert s["E_nl"] == pytest.approx(s["E_pair"] + s["E_loc"], rel=0, abs=1e-14)


@pytest.mark.slow
def test_L2_fragment_term_survives_screening(h2o2_lvl1):
    """L2：把 P1 需要的预算当约束，片间成对项 P_frz 必须仍在 1e-6 kcal/mol 内。

    `screen` 是单节点对的接受常数，**不是**预算；预算靠压 τ 直到 `cert_err` 达标
    来拿（计划书把 ε=1e-8 Ha 当成逐块阈值，那在有限体系上等于放弃屏蔽：实测苯夹心
    lvl0 有 95,481 个胞对各自 ≤ 1e-8 Ha，总界 1e-3 Ha）。
    锚是 `nlc.fragment_decomposition` —— fastpair 之外的另一条代码路径。
    """
    mol, mf = h2o2_lvl1
    frags = [list(range(mol.natm // 2)), list(range(mol.natm // 2, mol.natm))]
    X, W, owner = partition.atom_partition(mol, level=1, scheme="becke")
    ni = mf._numint
    b, C = ni.nlc_coeff(mf.xc)[0][0]
    rf = ni.eval_rho(mol, ni.eval_ao(mol, X, deriv=1), mf.make_rdm1(), xctype="GGA")
    ref = nlc.fragment_decomposition(X, W, rf[0],
                                     rf[1] ** 2 + rf[2] ** 2 + rf[3] ** 2,
                                     frags, b=b, C=C, owner=owner)
    p_ref = ref["inter"][(0, 1)] * KCAL
    budget = 1e-9                       # Ha：= 6.3e-7 kcal/mol，比 1e-6 留 1.6 倍余量
    chosen = None
    for tau in (1e-6, 1e-8, 1e-10, 1e-11, 1e-12, 1e-13):
        s = fastpair.screened_decomposition(mol, mf, level=1, screen=tau)
        if s["cert_err"] <= budget:
            chosen = (tau, s)
            break
    assert chosen is not None, f"压到 τ=1e-13 仍超预算 {budget} Ha，判据对这个体系不可用"
    tau, s = chosen
    half = sum(v for (a, q), v in s["pairs"].items() if a != q
               and (a < len(frags[0])) != (q < len(frags[0])))
    p_scr = 2.0 * half * KCAL
    print(f"\n  L2: 取 τ={tau:g} Ha ⇒ cert_err={s['cert_err']:.3e} Ha ≤ 预算 {budget:g}"
          f"  P_frz 屏蔽 {p_scr:.9f} vs 精确 {p_ref:.9f} kcal/mol"
          f"  差 {abs(p_scr-p_ref):.3e}   省下的点对占比 {1-s['total_frac']:.2%}")
    assert abs(p_scr - p_ref) <= 1e-6, f"P_frz 差 {abs(p_scr-p_ref):.3e} kcal/mol"
    assert s["cert_err"] >= abs(p_scr - p_ref) / KCAL - 1e-18
    assert s["n_accepted"] > 0, "预算内一个节点对都没跳 ⇒ 这条测的是恒真式"


@pytest.mark.slow
def test_ball_control_drops_nothing(h2o2_lvl1):
    """把负结果钉在测试里：整原子球判据在 τ=1e-8 Ha 下一个原子对都跳不掉，
    而同一体系同一 τ 下树判据真的跳得掉 —— 差别**不在**根节点的界谁更紧。

    `ball_sep` 对任意两个原子块都返回 0（尾巴把半径撑大 ⇒ 球两两重叠），于是界退化成
    与距离无关的常数。将来谁把默认判据换回球，这条会告诉他为什么不行。

    原来最后那条写的是 `assert tot_box < tot_ball`（盒界总量必须严格小于球界总量），
    实测两个数**逐位相等**：21723.206496881914 == 21723.206496881914 kcal/mol。这不是
    巧合，也不是算法错 —— 两个界函数在根上取的是同一个 D：原子块的包围盒就是那团
    密度尾巴的包络，任意两个这样的盒必然相交，于是 box_sep = ball_sep = 0，
    `node_bound` 和 `ball_bound` 一起退到 D=0 分支；又因为树根就是由同一个 `_node`
    在同一个 idx 上建的，mass/w0min/κmin 完全相同 ⇒ 逐位相同是必然。苯二聚体 lvl0 的
    探针给的是同一件事：276 个原子对里 0 个的根盒界 ≤ 1e-8 Ha，gapA 与 boxA 两栏全 0.00。
    所以"盒比球紧"这个说法在**根**上不成立；紧只来自**往下走**：细化让子盒彼此分开，
    box_sep 第一次 > 0（而它在细化下单调不降，这正是 `test_box_separation_is_never_
    increased_by_refinement` 验的那条）。
    因此这条改成断言真实的那个对比：球路径一层都下不去 ⇒ `cert_err == 0.0` 且原子对数
    不变；树路径同 τ 下得去 ⇒ `n_accepted > 0` 且真的省下了点对。
    外加把"根上 box_sep == ball_sep == 0"逐对断言并 print 出来，作为"紧不来自根节点"
    的证据留档。
    """
    mol, mf = h2o2_lvl1
    exact = fastpair.screened_decomposition(mol, mf, level=1, screen=None)
    s = fastpair.screened_decomposition(mol, mf, level=1, screen=1e-8, bound="ball")
    assert s["cert_err"] == 0.0, "球判据在 τ=1e-8 Ha 下本应一个块都跳不掉，cert_err 必须为 0"
    assert s["n_atom_pairs"] == exact["n_atom_pairs"], \
        "球判据跳不掉任何原子对 ⇒ 原子对数必须与不屏蔽时完全一致"
    assert s["n_accepted"] == 0
    assert s["E_nl"] == pytest.approx(exact["E_nl"], rel=0, abs=1e-14)

    # 同一体系、同一 τ：树路径确实跳掉了东西 —— 这才是与球路径的真实对比。
    t = fastpair.screened_decomposition(mol, mf, level=1, screen=1e-8, bound="tree")
    assert t["n_accepted"] > 0, "树判据在同一 τ 下应当接受掉节点对，否则这条对照无内容"
    assert 1.0 - t["total_frac"] > 0.0, "树判据应当真的省下点对"
    print(f"\n  τ=1e-8 Ha: 球路径 接受={s['n_accepted']} 原子对={s['n_atom_pairs']}"
          f" cert_err={s['cert_err']:.1e}  （与不屏蔽逐位同）")
    print(f"             树路径 接受={t['n_accepted']:6d}/{t['n_leafpairs_total']}"
          f" 访过内部节点={t['n_visited']:6d}  省下的点对占比 {1 - t['total_frac']:6.2%}"
          f"  cert_err={t['cert_err']:.3e} Ha")

    ref = fastpair.screened_decomposition(mol, mf, level=1, screen=None, bound="tree")
    off = [(a, q) for (a, q) in exact["pairs"] if a != q]
    tot_exact = sum(abs(v) for (a, q), v in exact["pairs"].items() if a != q)
    tot_ball = sum(fastpair.ball_bound(ref["blocks"][a], ref["blocks"][q], 2.0)
                   for (a, q) in off)
    tot_box = sum(fastpair.node_bound(ref["blocks"][a].tree, ref["blocks"][q].tree, 2.0)
                  for (a, q) in off)
    print(f"  Σ|精确半块|×2 = {tot_exact*KCAL:.4f} kcal/mol")
    print(f"  Σ球界 = {tot_ball*KCAL:.4e}   松 {tot_ball/tot_exact:.2e}x")
    print(f"  Σ盒界 = {tot_box*KCAL:.4e}   松 {tot_box/tot_exact:.2e}x")
    # 根节点上的两个间距：逐对断言恒 0，这就是 tot_box == tot_ball 的由来。
    worst = 0.0
    for (a, q) in off:
        Pa, Qa = ref["blocks"][a], ref["blocks"][q]
        bx, bs = fastpair.box_sep(Pa, Qa), fastpair.ball_sep(Pa, Qa)
        rbx, rbs = (fastpair.box_sep(Pa.tree, Qa.tree),
                    fastpair.ball_sep(Pa.tree, Qa.tree))
        assert bx == 0.0 and bs == 0.0 and rbx == 0.0 and rbs == 0.0, (a, q, bx, bs, rbx, rbs)
        worst = max(worst, bx, bs, rbx, rbs)
    print(f"  根节点间距：{len(off)} 个原子块对上 box_sep 与 ball_sep"
          f"（块与树根各一份，共 {4*len(off)} 个数）全为 {worst:.1e}"
          f" ⇒ 根上盒不比球紧，Σ盒界与Σ球界逐位相等：{tot_box == tot_ball}")
    assert tot_ball > 1e3 * tot_exact, "球判据应当是灾难性地松"
    assert worst == 0.0
    assert tot_box == tot_ball, "根上两个间距都是 0 ⇒ 两个界函数取到同一个值；" \
        "盒判据的收益不在根上，在细化（见上面的树路径 n_accepted）"
