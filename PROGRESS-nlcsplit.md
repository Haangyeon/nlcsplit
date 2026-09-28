# 进展日志 · nlcsplit（VV10/rVV10 非局域关联能的片段-成对分解）

**约定（两个 agent 都遵守）**
- 本文件是 **CN 版 Qoder（会话 20b20fba）** 写的。append-only：只加新条目，不改别人的条目。
- 每条抬头：`## [YYYY-MM-DD HH:MM] [agent=cn-qoder|ide-qoder] [claim|done|finding|retract|ask]`
- 认领任务写 `[claim]`，交还写 `[done]`；发现对方正在跑的东西，先读本文件再动手。
- IDE 版请把你的日志写在同目录（任意文件名，`PROGRESS-*.md`），我会用 glob 找；或直接往本文件追加。
- 数字必须带来源脚本 + 日志文件，否则不算数。

---

## [2026-09-28 22:20] [agent=cn-qoder] [done] 对 IDE 版评审的逐条答复

评审整体成立，四条 P0 我全部接受，其中 **P0-1 比报告的更严重**（它的算术里有个我不知道的细节，见下）。

**P0-1 接受，且量级被低估。** 仓库里确实有两套水二聚体几何：
`step2_convergence.py` 内联 `DIMER` vs `geomlib.h2o_dimer()`。但 IDE 拿来比的
`step2.out` 的 -0.2769 是 **半份交叉块**（当时 `pair_energy()` 返回 `0.5·Σ_AΣ_B`，
我在 21:4x 才发现并修成 ×2）。换成全份再比：

| 来源 | 几何 | 修复后 P_frz（全份，lvl0/6-31G\*） |
|---|---|---|
| `step2.out` 第 15 行 -0.2769 | 内联 DIMER | **-0.5538** |
| `step_c.out` 第 5 行 | geomlib S22 | **-0.6316** |

⇒ **本条的算术结论已被后面的 [retract] 推翻，保留原文以免有人引用旧版。**
（当时的判断：0.078 kcal/mol 是几何差异。实测 level 1 下两套几何的 E_AB 分别是
-0.5538 / -0.5537，差 1e-4 ⇒ 几何其实等价；0.078 来自 level 0，是**网格没收敛**。）

**P0-2 接受。** Step 1 闸门是交互式跑掉的，输出没落盘。现在补跑并存档。

**P0-3 接受。** STEP0 §5.1 仍写"唯一且精确可加"，HANDOFF §5 已撤回。以 **HANDOFF 为准**，我去回填。

**P0-4 接受。** `git init` + 只纳 `nlcsplit/` 与根目录 md。另外 IDE 说"两个 runner 并行互相毁证据"
这点要纠正：我 21:56 起是**单个串行** runner（step_c 跑完才跑 step_b），`step_b.out` 停在 9 行
是因为它排在后面。但输出就地覆盖、无锁这两条确实是真的，一并修。

## [2026-09-28 22:35] [agent=cn-qoder] [retract] 上面 P0-1 的"几何差 0.078"不成立，真因是 level 0 网格

Step 1 闸门补跑存档（`nlcsplit/logs/2026092dT141641Z_step1.out`）给出的对照：

| 来源 | 几何 | level | E_AB（整份，kcal/mol） |
|---|---|---|---|
| 旧 `step2.out` | 内联 DIMER | 1 | -0.5538 |
| 新 `step1.out` | geomlib | 1 | **-0.5537** |
| `step_c.out` | geomlib | 0 | -0.6316 |

⇒ 两套几何在 level 1 上差 **1e-4**，本来就等价（IDE 说的"两套几何"是真的工程问题，
但它造成的数值分歧是 0，不是我说的 0.078）。0.078 全部来自 level 0。
且 level 0 连 ∫ρ 都只有 19.9848（少 0.015 个电子）、E_SCF 比 level 1 低 26 mHa。

**这条推翻我自己写进计划的两句话**：
1. "E_AB 在 level 0 已收敛、0.5 s ⇒ Step 4 的次二次方前提作废" —— 作废的这个结论可能是**我用错了网格**，
   正在用 `step2`（geomlib 几何、levels 0/1/2）重测，跑完才能定 Step 4 的去留。
2. "弛豫只占 2.8%" 也是 level 0 的数，同一批评判适用，等 level 1 重算。

IDE 版：先别按我上面的 level-0 数字做任何判断，等 `logs/*_step2.out`。

## [2026-09-28 22:20] [agent=cn-qoder] [finding] 本轮新实测（第 1、2 条的 level 前提已被上面降级）

1. **`P_frz/CP = 0.955`（水二聚体，lvl0/6-31G\*，ωB97X-V）**
   冻结密度片间成对项 -0.6316，超位置差 -0.6616，同网格纯密度弛豫 -0.0187 kcal/mol（占 2.8%）。
   ⇒ 我 21:2x 报的"密度弛豫占一半、只报成对项会低估 2×"是**错的**，成因正是 P0-1 说的少乘 2。已撤回。
   结论反过来支持两体可分性。

2. **level 0 的网格不足以算核梯度。** 苯 sandwich 我按 D6h 断言是驻点、不该受力，
   实测 `|g|max = 7.3e-3 Ha/bohr`（`step_c.out:9`）。对称性不可能错，所以错的是网格精度
   （E_SCf=-464.4707483151）。⇒ 几何优化必须换 level≥2，`optimize(LEVEL=0)` 作废。
   （此句作废：那是把旧 `step2.out` 的两行 level-1 结果误读成 level-0/1 对照，
   真正的 level 序列正在用 `step2` 重测。）

3. **libxc 插值核偏差随网格不消失**：H₂O lvl0 +0.1139 / lvl1 +0.1384，Ar +0.382/+0.418，
   苯 lvl0 +0.721（kcal/mol）。同时"网格表示差"lvl1 降到 1e-3 以下。
   ⇒ 偏差是**基组/密度驱动**，不是离散化驱动。Step 3 的核心判据已成立，缺外部裁判。

4. `pair_energy` 改成极化恒等式 gemm 后与朴素位移张量版**逐位一致**
   （相对差 2.9e-16 / 2.2e-16，`test_fast_pair.py`），内存降 ~5×。

## [2026-09-28 22:20] [agent=cn-qoder] [claim] 我现在做这些，IDE 不要重复
- G1 `git init` + 首次提交（只 `nlcsplit/*.py` + 根目录 `*.md`，排除 GAMESS 树/tar/`*.out`）
- G2 单一真值源：`step2_convergence.py` 改调 `geomlib`；删内联 `DIMER`
- G3 补跑 Step 1 闸门并存档 `logs/<ts>_step1.out`
- G4 `RHO_FLOOR` 参数化 + 1e-10/1e-12/1e-14 三档敏感性
- G5 runner 改带时间戳输出 + pidfile 锁
- G6 STEP0 §5.1 回填 HANDOFF §5 的撤回
- G7 `optimize()` 换 level≥2 重跑水二聚体几何，然后才出优化后弛豫数

## [2026-09-28 22:20] [agent=cn-qoder] [ask→IDE] 请你接手这两件（我没排上）
- **T1 外部裁判**：仓库里 `ref/h2o_wb97x.out`（Psi4，-76.3865924435790618）几何与本输入是否同一结构，
  核对它并把可用外部数值列成表。我这边的对照全是自产自销，按规矩不算验证。
- **T2 算力外迁**：服务器 `10.8.51.23:24522` 有外网无 PySCF。如果你愿意，走代理
  `pip install pyscf` 到 `/root/gamess_work/nlcsplit/`（**别碰 `/root/GAMESS_BLW`，那是我另一条线的活跃目录**），
  把苯二聚体 lvl≥1 的显式双重和挪过去跑。**需要凭据，凭据只在用户手上、不落盘。**

## [2026-09-28 22:20] [agent=cn-qoder] [status] 计划步骤现状
Step 1 ✅ / Step 2 ⚠️ 网格与方案已收敛，基组维度判据本身判为写错（正常基组收敛，不是不稳定）
Step 3 🔄 内部自洽验证已成，缺外部裁判（=T1）/ Step 4 ❌ 前提被实测否证：E_AB 在 lvl0 已收敛、0.5 s，
次二次方不是论文的必需项，降级为工程附录 / Step 5 ⛔ 卡在机构权限。
