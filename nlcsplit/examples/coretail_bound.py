"""探针：把节点界拆成"核内质量 m̃ + 尾外质量 T"两段，界到底能不能做紧。

**这是测量，不是实现。** 本文件不修改 `fastpair.py`，只读它的 `build_blocks` /
`node_bound` / `box_sep` / `pair_energy` 口径，另起一张节点表和一套自顶向下模拟，
回答三个问题：

  Q1 可加性/正确性：m̃ + T == m（核与尾不重不漏），且新界仍 ≥ 实测 |pair_energy|。
  Q2 紧了多少：逐 τ 比旧节点界与新节点界的总和；多少节点对的界降到 1e-12 / 1e-13 Ha
     以下；τ=1e-12 预算下**能跳掉的点对占比**（水二聚体 lvl1 旧路 12.35%，出处
     `nlcsplit/logs/20260929T101447Z_probe_bound_forms.out:24`）抬不抬得动。
  Q3 r_core 怎么选才不引入新参数，且三种取法各自是否仍可证。

病根（简报给的诊断）：节点的 κ^min 由块内**最低密度点**决定。尾巴点 ρ→1e-12 时
κ = b(3π/2)(ρ/9π)^{1/6} ≈ 0.164，界随 κ^3 增长 ⇒ 混进一个尾巴点，整个节点的界就与
核附近密度无关。修法：把质量按到质心的距离切成核内 m̃ 与尾 T，κ̃^min 只取核内下界，
**任何含尾的乘积**改用 Φ 的上界，于是界由节点自己的尾质量决定。

界族（全部只依赖"盒包含其全部点"；核/尾是**质量切分**，几何一格未动）
--------------------------------------------------------------------------
D = box_sep(A,B)（旧路同一个轴对齐盒间距）。核 ⊆ 父盒 ⇒ 核-核点对的距离也 ≥ D。
ker(x,y) = 0.75/(x·y·(x+y)) 是半块口径（已含 pair_energy 的 1/2）的 |Φ| 上界核。
    a_P = w0_P^min·D²  + κ_P^min     （全块下界，旧口径）
    ã_P = w̃0_P^min·D² + κ̃_P^min     （核内下界）
  V1 简报 prescribed：
       m̃_A m̃_B·ker(ã_A,ã_B) + (m_A m_B − m̃_A m̃_B)·ker(κ_A^min, κ_B^min)
       —— 含尾的乘积用 D=0 处的全局 sup|Φ|。
  V2 含尾乘积也吃 D（仍用**整块**下界 a_P）：
       m̃_A m̃_B·ker(ã,ã) + (m_A m_B − m̃_A m̃_B)·ker(a_A,a_B)
       ≡ 旧界 + m̃_A m̃_B·(ker(ã,ã) − ker(a,a)) ⇒ **恒 ≤ 旧界**，T→0 时逐位退回旧界。
  V3 把 m_A m_B 按核/尾拆成 4 块质量积，交叉块用混合下界 (ã,a)（同样吃 D）。
  V4 V3 再让每个子块用**自己的盒**求间距（核盒/尾盒）。子盒 ⊆ 父盒 ⇒ "叶子的盒仍包含
       其全部点"这一前提不变，且每对子块的 D 不减。
  V1BAD 负对照：V1 的含尾项把 κ^min 换成**核内** κ̃^min。看着更紧，其实不再是界。

可证性 = "每个节点自己的界 ≥ 该节点块的实际值"，本文件逐节点对实测它。
细化单调/次可加只决定"往下走能不能真省东西"（球版当年死在这条上），它不是可靠性的
前提，但照样量出来并单独报数。

⚠ 本机多代理并发：**本文件不报任何墙钟/加速比结论**，计时一律 NOT_MEASURED。

跑法（WSL）：
    PYTHONPATH=. OMP_NUM_THREADS=3 python3 -u nlcsplit/examples/coretail_bound.py 1
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np                                        # noqa: E402
from pyscf import dft, gto                                # noqa: E402

from nlcsplit import fastpair, geomlib, nlc, partition    # noqa: E402

HA2K = 627.50947400
BOHR2A = 0.529177210903
BASIS = "6-31g*"
XC = "wb97x_v"
INF = float("inf")
TREE_KW = dict(mass_frac=0.01, radius_frac=1 / 3, min_pts=32)   # 与 fastpair 默认一致
TAIL_EPS = TREE_KW["mass_frac"]        # 规则 (a) 复用同一个 1%，不引入新常数
K_SIGMA = 1.0                          # 规则 (b) 的倍数固定为 1，不随体系调
RULES = ("none", "mass", "sigma", "halfdiag", "leafonly")
VARIANTS = ("V1", "V2", "V3", "V4")
TAUS_MAC = (1e-13, 1e-12, 1e-10)
CENSUS_T = (1e-12, 1e-13)
NPAIR_TREESTATS = 160                  # 界成立性：真实树上的节点对（另加 15 个根对）
NPAIR_SUBSET = 200                     # 界成立性：随机点集（任意两点集也必须成立）
MAX_PTS_PROD = 3.0e6                   # 抽样时限制 pair_energy 的规模，控成本
NLEAF_ACTUAL = 400                     # 叶对 界/实际 比值的抽样对数
NMONO = 2000                           # 次可加性抽样组数


# ============================================================ 0. 取场（复刻 fastpair）
def build_fields(mol, level):
    """复刻 `fastpair.screened_decomposition` 的取场口径（同一张网格、同一套 keep）。

    少一行对上，"旧界 vs 新界"比的就不是同一个对象。
    """
    X, W, owner = partition.atom_partition(mol, level=level, scheme="becke")
    ni = mf._numint
    dm = mf.make_rdm1()
    b, C = ni.nlc_coeff(mf.xc)[0][0]
    rho_full = ni.eval_rho(mol, ni.eval_ao(mol, X, deriv=1), dm, xctype="GGA")
    rho = rho_full[0]
    sig = rho_full[1] ** 2 + rho_full[2] ** 2 + rho_full[3] ** 2
    w0, kap, keep = nlc.vv10_fields(rho, sig, b=b, C=C)
    wr = W * rho
    idx_kept = np.flatnonzero(keep)
    owner_kept = np.full(len(wr), -1, dtype=np.intp)
    owner_kept[idx_kept] = owner[idx_kept]
    blocks = fastpair.build_blocks(X, wr, w0, kap, owner_kept, mol.natm,
                                   tree_kwargs=dict(TREE_KW))
    return dict(X=X, wr=wr, w0=w0, kap=kap, keep=keep, b=b, C=C, blocks=blocks,
                owner_kept=owner_kept, idx_kept=idx_kept,
                n_grid=len(wr), n_kept=int(idx_kept.size))


# ================================================== 1. 节点表 + 核/尾聚合量（规则实现）
def flatten_tree(root, atom, block_idx=None):
    """把一棵树摊平成记录列表（下标即节点 id），父/子用重编号后的 id 引用。

    内部节点在 `fastpair` 里**不存** idx（只有叶子上有），所以父节点的点集只能由子节点
    拼出来。`build_tree` 用 `idx[sel] / idx[~sel]` 分孩子，那是**重排**不是保序切分，
    拼回来的顺序与父节点求聚合量时的顺序不同——集合相同、求和次序不同，差的是浮点重排
    量级（~1e-16 相对）。因此这里断言的是**多重集相等 + 孩子不相交**，不是逐元素相等。
    """
    recs = []

    def rec(N, depth, parent):
        me = len(recs)
        recs.append(dict(idx=None if N.idx is None else np.asarray(N.idx),
                         atom=atom, depth=depth, isleaf=int(N.idx is not None),
                         left=-1, right=-1, parent=parent,
                         npts=0 if N.idx is None else int(N.idx.size),
                         mass=float(N.mass), lo=np.asarray(N.lo), hi=np.asarray(N.hi),
                         w0min=float(N.w0min), kmin=float(N.kmin),
                         centroid=np.asarray(N.centroid), radius=float(N.radius)))
        if N.idx is None:
            recs[me]["left"] = rec(N.left, depth + 1, me)
            recs[me]["right"] = rec(N.right, depth + 1, me)
            L = recs[recs[me]["left"]]["idx"]
            R = recs[recs[me]["right"]]["idx"]
            idx = np.concatenate([L, R])
            assert np.intersect1d(L, R).size == 0, "兄弟叶子重叠：不是划分"
            assert np.unique(idx).size == idx.size, "子块有重复点"
            recs[me]["idx"], recs[me]["npts"] = idx, int(idx.size)
        return me

    rec(root, 0, -1)
    if block_idx is not None:
        got = np.sort(np.asarray(recs[0]["idx"]))
        want = np.sort(np.asarray(block_idx))
        assert np.array_equal(got, want), \
            f"整棵树覆盖 != 原子块 idx（{got.size} vs {want.size} 点）"
    return recs


class Table:
    """全部原子树摊平后的 struct-of-arrays；判据只读这些数组。"""

    def __init__(self, recs_per_atom):
        recs, base = [], []
        for rs in recs_per_atom:
            # flatten_tree 每次只看见自己那棵原子树，left/right 是**块内局部 id**；
            # 拼成全局表必须加基址，否则父节点会指到别的原子上去（踩过，闭包断言抓的）。
            off = len(recs)
            for r in rs:
                if r["left"] >= 0:
                    r["left"] += off
                if r["right"] >= 0:
                    r["right"] += off
                if r["parent"] >= 0:
                    r["parent"] += off
            base.append(off)
            recs += rs
        self.recs, self.n = recs, len(recs)
        self.base, self.count = base, [len(rs) for rs in recs_per_atom]

        def g(key, dt=float):
            return np.array([r[key] for r in recs], dtype=dt)

        self.atom, self.depth = g("atom", np.intp), g("depth", np.intp)
        self.isleaf = g("isleaf", np.int8)
        self.left, self.right = g("left", np.intp), g("right", np.intp)
        self.npts, self.mass = g("npts", np.int64), g("mass")
        self.lo, self.hi = g("lo"), g("hi")
        self.w0min, self.kmin = g("w0min"), g("kmin")
        self.centroid, self.radius = g("centroid"), g("radius")
        self.diag = np.linalg.norm(self.hi - self.lo, axis=1)
        self.idx = [r["idx"] for r in recs]
        self.rules = {}

    def ids_of(self, atom, only_leaves=False):
        ids = np.arange(self.base[atom], self.base[atom] + self.count[atom])
        return ids[self.isleaf[ids] == 1] if only_leaves else ids


def choose_r_core(kind, r, w, m, halfdiag):
    """核心半径：全部由节点自身量导出，不引入需要手调的常数。

      none      +inf：核=全部点、T=0 —— 控制组，必须逐位退回旧界
      mass      (a) 使 T ≤ 1%·m 的**最小** r_core（1% 借 build_tree 的 mass_frac）
      sigma     (b) 质量加权半径的 r̄ + 1σ（倍数固定）
      halfdiag  (c) 盒半对角线 ½‖hi−lo‖、球心取密度质心 —— 树层级自己的几何尺度，
                  越往下盒越小 ⇒ 层内自适应，零质量调参
      leafonly  (c') 只有叶子用 halfdiag，内部节点不切 —— 回答"切分要不要一路切到根"
    """
    if kind == "none":
        return INF
    if kind == "mass":
        order = np.argsort(r, kind="stable")
        cw = np.cumsum(w[order])
        k = int(np.searchsorted(cw, (1.0 - TAIL_EPS) * m, side="left"))
        return float(r[order][min(k, r.size - 1)])
    if kind == "sigma":
        rbar = float((w * r).sum() / m)
        var = float((w * (r - rbar) ** 2).sum() / m)
        return rbar + K_SIGMA * np.sqrt(max(var, 0.0))
    if kind == "halfdiag":
        return float(halfdiag)
    raise KeyError(kind)


def agg_from_idx(X, wr, w0, kap, idx, rule, centroid=None, halfdiag=None):
    """任意点集（树节点或随机子集）的核/尾聚合量，返回 1 元素数组字典。

    界函数只吃这个字典 ⇒ 树上的节点与随机子集走**同一个**判据实现，
    不会出现"验的其实是另一套公式"。
    """
    P = X[idx]
    w = np.abs(wr[idx])
    m = float(w.sum())
    if m <= 0.0:
        raise ValueError("空质量点集没有界可谈")
    if centroid is None:
        centroid = (P * w[:, None]).sum(0) / m
    if halfdiag is None:
        halfdiag = 0.5 * float(np.linalg.norm(P.max(0) - P.min(0)))
    r = np.linalg.norm(P - centroid, axis=1)
    rc = choose_r_core("halfdiag" if rule == "leafonly" else rule, r, w, m, halfdiag)
    core = np.ones(idx.size, dtype=bool) if rule == "none" else (r <= rc)
    tail = ~core
    wa = w0[idx]
    ka = kap[idx]
    one = lambda v: np.array([float(v)], dtype=float)                   # noqa: E731
    agg = dict(mass=one(m), mtilde=one(float(w[core].sum())), T=one(float(w[tail].sum())),
               w0min=one(wa.min()), kmin=one(ka.min()),
               w0t=one(wa[core].min() if core.any() else 0.0),
               kt=one(ka[core].min() if core.any() else 0.0),
               lo=P.min(0)[None, :], hi=P.max(0)[None, :],
               clo=(P[core].min(0)[None, :] if core.any() else centroid[None, :]),
               chi=(P[core].max(0)[None, :] if core.any() else centroid[None, :]),
               tlo=(P[tail].min(0)[None, :] if tail.any() else centroid[None, :]),
               thi=(P[tail].max(0)[None, :] if tail.any() else centroid[None, :]),
               ncore=np.array([int(core.sum())], dtype=np.int64),
               ntail=np.array([int(tail.sum())], dtype=np.int64),
               npts=np.array([int(idx.size)], dtype=np.int64),
               r_core=one(rc))
    return agg, core


def apply_rule(tbl, X, wr, w0, kap, rule):
    """给整张节点表算一遍核/尾量，存成 (n,) / (n,3) 数组。

    `mass` 用 fastpair 存在 Node 上的值（`old` 变体靠它逐位复刻基线）；
    `mass_own` 是我按自己 idx 次序重算的 Σ|wr|，两套账的偏离在第 5 节单独打出来。
    """
    n = tbl.n
    out = {k: np.zeros(n) for k in ("mtilde", "T", "w0t", "kt", "r_core")}
    for arr in ("clo", "chi", "tlo", "thi"):
        out[arr] = np.zeros((n, 3))
    out["ncore"] = np.zeros(n, dtype=np.int64)
    out["ntail"] = np.zeros(n, dtype=np.int64)
    out["mass_own"] = np.zeros(n)
    out.update(mass=tbl.mass.copy(), w0min=tbl.w0min.copy(), kmin=tbl.kmin.copy(),
               npts=tbl.npts.copy(), lo=tbl.lo.copy(), hi=tbl.hi.copy(),
               diag=tbl.diag)
    for i, rec in enumerate(tbl.recs):
        kind = ("halfdiag" if rec["isleaf"] else "none") if rule == "leafonly" else rule
        agg, _ = agg_from_idx(X, wr, w0, kap, rec["idx"], kind,
                              centroid=rec["centroid"],
                              halfdiag=0.5 * float(np.linalg.norm(rec["hi"] - rec["lo"])))
        for k in ("mtilde", "T", "w0t", "kt", "r_core"):
            out[k][i] = agg[k][0]
        for k in ("clo", "chi", "tlo", "thi"):
            out[k][i] = agg[k][0]
        out["ncore"][i] = agg["ncore"][0]
        out["ntail"][i] = agg["ntail"][0]
        out["mass_own"][i] = agg["mass"][0]
    tbl.rules[rule] = out
    return out


# ================================================================ 2. 界族（向量化）
def box_sep_vec(loA, hiA, loB, hiB):
    gap = np.maximum(np.maximum(loA - hiB, loB - hiA), 0.0)
    return np.sqrt(np.einsum("ij,ij->i", gap, gap))


def ker(x, y):
    """0.75/(x·y·(x+y))；任一下界非正 ⇒ +inf（不敢跳），与 fastpair._beta 同口径。"""
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        out = 0.75 / (x * y * (x + y))
    return np.where((x <= 0.0) | (y <= 0.0) | ~np.isfinite(out), INF, out)


def _mul(mprod, k):
    """质量积 × 核；空子块（质量积 0）不许把 0×inf 变成 nan。"""
    with np.errstate(invalid="ignore", over="ignore"):
        t = mprod * k
    return np.where(mprod > 0.0, t, 0.0)


def bound_half_agg(P, Q, variant):
    """点对集合 P/Q 的**半块口径**界（未乘 ×2）。P/Q 是 agg 字典。"""
    D = box_sep_vec(P["lo"], P["hi"], Q["lo"], Q["hi"])
    D2 = D * D
    aA, aB = P["w0min"] * D2 + P["kmin"], Q["w0min"] * D2 + Q["kmin"]
    tA, tB, TA, TB = P["mtilde"], Q["mtilde"], P["T"], Q["T"]
    mA, mB = P["mass"], Q["mass"]
    if variant == "old":
        return _mul(mA * mB, ker(aA, aB))
    aaA = P["w0t"] * D2 + P["kt"]
    aaB = Q["w0t"] * D2 + Q["kt"]
    # 含尾乘积按 m̃/T 显式展开（不用 mass − m̃m̃）：mass 在表路径上是 fastpair 存的
    # Node.mass，m̃/T 是我自己重排的求和，两套账只差浮点末位，混用会引入 1 ulp 的系统偏差。
    rest = tA * TB + TA * tB + TA * TB
    cc = _mul(tA * tB, ker(aaA, aaB))
    if variant == "V1":
        tail = _mul(rest, ker(P["kmin"], Q["kmin"]))
    elif variant == "V1BAD":                              # 负对照，不该用核内 κ̃
        tail = _mul(rest, ker(P["kt"], Q["kt"]))
    elif variant == "V2":
        tail = _mul(rest, ker(aA, aB))
    elif variant == "V3":
        tail = (_mul(tA * TB, ker(aaA, aB)) + _mul(TA * tB, ker(aA, aaB))
                + _mul(TA * TB, ker(aA, aB)))
    elif variant == "V4":
        Dcc = box_sep_vec(P["clo"], P["chi"], Q["clo"], Q["chi"])
        Dct = box_sep_vec(P["clo"], P["chi"], Q["tlo"], Q["thi"])
        Dtc = box_sep_vec(P["tlo"], P["thi"], Q["clo"], Q["chi"])
        Dtt = box_sep_vec(P["tlo"], P["thi"], Q["tlo"], Q["thi"])
        cc = _mul(tA * tB, ker(P["w0t"] * Dcc ** 2 + P["kt"], Q["w0t"] * Dcc ** 2 + Q["kt"]))
        tail = (_mul(tA * TB, ker(P["w0t"] * Dct ** 2 + P["kt"],
                                  Q["w0min"] * Dct ** 2 + Q["kmin"]))
                + _mul(TA * tB, ker(P["w0min"] * Dtc ** 2 + P["kmin"],
                                    Q["w0t"] * Dtc ** 2 + Q["kt"]))
                + _mul(TA * TB, ker(P["w0min"] * Dtt ** 2 + P["kmin"],
                                    Q["w0min"] * Dtt ** 2 + Q["kmin"])))
    else:
        raise KeyError(variant)
    return cc + tail


def slice_agg(agg, ids):
    m = len(agg["mass"])
    return {k: (v[ids] if np.ndim(v) >= 1 and len(v) == m else v) for k, v in agg.items()}


def bound_table(tbl, A, B, rule, variant):
    """节点对 (A,B) 的半块界；variant=="old" 时退回旧界（与 rule 无关）。"""
    src = tbl.rules["none"] if variant == "old" else tbl.rules[rule]
    return bound_half_agg(slice_agg(src, A), slice_agg(src, B), variant)


def bound_aggs(P, Q, variant):
    return bound_half_agg(P, Q, variant)


# ================================================== 3. 自顶向下模拟（与 _mac 同规则）
def run_mac(tbl, start, tau, rule, variant, mult=2.0):
    """前沿式（向量化）接受/拒绝。接受集与 `fastpair._mac` 相同，因为逐对判据只看自己。

    展开规则与 `_mac` 一字对齐：A 是叶 ⇒ 展开 B；B 是叶 ⇒ 展开 A；
    都是内部节点 ⇒ 展开盒对角线更长的一侧（相等时展开 A）。
    """
    A = np.concatenate([np.repeat(p[0], p[1].size) for p in start])
    B = np.concatenate([p[1] for p in start])
    src = tbl.rules["none"] if variant == "old" else tbl.rules[rule]
    res = dict(dropped=0, evaluated=0, cert=0.0, accepted=0, visited=0,
               leafpairs=0, ninf=0)
    it = 0
    while A.size:
        it += 1
        if it > 300:
            raise RuntimeError("前沿没收敛，展开写错了")
        bnd = mult * bound_half_agg(slice_agg(src, A), slice_agg(src, B), variant)
        acc = bnd <= tau
        if acc.any():
            res["dropped"] += int((tbl.npts[A[acc]] * tbl.npts[B[acc]]).sum())
            res["cert"] += float(bnd[acc].sum())
            res["accepted"] += int(acc.sum())
        rej = ~acc
        if not rej.any():
            break
        Ar, Br = A[rej], B[rej]
        la, lb = tbl.isleaf[Ar] == 1, tbl.isleaf[Br] == 1
        both = la & lb
        if both.any():
            res["evaluated"] += int((tbl.npts[Ar[both]] * tbl.npts[Br[both]]).sum())
            res["leafpairs"] += int(both.sum())
        ex = ~both
        if not ex.any():
            break
        res["visited"] += int(ex.sum())
        Ae, Be = Ar[ex], Br[ex]
        le_a, le_b = tbl.isleaf[Ae] == 1, tbl.isleaf[Be] == 1
        exp_b = le_a | (~le_b & (tbl.diag[Be] > tbl.diag[Ae]))
        A1 = np.where(exp_b, Ae, tbl.left[Ae]); B1 = np.where(exp_b, tbl.left[Be], Be)
        A2 = np.where(exp_b, Ae, tbl.right[Ae]); B2 = np.where(exp_b, tbl.right[Be], Be)
        A = np.concatenate([A1, A2]); B = np.concatenate([B1, B2])
    res["iters"] = it
    return res


# ============================================================== 4. 实际值（真值锚）
def actual_half(F, iA, iB):
    return float(nlc.pair_energy(F["X"], F["wr"], F["w0"], F["kap"], iA, iB))


def _ratios(bnds, mults, acts):
    """返回 (违反次数, 最坏 actual/bound, 最坏 bound/actual)。违反必须为 0。"""
    b = np.asarray(bnds, dtype=float) * np.asarray(mults, dtype=float)
    acts = np.asarray(acts, dtype=float)
    bad = b + 1e-18 < acts
    viol = int(bad.sum())
    worst_v = float((acts[bad] / np.maximum(b[bad], 1e-300)).max()) if viol else 0.0
    pos = acts > 0.0
    worst_r = float((b[pos] / acts[pos]).max()) if pos.any() else INF
    return viol, worst_v, worst_r, pos


def check_bounds(F, tbl, live, rng):
    """Q1：界成立性。树上节点对 + 随机点集，逐 (rule,variant) 打最坏比值。

    口径：×2 用于不同原子对（pair_energy 返回半块），×1 用于同原子内的对。
    实际值 `pair_energy` 每对只算**一次**，所有变体共用，否则会被抽样成本压垮。
    """
    roots = [(a, b) for i, a in enumerate(live) for b in live[i + 1:]]
    ids_of = {a: tbl.ids_of(a) for a in live}
    pairs = [(tbl.base[a], tbl.base[b], 2.0) for a, b in roots]        # 15 个根对必测
    tried = 0
    while len(pairs) < NPAIR_TREESTATS + len(roots) and tried < 40000:
        tried += 1
        a, b = rng.choice(live, 2, replace=(len(live) == 1))
        A, B = int(rng.choice(ids_of[int(a)])), int(rng.choice(ids_of[int(b)]))
        if a == b and A == B:
            continue
        if tbl.npts[A] * tbl.npts[B] > MAX_PTS_PROD:
            continue
        pairs.append((A, B, 1.0 if a == b else 2.0))
    # 同一原子内的块对（自身项）：fastpair 从不跳它，但每节点成立性应无条件成立
    while len(pairs) < NPAIR_TREESTATS + len(roots) + NPAIR_TREESTATS // 3 \
            and tried < 80000:
        tried += 1
        a = int(rng.choice(live))
        A, B = (int(rng.choice(ids_of[a])) for _ in range(2))
        if tbl.npts[A] * tbl.npts[B] <= MAX_PTS_PROD:
            pairs.append((A, B, 1.0))
    Av = np.array([p[0] for p in pairs]); Bv = np.array([p[1] for p in pairs])
    mv = np.array([p[2] for p in pairs])
    acts = np.array([abs(actual_half(F, tbl.idx[a], tbl.idx[b])) for a, b in zip(Av, Bv)])

    owner = F["owner_kept"]
    subs = []
    for _ in range(NPAIR_SUBSET):
        a, b = rng.choice(live, 2, replace=(len(live) == 1))
        ia = np.flatnonzero(owner == a); ib = np.flatnonzero(owner == b)
        na = int(rng.integers(4, min(300, ia.size - 1) + 1))
        nb = int(rng.integers(4, min(300, ib.size - 1) + 1))
        sa = rng.choice(ia, na, replace=False); sb = rng.choice(ib, nb, replace=False)
        subs.append((sa, sb, 1.0 if a == b else 2.0))
    sub_acts = np.array([abs(actual_half(F, sa, sb)) for sa, sb, _ in subs])
    sub_smult = np.array([m for _, _, m in subs])
    # 随机点集：每个 (rule) 只建一次聚合量，四个变体共用
    subagg = {}
    for rule in RULES:
        lst = []
        for sa, sb, _ in subs:
            ca = (F["X"][sa] * np.abs(F["wr"][sa])[:, None]).sum(0) / np.abs(F["wr"][sa]).sum()
            cb = (F["X"][sb] * np.abs(F["wr"][sb])[:, None]).sum(0) / np.abs(F["wr"][sb]).sum()
            P, _ = agg_from_idx(F["X"], F["wr"], F["w0"], F["kap"], sa, rule, centroid=ca)
            Q, _ = agg_from_idx(F["X"], F["wr"], F["w0"], F["kap"], sb, rule, centroid=cb)
            lst.append((P, Q))
        subagg[rule] = lst

    print(f"\n[Q1] 界成立性（真实场）：节点对 {len(pairs)} 组（含全部 {len(roots)} 个原子根对，"
          f"随机对限制 npts 积 ≤ {MAX_PTS_PROD:.0e}）/ 随机点集 {len(subs)} 组")
    print(f"{'rule':>9} {'variant':>8} {'组数':>6} {'违反':>5} {'最坏 actual/bound':>18} "
          f"{'最坏 bound/actual':>18} {'中位 bound/actual':>17}")
    rows = {}
    combos = [("none", "old")] + [(r, v) for r in RULES[1:] for v in VARIANTS]
    combos += [("mass", "V1BAD"), ("halfdiag", "V1BAD")]
    for rule, variant in combos:
        r_tab = "none" if variant == "old" else rule
        bv = np.array([bound_table(tbl, np.array([A]), np.array([B]),
                                   r_tab, variant)[0] for A, B in zip(Av, Bv)])
        rr = "none" if variant == "old" else rule
        bs = np.array([float(bound_half_agg(P, Q, variant)[0]) for P, Q in subagg[rr]])
        v1, w1, m1, pos1 = _ratios(bv, mv, acts)
        v2, w2, m2, pos2 = _ratios(bs, sub_smult, sub_acts)
        allb = np.concatenate([bv * mv, bs * sub_smult])
        alla = np.concatenate([acts, sub_acts])
        ok = alla > 0.0
        med = float(np.median(allb[ok] / alla[ok])) if ok.any() else INF
        rows[(rule, variant)] = (v1 + v2, max(w1, w2), min(m1, m2), len(pairs) + len(subs))
        flag = "   <-- 负对照，故意让它破" if variant == "V1BAD" else ""
        print(f"{rule:>9} {variant:>8} {len(pairs)+len(subs):>6d} {v1+v2:>5d} "
              f"{max(w1, w2):>18.3e} {min(m1, m2):>18.3e}{med:>17.3e}{flag}")
    nviol = sum(v[0] for k, v in rows.items() if k[1] != "V1BAD")
    return rows, nviol


# ==================================== 5. r_core 规则本身的检查（Q1 可加性 / Q3 画像）
def check_additivity(tbl, live):
    """Q1 第一半：m̃ + T == m、核与尾不重不漏、核/尾子盒 ⊆ 父盒、叶子划分原子块。

    `m` 取 fastpair 存在 Node 上的 mass（不是我这一路算出来的数）⇒ 这条比的是
    两套独立记账，不是拿自己的输出对对自己的输出。
    """
    print(f"\n[Q1] 可加性/不重不漏（节点表 {tbl.n} 个节点 × {len(RULES)} 种 r_core 取法）")
    print(f"{'rule':>9} {'节点数':>7} {'max|mt+T-m|':>13} {'max 相对':>11} "
          f"{'重排 ulp 底':>12} {'ncore+ntail!=npts':>18} {'子盒越界':>10} "
          f"{'T=0 节点':>9} {'空核节点':>9}")
    res = {}
    for rule in RULES:
        agg = tbl.rules[rule]
        dev = np.abs(agg["mtilde"] + agg["T"] - agg["mass"])
        rel = dev / np.maximum(agg["mass"], 1e-300)
        own = np.abs(agg["mass_own"] - agg["mass"]) / np.maximum(agg["mass"], 1e-300)
        bad = int(((agg["ncore"] + agg["ntail"]) != agg["npts"]).sum())
        esc = int(((agg["clo"] < agg["lo"] - 1e-12) | (agg["chi"] > agg["hi"] + 1e-12)
                   | (agg["tlo"] < agg["lo"] - 1e-12) | (agg["thi"] > agg["hi"] + 1e-12)).sum())
        res[rule] = dict(max_abs=float(dev.max()), max_rel=float(rel.max()),
                         bad=bad, esc=esc)
        print(f"{rule:>9} {tbl.n:>7d} {dev.max():>13.3e} {rel.max():>11.3e} "
              f"{own.max():>12.3e} {bad:>18d} {esc:>10d} "
              f"{int((agg['T'] <= 0).sum()):>9d} {int((agg['mtilde'] <= 0).sum()):>9d}")
        assert bad == 0 and esc == 0 and rel.max() < 1e-12, f"{rule}: 可加性/包含前提不过"
    print("    ⇒ 断言通过：核与尾是**精确的索引集划分**（质量只对到浮点末位，"
          "末位量级见『重排 ulp 底』一栏）；核盒/尾盒 ⊆ 父盒 ⇒ 切分没动"
          "『叶子的盒仍包含其全部点』这一前提。")
    # 独立记账：叶子必须不重不漏地覆盖原子块，且每点的核/尾归属各计一次
    tot_pts = 0
    for a in live:
        rid = tbl.base[a]
        lids = tbl.ids_of(a, only_leaves=True)
        pts = np.concatenate([tbl.idx[i] for i in lids])
        assert np.unique(pts).size == pts.size == int(tbl.npts[rid]), \
            f"atom {a}: 叶子不是原子块的划分"
        assert np.array_equal(np.sort(pts), np.sort(tbl.idx[rid])), f"atom {a}: 覆盖集合不符"
        for rule in RULES:
            agg = tbl.rules[rule]
            s = int(agg["ncore"][lids].sum() + agg["ntail"][lids].sum())
            assert s == int(tbl.npts[rid]), f"atom {a}/{rule}: 叶子核尾计数 {s} != {tbl.npts[rid]}"
        tot_pts += int(tbl.npts[rid])
    print(f"    叶子覆盖核对：{len(live)} 个原子块共 {tot_pts:,} 点，"
          f"每点在恰好一个叶子里、且在其叶子的核或尾里恰好一次（全部断言通过）。")
    agg = tbl.rules["mass"]
    fr = agg["T"] / np.maximum(agg["mass"], 1e-300)
    print(f"    规则 mass：max(T/m) = {fr.max():.3e}（门限 {TAIL_EPS:.0e}），"
          f"超门槛节点 = {int((fr > TAIL_EPS + 1e-12).sum())}")
    # 质量分解恒等式：m_A m_B = m̃_A m̃_B + 含尾三项（同一套 mass_own 账）
    rng = np.random.default_rng(5)
    ids = rng.choice(tbl.n, size=(40, 2))
    dev_own = dev_np = 0.0
    for rule in RULES[1:]:
        a = tbl.rules[rule]
        for A, B in ids:
            rhs = (a["mtilde"][A] * a["mtilde"][B] + a["mtilde"][A] * a["T"][B]
                   + a["T"][A] * a["mtilde"][B] + a["T"][A] * a["T"][B])
            lhs_own = a["mass_own"][A] * a["mass_own"][B]
            lhs_np = a["mass"][A] * a["mass"][B]
            dev_own = max(dev_own, abs(lhs_own - rhs) / max(abs(lhs_own), 1e-300))
            dev_np = max(dev_np, abs(lhs_np - rhs) / max(abs(lhs_np), 1e-300))
    print(f"    恒等式 m·m = m̃m̃ + m̃T + Tm̃ + TT：最大相对偏差 自算质量 {dev_own:.3e}"
          f" / fastpair 存量 {dev_np:.3e}（差在浮点末位，不是划分错）")
    return res


def rule_profile(tbl, live):
    """各规则把多少质量划成尾、核内 κ̃ 比全块 κ 抬了多少（紧度的来源）。"""
    print(f"\n[Q3] r_core 取法画像")
    print(f"{'rule':>9} {'mean T/m':>10} {'max T/m':>10} {'mean κ̃/κ':>11} "
          f"{'min κ̃/κ':>10} {'mean w̃0/w0':>12} {'切分节点数':>10}")
    for rule in RULES:
        a = tbl.rules[rule]
        fr = a["T"] / np.maximum(a["mass"], 1e-300)
        kr = a["kt"] / np.maximum(a["kmin"], 1e-300)
        gr = a["w0t"] / np.maximum(a["w0min"], 1e-300)
        print(f"{rule:>9} {fr.mean():>10.3e} {fr.max():>10.3e} {kr.mean():>11.3e} "
              f"{kr.min():>10.3e} {gr.mean():>12.3e} {int((a['T'] > 0).sum()):>10d}")
    print("    树根（整原子块）的 κ^min vs 核内 κ̃^min、w0^min vs w̃0^min：")
    for a in live:
        rid = tbl.base[a]
        s = f"      atom {a}:"
        for rule in RULES[1:]:
            ag = tbl.rules[rule]
            s += (f"  [{rule}] κ̃={ag['kt'][rid]:.3f} w̃0={ag['w0t'][rid]:.2e} "
                  f"T/m={ag['T'][rid]/ag['mass'][rid]:.2e}")
        ag0 = tbl.rules["none"]
        print(s + f"   (全块 κ={ag0['kmin'][rid]:.3f} w0={ag0['w0min'][rid]:.2e})")


# ======================================================== 6. Q2：普查与 MAC 模拟
def census(tbl, F, live):
    """旧节点界 vs 新节点界：根对逐项、叶对总和、低于门限的对数、界/实际最坏比。"""
    roots = [(a, b) for i, a in enumerate(live) for b in live[i + 1:]]
    keys = ["none/old"] + [f"{r}/{v}" for r in RULES[1:] for v in VARIANTS]

    def get(key):
        return ("none", "old") if key == "none/old" else tuple(key.split("/"))

    print(f"\n[Q2a] 原子根对普查（{len(roots)} 对，×2 口径，单位 Ha）")
    print(f"{'pair':>6} {'D_盒(Å)':>8} {'2|exact|':>11} " + "".join(f"{k:>14}" for k in keys))
    rt = {k: dict(sum=0.0, le={t: 0 for t in CENSUS_T}, worst=0.0) for k in keys}
    for a, b in roots:
        A = np.array([tbl.base[a]]); B = np.array([tbl.base[b]])
        ag0 = tbl.rules["none"]
        D = box_sep_vec(ag0["lo"][A], ag0["hi"][A], ag0["lo"][B], ag0["hi"][B])[0]
        act = 2.0 * abs(actual_half(F, tbl.idx[int(A[0])], tbl.idx[int(B[0])]))
        line = f"{a:>3}-{b:<2} {D*BOHR2A:>8.3f} {act:>11.3e} "
        for k in keys:
            rule, variant = get(k)
            v = 2.0 * bound_table(tbl, A, B, rule, variant)[0]
            rt[k]["sum"] += float(v)
            for t in CENSUS_T:
                rt[k]["le"][t] += int(v <= t)
            rt[k]["worst"] = max(rt[k]["worst"], float(v) / max(act, 1e-300))
            line += f"{v:>14.3e}"
        print(line)
    base = rt["none/old"]["sum"]
    print("    根对界总和(Ha) / 相对旧界 / 界 ≤ 门限 的对数：")
    print(f"{'rule/variant':>16} {'sum':>12} {'old/new':>10}" +
          "".join(f"{'<='+format(t,'g'):>12}" for t in CENSUS_T) + f"{'worst b/e':>12}")
    for k in keys:
        s = rt[k]["sum"]
        print(f"{k:>16} {s:>12.3e} {(base/s if s > 0 else INF):>10.3e}" +
              "".join(f"{rt[k]['le'][t]:>12d}" for t in CENSUS_T) +
              f"{rt[k]['worst']:>12.3e}")

    # 叶对普查（全部 叶×叶 对）
    leaf_ids = {a: tbl.ids_of(a, only_leaves=True) for a in live}
    nlp = sum(len(leaf_ids[a]) * len(leaf_ids[b]) for a, b in roots)
    print(f"\n[Q2b] 叶对普查（{nlp:,} 个 叶×叶 对，×2 口径）")
    lt = {k: dict(sum=0.0, le={t: 0 for t in CENSUS_T}) for k in keys}
    rng = np.random.default_rng(11)
    sample = []
    for a, b in roots:
        IA, IB = leaf_ids[a], leaf_ids[b]
        Ah = np.repeat(IA, len(IB)); Bh = np.tile(IB, len(IA))
        for k in keys:
            rule, variant = get(k)
            v = 2.0 * bound_table(tbl, Ah, Bh, rule, variant)
            lt[k]["sum"] += float(v.sum())
            for t in CENSUS_T:
                lt[k]["le"][t] += int((v <= t).sum())
        pick = rng.choice(Ah.size, size=min(NLEAF_ACTUAL // len(roots), Ah.size),
                          replace=False)
        sample.append((Ah[pick], Bh[pick]))
    print(f"{'rule/variant':>16} {'sum(bnd) Ha':>13} {'old/new':>10} " +
          "".join(f"{'#<='+format(t,'g'):>12}" for t in CENSUS_T))
    for k in keys:
        s = lt[k]["sum"]
        print(f"{k:>16} {s:>13.3e} {(lt['none/old']['sum']/s if s > 0 else INF):>10.3e} " +
              "".join(f"{lt[k]['le'][t]:>12,d}" for t in CENSUS_T))
    print(f"    叶对总数 {nlp:,} ⇒ 旧界能整块跳掉的叶对占比 "
          f"{lt['none/old']['le'][1e-12]/nlp:.3%}（τ=1e-12）")

    print(f"\n[Q2c] 界/实际 最坏比值（叶对抽样 {sum(len(s[0]) for s in sample)} 对）")
    worst = {}
    for Ah, Bh in sample:
        acts = np.array([abs(actual_half(F, tbl.idx[int(x)], tbl.idx[int(y)]))
                         for x, y in zip(Ah, Bh)])
        pos = acts > 0.0
        if not pos.any():
            continue
        for k in keys:
            rule, variant = get(k)
            v = 2.0 * bound_table(tbl, Ah, Bh, rule, variant)
            worst[k] = max(worst.get(k, 0.0), float((v[pos] / acts[pos]).max()))
    for k in sorted(keys, key=lambda z: worst.get(z, INF)):
        print(f"    {k:>16} 最坏 bound/|actual| = {worst[k]:>10.3e}")
    return rt, lt, worst


def dominance(tbl, live):
    """两条结构性核对（用全部叶对，不抽样）：

      1) rule=none（T=0）时四个变体必须**逐位**退回 `old` ⇒ 新界是旧界的严格推广；
      2) V2/V3/V4 必须 ≤ old（V1 可以更大，因为它把含尾乘积按 D=0 计）。
    """
    roots = [(a, b) for i, a in enumerate(live) for b in live[i + 1:]]
    print(f"\n[Q2f] 与旧界的逐位/恒等关系（全部叶对，×2 口径）")
    st = {("none", v): 0.0 for v in VARIANTS}
    rel = {v: 0.0 for v in VARIANTS}
    over = {v: 0 for v in VARIANTS}
    ntot = 0
    for a, b in roots:
        IA, IB = tbl.ids_of(a, only_leaves=True), tbl.ids_of(b, only_leaves=True)
        Ah = np.repeat(IA, len(IB)); Bh = np.tile(IB, len(IA))
        old = 2.0 * bound_table(tbl, Ah, Bh, "none", "old")
        ntot += int(Ah.size)
        for v in VARIANTS:
            nn = 2.0 * bound_table(tbl, Ah, Bh, "none", v)      # T=0 ⇒ 应当 == old
            st[(("none"), v)] = max(st[("none", v)],
                                    float(np.abs(nn - old).max()))
            got = 2.0 * bound_table(tbl, Ah, Bh, "halfdiag", v)
            d = got - old
            rel[v] = max(rel[v], float((d / np.maximum(old, 1e-300)).max()))
            over[v] += int((got > old * (1.0 + 1e-12)).sum())
    print(f"    叶对 {ntot:,} 个；rule=none 时 |变体−old| 最大绝对差（期望是求和次序带来的"
          f"浮点末位，量级 ~1e-16×m²；若到 1e-10 就是真 bug）："
          + "  ".join(f"{v}={st[('none', v)]:.3e}" for v in VARIANTS))
    print(f"    halfdiag 相对 old 的最大 (新−old)/old：" +
          "  ".join(f"{v}={rel[v]:+.3e}" for v in VARIANTS))
    print(f"    新界严格大于旧界的叶对数（容差 1e-12）：" +
          "  ".join(f"{v}={over[v]}" for v in VARIANTS))
    for v in ("V2", "V3", "V4"):
        assert over[v] == 0, f"{v} 在 {over[v]} 个叶对上超过旧界，单调收紧的说法不成立"
    return dict(bit=st, rel=rel, over=over, n=ntot)


def mac_census(tbl, live, exact, old_run):
    """τ 预算下能跳掉的点对占比：旧界 vs 新界，同一棵树、同一展开规则。"""
    roots = [(a, b) for i, a in enumerate(live) for b in live[i + 1:]]
    start = [(np.array([tbl.base[a]]), np.array([tbl.base[b]])) for a, b in roots]
    far, self_pp = exact["pointpairs_far"], exact["pointpairs_self"]
    denom = far + self_pp
    keys = ["none/old"] + [f"{r}/{v}" for r in RULES[1:] for v in VARIANTS]

    def get(k):
        return ("none", "old") if k == "none/old" else tuple(k.split("/"))

    print(f"\n[Q2d] MAC 模拟（前沿式，展开规则与 _mac 一致；可跳占比 = dropped/(far+self)）")
    print(f"    far={far:,}  self={self_pp:,}  denom={denom:,}")
    if old_run is not None:
        print(f"    归档口径核对：τ=1e-12 旧界 accepted={old_run['n_accepted']:,} "
              f"cert={old_run['cert_err']:.4e} evaluated点对="
              f"{old_run['pointpairs_evaluated']:,} 省下={1-old_run['total_frac']:.3%}")
    out = {}
    for tau in TAUS_MAC:
        print(f"\n  τ={tau:.0e} Ha"
              f"{'accepted':>11}{'dropped点对':>16}{'可跳占比':>10}{'cert(Ha)':>12}"
              f"{'叶对评估':>10}{'闭合':>8}")
        for k in keys:
            rule, variant = get(k)
            rs = run_mac(tbl, start, tau, rule, variant)
            frac = rs["dropped"] / denom if denom else 0.0
            out[(k, tau)] = dict(frac=frac, cert=rs["cert"], acc=rs["accepted"],
                                 drop=rs["dropped"], eval=rs["evaluated"],
                                 leafpairs=rs["leafpairs"], visited=rs["visited"])
            closed = "OK" if rs["dropped"] + rs["evaluated"] == far else "MISS"
            print(f"    {k:>16}{rs['accepted']:>11,d}{rs['dropped']:>16,d}"
                  f"{frac:>10.3%}{rs['cert']:>12.3e}{rs['leafpairs']:>10,d}{closed:>8}")
            if k == "none/old":
                assert closed == "OK", "接受集没有划分 P×Q，我的 MAC 复刻有 bug"
                if old_run is not None and tau == 1e-12:
                    # fastpair 基准只在 τ=1e-12 这一档跑过，别的档没有对照物
                    assert rs["accepted"] == old_run["n_accepted"], \
                        f"旧界接受数对不上 {rs['accepted']} vs {old_run['n_accepted']}"
                    assert rs["evaluated"] == old_run["pointpairs_evaluated"], \
                        f"旧界评估点对对不上 {rs['evaluated']} vs " \
                        f"{old_run['pointpairs_evaluated']:,}"
                    assert abs(rs["cert"] - old_run["cert_err"]) <= \
                        1e-8 * max(old_run["cert_err"], 1e-300), \
                        f"旧界 cert 对不上 {rs['cert']:.6e} vs {old_run['cert_err']:.6e}"
        if tau == 1e-12:
            base = out[("none/old", tau)]["frac"]
            best = max([k for k in keys if k != "none/old"],
                       key=lambda z: out[(z, tau)]["frac"])
            print(f"    ⇒ τ=1e-12 旧 {base:.3%} → 新最好 {out[(best,tau)]['frac']:.3%}"
                  f"（{best}），倍数 {out[(best,tau)]['frac']/max(base,1e-15):.1f}x")
    return out


def subadditivity(tbl, live, rng, n=NMONO):
    """往下走会不会把界推高：bound(P,Q) vs bound(P左,Q)+bound(P右,Q)。

    可靠性只要求"每节点自己的界 ≥ 该节点块"（第 4 节已测）；这条量的是**效率**——
    球版当年就是死在它上面（细化后界反而更大 ⇒ 树白建）。
    """
    print(f"\n[Q2e] 细化次可加性（父界 vs 两子界之和；抽样 {n} 组节点对）")
    cand = []
    for i, a in enumerate(live):
        for b in live[i + 1:]:
            for x in tbl.ids_of(a):
                if tbl.isleaf[x]:
                    continue
                for y in tbl.ids_of(b):
                    cand.append((int(x), int(y)))
    picks = rng.choice(len(cand), size=min(n, len(cand)), replace=False)
    cand = [cand[p] for p in picks]
    print(f"{'rule/variant':>16}{'测过':>8}{'父<子和':>10}{'最坏 子和/父':>14}")
    res = {}
    for k in ["none/old"] + [f"{r}/{v}" for r in RULES[1:] for v in VARIANTS]:
        rule, variant = (("none", "old") if k == "none/old" else tuple(k.split("/")))
        npar = len(cand)
        A = np.array([x for x, _ in cand]); B = np.array([y for _, y in cand])
        par = bound_table(tbl, A, B, rule, variant)
        cl = bound_table(tbl, tbl.left[A], B, rule, variant)
        cr = bound_table(tbl, tbl.right[A], B, rule, variant)
        s = cl + cr
        ok = np.isfinite(par) & np.isfinite(s) & (par > 0)
        bad = ok & (s > par + 1e-18)
        worst = float((s[bad] / par[bad]).max()) if bad.any() else 0.0
        res[k] = (int(bad.sum()), npar, worst)
        print(f"{k:>16}{npar:>8d}{int(bad.sum()):>10d}{worst:>14.3e}")
    return res


# ================================================ 7. 合成场（不调 PySCF 的定理复核）
def adversarial_tail_kernel():
    """最小构造夹具：证明"含尾乘积的 sup|Φ| 只能用**全块** κ^min"。

    随机抽样很难抓到这条（尾巴点自己带的 |wr| 极小，它的贡献被质量因子压掉了），
    所以光报"负对照 0 次违反"是空的。这里把它做成能手算的反例：
      点 1：ρ=0.3（核内，κ₁ 大），|wr|=1
      点 2：ρ≈rho_floor（尾巴，κ₂≈0.12），|wr|=0.009 ≤ 1% ⇒ 按规则 (a) 落在尾集合
      两点距离 0.2 bohr ⇒ 核盒与尾盒几乎重合
    自身块 (idx, idx) 的真实值里，0.5·w₂²·|Φ₂₂| = 0.5·w₂²·3/(4κ₂³) 由 κ₂ 决定；
    而把含尾项的核换成**核内** κ̃=κ₁ 之后，界小 κ₁³/κ₂³ 倍 ⇒ 直接跌破真实值。
    """
    b, C = 6.0, 0.01
    rho = np.array([0.3, 1.1 * nlc.RHO_FLOOR])
    sig = np.array([1e-3, 1e-8])
    w0, kap, _ = nlc.vv10_fields(rho, sig, b=b, C=C)
    coords = np.array([[0.0, 0.0, 0.0], [0.2, 0.0, 0.0]])
    wr = np.array([1.0, 0.009])
    idx = np.arange(2)
    P, core = agg_from_idx(coords, wr, w0, kap, idx, "mass")
    act = abs(float(nlc.pair_energy(coords, wr, w0, kap, idx, idx)))
    out = {v: float(bound_half_agg(P, P, v)[0])
           for v in ("old", "V1", "V2", "V3", "V4", "V1BAD")}
    print(f"\n[Q1g] 负对照夹具（2 点，核内 κ̃={P['kt'][0]:.4f}，全块 κ={P['kmin'][0]:.4f}，"
          f"尾质量占比 {P['T'][0]/P['mass'][0]:.3%}，核内点数 {int(core.sum())}/2）")
    print(f"    真实 |pair_energy(idx,idx)| = {act:.6e} Ha（自身块，×1 口径）")
    for v in ("old", "V1", "V2", "V3", "V4", "V1BAD"):
        verdict = "成立" if out[v] + 1e-18 >= act else "**破了，界 < 实际**"
        print(f"    {v:>6} bound = {out[v]:.6e}   bound/actual = {out[v]/act:.3e}   {verdict}")
    assert out["V1BAD"] < act, "负对照没破：这条测试是空的，得重做夹具"
    for v in ("old", "V1", "V2", "V3", "V4"):
        assert out[v] + 1e-18 >= act, f"{v} 在自己的夹具上破了"
    return act, out


def synthetic_check(n=200):
    coords0 = np.random.default_rng(3).normal(scale=4.0, size=(400, 3))
    rng = np.random.default_rng(3)
    coords = coords0
    rho = np.exp(rng.normal(scale=1.5, size=400)) * 1e-3
    sig = np.abs(rng.normal(size=400)) * 1e-2
    weights = rng.uniform(1e-4, 1e-3, size=400)
    w0, kap, keep = nlc.vv10_fields(rho, sig, b=6.0, C=0.01)
    idx = np.flatnonzero(keep)
    wr = weights * rho
    nviol = 0
    worst = 0.0
    tested = 0
    for _ in range(n):
        nA = int(rng.integers(4, idx.size // 2)); nB = int(rng.integers(4, idx.size // 2))
        A = rng.choice(idx, nA, replace=False); B = rng.choice(idx, nB, replace=False)
        act = abs(float(nlc.pair_energy(coords, wr, w0, kap, A, B)))
        for rule in RULES:
            ca = (coords[A] * np.abs(wr[A])[:, None]).sum(0) / np.abs(wr[A]).sum()
            cb = (coords[B] * np.abs(wr[B])[:, None]).sum(0) / np.abs(wr[B]).sum()
            P, _ = agg_from_idx(coords, wr, w0, kap, A, rule, centroid=ca)
            Q, _ = agg_from_idx(coords, wr, w0, kap, B, rule, centroid=cb)
            for variant in (("old",) if rule == "none" else VARIANTS):
                bnd = float(bound_half_agg(P, Q, variant)[0])
                tested += 1
                if act > 0:
                    worst = max(worst, bnd / act)
                if bnd + 1e-18 < act:
                    nviol += 1
    return tested, nviol, worst


# ==================================================================== 8. 主流程
def main(level=1, with_fastpair=True):
    global mf
    mol = gto.M(atom=geomlib.h2o_dimer(), basis=BASIS, verbose=0, unit="Angstrom")
    mf = dft.RKS(mol); mf.xc = XC; mf.grids.level = level; mf.kernel()
    print(f"=== coretail_bound  水二聚体 {BASIS}  xc={XC}  level={level}  scheme=becke")
    print(f"    SCF E={mf.e_tot:.10f} Ha；耗时 NOT_MEASURED（本机多代理并发，不作计时结论）")
    F = build_fields(mol, level)
    live = [b.atom for b in F["blocks"] if b is not None]
    print(f"    网格点 {F['n_grid']}，保留 {F['n_kept']}，活原子 {live}")

    tbl = Table([flatten_tree(b.tree, b.atom, b.idx) for b in F["blocks"] if b is not None])
    print(f"    节点总数 {tbl.n}（叶 {int(tbl.isleaf.sum())}，内部 "
          f"{tbl.n - int(tbl.isleaf.sum())}），最大深度 {int(tbl.depth.max())}")
    for rule in RULES:
        apply_rule(tbl, F["X"], F["wr"], F["w0"], F["kap"], rule)

    exact = fastpair.screened_decomposition(mol, mf, level=level, scheme="becke")
    old_run = (fastpair.screened_decomposition(mol, mf, level=level, scheme="becke",
                                               screen=1e-12) if with_fastpair else None)
    print(f"\n[0] fastpair 基准：E_pair={exact['E_pair']:.6e} Ha  E_nl={exact['E_nl']:.6e} Ha"
          f"  叶 {exact['n_leaves']}  叶对 {exact['n_leafpairs_total']:,}")
    if old_run is not None:
        print(f"    τ=1e-12 旧界实测：accepted={old_run['n_accepted']:,} "
              f"visited={old_run['n_visited']:,} "
              f"leafpairs={old_run['n_leafpairs_evaluated']:,}/"
              f"{old_run['n_leafpairs_total']:,} cert={old_run['cert_err']:.4e} Ha "
              f"|dE|={abs(old_run['E_nl']-exact['E_nl']):.3e} Ha  "
              f"省下点对占比={1-old_run['total_frac']:.3%}")
        assert old_run["cert_err"] + 1e-18 >= abs(old_run["E_nl"] - exact["E_nl"]), "旧界破了"

    rng = np.random.default_rng(20260929)
    check_additivity(tbl, live)
    rows, nviol = check_bounds(F, tbl, live, rng)
    vbad = rows.get(("mass", "V1BAD"), (0, 0, 0, 0))
    print(f"\n[Q1 结论] 除负对照外全部 (rule,variant) 组合共 {nviol} 次违反（要求 0）。")
    print(f"    注意：真实抽样**抓不到**负对照 V1BAD（它违反 {vbad[0]} 次）——尾巴点自带的"
          f" |wr| 极小，含尾乘积的真实值被质量因子压掉了。所以『含尾项只能用全块 κ^min』"
          f"这条不能靠抽样立，必须靠下面 Q1g 的手算夹具立。")
    n, nv, wst = synthetic_check(200)
    print(f"[Q1 补充] 合成场（rho>0、权重>0、sigma>=0；{n} 次判据评估）：违反 {nv} 次，"
          f"最坏 bound/actual = {wst:.3e}")
    adversarial_tail_kernel()

    rule_profile(tbl, live)
    dom = dominance(tbl, live)
    rt, lt, worst = census(tbl, F, live)
    mac = mac_census(tbl, live, exact, old_run)
    subadditivity(tbl, live, rng)

    key = 1e-12
    oldfrac = mac[("none/old", key)]["frac"]
    best = max([k for k, t in mac if t == key and k != "none/old"],
               key=lambda z: mac[(z, key)]["frac"])
    newfrac = mac[(best, key)]["frac"]
    nlpairs = len(live) * (len(live) - 1) // 2
    bestsum = min(lt[k]["sum"] for k in lt if k != "none/old")
    bestk_sum = min((k for k in lt if k != "none/old"), key=lambda z: lt[z]["sum"])
    print("\n" + "=" * 78)
    print("[判定摘要]")
    print(f"    τ=1e-12：可跳点对占比 旧 {oldfrac:.3%} → 新最好 {newfrac:.3%}"
          f"（{best}），{newfrac/max(oldfrac,1e-15):.2f}x；归档基线 12.349%"
          f"（`logs/20260929T101447Z_probe_bound_forms.out:24`）")
    print(f"    翻盘阈值（简报给的）：>30% ⇒ {'达到' if newfrac > 0.30 else '未达到'}"
          f"；本体系实测 {newfrac:.3%}")
    print(f"    叶对界总和：旧 {lt['none/old']['sum']:.3e} Ha → 新最好 "
          f"{bestsum:.3e} Ha（{bestk_sum}，{lt['none/old']['sum']/bestsum:.2f}x）")
    print(f"    叶对界 ≤1e-12 Ha 的对数：旧 {lt['none/old']['le'][1e-12]:,} → 新最好 "
          f"{max(lt[k]['le'][1e-12] for k in lt if k != 'none/old'):,}"
          f"（共 {exact['n_leafpairs_total']:,} 个叶对）")
    print(f"    根对界 ≤1e-12 Ha：旧 {rt['none/old']['le'][1e-12]}/{nlpairs}，"
          f"新最好 {max(rt[k]['le'][1e-12] for k in rt if k!='none/old')}/{nlpairs}"
          f"（根对界总和 {rt['none/old']['sum']:.3e} → "
          f"{min(rt[k]['sum'] for k in rt if k!='none/old'):.3e} Ha）")
    print(f"    可证性：非负对照违反 {nviol} 次；新界是旧界的严格推广"
          f"（rule=none 时 |变体−old| 最大 {max(dom['bit'].values()):.3e}；"
          f"V2/V3/V4 超过旧界的叶对数 {dom['over']['V2']}/{dom['over']['V3']}/{dom['over']['V4']}"
          f"，共 {dom['n']:,} 个叶对）。负对照在真实抽样里 {vbad[0]} 次没抓到，"
          f"靠 Q1g 夹具才证伪。")
    print(f"    墙钟/加速比：NOT_MEASURED（本机多代理并发）。")


if __name__ == "__main__":
    main(level=int(sys.argv[1]) if len(sys.argv) > 1 else 1)
