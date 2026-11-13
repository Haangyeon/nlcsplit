"""A2a：VV10 双重和的**可证屏蔽**，保住 (i, j) 成对结构。

这是计划书 crisp-brook-smew.md 里 B 案（P2）的我方实现，与 ide-qoder 的
`fastpair_ide.py` **相互独立**：本模块不 import、不参考对方文件，两边各自对
三个外部锚点负责（全量 `nlc.pair_energy`、PySCF 原生核、ORCA 6.0.1）。

判据
----
同一中心配对下
    g = w0_i R² + κ_i ,  g' = w0_j R² + κ_j ,  |Φ| = 3 / (2 g g' (g + g'))
在 κ>0、w0>0 时 |Φ| 对 g、g' 均单调递减。于是对两个点集 P、Q，用**它们之间可达的
最短距离** D、各自的下界 a_P = w0_P^min·D² + κ_P^min，以及密度质量 m_P = Σ|wr|：

    bound(P,Q) = 0.75 · m_P m_Q / ( a_P a_Q (a_P + a_Q) )

它界住的是 **半块** |0.5·ΣΣ_{i∈P,j∈Q} wr_i wr_j Φ|，即 `nlc.pair_energy` 的返回口径。
ρ≥0、求积权重>0、Φ<0 ⇒ 块内**没有**符号抵消可用，所以质量因子取绝对值是对的，
不是 looseness 的来源。

D 从哪来：必须用**盒**，不能用"质心 + 最大半径"的球（这条是踩出来的）
--------------------------------------------------------------------
球版看起来更紧（球包含点集，三角不等式给 D = |c_P−c_Q| − r_P − r_Q ≥ 真实最近距离），
但它**在细化下不单调**：子块的质心可以比父块的质心更靠近对方，于是孩子的 D 可以
**小于**父亲的 D，界可以细化后反而变大。这直接否掉自顶向下的用法——"整块界 ≤ τ 就跳"
只有在细化不会把界推高时才安全。实测（水二聚体 lvl1，`test_mac_acceptance_is_monotone`）
球版在若干对父子上确实违反单调。

盒版单调性是构造给的：子盒 ⊆ 父盒，两个集合各自缩小时，它们之间的最小距离不减。
所以 `box_sep` 给的是真实最近距离的下界，且细化只让它变大或不变。
w0^min、κ^min 在细化下不减、质量在细化下不增 ⇒ **整个界函数在细化下单调不增**，
这才是 MAC 能用的全部依据。

为什么是**树**，不是"一个原子一个球"，也不是"一片叶子集合"
---------------------------------------------------------
`examples/probe_bound_forms.py` 在苯夹心 level 0 上量了原子块对：球界的总和
3.71e8 kcal/mol 对真值 56.8 kcal/mol，且 gap 一栏几乎全是 0.00 Å——因为 radius 取
块内点到质心的**最大**距离，密度尾巴能拖出去好几 bohr（实测一个氧：块半径 11.07 bohr，
而整个 O···O 才 5.48）⇒ 任意两个原子球互相重叠 ⇒ D=0 ⇒ 界退化成与距离无关的常数。
病根在几何表示，不在质量因子。

那把它切成一片叶子行不行？也不行，我第一版就是这么写的：判据要作用在**胞对**上，
而"把所有胞对枚举一遍"本身是 O(M²)——苯夹心 level 0 光叶子就 18,792 个，上亿对，
为了躲开 O(N²) 引入一个同样二次的预处理，方向就错了。
而且只按质量停会留下一整坨"尾巴叶"：质量确实 <1%，半径跟整个原子球一样大，
它对谁的 D 又都是 0，前面白切。

所以要有**树**：接受/拒绝自顶向下做，界够小就整块跳掉、根本不去枚举它下面的点，
够大就细分（`_mac`）。这才是亚平方的来源。

记账口径（唯一一处 ×2）
-----------------------
v(a,b) := pair_energy(..., idx_a, idx_b) = 0.5·ΣΣ_{i∈a, j∈b}
E_双重和 = Σ_a v(a,a) + 2·Σ_{a<b} v(a,b)
被跳过的项往 `cert_err` 里累加**同样**的系数，所以 |真值 − 本值| ≤ cert_err，
与 E 同单位同口径。×2 只在 `_mac(..., mult=2.0)` 这一处施加。
自身块 (a==a) **永不屏蔽**：那是任何距离判据都跳不掉、也不该跳的部分。
接受集与求和集构成 P×Q 的一个划分 ⇒ 可加性由构造保证，不需要"另跑一遍带屏蔽的总量"
去对账。

一个必须记住的口径差别：`screen` 是**单个节点对**的接受常数 τ，不是全局预算。
"每个界各自 ≤ 1e-8 Ha"绝不等于"总误差 ≤ 1e-8 Ha"——实测苯夹心 lvl0 有 95,481 个
胞对各自 ≤ 1e-8 Ha，全跳掉的总界约 1e-3 Ha。真实保证只读 `cert_err`（它确实是累加的）；
要按预算用就往下压 τ 直到 `cert_err` 达标，别拿 `screen` 当预算。

默认关闭
--------
`screen is None` ⇒ τ=0 ⇒ 一个都不跳，且**不走树**：走原子块精确路径，与引入树之前逐位
相同，却不为每对叶子调一次 `pair_energy`（水二聚体一个氧就上万胞 ⇒ 测试从 ~2 分钟涨到
5 分钟）。`bound="ball"` 保留整原子球判据作 A/B 对照——它实测一个都跳不掉。
β∫ρ 不参与屏蔽，且照 `step_f_dispersion.terms` 的口径在**全部**网格点上求和
（不是只在保留点上）；搞错的话 L2 复现表 1 会差在末位。
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import nlc, partition

__all__ = ["AtomBlock", "Node", "build_blocks", "build_tree", "leaves",
           "box_sep", "ball_sep", "node_bound", "ball_bound",
           "screened_decomposition"]

INF = float("inf")




@dataclass(frozen=True)
class Node:
    """树上的一个节点：叶子带 `idx`，内部节点带 `left`/`right`。

    判据只用聚合量 (lo, hi, mass, w0min, kmin)，所以内部节点和叶子共用同一个界函数。
    `centroid`/`radius` 只服务于球判据的对照与诊断，树的路径不读它们。
    """
    idx: object            # 叶子是索引数组；内部节点是 None
    mass: float
    lo: np.ndarray
    hi: np.ndarray
    w0min: float
    kmin: float
    centroid: np.ndarray
    radius: float
    left: object = None
    right: object = None


@dataclass(frozen=True)
class AtomBlock:
    """一个原子在保留点上的子块，含算界所需的全部量。"""
    atom: int
    idx: np.ndarray        # 全局网格点索引（int）
    mass: float            # Σ|wr|
    w0min: float           # 块内 w0 最小值
    kmin: float            # 块内 κ 最小值
    centroid: np.ndarray   # 按 |wr| 加权的质心（Bohr）
    radius: float          # 块内点到质心的最大距离（Bohr）
    lo: np.ndarray         # 逐轴包围盒（Bohr）——盒判据用它
    hi: np.ndarray
    tree: object = None    # 该原子的二分树根；没要求建树时是 None


def _node(coords, wr, w0, kap, idx):
    """一个点集的聚合量。质心按 |wr| 加权；半径是到质心的最大距离。"""
    P = coords[idx]
    w = np.abs(wr[idx])
    mass = float(w.sum())
    c = (P * w[:, None]).sum(axis=0) / mass if mass > 0.0 else P.mean(axis=0)
    lo, hi = P.min(axis=0), P.max(axis=0)
    return Node(idx=idx, mass=mass, lo=lo, hi=hi, centroid=c,
                radius=float(np.linalg.norm(P - c, axis=1).max()),
                w0min=float(w0[idx].min()), kmin=float(kap[idx].min()))


def build_tree(coords, wr, w0, kap, idx, mass_frac=0.01, radius_frac=1 / 3,
               min_pts=32, total=None, r_ref=None, depth=0):
    """沿最长轴二分，直到单胞**既**质量小**又**空间紧，或切不动。

    两个终止条件缺一不可（各自都栽过一次）：
      * 只按质量停 ⇒ 留下半径 ≈ 原子球的"尾巴叶"，D 又是 0，白切；
      * 只按半径停 ⇒ 把核附近切成一堆没必要的小块，那里质量集中、本就该精确算。
    质量分母一路传**块总质量**（`total`），不是父节点质量——否则越深的孩子拿越小的
    分母冒充"够小"，永远切不完。
    """
    me = _node(coords, wr, w0, kap, idx)
    if total is None:
        total = me.mass
    if r_ref is None:
        r_ref = me.radius
    if idx.size <= min_pts or me.mass <= 0.0 or depth >= 24:
        return me
    if me.mass <= mass_frac * total and me.radius <= radius_frac * r_ref:
        return me
    P = coords[idx]
    span = me.hi - me.lo
    ax = int(np.argmax(span))
    sel = P[:, ax] <= 0.5 * (me.lo[ax] + me.hi[ax])
    left_idx, right_idx = idx[sel], idx[~sel]
    if left_idx.size == 0 or right_idx.size == 0:      # 点挤在同一张超平面上
        return me
    kids = [build_tree(coords, wr, w0, kap, left_idx, mass_frac, radius_frac,
                       min_pts, total, r_ref, depth + 1),
            build_tree(coords, wr, w0, kap, right_idx, mass_frac, radius_frac,
                       min_pts, total, r_ref, depth + 1)]
    return Node(idx=None, mass=me.mass, lo=me.lo, hi=me.hi, w0min=me.w0min,
                kmin=me.kmin, centroid=me.centroid, radius=me.radius,
                left=kids[0], right=kids[1])


def leaves(N):
    """树的全部叶子。"""
    if N is None:
        return ()
    if N.idx is not None:
        return (N,)
    return leaves(N.left) + leaves(N.right)


def _beta(aP, aQ):
    """|Φ| 的上界因子；两集合各自用其 (w0, κ) 下界在同一 D 处取值。"""
    if aP <= 0.0 or aQ <= 0.0:
        return INF                       # 下界非正 ⇒ 不敢跳
    return 0.75 / (aP * aQ * (aP + aQ))


def box_sep(A, B):
    """两个点集的**轴对齐包围盒**之间的最小距离（Bohr），盒相交时为 0。

    它是集合内任意两点真实距离的下界，且在细化下单调不降——子盒 ⊆ 父盒。
    """
    gap = np.maximum(np.maximum(A.lo - B.hi, B.lo - A.hi), 0.0)
    return float(np.linalg.norm(gap))


def ball_sep(A, B):
    """质心 + 最大半径的球版间距；尾巴把半径撑大后几乎恒为 0，且不单调。只作对照。"""
    d = float(np.linalg.norm(A.centroid - B.centroid)) - A.radius - B.radius
    return d if d > 0.0 else 0.0


def node_bound(A, B, mult=1.0):
    """|mult·0.5·ΣΣ_{i∈A, j∈B} wr_i wr_j Φ_ij| 的可证上界（盒判据）。

    细化不增：质量不增、w0min/κmin 不减、box_sep 不减 ⇒ 父对 ≥ 子对。这是 `_mac`
    能自顶向下接受/拒绝的依据，`test_mac_acceptance_is_monotone` 逐点验它。
    """
    if A is None or B is None:
        return 0.0
    D = box_sep(A, B)
    return mult * A.mass * B.mass * _beta(A.w0min * D * D + A.kmin,
                                         B.w0min * D * D + B.kmin)


def ball_bound(A, B, mult=1.0):
    """同一个界换成球间距。用来把负结果钉在代码里：它松到跳不掉任何东西。"""
    if A is None or B is None:
        return 0.0
    D = ball_sep(A, B)
    return mult * A.mass * B.mass * _beta(A.w0min * D * D + A.kmin,
                                         B.w0min * D * D + B.kmin)


def _mac(X, wr, w0, kap, A, B, tau, mult, stats):
    """自顶向下的接受/拒绝，返回**精确算出来的那部分**之和（半块口径）。"""
    bnd = node_bound(A, B, mult)
    if bnd <= tau:
        stats["accepted"] += 1
        stats["cert"] += bnd
        stats["pointpairs_dropped"] += _npts(A) * _npts(B)
        return 0.0
    if A.idx is not None and B.idx is not None:
        stats["evaluated"] += 1
        stats["pointpairs_evaluated"] += A.idx.size * B.idx.size
        return float(nlc.pair_energy(X, wr, w0, kap, A.idx, B.idx))
    stats["visited"] += 1
    # 细分"更大"的那一侧（按盒边长），两侧都是内部节点时优先 A。
    if A.idx is not None:
        kids = [(A, B.left), (A, B.right)]
    elif B.idx is not None:
        kids = [(A.left, B), (A.right, B)]
    elif _diag(B) > _diag(A):
        kids = [(A, B.left), (A, B.right)]
    else:
        kids = [(A.left, B), (A.right, B)]
    return sum(_mac(X, wr, w0, kap, C, D, tau, mult, stats) for C, D in kids)


def _npts(N):
    return 0 if N is None else (int(N.idx.size) if N.idx is not None
                                else _npts(N.left) + _npts(N.right))


def _diag(N):
    return float(np.linalg.norm(N.hi - N.lo))


def build_blocks(coords, wr, w0, kap, owner_kept, natm, tree_kwargs=None):
    """由 owner 切原子块；没有保留点或质量为零的原子给 None。

    给了 `tree_kwargs` 才建树；不给则 `tree` 是 None，走的路径与引入树之前逐位相同。
    """
    blocks = []
    for a in range(natm):
        idx = np.flatnonzero(owner_kept == a)
        if idx.size == 0:
            blocks.append(None)
            continue
        w = np.abs(wr[idx])
        mass = float(w.sum())
        if mass <= 0.0:
            blocks.append(None)
            continue
        me = _node(coords, wr, w0, kap, idx)
        tree = build_tree(coords, wr, w0, kap, idx,
                          **(tree_kwargs or {})) if tree_kwargs is not None else None
        blocks.append(AtomBlock(atom=a, idx=idx, mass=mass,
                                w0min=me.w0min, kmin=me.kmin,
                                centroid=me.centroid, radius=me.radius,
                                lo=me.lo, hi=me.hi, tree=tree))
    return blocks


def screened_decomposition(mol, mf, level=1, scheme="becke", screen=None,
                           bound="tree", mass_frac=0.01, radius_frac=1 / 3,
                           min_pts=32):
    """带可证截断误差的原子对分解；`pairs` 按原子对记账，片段和只是它的分组求和。

    screen: None ⇒ 不跳；否则是**单个节点对**的接受阈值 τ（Hartree，已含 ×2 口径）。
            真实保证读 `cert_err`，它才是累加的那个量。
    bound:  "tree" 自顶向下接受/拒绝（默认）；"ball" 只用整原子球判据，留作对照；
            `screen is None` 时三者走的是同一条精确路径，逐位相同。
    返回 dict(E_nl, E_pair, E_loc, cert_err, pairs, blocks,
              n_atom_pairs, n_leaves, n_leafpairs_total, n_leafpairs_evaluated,
              n_accepted, n_visited, work_frac, ...)
    """
    if bound not in ("tree", "ball"):
        raise ValueError(f"未知 bound {bound!r}，可选 'tree' / 'ball'")
    X, W, owner = partition.atom_partition(mol, level=level, scheme=scheme)
    ni = mf._numint
    dm = mf.make_rdm1()
    b, C = ni.nlc_coeff(mf.xc)[0][0]
    # vv10_fields 要的是**标量密度** rho[0] 与 sigma，不是 eval_rho 的完整 (4,N)。
    # 传错会得到 (4,N) 的 keep 掩膜，展平索引直接越界 —— 这是第一次跑 L1 炸掉的真正原因。
    rho_full = ni.eval_rho(mol, ni.eval_ao(mol, X, deriv=1), dm, xctype="GGA")
    rho = rho_full[0]
    sig = rho_full[1] ** 2 + rho_full[2] ** 2 + rho_full[3] ** 2
    w0, kap, keep = nlc.vv10_fields(rho, sig, b=b, C=C)
    wr = W * rho
    idx_kept = np.flatnonzero(keep)

    # 全部数组都在这**一张**网格上。scf_grid(level=1) 给的是另一张（水二聚体实测
    # 18368 vs 19936），两套点数不可混用，所以锚点也只能取同样架在 atom_partition 上
    # 的那条路（step_h 正是这么做的）。
    owner_kept = np.full(len(wr), -1, dtype=np.intp)
    owner_kept[idx_kept] = owner[idx_kept]
    tau = 0.0 if screen is None else float(screen)
    use_tree = bound == "tree" and tau > 0.0
    tree_kwargs = {"mass_frac": mass_frac, "radius_frac": radius_frac,
                   "min_pts": min_pts}
    blocks = build_blocks(
        X, wr, w0, kap, owner_kept, mol.natm,
        tree_kwargs=dict(tree_kwargs) if bound == "tree" else None)
    live = [blocks[a] for a in range(mol.natm) if blocks[a] is not None]
    leafcounts = {b.atom: (len(leaves(b.tree)) if b.tree is not None else 1)
                  for b in live}
    n_leaves = sum(leafcounts.values())
    n_leafpairs_total = sum(leafcounts[Pa.atom] * leafcounts[Pb.atom]
                           for i, Pa in enumerate(live) for Pb in live[i + 1:])
    # 真正的访存量按**点对**算，不是按叶对数：一个 32x32 的叶对和一个 3000x3000 的
    # 原子对差五个数量级。`work_frac`（叶对）会系统性高估收益，所以两个都报。
    nppts = {b.atom: int(b.idx.size) for b in live}
    pointpairs_far = sum(nppts[Pa.atom] * nppts[Pb.atom]
                         for i, Pa in enumerate(live) for Pb in live[i + 1:])
    pointpairs_self = sum(nppts[b.atom] ** 2 for b in live)
    eps = np.finfo(float).eps
    pairs = {}
    cert = 0.0
    stats = dict(accepted=0, evaluated=0, visited=0, cert=0.0,
                 pointpairs_dropped=0, pointpairs_evaluated=0)
    E = 0.0

    for Pa in live:                                  # 自身块：永不跳
        v = float(nlc.pair_energy(X, wr, w0, kap, Pa.idx, Pa.idx))
        pairs[(Pa.atom, Pa.atom)] = v
        E += v

    if not use_tree:
        # 精确路径，或 bound="ball" 的对照路径：整原子球判据。
        for i, Pa in enumerate(live):
            for Pb in live[i + 1:]:
                bnd = ball_bound(Pa, Pb, 2.0)          # ×2 只在这里出现
                if bound == "ball" and bnd <= tau:
                    cert += bnd
                    continue
                v = float(nlc.pair_energy(X, wr, w0, kap, Pa.idx, Pb.idx))
                if Pa.atom != Pb.atom and abs(v) > eps:
                    # 半块对称性是 pair_energy 的应有性质；不等说明口径理解错了，当场炸。
                    # 只在没有跳任何东西时检查：跳过之后 v 与全量不可比（上一版无条件断言，
                    # 被一次合法的跳块绊倒，报出 (0,1,-5.394867e-4,-5.394943e-4)）。
                    v2 = float(nlc.pair_energy(X, wr, w0, kap, Pb.idx, Pa.idx))
                    assert abs(v - v2) <= 1e-10 * max(1.0, abs(v)), (Pa.atom, Pb.atom, v, v2)
                pairs[(Pa.atom, Pb.atom)] = v
                E += 2.0 * v
    else:
        for i, Pa in enumerate(live):
            for Pb in live[i + 1:]:
                v = _mac(X, wr, w0, kap, Pa.tree, Pb.tree, tau, 2.0, stats)
                pairs[(Pa.atom, Pb.atom)] = v
                E += 2.0 * v
        cert = stats["cert"]

    beta = (1.0 / 32.0) * (3.0 / (b * b)) ** nlc.BETA_EXP
    E_loc = float(nlc.local_term(beta, wr))         # 全部网格点，与 terms() 同口径
    n_atom_pairs = len(pairs)
    denom = pointpairs_far + pointpairs_self
    return dict(E_nl=E + E_loc, E_pair=E, E_loc=E_loc, cert_err=cert,
                pairs=pairs, blocks=blocks,
                live=[b.atom for b in live],
                n_atoms=len(live), n_atom_pairs=n_atom_pairs,
                n_leaves=n_leaves, n_leafpairs_total=n_leafpairs_total,
                n_leafpairs_evaluated=stats["evaluated"],
                n_accepted=stats["accepted"], n_visited=stats["visited"],
                pointpairs_far=pointpairs_far, pointpairs_self=pointpairs_self,
                pointpairs_evaluated=stats["pointpairs_evaluated"],
                pointpairs_dropped=stats["pointpairs_dropped"],
                work_frac=(stats["evaluated"] / n_leafpairs_total
                           if n_leafpairs_total else 0.0),
                flop_frac=(stats["pointpairs_evaluated"] / pointpairs_far
                           if pointpairs_far else 0.0),
                total_frac=(stats["pointpairs_evaluated"] + pointpairs_self) / denom
                if denom else 0.0,
                screen=screen, tau=tau, bound=bound, level=level, scheme=scheme,
                n_grid=int(len(wr)), n_kept_points=int(idx_kept.size))
