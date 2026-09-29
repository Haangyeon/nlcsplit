"""A2b：带可证误差界的亚平方 VV10 双重和（原子块屏蔽，保住 (i,j) 成对归属）。

为什么需要它
------------
`nlc.pair_energy` 在整张网格上是 O(N²)：`block=256` 只是访存分块，**全仓不存在任何
距离屏蔽或块截断**（唯一的剪枝是密度掩膜 `RHO_FLOOR=1e-12`）。本模块在**不改动**
`nlc.py` 的前提下加一层块级剪枝，并且**保住 (i,j) 成对索引**——剪掉的必须是
"块对 (P,Q)"这一整个划分单元，不能是散点，否则 `inter[(A,B)]` 的归属含义就没了。

误差界（本文件的立身之本）
--------------------------
保留集上 `w0_i > 0`、`κ_i > 0`，且 `|Φ| = 1.5/(g·g'·(g+g'))` 对 `g, g'` 单调递减。
对块 P、Q，令

    a_P(D) = w0_P^min · D² + κ_P^min,   D = D_PQ = max(0, |c_P−c_Q| − rad_P − rad_Q)

则块内任意 (i,j) 都有 `g_i ≥ a_P(D_PQ)`、`g'_j ≥ a_Q(D_PQ)`（同中心配对，见下），于是

    |Σ_{i∈P,j∈Q} wr_i wr_j Φ_ij| ≤ 1.5 · m_P m_Q / (a_P a_Q (a_P + a_Q)),  m_P = Σ_{i∈P}|wr_i|

右边是这个块和的**上界**，只依赖块统计量 ⇒ 可以在求和之前算出来，用来决定屏不屏。

**为什么必须是逐块最小值**：全局最小值版本无效——`rho_floor=1e-12` 下实测
`κ_min=0.162`、`w0_min=2.05e-6`，R⁻⁶ 渐近要到 281 bohr ≈ 149 Å 才接管 ⇒ 真正做剪枝的
是**密度质量 m_P**，不是距离。这条是任务书给的口径，本文件按它实现。

**适用口径（写死在断言里，别用错场景）**
- `pairing="same-centre"`：共同的被测口径，也是 `nlc.pair_energy` 的默认值。
- `b, C > 0` ⇒ 由 `nlc.vv10_fields` 的构造保证 `w0 > 0`、`κ > 0`（块内 `a ≥ κ_min > 0`）。
- **`cross` 口径的界不在本文件里**：交叉配对下 `g = w0_j R² + κ_i` 的跨块下界是混合量
  `w0_Q^min·D² + κ_P^min`，不是 `a_P`。我没有实现它，`pairing="cross"` 直接 raise。
  要加就另写一条链并在测试里独立验证，别改上面这条判据去"兼容"它。

预算与选择（这是"ε ≤ 1e-8 Ha"能成立的原因）
------------------------------------------
只保证"每个被屏块对的界 ≤ τ"，**对任意子集成立**，但对"被屏块对的全部并"不成立：
块对可能有 O(M²) 个，τ 固定则 Σ bound 可以远超 ε。所以主模式是**预算贪心**：

    按界从大到小排序，第 k 名（从 1 起）分到的预算 b_k = ε · w_k / Σ w（w_k = 1/k），
    屏掉 bound ≤ b_k 的块对，保留其余。

被屏集合是"最弱的一批后缀"，其预算之和 ≤ ε · Σ_{k>K} 1/(k(k+1)) = ε/(K+1) < ε，
对**任何**后缀成立 ⇒ `Σ_{dropped} bound ≤ ε` 是构造保证的，不是碰运气。
实测中它和"筛掉 bound ≤ ε/2"通常给出几乎同一份清单，但只有前者有证明。

判据与总量解耦（纪律要求的三条，逐条落在这里）
--------------------------------------------
1. 判据只用块统计量，**不看真实块和**；
2. `E_nl` 与所有 `intra`/`inter` **从同一份保留清单加出来**，绝不另跑一遍"带屏蔽的总量"
   （`full_ref=True` 那一遍是外部对照，不参与任何返回的总量）；
3. `pair_energy` 返回**半份**交叉块 ⇒ ×2 只在块级别施加一次。

两条截断分开报告
----------------
`rho_floor`（`nlc.vv10_fields` 的 keep 掩码）与**本模块的屏蔽**是两条独立截断。
本模块只碰后者，返回值里 `n_dropped_rho` / `n_dropped_screen` 分列，不许混成一个数。

独立性与裁判
------------
冻结前未读 A2a 的 `fastpair.py`。裁判不是对方：外部锚点是
(a) `nlc.pair_energy` 全量 O(N²) 路径（屏蔽关闭）、(b) PySCF 原生核 `numint.nr_nlc_vxc`、
(c) ORCA 6.0.1（水 −0.5931 / 苯 −4.3252 kcal/mol）。两版彼此吻合只算旁证。
"""
import numpy as np

from nlcsplit import nlc

__all__ = [
    "PHI_NUMERATOR", "BUDGET_HARMONIC", "phi_abs_max", "budget_weights",
    "block_stats", "pair_bound", "select_screened", "screened_decomposition",
]

PHI_NUMERATOR = 1.5   # |Φ| = 1.5 / (g g' (g+g'))


def phi_abs_max(g, gp):
    """|Φ| = 1.5/(g·g'·(g+g'))，界推导里唯一依赖的量。单调递减于 g 与 g'。"""
    return PHI_NUMERATOR / (g * gp * (g + gp))


# ------------------------------------------------------------------ 块统计量
def block_stats(coords, wr, w0, kap, idx):
    """一个原子子网格块的统计量 dict(idx, m, w0_min, kap_min, centroid, radius)。

    `idx` 必须**已经**与 keep 掩码交过——被 rho_floor 丢掉的点不该进 m_P，
    否则质量被虚增、屏蔽变保守（少屏），报告里也分不清两条截断。

    返回 None 表示块空，或质量恰为 0（质量为 0 的块对任何归属口径贡献恒为 0）。

    - `m = Σ|wr|`：密度质量，剪枝主力
    - `w0_min / kap_min`：块内下界，进误差界
    - `centroid / radius`：**质心**与到质心的最大偏离。不用几何中心——几何中心
      可以被网格不均匀性推到很远，质心 + 最大偏离是最省事的球覆盖。球界对
      **任意**选择（含被屏集合的任意子集）都成立，这是它相对"逐对精确距离"的安全性来源。
    """
    idx = np.asarray(idx, dtype=np.intp)
    if idx.size == 0:
        return None
    m = float(np.abs(np.asarray(wr)[idx]).sum())
    if not np.isfinite(m) or m == 0.0:
        return None
    c = np.asarray(coords)[idx]
    centroid = c.mean(axis=0)
    radius = float(np.max(np.linalg.norm(c - centroid, axis=1)))
    return dict(idx=idx, m=m, w0_min=float(np.min(w0[idx])),
                kap_min=float(np.min(kap[idx])), centroid=centroid, radius=radius)


def pair_bound(P, Q, D=None, r2_min=None):
    """块对 (P,Q) 的绝对值上界 `1.5 m_P m_Q / (a_P a_Q (a_P+a_Q))`。

    `D`：球间隔 `max(0, |c_P−c_Q| − rad_P − rad_Q)`（默认；保守，对任意子集安全）。
    `r2_min`：逐点精确的最小 R²。**只用于诊断**——拿它做判据会让界依赖"哪个点配
    哪个点"，被屏集合的界不再由构造保证。两者都传时以 `r2_min` 优先，调用方负责。
    """
    if r2_min is not None:
        D2 = max(float(r2_min), 0.0)
    else:
        if D is None:
            d = float(np.linalg.norm(P["centroid"] - Q["centroid"]))
            D = max(d - P["radius"] - Q["radius"], 0.0)
        D2 = D * D
    aP = P["w0_min"] * D2 + P["kap_min"]
    aQ = Q["w0_min"] * D2 + Q["kap_min"]
    return PHI_NUMERATOR * P["m"] * Q["m"] / (aP * aQ * (aP + aQ))


# ------------------------------------------------------------------ 预算与选择
BUDGET_HARMONIC = "harmonic"


def budget_weights(n, scheme=BUDGET_HARMONIC):
    """第 k 名（0-based，按界降序）的预算权重（未归一）。

    harmonic：w_k = 1/(k+1) ⇒ 后缀占比随 K 衰减、尾部预算总和有限，
    这是"被屏后缀的界之和 ≤ ε"的来源。uniform 故意**不**安全，只作对照，
    测试里要证明它会破（否则这条选择方案等于没测）。
    """
    if scheme == BUDGET_HARMONIC:
        return 1.0 / (np.arange(n) + 1.0)
    if scheme == "uniform":
        return np.ones(n)
    raise ValueError(f"未知预算方案 {scheme!r}，可选 '{BUDGET_HARMONIC}' / 'uniform'")


def select_screened(bounds, epsilon, mode="budget", scheme=BUDGET_HARMONIC):
    """给定所有块对的界，返回 (被屏掩码, 证得界 = 被屏块对的界之和)。

    mode
      "full"   不屏（屏蔽关闭 / ε→0 的对照路径，L4 靠它）
      "budget" 预算贪心（主模式，界 ≤ ε 由构造保证）
      "tau"    筛掉 bound ≤ ε/2（简单，但界只对**实际被屏集合**成立，报的是实测值）

    预算贪心（实现修正）：**被屏集合必须是按界降序的最弱后缀**，否则
    “Σ bound ≤ ε”不成立——逐元素 `bound ≤ 各自预算` 可以挑出非后缀的子集，
    它们的界之和可以远超 ε。正确做法：从最弱一端往回累加，只要
    累加和 ≤ ε 就一直屏；一旦某个前缀使累加和超 ε 就停。这保证
    被屏集是后缀、且 `Σ_{dropped} bound ≤ ε`（构造保证，不看数据分布）。
    """
    bounds = np.asarray(bounds, dtype=float)
    n = bounds.size
    if mode == "full":
        return np.zeros(n, dtype=bool), 0.0
    if mode == "budget":
        if epsilon <= 0.0:
            raise ValueError(f"budget 模式需要 epsilon > 0（收到 {epsilon}）；"
                             f"要退回全量请用 mode='full'")
        if n == 0:
            return np.zeros(0, dtype=bool), 0.0
        # 按界升序（最弱在前），从前往后累加，累加和超 ε 前能拿多少拿多少
        asc = np.argsort(bounds, kind="stable")
        cs = np.cumsum(bounds[asc])
        k_keep = int(np.sum(cs <= epsilon))          # 前 k_keep 个最弱的屏掉
        screened = np.zeros(n, dtype=bool)
        screened[asc[:k_keep]] = True
        return screened, float(bounds[screened].sum())
    if mode == "tau":
        screened = bounds <= epsilon / 2.0
        return screened, float(bounds[screened].sum())
    raise ValueError(f"未知 mode {mode!r}，可选 'full' / 'budget' / 'tau'")


# ------------------------------------------------------------------ 主入口
def screened_decomposition(coords, weights, rho, sigma, fragments,
                           b=6.0, C=0.01, owner=None, soft=None,
                           rho_floor=nlc.RHO_FLOOR, epsilon=1.0e-8,
                           mode="budget", scheme=BUDGET_HARMONIC,
                           pairing="same-centre", full_ref=False):
    """`nlc.fragment_decomposition` 的带屏版本，返回同一套键 + 屏蔽审计量。

    fragments / owner / soft / rho_floor / b / C 的语义与 `nlc.fragment_decomposition`
    一致（soft 给定时同样要求每点归属权重和为 1，沿用它的护栏阈值）。新增：
      epsilon  总预算（Ha）；mode='full' 时忽略
      mode     'budget'（默认）/ 'tau' / 'full'
      scheme   预算方案，见 `budget_weights`
      full_ref 额外跑一遍**不屏**的 `nlc.fragment_decomposition`，把实测差写进
               `actual_ha`。只给验证脚本用：`E_nl` 依旧只从保留清单加出来，
               多出来那一遍是外部对照，不参与任何返回的总量。

    返回 dict：
      E_loc, E_nl, E_total, intra{A}, inter{(A,B)}   口径同 nlc.fragment_decomposition
      blocks{(A,B,a,b)}                              存活块原始值（交叉块是**半份**）
      intra_blocks / inter_blocks                    同一批半份值按 kind 分家（同键）
      kept / dropped                                 保留与屏蔽的原子块对清单
      pairs                                          全部块对审计（含 bound/mult/cost/value）
      bound_ha                                       **证得界**（被屏块对的界之和）
      actual_ha                                      实测差（仅 full_ref=True 时给出）
      n_dropped_rho / n_dropped_screen               两条独立截断，分列
      n_pairs_full / points_full / points_kept       工作量，用于诚实的加速比
      epsilon / mode / scheme / pairing / soft       原样回显，日志不许靠上下文推断档位
    """
    if pairing != "same-centre":
        raise NotImplementedError(
            f"本模块只证了 same-centre 的界（cross 的跨块下界是 w0_Q^min·D²+κ_P^min，"
            f"不是 a_P）；收到 pairing={pairing!r}")
    coords = np.asarray(coords)
    weights = np.asarray(weights)
    w0, kap, keep = nlc.vv10_fields(rho, sigma, b, C, rho_floor)
    wr = weights * rho
    if owner is None:
        raise ValueError("需要 owner：原子子网格是划分骨架，屏蔽离不开它")
    owner = np.asarray(owner)
    n_atom = int(owner.max()) + 1
    nf = len(fragments)
    if soft is not None:
        soft = np.asarray(soft)
        dev = float(np.abs(soft.sum(axis=0) - 1.0).max())
        if dev > 1e-8:
            raise ValueError(f"软分区权重每点之和偏离 1 达 {dev:.3e}，不可用")
        keepf = keep.astype(float)
        # 与 nlc.fragment_decomposition 同一套片段归属权重
        f_frag = [sum(soft[a] for a in fragments[k]) * keepf for k in range(nf)]
        # 判据用的逐片段逐点因子（m_P^A = Σ_{i∈P}|wr_i f^A_i| 靠它）
        f_pt = [soft[k] * keepf for k in range(nf)]
    else:
        f_frag = f_pt = None

    # 块统计：软分区下同原子在 (A,B) 与 (A,C) 里质量不同 ⇒ 按 (片段,原子) 缓存。
    # 硬分区只有一套权重，A 恒 0，走同一条代码路径。
    # 块统计缓存。键 = (权重片段 A, owner 原子 a)：
    #   硬分区：f^A 是 one-hot，a 的非本片段块权重为 0 ⇒ 只需枚举 a∈fragments[A]。
    #   软分区：f^A 在所有原子的点上都可能非零（Becke 尾巴泄到别片），质量/下界随 A 变，
    #           ⇒ 必须对每个片段 A 枚举**全部** owner 原子。否则 intra[A] 会漏掉
    #           被其它片段原子子网格拥有、却带 f^A 权重的点（今天实测软分区残差 ~5e-3）。
    stat_weight = [None] * nf
    if f_pt is not None:
        stat_weight = [wr * f_pt[k] for k in range(nf)]
    else:
        stat_weight[0] = wr
    idx_cache = {}
    stat_cache = {}

    def block_of(A, atom):
        key = (A if f_pt is not None else 0, int(atom))
        if key not in stat_cache:
            if key not in idx_cache:
                idx_cache[key] = np.where((owner == atom) & keep)[0]
            stat_cache[key] = block_stats(coords, stat_weight[key[0]], w0, kap,
                                          idx_cache[key])
        return stat_cache[key]

    all_atoms = range(n_atom)
    pairs = []
    for A in range(nf):
        for B in range(A, nf):
            # 行的候选原子：硬分区限本片段；软分区遍历全部
            row_atoms = fragments[A] if f_pt is None else all_atoms
            for a in row_atoms:
                Pa = block_of(A, a)
                if Pa is None:
                    continue
                if A == B:
                    # 片段自身：上三角枚举，(a,a) 计 1 份、(a,b) 计 2 份（成对块对称）
                    if f_pt is None:
                        col_atoms = [x for x in fragments[B] if x >= a]
                    else:
                        col_atoms = [x for x in all_atoms if x >= a]
                else:
                    col_atoms = fragments[B] if f_pt is None else all_atoms
                for bb in col_atoms:
                    Qb = block_of(B, bb)
                    if Qb is None:
                        continue
                    # 自块 (A==B 且 a==b) 计 1 份；其余（上三角非对角、片间）计 2 份
                    mult = 1 if (A == B and a == bb) else 2
                    pairs.append(dict(
                        A=A, B=B, a=int(a), b=int(bb),
                        kind="intra" if A == B else "inter", mult=mult,
                        cost=int(Pa["idx"].size) * int(Qb["idx"].size),
                        bound=mult * float(pair_bound(Pa, Qb))))

    bounds = (np.array([p["bound"] for p in pairs], dtype=float)
              if pairs else np.zeros(0))
    screened, bound_ha = select_screened(bounds, epsilon, mode=mode, scheme=scheme)

    # ---- 存活块原样调 nlc.pair_energy；E_nl / intra / inter 全部从这份清单加出来
    #
    # 块一律按 **owner 原子** 切索引（不是片段索引）：
    #   · 传片段索引会把同一个片段块重算 N 次（今天真就这么错了：E_nl 被放大 2.93 倍，
    #     而界按原子算，两边口径不同源 ⇒ 测试才抓出来）。
    #   · 每块是半份交叉（pair_energy 自带 0.5）⇒ 向 E_nl 的贡献乘 p["mult"]（上三角枚举，
    #     非对角块 mult=2、自块 mult=1），×2 只在这里施加一次。
    #   · 硬分区：f^A one-hot，只需枚举本片段原子；软分区：枚举全部原子（见上方注释）。
    atom_idx = {int(a): np.where((owner == a) & keep)[0] for a in range(n_atom)}
    intra, inter, blocks = {}, {}, {}
    intra_blocks, inter_blocks = {}, {}
    for A in range(nf):
        intra[A] = 0.0
    for A in range(nf):
        for B in range(A + 1, nf):
            inter[(A, B)] = 0.0

    for p, use in zip(pairs, ~screened):
        if not use:
            p["value"] = None
            continue
        iA, iB = atom_idx[p["a"]], atom_idx[p["b"]]
        if f_frag is None:
            v = float(nlc.pair_energy(coords, wr, w0, kap, iA, iB))
        else:
            v = float(nlc.pair_energy(coords, wr * f_frag[p["A"]], w0, kap, iA, iB,
                                      wB=wr * f_frag[p["B"]]))
        p["value"] = v
        contrib = p["mult"] * v                    # 半份块 × mult ⇒ 整份贡献
        key4 = (p["A"], p["B"], p["a"], p["b"])
        blocks[key4] = v                           # 存**原始半份**（口径同 docstring）
        if p["kind"] == "intra":
            intra_blocks[key4] = v
            intra[p["A"]] += contrib
        else:
            inter_blocks[key4] = v
            inter[(p["A"], p["B"])] += contrib

    E_nl = float(sum(intra.values()) + sum(inter.values()))
    res = {
        "E_loc": nlc.local_term((1.0 / 32.0) * (3.0 / (b * b)) ** nlc.BETA_EXP, wr),
        "E_nl": E_nl,
        "intra": intra, "inter": inter, "blocks": blocks,
        "intra_blocks": intra_blocks, "inter_blocks": inter_blocks,
        "kept": [(p["a"], p["b"]) for p, u in zip(pairs, ~screened) if u],
        "dropped": [(p["a"], p["b"]) for p, u in zip(pairs, screened) if u],
        "pairs": pairs,
        "bound_ha": float(bound_ha),
        "n_dropped_rho": int((~keep).sum()),
        "n_dropped_screen": len(pairs) - len([1 for p, u in zip(pairs, ~screened) if u]),
        "n_pairs_full": len(pairs),
        "points_full": int(sum(p["cost"] for p in pairs)),
        "points_kept": int(sum(p["cost"] for p, u in zip(pairs, ~screened) if u)),
        "epsilon": float(epsilon), "mode": mode, "scheme": scheme,
        "pairing": pairing, "soft": soft is not None,
        "n_atoms": n_atom, "n_points": int(len(coords)),
    }
    res["E_total"] = res["E_loc"] + res["E_nl"]
    if full_ref:
        ref = nlc.fragment_decomposition(coords, weights, rho, sigma, fragments,
                                         b=b, C=C, owner=owner, soft=soft,
                                         rho_floor=rho_floor)
        res["full_ref_nl"] = float(ref["E_nl"])
        res["full_ref_inter"] = dict(ref["inter"])
        res["actual_ha"] = abs(res["E_nl"] - float(ref["E_nl"]))
    return res
