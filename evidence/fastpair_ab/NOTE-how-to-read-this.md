# 读这份 sidecar 之前必须知道的三件事

归档日期 2026-09-29。对象：`fastpair_ide.py` / `examples/check_screen_bound_ide.py` /
`tests/test_fastpair_ide.py`（ide-qoder 的 A2b 交付，冻结对照），以及它写出的
`fastpair_ide_validation.json`。本文件只加解释，**不改**任何被哈希锁住的工件。

## 1. `l1_pass: true` 是空转，不是"屏蔽已验证"

sidecar 里那行的判据是 `bound_ha + 1e-13 >= actual_ha`。ε=1e-8 时两条记录都是
`bound_ha = 0.0`、`actual_ha ≈ 1.7e-18 / 2.8e-17`，也就是 **`0 ≥ 0`**。
按计划书 v2 的新 L1（要求 `n_accepted > 0` 且 `cert_err > 0`，非空）判语为
**FAIL（机制未开火）**。ide-qoder 自己在 `PROGRESS-ide-qoder.md` 2026-09-29 23:1x 条目
里已撤回 "L1 PASS"，与此一致。

同一份 sidecar 里可直接读出"没开火"的三个字段，两条记录均为：

| 字段 | (H2O)2 lvl1 | (C6H6)2 lvl0 |
|---|---|---|
| `n_pairs_full` → `n_dropped_screen` | 21 → **0** | 300 → **0** |
| `points_full` / `points_kept` | 176,354,266 / **相等** | 184,464,356 / **相等** |
| `full_pfrz` vs `screened_pfrz` | 差 1 个 ulp | 差 2 个 ulp |

所以这份工件支持的结论只有两条：**核正确**（对同一张网格上的显式双重和
`abs_mismatch_vs_anchor_a_ha = 1.7e-18`，ORCA 锚见 `fastpair_ab_compare.json`），
**屏蔽正确但惰性**。不得引为"加速已交付"。

`fastpair_ab_compare.json` 把这件事写成了布尔量，别再从 `l1_pass` 读：
ide 侧 `"L1_cert_ge_actual": true, "L1_nonvacuous": false`；
我方侧同字段为 `true / true`（τ=1e-8 下 `n_accepted=32131`、
`pointpairs_dropped=71,864,510 / 120,415,263`）。**开火的是我方实现，不是 sidecar。**

## 2. `min_block_bound_ha` 是 P2 负结果的主证，不是笔误

定义见 `nlcsplit/examples/check_screen_bound_ide.py:111`：
`min(p["bound"] for p in res["pairs"])` —— 所有**块对**可证界里最小的那个。
(H2O)2 只有 21 个原子块对，最小者 **197.96 Ha**；(C6H6)2 有 300 对，最小者 **261.04 Ha**。
对照它们本该判定的量：整个水二聚体的片段间非局域项
`P_frz_inter_frag = −8.3449e-4 Ha`。**最松不过的一个块对界比整个待判量大约 2.4e5 倍**，
所以同一份工件里 `n_pairs_bound_below_value = 0`、`dropped_pairs = []` ——
在原子块粒度上，任何正容差都筛不出东西。`p2.md` §3 引这组数。

## 3. `d_orca_kcal: 0.07828` 不是跨程序锚点

(H2O)2 那一行的 ORCA 差值混了几何与量的口径（官方几何 vs 我方优化几何；总非局域项
vs 片段对分量）。`paper/main.md` 与 `paper/p2.md` **均未引用它**，跨程序锚点只用
`evidence/orca_control/` 里已核过的水 4e-4 / 苯 0.042。今后要引用须先标 UNVERIFIED 或删。

## 4. 冻结件里两处已知缺陷，按"不改"处理及理由

- `examples/check_screen_bound_ide.py:40-41`：默认数据目录拼成 `<repo>/s22`，
  本仓实际在 `scratch/lit/s22/`。**外人 clone 后此脚本不可跑**（设 `S22DIR` 可绕，
  但 `scratch/` 本身不随包发布）。
  处理：不补。该文件不在 `tools/make_public_repo.js` 的 `EXAMPLES` 白名单
  （只发 `__init__.py, quickstart.py, check_fast_pair.py, check_soft_partition.py`），
  不进发布物，也没有任何 `[S#]` 主张指向它 —— 改了只会碎掉上面这些哈希。
  若将来要发布，判据是：路径缺失必须**显式报错**，不能退回一个不存在的默认值。
- `one_l1` 的 `l1_pass` 定义：见 §1，v2 口径下应换成非空条件。属于源件改动，
  同样留到 P2 定稿一并决定，本文件先把口径钉住，防止下次会话又把它读成"机制生效"。
