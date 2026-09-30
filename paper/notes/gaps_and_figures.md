# 待补清单 / 图件 与正文的全量对账

生成时间：2026-09-29（只读核查，未修改任何既有文件）。判据一律是仓里的文件或日志行，
不是印象；没有文件依据的句子标 `UNVERIFIED`。核查手段：`git ls-files` / `git check-ignore -v` /
`git show <commit>:<file>` / `git diff HEAD` / 侧车 JSON 直接解析 / 逐行 grep 正文与骨架。

三份承重文档的行号以工作区当前版本为准：`MAIN-skeleton.md`(244 行)、`paper/main.md`(687 行)、
`paper/main.tex`(241 行)。

---

## 表 1 — `MAIN-skeleton.md` 「### 待补（按优先级）」逐条对账（清单在 :196-221）

| # | 条目 | 骨架位置 | 现在的真实状态 | 依据（文件:键 / 归档 stdout 行） | 若已关闭，正文/骨架该改成什么 |
|---|---|---|---|---|---|
| 1 | 其余体系的 CCSD(T)/CBS 色散分量参考值（带 DOI） | :197（另见 :159-160 表 3b 指向"待补项 3"） | **未开始** | `RESEARCH-20260929-lit.md:116`「水二聚体的对应数这篇**没有**…仍待补」、`:120`「水/甲烷/氨-水/苯-水 的 CCSD(T)/CBS 色散分量参考值（带 DOI）」仍列为欠；`grep -n "CCSD\|CBS" paper/main.md` 只命中 :272 的几何参考值，**正文从未引用过任何 CCSD(T)/CBS 数** ⇒ 没有来源的数字确实没进稿（写作纪律守住了） | 正文无需改。骨架 :160 的括号「（待补项 3）」是**错指**——它指的是清单第 **1** 条，第 3 条是第三裁判。改成「（待补项 1）」 |
| 2 | ~~WoS/Scopus 正式检索~~ | :198-200 | **已关闭**（WoS 两轮，第二轮全量枚举；Scopus 未订阅是已交代的限制，不是欠项） | `RESEARCH-20260929-lit.md:374`「## 13. 第二轮：改用 WoS 自己的记录接口，全量枚举」、`:392`/`:470` `RecordsSearched = 58,664,816`；正文 `paper/main.md:5-15`、`:156-176`、`:518-535`，落点 `[S17]` = `RESEARCH…:§13` | 正文与骨架已同步，无需改 |
| 3 | 第三个真正独立的裁判 | :201-210 | **部分关闭**：跨**程序**锚点已成立；跨**实现**（libxc `xc_nlc_vxc` / Psi4）未开始 | 已成立：`nlcsplit/logs/orca_anchor.json` `runs` 长度 6、`/program = "ORCA 6.0.1 RELEASE"`、`/quantity_printed = "ORCA's 'NL Energy, E(C,NL)' line"`、`runs[2]/E_vv10_kcal_mol = 52.93559`；原件 `evidence/orca_run/{h2o,benz}_{mono0,mono1,dimer}.out` **全部 git 跟踪**（`git ls-files evidence` 24 条）+ `MANIFEST.sha256`。未开始：`ls nlcsplit/examples/` **无 `libxc_referee.py`**（该文件只出现在 `PROGRESS-nlcsplit.md:1745` 的任务表里，无产物）⇒ **未找到依据** | 见下方「表 1b」——这条是本次最严重的失联点，正文 4 处 + 骨架 4 处仍是旧话 |
| 4 | 图 3：ΔE_NLC vs 文献 E_disp 相关性（A 案 go/no-go） | :211 | **未开始** | `ls figs/` 只有 `fig1_xc_split.png`、`fig2_scheme_sensitivity.png`；`nlcsplit/figures.py` 只定义 `fig1`(:31) 与 `fig2`(:55) 两个函数 ⇒ 无 fig3 产物、无脚本。**另**：`paper/p2_skeleton.md:213` 有一个 `figs/fig3_scaling.png` 标 **PENDING**，那是**另一篇**的标度曲线，与本条同名不同物 | 正文/骨架无需改（都没引它）。但两个「图 3」要立刻编号隔离，见「动手清单」第 9 条 |
| 5 | 苯二聚体两构型的 level 1 | :212 | **已关闭** | `nlcsplit/logs/step_h.json` 顶层 `level: 1`、`rows` 8 条，`苯二聚体(A).dnlc = -4.366812838084419`、`(B) = -2.3880343911483055`；`git diff HEAD -- nlcsplit/logs/step_h.json` **空**，且 `git show 5db35d5:…`（12:11）与 HEAD 逐位相同 | 骨架 :172-175 与正文 Table 1（`main.md:334-335`）已按 level 1。**但正文 §3.3 仍在用 level-0 旧值**，见「表 1b」第 6 行 |
| 6 | level-2 + 反泊松全表 | :213-215 | **已关闭**（六体系全齐；「差苯-甲烷一个体系」作废） | `nlcsplit/logs/step_h_l2cp.json`：`systems: 6`、`rows` 6 条全 `level: 2` 且 `dcp` 非空 ⇒ BSSE = `dcp − dtot` = **1.687 / 1.491 / 0.196 / 1.075 / 0.760 / 0.578** kcal/mol（水/氨/甲烷/苯-水/苯-氨/苯-甲烷）；苯-甲烷单独一次：`evidence/l2cp/20260929T051912Z_centos-l2_benzmeth_cp.out` 第 6 行行尾 **`4136s`**、`ΔE_int(反泊松) -1.202`；为什么需要补跑：`evidence/l2cp/MANIFEST.txt`「20260928T213839Z step_h_l2cp **rc=124**」 | 正文 `main.md:352-367` 已写对。**骨架 :226-227 是旧话**：「六个体系里的**五个**…（BSSE 1.69 / 1.49 / 0.20 / 1.07 / 0.76）」五个数 → 应六个。替换句：「batch5 + 2026-09-29 的苯-甲烷补跑，六个体系全部 level 2 + 完整反泊松（BSSE 1.687 / 1.491 / 0.196 / 1.075 / 0.760 / 0.578 kcal/mol，`evidence/l2cp/`）」 |
| 7 | 反泊松 ΔE_int 跨 PySCF 版本差 0.139（机制未验） | :216-218 | **未关闭**（差值本身已实测；机制**未验**，骨架自己这么说） | 两个端点：CentOS 2.14.0 = `evidence/l2cp/20260929T051912Z_centos-l2_benzmeth_cp.out:6` `-1.202`；WSL 2.12.1 = `nlcsplit/logs/20260929T051849Z_l2_benzmeth-wsl.out:6` `-1.341`。**⚠ 后一份日志被 `nlcsplit/logs/.gitignore:1:*.out` 排除、未跟踪、也不在发布白名单 `CITED_LOGS`（`make_public_repo.js:129-130`）里**；`git grep -l "1\.341"` 只命中 `paper/main.md` 与 `paper/main.tex` ⇒ 这个数是**正文自述、仓里无原件**（见「动手清单」第 1 条） | 措辞可保持（正文 §2.5/§6 的"report the split, not a diagnosis"是对的），但**必须先补归档件**才配叫开放项 |
| 8 | 基组阶梯需在弛豫几何上重跑 | :219-221 | **未开始** | 现有两件产物都在**构造几何**上：`nlcsplit/logs/20260929T003144Z_stepg-recompute.out`、`evidence/centos/20260928T165857Z_centos-step2.out`；`figs/`、`evidence/` 里没有任何 relaxed-geometry ladder 日志 ⇒ **未找到依据** | 正文 `main.md:621-623`、`:686-687` 已如实写「stays an open task rather than a claim」，与骨架一致，无需改 |

### 用户点名的三条已知未关闭项（逐一验物）

| 条目 | 状态 | 依据 |
|---|---|---|
| 干净 venv + 树外 `pytest --pyargs nlcsplit` | **PENDING**（截至本次核查，产物不存在） | `find` 全仓（排除 `source/`）无 `*pyargs*` / `*cleanven*` / `*clean_venv*` 文件；`grep -rn pyargs` 只命中 `CONTRIBUTING.md:28`（规程本身）、`paper/software.md:188`、`PROGRESS-nlcsplit.md:485/954/1557/1616/1744`，其中 `:1616`「实际状态：**那条没跑过**（task #13 至今未做）」。`software.md:187-195` 已写成 "specified end to end but **not yet fully executed**" ⇒ **正文措辞正确，不要动** |
| libxc 第三裁判 | **未开始** | `ls nlcsplit/examples/` = `__init__.py check_fast_pair.py check_screen_bound_ide.py check_soft_partition.py probe_bound_forms.py quickstart.py`，无 referee 脚本；无任何 libxc stdout |
| CI 真正执行过 | **从未执行** | `git remote -v` **空输出**（无远端）；`PATH` 里无 `gh`；`.github/workflows/ci.yml` 存在且已跟踪（`git ls-files .github` 命中 1 条）。`software.md:197-199` 已写 "written but has **never executed**, because there is no remote repository yet" ⇒ 正确 |

---

## 表 1b — 正文/骨架里其余「未做 / 待补 / outstanding / open」表述的对账

（`grep` 词集：`未做\|待补\|尚缺\|未跑\|not yet\|remain(s)? open\|outstanding\|left open\|has not been\|we do not apply`）

| # | 位置 | 原话（节选） | 真实状态 | 依据 | 申请的具体替换句 |
|---|---|---|---|---|---|
| 1 | `paper/main.md:36-37`（Abstract 末） | "A check against a second *program* is **outstanding** and is listed as a load-bearing limitation in §4" | **已关闭**，Abstract 落后于 §4 | `nlcsplit/logs/orca_anchor.json`；正文自己 §4 `:476`「**Cross-program check: ORCA 6.0.1 agrees on the reported quantity.**」 | → "A check against a second *program* is now in hand: ORCA 6.0.1's `NL Energy, E(C,NL)` agrees to 0.0004 kcal/mol on the water dimer and 0.0416 on the benzene dimer (section 4). What remains outstanding is a second independent *implementation* (libxc `xc_nlc_vxc` or Psi4), listed as a limitation." |
| 2 | `paper/main.md:222`（§2.1 末） | "No agreement with a second program **has been established yet**; see §4." | **已关闭** | 同上；`evidence/orca_run/h2o_dimer.out` 跟踪在库 | → "Agreement with a second program has since been established against ORCA 6.0.1 (section 4); the grid is not matched, so the residual is joint grid-plus-implementation." |
| 3 | `paper/main.md:279-280`（§2.5） | "…so a second-program anchor **is treated as an outstanding requirement rather than as satisfied** (§4, §3.1)" | **已关闭** | 同上 | → "…so the anchor against a second program is reported in §4 as an independent ORCA 6.0.1 evaluation, with its own grid caveat; only a second independent *implementation* remains outstanding." |
| 4 | `paper/main.md:195-196`（§1 两处限制的第一条） | "we do not separate electrostatics, … **and we do not apply a basis-set superposition-error correction to interaction energies**" | **已关闭**，且与同文 §3.2/§4 直接自相矛盾 | `step_h_l2cp.json` 6 行 `dcp` 全非空；`main.md:362-364` 明列六个 BSSE 数；`main.md:461-462`「Counterpoise-corrected interaction energies **are reported in section 3.2 for six of the eight systems**」 | → "…and we do not separate electrostatics, exchange-repulsion, polarisation or charge transfer. Counterpoise correction is applied and reported for the six systems at grid level 2 (section 3.2), but the nonlocal pair term itself needs none, being evaluated at fixed superposed density." |
| 5 | `paper/main.md:74-77`（§1） | "We have not audited the equivalent paths inside **libxc, ORCA**, Psi4 or Gaussian … a direct `xc_nlc_vxc` comparison … is left open" | **部分关闭**（ORCA 已审，其余三家仍未） | ORCA：`orca_anchor.json /program`；libxc：`PROGRESS-nlcsplit.md:977`「PySCF 里 libxc 静态链在 libdft.so，**取不到符号**」+ 无产物；Psi4/Gaussian：全仓无命中 | → "The ORCA 6.0.1 path is now audited (section 4). We have not audited libxc, Psi4 or Gaussian: libxc's VV10 kernel is statically linked into the same shared object PySCF calls, so a direct `xc_nlc_vxc` comparison needs its own bindings and is left open." |
| 6 | `paper/main.md:389`（§3.3） | "our **-4.448** is the same kind of quantity to within functional-generation and basis-set differences" | **数字过时**：-4.448 是 level-0 值，同文 Table 1 已改 level 1 | `PROGRESS-nlcsplit.md:1096`「| **ΔE_NLC** | **-4.448** | **-4.367** | **0.081** |」；`:608` 苯(A) 那行标 level 0；现值 `step_h.json 苯二聚体(A).dnlc = -4.366812838084419`；`main.md:334` = -4.367、`:490` = -4.3668、`:343` 自己写了「moving them to level 1 shifts dE_NLC by 0.081」 | → "our -4.367 (level 1; the level-0 value was -4.448, a 0.081 kcal/mol shift) is the same kind of quantity…" 同源旧值还有 `MAIN-skeleton.md:192`「苯 sandwich −4.45」→ 一并改 -4.367 |
| 6b | `MAIN-skeleton.md:138` 与 `:234` | 「相对值 **0.8%–18.2%** 且无体系类型规律（**苯 sandwich 1.8%** vs 苯-水 18.2%）」/「已被八体系表否证（**苯 sandwich 1.8%** …）」 | **过时，且 :138 在同一行里自相矛盾**：区间写 0.8%、举例写 1.8% | level-0：`PROGRESS-nlcsplit.md:608` 苯(A) 方案跨度 0.072 / P_frz −4.062 = **1.77%**；level-1：`step_h.json` 0.031965683 / 4.037657 = **0.79%**，即同文件表 4b `:175` 的 0.8% | 两处「苯 sandwich 1.8%」→「苯(A) **0.8%**（level 1；level 0 旧值 1.8%，见待补项 5）」 |
| 7 | `MAIN-skeleton.md:114` | "⇒ 诚实表述（2026-09-29 11:20 更正）：**目前没有任何已核实的跨程序锚点**" | **已被同文件自己的 :201-208 否证**（同一条待补在 :114 说没有、在 :201 说已成立） | `orca_anchor.json` + `evidence/orca_run/*` 跟踪件 | → 保留 11:20 的撤回过程（那是轨迹），末句改为「⇒ 13:3x 重跑后跨程序锚点**已成立**，见待补项 3；撤回记录留此以留下轨迹」 |
| 8 | `MAIN-skeleton.md:117-121` | "第三独立实现…从'待补'升格为主篇的承重项…**要拿 ORCA 的非局域项需要 NL-DFT 那类运行，待重算**" | **部分关闭**：ORCA 那类运行**已重算并入库**；仍欠独立实现 | `evidence/orca_run/h2o_dimer.out` 等 6 个 .out（已跟踪）+ `MANIFEST.sha256` | → 把「待重算」改为「已重算，6 次串行单点归档在 `evidence/orca_run/`」，承重项一句改挂在 libxc/Psi4 上 |
| 9 | `MAIN-skeleton.md:231-232`（§4 Limitations） | "**独立裁判：目前 0 个（不是 1 个）**…**拿到第二个程序的 E_NLC 是投稿前的硬任务**" | **已关闭**（第二个程序已到手） | 同 #7/#8 | → "独立裁判：程序层面 1 个（ORCA 6.0.1，见待补项 3）；**实现层面仍 0 个**（libxc/Psi4 未落地）。第二个程序的 E_NLC 已拿到，剩下的是同泛函参数在另一套实现里再算一遍。" |
| 10 | `MAIN-skeleton.md:109`（表 1 撤回行的**理由**） | "`ref/h2o_wb97xv.out` 是普通单点输出，只有 `EX=-5.966547477 / EC=-0.409475923`（**非局域项折在 EC 里、从未单列**）" | **该理由被文件本身否证** | `ref/h2o_wb97xv.out` 第 651-657 行是 `DFT components:` 块，`:654 E(X)`、`:655 E(C)`、**:657 `NL Energy, E(C,NL) :  0.042653836648 Eh`** = **+26.7657 kcal/mol**，非局域项**单列**存在 | ⚠ 这条只推翻**撤回的理由**，不推翻撤回本身：该文件与锚点跑的**不是同一次运行**（此文件 `Total Energy -76.376956199`，锚点 `runs[0] -76.377040692`，网格/基组设置不同），且它在 gitignore 的 `ref/` 里（`git check-ignore -v` → `.gitignore:5:ref/`），数值是否就是当年那个 6e−4 **UNVERIFIED**。建议改为：「撤回仍然成立——该值不可与本文表 1 并排（不同网格/基组，且原件在 gitignore 的 `ref/` 里不可重建），但我当时写的'非局域项从未单列'是**错的**：`ref/h2o_wb97xv.out:657` 就单列着 `NL Energy, E(C,NL)`」——这正是「只按字样 grep 就下结论」的老毛病换了个方向再犯一次 |
| 11 | `paper/main.md:676-677`（附录"三条明说的缺失"之二） | "S15's files **were sitting in `scratch/`**, which is gitignored - they **were promoted** into `evidence/` on 2026-09-29" | **已完成**，读起来却像进行中 | `git ls-files evidence/retrieval_calibration` 命中 **6** 条（4 个被引文件 + 2 个 MANIFEST）全部跟踪 | → 过去式即可，但建议补一句落点哈希「现均在 `evidence/retrieval_calibration/`，逐文件对 `MANIFEST.sha256`」 |

---

## 表 2 — 图件对账

**脚本侧**：`nlcsplit/figures.py` 只定义两图，输出目录**写死**在 `nlcsplit/../figs`（:20 `OUT`），数据源**只有一个**——`load("step_h.json")`（:74），即 level-1、未做反泊松的 8 体系侧车。

| 图 | 数据来源脚本 / 侧车 | 文件是否存在 | 正文是否引用 | caption / 轴 / 单位 | 与正文数字是否一致 | 是否在发布白名单 |
|---|---|---|---|---|---|---|
| **Fig 1** `fig1_xc_split.png` | `figures.py:31 fig1()` ← `nlcsplit/logs/step_h.json` `rows[].dnlc`、`dxc − dnlc` | `figs/` 有（56195 B，md5 `b0d3ce54e9a6b6ef87d22a05b970dcd8`）；`paper/figures/` 有**同一份**（md5 完全相同） | **没有引用** | 无 caption。轴：`set_ylabel("kcal/mol")` ✓、图例两条 label 带单位说明（:38,:40-41）、标题 `(superposition, no BSSE)`（:46-47）✓ 与 §3.2 只在六体系做 CP 一致 | **一致**：8 柱对 = (-4.3668,-0.119) (-2.3880,-2.1674) (-0.5935,-3.1146) (-0.678,-0.203) (-0.517,**+0.285**) (-1.259,-2.753) (-1.327,-1.588) (-1.404,-0.918) ⇔ `main.md:334-341` Table 1 与骨架 4b 逐行同；甲烷"其余 XC"为正 ⇔ `main.md:129-130` 的排斥说法 | **不在**（:26-33 五个清单无 png；:38、:258 明确把 `figs/`、`paper/**` 列为不带；`ls -R dist/nlcsplit` 无 figs 目录） |
| **Fig 2** `fig2_scheme_sensitivity.png` | `figures.py:55 fig2()` ← 同侧车 `rows[].span`、`pint.becke`。**注意 `:57` 按百分比降序重排**，所以柱序是 苯-水 18.16 → 苯-氨 16.08 → 苯-甲烷 14.77 → 苯(B) 9.23 → 水 7.23 → 氨 4.47 → **甲烷 0.84 → 苯(A) 0.79** | `figs/` 有（95890 B，md5 `5895053f582b872f3314dd8c62537af2`）；`paper/figures/` 有同一份 | **没有引用** | 无 caption。轴：`set_xlabel("scheme spread / |P_frz|  (%)")` ✓、`set_title(...0.8-18%...)`（:65-66）；**无 y 轴 label**（靠体系名 tick） | **数值一致**：按侧车行序（苯A/苯B/水/氨/甲烷/苯-水/苯-氨/苯-甲烷）算得 0.792 / 9.233 / 7.231 / 4.468 / 0.844 / 18.162 / 16.080 / 14.771 %，与 `main.md:406-413` 的 0.8 / 9.2 / 7.2 / 4.5 / 0.8 / 18.2 / 16.1 / 14.8 逐体系吻合。**但** `main.md:406-407` 自称按 relative 升序，却把甲烷(0.844)排在苯(A)(0.792)之前，升序应是苯(A) 先。**且分母口径三处三种叫法**：图轴 `|P_frz|`、`main.md:106` `relative to |E_AB|`、Abstract `main.md:49` `relative to the Becke-scheme value` | **不在**（同上） |
| Fig 3 | `MAIN-skeleton.md:211` 想要的 ΔE_NLC vs 文献 E_disp 相关性图 | **不存在**（`ls figs/` 无） | — | — | — | — |

### 图件侧四项硬伤（逐条给证据）

1. **一张图都没被引用**（最反直觉的一条）。`grep -in "fig1\|fig2\|Figure\|图 [0-9]\|includegraphics\|figures/" paper/main.md paper/main.tex` **零命中**（唯一两处 "fig" 是 "blanket uncertainty **figure**" 和 "**config**uration" 的假命中）；`grep -c "begin{figure}" paper/main.tex` = **0**；`paper/main.log` 首行「Output written on main.pdf (14 pages」。⇒ 那 14 页 PDF **不含任何图**；`figs/` 与 `paper/figures/` 都是孤儿产物。骨架 :139「（图 2 标题已按此改）」指的是一份正文里并不存在的图。
2. **`figs/` 的 png 从未进 git，而且是被一条看着像能用的规则悄悄吞掉的**。`.gitignore` 第 23 行 `figs/` + 第 24 行 `!figs/*.png`：git 无法重新纳入被排除目录下的文件，故 negation 无效。实测 `git check-ignore -v figs/fig1_xc_split.png` → 「`.gitignore:23:figs/  figs/fig1_xc_split.png`」；`git ls-tree -r HEAD --name-only | grep fig` 只有 `nlcsplit/figures.py`。⇒ 写 `!figs/*.png` 的人以为自己在跟踪图，实际没有。
3. **`paper/figures/` 是未跟踪副本**：`git status --short paper/` → `?? paper/figures/`（不是 ignored，只是从没 add 过）。它与 `figs/` 逐字节相同（两对 md5 互相吻合），时间戳 13:27 vs 12:19 ⇒ 手工拷贝。投稿包若从这里取图，等于**用未跟踪文件投稿**。
4. **⚠ 未入白名单 = 正文引用公开仓里不存在的东西**（用户点名的最严重一条，结论：目前"侥幸未爆 + 已经埋好"**）。`tools/make_public_repo.js` 的白名单 :26-33 只有 `PKG/STEPS/TESTS/EXAMPLES/ROOT` 五个清单，:38 与 :258 明确把 `figs/` 与 `paper/**` 排除。所以公开仓里连 `figs/` 目录都没有——只有生成它的 `nlcsplit/figures.py`(:26) 和它读的两份侧车（:112 `step_h.json`、:116 `step_h_l2cp.json`），读者**能重算、看不到成品**。因为正文一张图都没引（第 1 条），这条失败模式**尚未被触发**；但 `paper/figures/` 的存在说明有人已在往投稿包里放图，一旦正文写出 "Fig. 1 shows…"，就正好落进闸门 D 抓不到的那个盲区——闸门 D 只 `app.slice(app.indexOf('## Appendix'))`（:160）扫附录行，**不扫正文**（同一条盲区本次已实测到两个实例，见表 2b）。

### 表 2b — 正文**引用了但 git/公开仓里没有**的东西（闸门 D 的结构性盲区，实测命中）

用与闸门 D 相同的正则扫 `main.md` 前 646 行（附录之前）的所有反引号路径，逐条查存在性与跟踪状态：

| 位置 | 正文写的 | 真实情况 | 危险 |
|---|---|---|---|
| `main.md:481`（§4 跨程序锚点的**控制组**） | "`ref/h2o_wb97x.out`, an ωB97X run with no `-V`, which contains **no such line**" | 文件**存在且论断为真**（`grep -c "NL Energy" ref/h2o_wb97x.out` = **0**，对照 `ref/h2o_wb97xv.out` = **2**），**但** `git check-ignore -v` → 「`.gitignore:5:ref/`」：不跟踪、不在白名单、不在任何附录 `[S#]` 行里 ⇒ 公开仓读者打不开这条**唯一**支撑"标签是 VV10 专属而非泛 DFT 打印"的证据 | **最高**：锚点主张的控制组是个不可公开的本地文件 |
| `main.md:293`（§2.5）与 `:618-619`（§6 开放项 1） | "-1.341 vs -1.202 kcal/mol, a difference of 0.139" | `-1.341` 只活在 `nlcsplit/logs/20260929T051849Z_l2_benzmeth-wsl.out:6`，被 `nlcsplit/logs/.gitignore:1:*.out` 排除；`git grep -l "1\.341"` 只命中 `paper/main.md` 和 `paper/main.tex`；`[S8]` 的产物清单（`main.md:662`）里**没有**这一份 | **高**：整条"跨版本 CP 不可移植"的开放项建立在仓里无原件的数上 |
| `main.md:257`（§2.4） | "fetched by `tools/get_s22.sh`" | 路径不存在。实际是 `nlcsplit/tools/get_s22.sh`（存在，755），发布时落 `nlcsplit/tools/get_s22.sh`（`make_public_repo.js:88`）⇒ 工作仓和公开仓**两边都打不开**这个写法 | 中：纯路径笔误，闸门 D 同样扫不到 |

（同一扫描的良性命中：`paper/tex_audit.md` :5 存在 ✓；`S22/NN/struc.xyz` :257 指 GMTKN55 仓内相对路径，不是本仓文件 ✓。）

---

## 表 3 — 正文 §6/§7 自认的开放项，逐条现在还能不能划

`main.md` 实际只有 §1–§6（无 §7；"two items remain open" 出现在 §4 末并复述进 §6）。

| # | 正文位置 | 自认开放的说法 | 现在是否仍开放 | 依据 | 处置 |
|---|---|---|---|---|---|
| 1 | `:612-613` | "Two items remain open there: **the absolute per-fragment values are still unrefereed**" | **可划一半，且与 §4 直接打架** | §4 `:507-511` 明写 "**That flag is now retired**"，给的是绝对量：二聚体 +52.9345 vs ORCA `+0.084358235 Eh = +52.9356`（= `orca_anchor.json runs[2].E_vv10_kcal_mol 52.93559`）、两单体 +26.7635/+26.7644 vs `runs[0] 26.764561`/`runs[1] 26.764125` | **必须二选一**：严格讲 ORCA 锚的是**整块**单体/二聚体 E_NLC，不是 Becke 切完的**片内绝对量** `β·N_A`（§3.5 说那是恒等式，外部程序给不了）。建议把 §6 这半句改成「整块绝对量已由 ORCA 锚到 1e-3 kcal/mol（§4）；**按片段切开**的绝对值仍是 Becke 布居的恒等式，无外部裁判」——同时把 §4 `:507` 的 "retired" 收窄为 "retired for the total monomer/dimer values" |
| 2 | `:613-614` | "the anchor covers **2 of the 8** systems" | **仍开放，有据** | `orca_anchor.json runs` 长度 6 = 2 体系 × (complex + 2 inequivalent monomer)，仅 water S22#2 与 benzene A S22#11；其余 6 体系无 ORCA 单点 | 保留；建议点名哪 6 个体系缺（水/苯A 之外全缺） |
| 3 | `:616-620` | 开放项一：跨版本反泊松 0.139 kcal/mol，"a counterpoise denominator is not portable" | **仍开放（差值已实测，机制未验）**——但**证据不合规** | 见表 2b 第 2 行：`-1.341` 无跟踪原件 | 保留结论，先把 `logs/20260929T051849Z_l2_benzmeth-wsl.out` 提升进 `evidence/` 并补 `MANIFEST.sha256` |
| 4 | `:621-623` | 开放项二：基组阶梯跑在几何修复前，"the full ladder has not been re-run on the relaxed geometry" | **仍开放，有据** | 两份 ladder 产物都在构造几何（表 1 #8） | 保留 |
| 5 | `:624-626` | "the literature search covers **one index** … Scopus measured as unsubscribed … Embase and SciFinder were not searched at all" | **仍开放（真限制，已如实交代）** | `MAIN-skeleton.md:199-200` 同口径 | 保留 |
| 6 | `:261-264` | Jurečka PCCP 5, 1811 (2003)「we were unable to resolve that DOI through Crossref today and cite it **without a DOI**」 | **仍开放，且无产物** | `evidence/retrieval_calibration/` 只有 OpenAlex/Crossref 稳定性脚本，无该 DOI 的查询记录 ⇒ **未找到依据**（连"试过"的原始返回都没归档） | 补一条 Crossref 查询 stdout，或改「未尝试解析」 |
| 7 | `:561-564` | rVV10「have not been tested and may not share the pairing convention」 | **仍开放，有据**（确无 rVV10 产物） | `grep` 全仓无 rVV10 运行日志 | 保留 |
| 8 | `:550-552` | "we have not implemented a sub-quadratic approximation" | **仍开放**（`fastpair.py` / `fastpair_ide.py` 未跟踪、属另一代理，未进正文主张） | `git status` → `?? nlcsplit/fastpair.py`、`?? nlcsplit/fastpair_ide.py`；`figures.py`/白名单均无它 | 保留；正文别提前引用未跟踪的实现 |
| 9 | `:686-687` | "re-running the full ladder on the relaxed geometry stays **an open task rather than a claim**" | 与 #4 同一件事，**措辞正确** | 同 #4 | 保留（注意别与 :621-623 双写双改） |

---

## 投稿前必须动手的 9 件事（按危险排序，每条给具体动作）

1. **先修"正文引用了公开仓里不存在的东西"这一整类**（闸门 D 只扫附录行，`make_public_repo.js:160` 的 `indexOf('## Appendix')` 就是它的天花板）。
   动作：(a) 把 `ref/h2o_wb97x.out`（§4 控制组，`main.md:481`）和 `nlcsplit/logs/20260929T051849Z_l2_benzmeth-wsl.out`（0.139 的一端，`main.md:293`）照 `evidence/retrieval_calibration/` 的先例提升进 `evidence/`，补逐文件 `MANIFEST.sha256`，并把它们写进 `[S4]`/`[S8]` 附录行；(b) 给闸门 D 加一条"扫 `## Appendix` **之前**正文里所有反引号路径"，与附录同标准；(c) 把 `main.md:257` 的 `tools/get_s22.sh` 改成 `nlcsplit/tools/get_s22.sh`。
2. **决定这篇到底放不放图，然后三处一起改**——这是唯一一条"现状自洽只因为正文压根没引图"的定时炸弹。
   放图 ⇒ (i) `.gitignore` 把 `figs/` 改成 `/figs` 再加 `!/figs/*.png`（或直接 `git add -f figs/*.png`，并删掉那条无效 negation 留下的假安全感），(ii) 把 `figs/*.png` 加进 `make_public_repo.js` 的白名单或在 caption 里声明为投稿包附件，(iii) `tools/md2tex.js` 目前**完全没有**图形映射（只塞了 `\usepackage{graphicx}`，:187），markdown 里写图引用会被静默丢掉，必须加 `\begin{figure}` 转换 + `grep -c "begin{figure}"` 作为出稿前的非零断言。不放 ⇒ 删掉 `paper/figures/` 的未跟踪副本，并删掉骨架 :139/:211 对图 2/图 3 的引用。**无论哪条路，`paper/figures/` 现在处于未跟踪状态，投稿包不能从这里取图。**
3. **同步"跨程序锚点"这一个事实的 8 个副本**（正文 4 处：`main.md:36-37`、`:74-77`、`:222`、`:279-280`；骨架 4 处：`:114`、`:117-121`、`:231-232`、表 1 的 `:109`）。这正是本次暴露的"人肉同步会漏"的实例：骨架同一条待补在 :114 写"没有任何已核实的跨程序锚点"、在 :201 写"已成立"。
   动作：按表 1b 的替换句逐处改；根治办法是在 `nlcsplit/logs/orca_anchor.json` 里加一个 `referee_status` 字段（如 `{"program": "ORCA 6.0.1", "n_systems_anchored": 2, "n_systems_total": 8, "independent_implementation": null}`），骨架和正文都从它抄，并由闸门 D 校验字段与附录 [S4] 行一致。
4. **正文/骨架内部数字自相矛盾（同一件事两档网格各留一份旧值）**：`main.md:389` 的 `-4.448`（level 0）与同文 Table 1 `:334` 的 `-4.367`、锚点表 `:490` 的 `-4.3668` 冲突；骨架 `:192`「苯 sandwich −4.45」同源；骨架 `:138` 更在一行里同时写「0.8%–18.2%」和「苯 sandwich **1.8%**」（1.8% 是 level-0 的 0.072/4.062，0.8% 是 level-1 的 0.031966/4.037657），`:234` 重复同一旧值。按表 1b 第 6/6b 行改，并把 `MAIN-skeleton.md:226-227` 的"五个体系/5 个 BSSE 数"补成六体系/6 个数（0.578）。根治：表 4b / Table 1 的数应当从 `step_h.json` 生成而不是手抄——侧车已是唯一真值源（`PROGRESS-nlcsplit.md:1557` 附近 commit 5db35d5 的说明就是这么写的），但正文那一列仍是人肉搬的。
5. **§6 的"绝对值无裁判"与 §4 的"flag 已撤"必须拆开表述**（表 3 第 1 行）：整块绝对量已锚到 1e-3，片内绝对量是 Becke 恒等式、外部程序给不了。现在两节各说各话，审稿人会拿其中一版打另一版。
6. **Fig 2 的分母口径统一成一个符号、只定义一次**（`|P_frz|` vs `|E_AB|` vs "Becke-scheme value"，见 `:49`/`:106` 与 `figures.py:63`）：三者数值上指的是同一个东西（Becke 片间项），但正文从没定义过 `|E_AB|` 与 `P_frz` 的关系。
7. **两个 PENDING 别提前写成已完成**：干净 venv + 树外 `pytest --pyargs nlcsplit`（全仓无产物，`PROGRESS-nlcsplit.md:1616` 明说没跑）、libxc 第三裁判（`examples/` 无 `libxc_referee.py`）。`software.md:187-199` 现有措辞正确，**照抄进 main.md 就行，不要升级**；CI 从未执行同理（无远端、无 `gh`）。
8. **补一条 rVV10/泛函代差的"未测"落点**（`:561-564`）和 Jurečka 2003 DOI 的查询原件（`:261-264`）——后者连"试过"的证据都没归档，属于"未找到依据"而不是"已查过无果"。
9. **"图 3" 名字撞车要按篇隔离**：骨架 `:211` 的图 3 = ΔE_NLC vs 文献 E_disp（未开始）；`paper/p2_skeleton.md:213` 的 `figs/fig3_scaling.png` = 第二篇的标度曲线（PENDING，另一代理）。两稿共用 `figs/` 目录 + 同一套 `figN_` 前缀，一旦 p2 先落盘，主篇的"图 3"就变成别人的图。建议主篇用 `figs/main_fig*.png` 或各篇独立子目录。

### 一句话总账

待补 8 条：**已关闭 3**（#2 WoS、#5 苯 level 1、#6 level-2+反泊松六体系）、**部分关闭 1**（#3 程序层面成、实现层面欠）、**未关闭但已实测/措辞正确 1**（#7）、**未开始 3**（#1 CCSD(T)/CBS、#4 图 3、#8 弛豫几何重跑阶梯）；另有用户点名 3 条待办 = **PENDING 1**（干净 venv `--pyargs`，无产物）、**未开始 1**（libxc 裁判）、**从未执行 1**（CI，无远端）。图件：定义 2 张、存在 2 张（两份逐字节相同副本）、**正文引用 0 张**、**git 跟踪 0 张**、**白名单 0 张**。正文自认开放项 9 条中，**1 条能划一半、0 条能全划**，其余 8 条经核实仍然成立——但有 2 条（`ref/h2o_wb97x.out`、`-1.341`）的原件不在仓里。

**未修改任何文件。** 本文件是唯一新增产物。

---

## 2026-10-01 更正（本文件的两句总账已经过期）

末行"另有 2 条（`ref/h2o_wb97x.out`、`-1.341`）的原件不在仓里"**两句都不成立**，本轮逐条实测：

* `-1.341` 的原件在仓里且已跟踪：`evidence/l2cp/20260929T051849Z_l2_benzmeth-wsl.out`（11 行，第 6 行即苯-甲烷那行），`main.md` 的 [S8] 行也点名了它。本文件第 80 行说"只活在 `nlcsplit/logs/…`、被 .gitignore 排除"是**归档之后没回来改**——即这条缺口早被关掉了，是笔记过期而不是稿件有洞。
* `ref/h2o_wb97x.out` 那条：工作目录里的 `ref/` 副本确实未跟踪，但正文与 [S18] 引的已经不是那个路径，而是已跟踪的 `evidence/orca_control/h2o_wb97x.out`（`main.md:603`）。`grep -c "NL Energy"` 在该归档件里为 0，正是 §4 控制组要的那句话。

同轮补真正缺的两份，都进了仓并写进引用：`evidence/recompute/20260928T150222Z_step_d_floor.out`（rho_floor 扫描的全部读数原先只在被忽略的工作日志里）与 `evidence/fastpair_ab/20260929T105823Z_pytest_fastpair_L2_L4.out`（p2 引的 2.763e-8 三元组与"15 个根间距全为 0"原先同样只在忽略区）。教训写在这里：**审计文件本身也是数字与路径的载体，它过期时会把已关的缺口重新报成开的**——下一轮读它之前先 `git ls-files` 复核，别照抄它的路径缺失结论。
