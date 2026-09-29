"""A2b（`fastpair_ide`）的单元/回归测试。

分两层：
  * 不跑自洽场的合成夹具（秒级）——证界的**数学前提**、划分、×2 口径、ε→0 退回全量；
  * `@pytest.mark.slow` 的真实体系（水二聚体）——界 ≥ 实测差、与 `nlc` 同口径。

注意本文件的定位：**这是 A2b 自己的判据**，不构成跨程序验证。跨程序锚点
（全量 O(N²) 路径 / PySCF 原生核 / ORCA 6.0.1）在
`nlcsplit/examples/check_screen_bound_ide.py` 与 `PROGRESS-ide-qoder.md` 里核。
"""
import numpy as np
import pytest

from nlcsplit import fastpair_ide as fp
from nlcsplit import nlc

KCAL = 627.509474


# ------------------------------------------------------------------ 夹具
@pytest.fixture
def toy():
    """9 个合成网格点 / 3 个原子块，含**负权重点**。

    负权重是刻意的：`m_P = Σ|wr|` 用绝对值，若某处漏了 abs，负质量会让界变负、
    屏蔽变成"全屏"，测试能立刻抓到（全正数据下这个 bug 是静默的）。
    种子固定，不随运行变。
    """
    rng = np.random.default_rng(20260929)
    coords = rng.normal(scale=1.5, size=(9, 3))
    rho = np.abs(rng.normal(scale=0.4, size=9)) + 1e-3
    sigma = np.abs(rng.normal(scale=0.3, size=9))
    w0, kap, keep = nlc.vv10_fields(rho, sigma, b=6.0, C=0.01)
    weights = np.ones(9) / 9.0
    weights[4] = -0.5
    owner = np.array([0, 0, 1, 1, 2, 2, 2, 0, 1])
    frags = [[0, 1], [2]]
    return dict(coords=coords, wr=weights * rho, w0=w0, kap=kap, keep=keep,
                weights=weights, rho=rho, sigma=sigma, owner=owner, frags=frags)


def _stats(toy, atom):
    idx = np.where((toy["owner"] == atom) & toy["keep"])[0]
    return fp.block_stats(toy["coords"], toy["wr"], toy["w0"], toy["kap"], idx)


def brute_abs_sum(coords, wr, w0, kap, iA, iB):
    """块和的**逐点精确**绝对值上界：Σ|wr_i||wr_j|·|Φ_ij|（用真实 R²，不用球下界）。

    它 ≥ 任何真实块和，且 ≤ 解析界（后者用 D_ball 与块最小值）。
    写在这里是为了让"解析界确实盖住真实块"这件事被直接检查，而不是靠推导。
    """
    iA, iB = np.asarray(iA), np.asarray(iB)
    d2 = ((coords[iA][:, None, :] - coords[iB][None, :, :]) ** 2).sum(-1)
    g = w0[iA][:, None] * d2 + kap[iA][:, None]
    gp = w0[iB][None, :] * d2 + kap[iB][None, :]
    phi = fp.phi_abs_max(g, gp)
    return float(np.sum(np.abs(wr[iA])[:, None] * np.abs(wr[iB])[None, :] * phi))


# ------------------------------------------------------------------ 界的前提
def test_phi_bound_is_antecedent_monotone():
    """`|Φ| = 1.5/(g g'(g+g'))` 必须对 g、g' 单调递减——整条界的立身前提。

    前提一旦不成立（比如哪天改了核形式），下面所有"界"都是空话，所以这条
    要在最前面独立测，而不是藏在块测试里。
    """
    gp = 0.7
    gs = np.geomspace(0.05, 50.0, 64)
    vals = fp.phi_abs_max(gs, gp)
    assert np.all(np.diff(vals) < 0.0), "|Φ| 对 g 不单调递减"
    assert np.all(np.diff(fp.phi_abs_max(gs, 3.0)) < 0.0)
    # 对称性：Φ(g,g') = Φ(g',g)
    assert fp.phi_abs_max(1.3, 4.7) == pytest.approx(fp.phi_abs_max(4.7, 1.3))


def test_pairing_cross_is_refused():
    """cross 口径的界没被证明过，必须**拒绝**而不是悄悄给个错的界。"""
    with pytest.raises(NotImplementedError):
        fp.screened_decomposition(np.zeros((3, 3)), np.ones(3), np.ones(3),
                                  np.ones(3), [[0], [1]], owner=np.array([0, 1, 1]),
                                  pairing="cross")


def test_block_stats_requires_nonempty_and_mass(toy):
    st = _stats(toy, 0)
    assert st["m"] == pytest.approx(np.abs(toy["wr"][toy["owner"] == 0]).sum())
    assert st["w0_min"] > 0 and st["kap_min"] > 0
    # 半径是"到质心的最大偏离"，不是几何半径
    c = toy["coords"][st["idx"]]
    assert st["radius"] == pytest.approx(
        np.max(np.linalg.norm(c - c.mean(axis=0), axis=1)))
    empty = fp.block_stats(toy["coords"], toy["wr"], toy["w0"], toy["kap"],
                           np.array([], dtype=np.intp))
    assert empty is None
    zero = fp.block_stats(toy["coords"], np.zeros_like(toy["wr"]), toy["w0"],
                          toy["kap"], np.array([0, 1]))
    assert zero is None, "质量恰为 0 的块应被丢弃（它对任何口径贡献恒为 0）"


# ------------------------------------------------------------------ 界的有效性
def test_analytic_bound_covers_brute_and_truth(toy):
    """对若干块对：|真实块和| ≤ 逐点精确 Σ|·| ≤ 解析界。"""
    atoms = [0, 1, 2]
    for a in atoms:
        for b in atoms:
            P, Q = _stats(toy, a), _stats(toy, b)
            iA = np.where((toy["owner"] == a) & toy["keep"])[0]
            iB = np.where((toy["owner"] == b) & toy["keep"])[0]
            truth = abs(nlc.pair_energy(toy["coords"], toy["wr"], toy["w0"],
                                        toy["kap"], iA, iB))
            brute = brute_abs_sum(toy["coords"], toy["wr"], toy["w0"], toy["kap"],
                                  iA, iB)
            analytic = fp.pair_bound(P, Q)
            assert truth <= brute <= analytic, (
                f"块 ({a},{b}): truth={truth:.3e} brute={brute:.3e} "
                f"analytic={analytic:.3e}")


def test_screening_predicate_never_looks_at_true_block_sum(toy, monkeypatch):
    """纪律第 1 条：判据只用块统计量，**不许**读真实块和。

    做法：把 `nlc.pair_energy` 换成"一被调用就抛"的桩，只跑判据那一段
    （构造块对 + 算界 + 选择）。若判据里混进了求值，这条立刻炸。
    """
    calls = []

    def boom(*a, **k):
        calls.append(1)
        raise AssertionError("判据阶段调用了 pair_energy —— 选择被求值污染了")

    monkeypatch.setattr(nlc, "pair_energy", boom)
    res = fp.screened_decomposition(toy["coords"], toy["weights"], toy["rho"],
                                    toy["sigma"], toy["frags"], owner=toy["owner"],
                                    epsilon=1e-3, mode="budget", full_ref=False)
    assert calls == []
    assert res["n_pairs_full"] > 0
    # 选择本身要真的屏掉点东西，否则这条测试什么都没验
    assert res["n_dropped_screen"] > 0


# ------------------------------------------------------------------ 划分与口径
def test_partition_of_pair_space(toy):
    """原子块对必须是**成对空间的一个划分**：块级值加起来 == 片段级 intra/inter。

    可加性由构造保证，不是事后凑出来的——这条就是那个"构造"本身。
    故意按 (A,B,a,b) 四元组键分家来核，而不是拿原子对 (a,b) 自己推归属：
    后者会把"枚举顺序"当成"大小顺序"，上一版就是踩在这个测试自写的过滤器上。
    """
    res = fp.screened_decomposition(toy["coords"], toy["weights"], toy["rho"],
                                    toy["sigma"], toy["frags"], owner=toy["owner"],
                                    mode="full")
    # 用 pairs（带 mult/value）核：mult×半份块 加起来 == 片段级 intra/inter
    for A, tot in res["intra"].items():
        s = sum(p["mult"] * p["value"] for p in res["pairs"]
                if p["kind"] == "intra" and p["A"] == A)
        assert s == pytest.approx(tot, rel=1e-13, abs=0.0)
    for (A, B), tot in res["inter"].items():
        s = sum(p["mult"] * p["value"] for p in res["pairs"]
                if p["kind"] == "inter" and (p["A"], p["B"]) == (A, B))
        assert s == pytest.approx(tot, rel=1e-13, abs=0.0), \
            "inter 存的是整份（×2 已在 mult 里施加一次）"
    # 交叉块的 mult 必须恰好为 2，自块为 1
    assert all(p["mult"] == 2 for p in res["pairs"] if p["kind"] == "inter")
    assert all(p["mult"] in (1, 2) for p in res["pairs"] if p["kind"] == "intra")
    assert res["n_pairs_full"] == len(res["kept"]) + len(res["dropped"])


def test_double_counting_is_exactly_once(toy):
    """×2 只能有一次：用 mult×半份值手工求和，应等于 `E_nl`。"""
    res = fp.screened_decomposition(toy["coords"], toy["weights"], toy["rho"],
                                    toy["sigma"], toy["frags"], owner=toy["owner"],
                                    mode="full")
    manual = sum(p["mult"] * p["value"] for p in res["pairs"])
    assert manual == pytest.approx(res["E_nl"], rel=1e-13, abs=0.0)


def test_off_matches_fragment_decomposition(toy):
    """屏蔽关闭时必须与 `nlc.fragment_decomposition` 同口径（差只有浮点重排）。

    用 `full_ref=True` 让两边走**同一份** weights/rho/owner（上一版手写了一个
    np.full 的权重、与夹具里带负权重的 wr 不同 ⇒ 假不一致）。
    """
    res = fp.screened_decomposition(toy["coords"], toy["weights"], toy["rho"],
                                    toy["sigma"], toy["frags"], owner=toy["owner"],
                                    mode="full", full_ref=True)
    ref = nlc.fragment_decomposition(toy["coords"], toy["weights"], toy["rho"],
                                     toy["sigma"], toy["frags"],
                                     b=6.0, C=0.01, owner=toy["owner"])
    assert res["E_nl"] == pytest.approx(ref["E_nl"], rel=1e-12, abs=0.0)
    assert res["E_loc"] == pytest.approx(ref["E_loc"], rel=1e-14)
    for k in ref["intra"]:
        assert res["intra"][k] == pytest.approx(ref["intra"][k], rel=1e-12, abs=0.0)
    for k in ref["inter"]:
        assert res["inter"][k] == pytest.approx(ref["inter"][k], rel=1e-12, abs=0.0)


# ------------------------------------------------------------------ 预算/选择
def test_budget_screened_set_is_weakest_suffix(toy):
    """被屏集合按界降序必须是**一段后缀**（这是"界 ≤ ε"的组合学根据）。"""
    res = fp.screened_decomposition(toy["coords"], toy["weights"], toy["rho"],
                                    toy["sigma"], toy["frags"], owner=toy["owner"],
                                    epsilon=1e-4, mode="budget")
    bounds = sorted((p["bound"] for p in res["pairs"]), reverse=True)
    kept = {tuple(t) for t in res["kept"]}
    flags = [tuple((p["a"], p["b"])) in kept for p in
             sorted(res["pairs"], key=lambda p: -p["bound"])]
    # flags 形如 [T,T,...,F,F,...]：一旦出现过 F 就不许再出现 T
    assert flags == sorted(flags, reverse=True)
    assert res["bound_ha"] <= res["epsilon"]
    assert len(bounds) == res["n_pairs_full"]


def test_additivity_holds_with_screening_on(toy):
    """纪律第 2 条：屏蔽开启时可加性仍然成立，且**总量与分块同源**。"""
    for eps in (1e-2, 1e-4, 1e-8):
        res = fp.screened_decomposition(toy["coords"], toy["weights"], toy["rho"],
                                        toy["sigma"], toy["frags"],
                                        owner=toy["owner"], epsilon=eps)
        recon = sum(res["intra"].values()) + sum(res["inter"].values())
        assert abs(recon - res["E_nl"]) < 1e-14
        assert res["E_total"] == pytest.approx(res["E_loc"] + res["E_nl"], rel=1e-15)


def test_epsilon_to_zero_recovers_full_path(toy):
    """L4：ε 小到谁都屏不动 ⇒ 清单 = 全量清单，值与关闭屏蔽只差浮点重排。"""
    full = fp.screened_decomposition(toy["coords"], toy["weights"], toy["rho"],
                                     toy["sigma"], toy["frags"], owner=toy["owner"],
                                     mode="full")
    tiny = fp.screened_decomposition(toy["coords"], toy["weights"], toy["rho"],
                                     toy["sigma"], toy["frags"], owner=toy["owner"],
                                     epsilon=1e-300, mode="budget")
    assert tiny["n_dropped_screen"] == 0
    assert tiny["bound_ha"] == 0.0
    assert tiny["points_kept"] == full["points_full"]
    rel = abs(tiny["E_nl"] - full["E_nl"]) / max(abs(full["E_nl"]), 1e-300)
    assert rel < 1e-13, f"ε→0 退回全量的差 {rel:.3e} 超出浮点重排量级"


def test_budget_never_exceeds_epsilon_and_is_suffix():
    """预算贪心的两条命门：证得界 ≤ ε，且被屏集是最弱后缀。

    上一版用逐元素 `bound ≤ 各自预算` 选，会挑出非后缀子集、把界之和推到 ε 之上
    （今天实测 harmonic 版 bnd=6.3e-7 ≫ ε=1e-8）。现在从最弱往回累加，
    累加和不超 ε ⇒ 两条都由构造保证。对数分布反复扫，不靠单一数据点。
    """
    rng = np.random.default_rng(7)
    for eps in (1e-8, 1e-6, 1e-3):
        for n in (50, 200, 1000):
            bounds = 10.0 ** rng.uniform(-4, 2, size=n) * eps
            sc, bnd = fp.select_screened(bounds, eps, mode="budget")
            assert bnd <= eps + 1e-30, f"ε={eps:g} n={n}: 界 {bnd:.3e} 超预算"
            assert bnd == pytest.approx(float(bounds[sc].sum()), rel=1e-15)
            # 后缀性：降序排列后 True（被屏）只能出现在尾部一段
            order = np.argsort(-bounds, kind="stable")
            flags = [bool(x) for x in sc[order]]
            first = flags.index(True) if True in flags else len(flags)
            assert all(flags[first:]), "被屏集不是最弱后缀"


def test_budget_screens_maximal_weakest_set():
    """贪心应把"能屏的最多弱块"屏掉：再加一个就超 ε（不是随便屏一两个）。"""
    rng = np.random.default_rng(3)
    eps = 1e-6
    bounds = 10.0 ** rng.uniform(-3, 1, size=80) * eps
    sc, bnd = fp.select_screened(bounds, eps, mode="budget")
    kept_bounds = np.sort(bounds[~sc])          # 保留的按界升序，最小那个就是"下一个候选"
    assert kept_bounds.size > 0
    assert bnd + kept_bounds[0] > eps, "还能再多屏一个最弱的却没收，贪心没吃满预算"


def test_suffix_bound_is_genuine():
    """被屏集后缀的界：直接求和重算应与 bound_ha 一致（防它是个平均值）。"""
    rng = np.random.default_rng(11)
    bounds = 10.0 ** rng.uniform(-4, 1, size=137) * 1e-8
    sc, bnd = fp.select_screened(bounds, 1e-8, mode="budget")
    assert bnd == pytest.approx(float(bounds[sc].sum()), rel=1e-15)
    assert sc.sum() > 0 and (~sc).sum() > 0, "这条测试要有两类块对才算数"


def test_tau_mode_reports_measured_bound():
    """tau 模式：每个被屏块对界 ≤ ε/2，但并的界可以超 ε —— 报的必须是实测和。"""
    bounds = np.full(10, 0.4)
    sc, bnd = fp.select_screened(bounds, 1.0, mode="tau")
    assert sc.all() and bnd == pytest.approx(4.0)
    assert bnd > 1.0, "这里就是要让'界 > ε'暴露出来，而不是被静默掩盖"


# ------------------------------------------------------------------ 两条截断
def test_blocks_are_atom_indexed_not_fragment_indexed(toy):
    """硬分区块必须是**本片段原子对**：片段 0 有 2 个原子 ⇒ intra 块有 3 个（上三角）。"""
    res = fp.screened_decomposition(toy["coords"], toy["weights"], toy["rho"],
                                    toy["sigma"], toy["frags"], owner=toy["owner"],
                                    mode="full")
    frag0 = [p["value"] for p in res["pairs"]
             if p["kind"] == "intra" and p["A"] == 0]
    assert len(frag0) == 3, "两个原子应有 (0,0),(0,1),(1,1) 三个上三角块"
    assert len(set(frag0)) == len(frag0), "不同原子块塔到同一个值 = 块没按原子切"


def test_rho_floor_and_screening_are_reported_separately(toy):
    """两条截断分开报：一条数点（rho_floor），一条数块对（屏蔽）。"""
    # 拿中位数当 ε ⇒ 保证一半左一半右（既非全屏也非全不屏）
    bounds_all = [p["bound"] for p in fp.screened_decomposition(
        toy["coords"], toy["weights"], toy["rho"], toy["sigma"], toy["frags"],
        owner=toy["owner"], mode="full")["pairs"]]
    mid = sorted(bounds_all)[len(bounds_all) // 2]
    res = fp.screened_decomposition(toy["coords"], toy["weights"], toy["rho"],
                                    toy["sigma"], toy["frags"], owner=toy["owner"],
                                    epsilon=mid * 1.0001)
    assert res["n_dropped_rho"] == int((~toy["keep"]).sum())
    assert 0 < res["n_dropped_screen"] < res["n_pairs_full"], \
        "这条夹要落在部分屏的档位上，两个计数器才能分得开"
    # 收紧 floor：点数与块总工作量都变小 ⇒ 被 floor 掉的点没混进块质量
    full_default = fp.screened_decomposition(toy["coords"], toy["weights"], toy["rho"],
                                             toy["sigma"], toy["frags"],
                                             owner=toy["owner"], mode="full")
    tight = fp.screened_decomposition(toy["coords"], toy["weights"], toy["rho"],
                                      toy["sigma"], toy["frags"], owner=toy["owner"],
                                      mode="full", rho_floor=1e-1)
    assert tight["n_dropped_rho"] > full_default["n_dropped_rho"]
    assert tight["points_full"] < full_default["points_full"], \
        "收紧 floor 后块工作量未变小 ⇒ 被 floor 掉的点混进了块质量"


def test_select_screened_rejects_nonpositive_epsilon_in_budget():
    with pytest.raises(ValueError):
        fp.select_screened(np.array([1e-9]), 0.0, mode="budget")
    with pytest.raises(ValueError):
        fp.select_screened(np.array([1e-9]), 1e-8, mode="nonsense")
    with pytest.raises(ValueError):
        fp.budget_weights(3, scheme="flat")


# ------------------------------------------------------------------ 真实体系
@pytest.fixture(scope="module")
def water_lvl0():
    gto = pytest.importorskip("pyscf.gto")
    from nlcsplit import geomlib, partition
    mol = gto.M(atom=geomlib.h2o_dimer(), basis="6-31g*", verbose=0,
                unit="Angstrom")
    mf, X, W, rho, sig = partition.scf_grid(mol, xc="wb97x_v", level=0)
    b, C = mf._numint.nlc_coeff("wb97x_v")[0][0]
    co, we, owner = partition.atom_partition(mol, level=0, scheme="becke")
    ao = mf._numint.eval_ao(mol, co, deriv=1)
    r = mf._numint.eval_rho(mol, ao, mf.make_rdm1(), xctype="GGA")
    s = r[1] ** 2 + r[2] ** 2 + r[3] ** 2
    return dict(mol=mol, mf=mf, frags=geomlib.FRAGS["(H2O)2"], b=b, C=C,
                partition=(co, we, r[0], s, owner))


@pytest.mark.slow
def test_water_partition_grid_bound_covers_actual(water_lvl0):
    """真实 Becke 网格上：证得界 ≥ 实测 |screened − full|（L1 的合成版）。"""
    co, we, rho, sig, owner = water_lvl0["partition"]
    frags, b, C = water_lvl0["frags"], water_lvl0["b"], water_lvl0["C"]
    for eps in (1e-6, 1e-8, 1e-10):
        res = fp.screened_decomposition(co, we, rho, sig, frags, b=b, C=C,
                                        owner=owner, epsilon=eps, full_ref=True)
        assert res["bound_ha"] <= eps * 1.000001, "界超出请求预算"
        assert res["actual_ha"] <= res["bound_ha"] + 1e-16, (
            f"ε={eps:g}: 实测差 {res['actual_ha']:.3e} > 界 {res['bound_ha']:.3e}")
        recon = sum(res["intra"].values()) + sum(res["inter"].values())
        assert abs(recon - res["E_nl"]) < 1e-10, "屏蔽开启时可加性破了"


@pytest.mark.slow
def test_water_soft_partition_mass_and_bound(water_lvl0):
    """软分区：界要用逐片段质量 m_P^A，否则 `_soft_pair` 的界不成立（任务书点名）。

    owner 用原子子网格那个（块的定义就是它）；本模块的软分支不再拿片段索引全集
    去喂 `pair_energy` —— 上一版那样做会把片段对重算 |A|·|B| 倍（实测 8.9×）。
    """
    pytest.importorskip("pyscf")
    from nlcsplit import nlc as _nlc, partition
    mol = water_lvl0["mol"]
    frags, b, C = water_lvl0["frags"], water_lvl0["b"], water_lvl0["C"]
    co, base_w, S = partition.partition_factors(mol, level=0, scheme="becke")
    _co_h, _w_h, owner = partition.atom_partition(mol, level=0, scheme="becke")
    assert len(co) == len(_co_h), "partition_factors 与 atom_partition 应当同一批点"
    ao = water_lvl0["mf"]._numint.eval_ao(mol, co, deriv=1)
    r = water_lvl0["mf"]._numint.eval_rho(mol, ao, water_lvl0["mf"].make_rdm1(),
                                          xctype="GGA")
    s = r[1] ** 2 + r[2] ** 2 + r[3] ** 2
    soft = S.T                                  # (natm, N)
    for eps in (1e-6, 1e-8):
        res = fp.screened_decomposition(co, base_w, r[0], s, frags, b=b, C=C,
                                        owner=owner, soft=soft, epsilon=eps,
                                        full_ref=True)
        assert res["soft"] is True
        assert res["actual_ha"] <= max(res["bound_ha"], 1e-15), (
            f"软分区 ε={eps:g}: 实测 {res['actual_ha']:.3e} > 界 {res['bound_ha']:.3e}")
        ref = _nlc.fragment_decomposition(co, base_w, r[0], s, frags, b=b, C=C,
                                         soft=soft)
        assert res["full_ref_nl"] == pytest.approx(ref["E_nl"], rel=1e-12, abs=0.0)
        # 不屏时两边的**逐片段量**也要同口径（不只总量）
        off = fp.screened_decomposition(co, base_w, r[0], s, frags, b=b, C=C,
                                        owner=owner, soft=soft, mode="full")
        for k in ref["intra"]:
            assert off["intra"][k] == pytest.approx(ref["intra"][k], rel=1e-10, abs=0.0)
        for k in ref["inter"]:
            assert off["inter"][k] == pytest.approx(ref["inter"][k], rel=1e-10, abs=0.0)
