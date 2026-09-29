# number_audit — `paper/main.md` 逐数回源（2026-09-29，只读审计）

审计对象：`paper/main.md`（实测 687 行，非 684）。
真值源优先级：`nlcsplit/logs/{step_h.json,step_h_l2cp.json,orca_anchor.json}`（tracked）
> `evidence/**`（tracked，24 个文件）> `nlcsplit/logs/*.out`（**全部 gitignored**）
> `nlcsplit/step_*.py` / `geomlib.py` 定义 > `MAIN-skeleton.md` / `PROGRESS-*.md`（散文，不入库即不算出处）。

结论汇总（明细见下表，行号 = main.md 行号；共 **97 行**逐数判定，实测命令 `grep -c "^| [0-9]" paper/notes/number_audit.md`）：

| 判定 | 条数 |
|---|---|
| 一致 | 58 |
| 不一致 | 21 |
| 口径混用（同一名不同几何 / 不同网格路径 / 不同分母 / 不同档位） | 6 |
| 正文自相矛盾（同一文档两处说法互斥） | 6 |
| 找不到出处（tracked 工件里重建不出，或该交付物不存在） | 4 |
| 精度不匹配 | 2 |

判定按"一票一档"计：若干行同时带两个标签（如"精度不匹配＋找不到出处"、"不一致＋找不到出处"），
按 不一致 > 精度不匹配 > 口径混用 > 找不到出处 > 自相矛盾 > 一致 的优先级只计一次；
带复合标签的行在表内均已把第二个问题写在"判定"格里，不因计数而丢掉。

**全部要求改 main.md 的替换句集中在最后一节「替换句清单」，我未修改任何文件。**

---

## 1. 逐条审计表

### §Abstract（行 24–59）

| 行 | 摘录 | 该数 | 真值源 | 判定 | 应改成 |
|---|---|---|---|---|---|
| 32–33 | "block additivity holds to 3.5e-18 Ha" | 3.5e-18 Ha | `nlcsplit/logs/20260929T010500Z_step1_geomfix.out:6,8,13`（分块和差最大 6.94e-18 Ha）；`nlcsplit/logs/20260929T050035Z_ide-s5full.out:50,70`（最大可加性残差 5.551e-17、**1.110e-16 Ha**）；来源见 `MAIN-skeleton.md:80` | **不一致** | "block additivity holds to 1.1e-16 Ha" |
| 33–34 | "reproduces PySCF's native kernel to ~1e-8 Ha" | 1e-8 Ha | `nlcsplit/logs/20260929T_step_i_gridrepr.out:3,8,13`（+1.541e-8 / +1.012e-8 / +8.489e-9 Ha） | 一致 | — |
| 35 | "to 2e-3 kcal/mol an independently written script ... seven-level grid sweep" | 2e-3 / 七档 | `ref/agentB/sweep_631gstar.txt:6-14`（**level 0–9 共十档**，收敛值 +0.042650982 Ha）、`MAIN-skeleton.md:110` | **不一致**（档数）+ **找不到出处**（`ref/` 被 .gitignore:5 排除；且 PySCF 侧 26.765917 只在 `PROGRESS-nlcsplit.md:915`） | "over a ten-level grid sweep (levels 0–9)"，并把该 txt 提升进 `evidence/` |
| 36–37 | "A check against a second *program* is outstanding" | — | `nlcsplit/logs/orca_anchor.json:157-188`、`evidence/orca_run/*.out`（6 个 run，各 1 行 `NL Energy, E(C,NL)`、各 1 行 ORCA TERMINATED NORMALLY，已实测 grep 计数=1/1） | **正文自相矛盾**（与 §4 行 476、§6 行 606–609 直接冲突） | 见替换句 R1 |
| 39–40 | "eight S22 complexes at official GMTKN55 geometries (omegaB97X-V/6-31G*)" | 8 | `nlcsplit/logs/step_h.json` `rows` 长度 = 8，逐行 `level:1`、`basis:"6-31g*"`、`cpcorr:false`；点数与 `scratch/lit/s22/S22_02.xyz` n=6 / `S22_11.xyz` n=24 一致 | 一致 | — |
| 42–43 | "16% (water) ... 223% (methane) ... 97% and 52%" | 4 个百分比 | `step_h.json` rows：水 -0.5934947874882619/-3.708131402473137=16.0%；甲烷 -0.517/-0.232=222.8%；苯A -4.3668128/-4.4862103=97.3%；苯B -2.3880344/-4.5554625=52.4% | 一致 | — |
| 46 | "inter-fragment pair term accounts for 0.92-1.08 of the frozen-density superposition difference" | 0.92–1.08 | `step_h_l2cp.json` `rows[].p_over_ds`：1.01, 0.96, 0.92, 1.08, 1.05, 1.03（**只有 6 行**） | 一致（数值），但见行 374 的体系数问题 | — |
| 49–51 | "0.004-0.247 kcal/mol absolute, 0.8-18.2% relative ..., invariant across five basis sets and across grid levels" | 五基组不变 | `nlcsplit/logs/20260929T003144Z_stepg-recompute.out:4-8`：方案跨度 sto-3g **+0.0249**、6-31g\* 0.0400、aug 0.0382、def2-svp 0.0390、def2-tzvp 0.0398 | **不一致** | 见替换句 R2 |
| 53–55 | "exactly beta times ... 3.04 kcal/mol per electron" | 3.04 / 3.0415 | `20260929T_step_i_gridrepr.out:17`（β = 0.004847 Ha/电子 = 3.0415 kcal/mol/电子）、`step_h_l2cp.json` `beta_int_rho_kcal/∫ρ` | 一致 | — |

### §1 Introduction（行 61–202）

| 行 | 摘录 | 该数 | 真值源 | 判定 | 应改成 |
|---|---|---|---|---|---|
| 106–107 | "0.004–0.247 ... 0.8–18.2% ... benzene **sandwich** sits at 0.8%" | 0.8% | `step_h.json` 苯二聚体(A) span 0.03196568 ÷ abs(−4.037656678) = 0.79% | 一致（数值）；**称谓混用**：Table 1 行 334 把同一个 A 叫 "parallel-displaced" | 统一为 "benzene dimer A (parallel-displaced)" |
| 109–111 | "spread stays 0.038–0.040 kcal/mol across five basis sets while the quantity itself drifts by 0.17" | 0.038–0.040 / 0.17 | `20260929T003144Z_stepg-recompute.out:4-8`：0.0249（sto-3g）被漏；漂移 −0.3857→−0.5537 = 0.168 ✓ | **不一致** | "stays 0.025–0.040 kcal/mol across five basis sets (0.038–0.040 for the four beyond STO-3G) while the quantity itself drifts by 0.17" |
| 120 | "Δβ∫ρ vanishes to 3.7×10⁻⁵ kcal/mol in our level-1 test [S3]" | 3.7e-5 | `evidence/centos/20260928T165857Z_centos-step_f_h2o2.out:9`（ΔE_loc=+3.736e-05，`level=1`） | 一致（注：该 run 是几何修复前的构造几何，片间最短 2.0258 Å；正文附录已声明只取记账量） | — |
| 130 | "ΔE_NLC = −0.517 against ΔE_xc = −0.232" | 2 数 | `step_h.json` 甲烷二聚体行 | 一致 | — |
| 141–147 | "OpenAlex and Crossref ... four-repetition test ... rank 0 in 4/4 runs ... at 0/4 each" | 4/4, 0/4 | `RESEARCH-20260929-lit.md:303-305`（§11.2 OpenAlex 重试版：题名式 4/4 rank0，两条主题式各 0/4）＋`:213,215`（§9.2 Crossref 4/4 是**四条不同已知题名**，非四次重复） | **口径混用**（把 OpenAlex 的四次重复测法归到两台仪器头上） | "OpenAlex repeated one title-like query four times and hit rank 0 in 4/4; Crossref retrieved four distinct known titles 4/4 at rank 0" |
| 158 | "58,664,816 records searched, 2026-09-29" | 58,664,816 | `RESEARCH-20260929-lit.md:392`（§13.2 标题）、`:470` | 一致 | — |
| 160–162 | 最贴主张那条 TS 式（逐字引用） | 检索式原文 | `RESEARCH-20260929-lit.md:427`（式 A 含 **`"pair-resolved" OR "pair resolved"`** 两个变体） | **不一致**（引文漏了一个 OR 分支，审稿人照抄会跑成另一条式子） | 按 §13.4 原文补齐 `"pair resolved"` |
| 165 | "one of 29 benchmarked functionals" | 29 | `RESEARCH-20260929-lit.md:347`（#7 判定行） | 一致 | — |
| 171–176 | "two further result lists of 33 and 33 records" | 33+33 | `RESEARCH-20260929-lit.md:430-431`（式 D=33、式 E=33） | 一致 | — |
| 187 | "five keyword-shaped queries in the first round missed it" | 5 | `RESEARCH-20260929-lit.md:346-351`（§12.2 先例式 = #4/#6/#7/#8/#9/#10 **共 6 条**）；`:367-368`（面板 9 条 = 3 校准 + 6 先例） | **不一致**（本文行 630 自己写的是 Six；`RESEARCH` §13.5 也误写"五轮"） | "six keyword-shaped queries in the first round" |
| 190 | "1 record / 3,317 records / 33 records" | 3 数 | `RESEARCH-20260929-lit.md:337-339` 与 `:395-397`（两轮逐条相同） | 一致 | — |
| 198 | "interpolation residual ... of order 4×10⁻⁶ kcal/mol" | 4e-6 | `nlcsplit/logs/20260929T071016Z_ide-s7.out:55-57`（H2O lvl0/1/2 = +4.98e-6/+3.70e-6/+4.00e-6）、`step_h_l2cp.json` `two_impl_diff_kcal` 3.8e-6–2.2e-5 | 一致 | — |
| 200 | "≈0.1–0.9 kcal/mol offsets ... a pairing error in our own kernel" | 0.1–0.9 | `nlcsplit/logs/kernel_variants.out:3,10,17,24`（0.1346–0.9057）、`20260929T012238Z_ide-s4l1nobz.out:7-13`（0.0076–0.9143） | 一致 | — |

### §2 Method（行 204–299）

| 行 | 摘录 | 该数 | 真值源 | 判定 | 应改成 |
|---|---|---|---|---|---|
| 213 | "(b, C) = (6.0, 0.01) for ωB97X-V" | b, C | `20260929T071016Z_ide-s7.out:44`（libxc 与 `PySCF nlc_coeff=(((6.0, 0.01), 1),)` 并列）、`step_d_floor.out:14` | 一致 | — |
| 216–217 | "+0.138 water, +0.418 argon, +0.914 benzene" | 3 数 | `20260929T012238Z_ide-s4l1nobz.out:10,9,13`（**同批 level=1**：+0.1379 / +0.4182 / +0.9143）；另 `kernel_variants.out`（lvl0 苯 +0.9057，不可混） | 一致 | — |
| 219 | "reproduces PySCF's native kernel to **3×10⁻⁵** kcal/mol on the water monomer" | 3e-5 | `20260929T012238Z_ide-s4l1nobz.out:10`（H2O v2−PySCF = **+0.000004**）；`20260929T071016Z_ide-s7.out:56`（+3.70e-06）；`s4selftest2:19-24`（5.9e-9 Ha=3.7e-6 kcal）。3e-5 只出现在**苯 lvl0**（s7:59 = +2.87e-05）与 `step_h_l1.out:22`（苯-甲烷 2.5e-5） | **不一致** | "reproduces PySCF's native kernel to 4×10⁻⁶ kcal/mol on the water monomer (and to ≤2.5×10⁻⁵ for any species tabulated here)" |
| 220–221 | "agrees to 2×10⁻³ kcal/mol ... seven-level grid sweep" | 2e-3 / 七档 | 同上 `sweep_631gstar.txt`（十档）；差值 26.765917−26.763873=2.04e-3 ✓ 但 26.765917 无归档 stdout | **不一致**（档数）+ **找不到出处** | 见 R3 |
| 222 | "No agreement with a second program has been established yet" | — | `orca_anchor.json` delta 段（0.0004 / 0.0416）+ `evidence/orca_run/` | **正文自相矛盾** | 见 R1 |
| 233–234 | "additivity residual ... 0.00–3.5×10⁻¹⁸ Ha across all systems and partitions reported here" | 3.5e-18 | 同 abstract 行 33；实测最大 **1.110e-16 Ha**（`20260929T050035Z_ide-s5full.out:70`，(C6H6)2 lvl1 nearest 行），水二聚体侧 2.776e-17（:17,28）；分块和差列最大 6.94e-18（`step1_geomfix.out:6,13`） | **不一致** | "0.00–1.1×10⁻¹⁶ Ha" |
| 236–237 | "reduces peak memory by roughly a factor of five at this system size" | 5× | 仅 `PROGRESS-nlcsplit.md:77`（"内存降 ~5×"）散文，无归档测量 | **找不到出处 / UNVERIFIED** | 删掉倍数，或补一次可归档的峰值内存测量后再写 |
| 246 | "default 10⁻¹²" | 1e-12 | `nlcsplit/logs/step_d_floor.out:7-8`（"参照档 = 1e-12（= nlc.RHO_FLOOR 默认值）"） | 一致 | — |
| 246–247 | "removes 10.7–22.6% of points" | 10.7/22.6% | `step_d_floor.out:25`（lvl1 floor1e-16 丢 10.7%）、`:33`（lvl2 floor1e-8 丢 22.6%） | 一致 | — |
| 247 | "changing E_AB by 2.1×10⁻¹¹ kcal/mol **between floors of 10⁻⁸ and 10⁻¹⁶**" | 2.1e-11 | `step_d_floor.out:79`（"区间 1e-10..1e-14 跨度 = ... (2.149e-11)"）、`:81`（lvl2 同区间 4.181e-11）；全五档跨度看 `:63-64` 八位小数矩阵 = 1e-8 kcal/mol | **口径混用**（2.1e-11 属于 1e-10–1e-14 区间，不是 1e-8–1e-16） | "changing E_AB by 2.1×10⁻¹¹ kcal/mol over floors 10⁻¹⁰–10⁻¹⁴ (1×10⁻⁸ over the full 10⁻⁸–10⁻¹⁶ range)" |
| 248 | "dropped points carry at most 2.3×10⁻⁶ electrons" | 2.3e-6 | `step_d_floor.out:17`（2.279e-06，全部十档里最大） | 一致 | — |
| 257 | "fetched by `tools/get_s22.sh`" | 脚本名 | `tools/` 实测只有 `build_pdf.sh`、`make_public_repo.js`、`md2tex.js`；`git ls-files tools/get_s22.sh` = 无；`MAIN-skeleton.md:243` 写的是 `scratch/lit/get_s22.sh`（scratch 被 .gitignore:4 排除） | **不一致（文件不存在）** | 见 R4 |
| 265–266 | "1.65 Å cutoff ... longest covalent bond ... aromatic C–C, **1.397** Å" | 1.65 / 1.397 | 1.65 ✓ `nlcsplit/geomlib.py:144-145 COV_CUTOFF`；1.397 = `geomlib.py:7,78`（**我们构造的苯**），官方 `scratch/lit/s22/S22_11.xyz` 实测最长 C–C = **1.3939 Å**（22 个文件全扫，八体系最大键长 ≤1.5016 Å） | **口径混用**（拿构造几何冒充官方几何） | "aromatic C–C, 1.394 Å in the official files" |
| 266 | "shorter than the shortest hydrogen bond (O···H 1.95 Å)" | 1.95 | `scratch/lit/s22/S22_02.xyz` 实算 O1···H2 = 1.9516 Å；`step_h.json` 水行 `dmin:1.9515856687929185` | 一致（注：`geomlib.py:144` 注释写的是 1.81，另一条口径） | — |
| 268–270 | "atoms are ordered so that the fragments interleave" | — | `S22_02.xyz:3-8` 顺序 O,O,H,H,H,H ⇒ 半数切分会把两片混在一起 | 一致 | — |
| 272 | "R(O···O) = 2.901 Å, 0.009 Å from the reference value [S6]" | 2.901 / 0.009 | `evidence/centos/20260928T165857Z_centos-step_c.out:19`（优化后 O..O = 2.901 Å）；参照 2.9104 = `S22_02.xyz` 实算，`MAIN-skeleton.md:147` | 一致 | — |
| 279–280 | "a second-program anchor is treated as an outstanding requirement rather than as satisfied" | — | 同 orca_anchor | **正文自相矛盾** | 见 R1 |
| 283–284 | "close e_tot = ... to **≤9×10⁻¹²** kcal/mol" | 9e-12 | 全部归档 stdout 的「闭合」列实测最大 **1.1e-10 kcal/mol**（`evidence/l2cp/20260928T213839Z_centos-step_h_l2cp.out:27`；同值 `step_h_l2cp.json` 苯-水/苯-氨 `terms[].closure_kcal`）；代码闸门是 `step_f_dispersion.py:75`（>1e-8 Ha 才报错） | **不一致** | "to ≤1.1×10⁻¹⁰ kcal/mol" |
| 287–288 | "10% different numbers of grid points at the same level (**18368 vs 20248** for the water dimer at level 1)" | 18368 / 20248 | 20248 = `nlcsplit/logs/20260928T193520Z_centos-step_h_l1.out:2`（CentOS 2.14.0，**atom_partition 网格**）；同一条式子在 2.12.1 上的分区网格是 **18336**（`nlcsplit/logs/20260929T040643Z_steph-wsl-repro.out:2`）；18368 = `20260929T_step_i_gridrepr.out:6` 的 `N_ref`（**同版本、未分区的参照网格**），与 `N_part=19936` 同批 | **口径混用**（跨版本对比取了参照网格的数） | "(18336 vs 20248 for the water dimer at level 1); the unpartitioned reference grid at the same level has 18368 points, which is a different quantity and must not be quoted here" |
| 289–292 | "ΔE_NLC agrees to 3.3e-4 (-1.404667 vs -1.405), ΔE_xc to 4e-4, ΔE_int to 4.5e-5, span to 2e-4, P_frz to 1e-3" | 5 个"一致到" | 3 位小数一侧全部来自 `evidence/l2cp/20260929T051912Z_centos-l2_benzmeth_cp.out:6`（ΔE_NLC -1.405 / ΔE_xc -2.325 / ΔE_int -1.780 / 跨度 0.213 / P_frz -1.441，**该 stdout 只印三位**）；全精度一侧只在 `PROGRESS-nlcsplit.md:1444-1448`（−1.4046666688504081 等，散文表，WSL 侧车落在仓库外） | **精度不匹配**（差值本身被 5e-4 的四舍五入半格淹没，"4.5e-5 一致"不可能被测出）＋**找不到出处**（全精度侧无 tracked 工件） | 见 R5 |
| 292–294 | "-1.341 vs -1.202 kcal/mol, a difference of 0.139 that is two thirds of the level-2 attribution span" | −1.341 / −1.202 / 0.139 / 三分之二 | `20260929T051849Z_l2_benzmeth-wsl.out:6`（反泊松 −1.341，N=110288，2713 s，PySCF 2.12.1 见 `PROGRESS-agent-l2.md:20`）；`evidence/l2cp/20260929T051912Z_centos-l2_benzmeth_cp.out:6`（−1.202）；`step_h_l2cp.json` 苯-甲烷 `span:0.213` ⇒ 0.139/0.213=0.653 | 一致 | — |

### §3 Results（行 303–451）

| 行 | 摘录 | 该数 | 真值源 | 判定 | 应改成 |
|---|---|---|---|---|---|
| 311–316 | "+1.5e-8, +1.0e-8, +8.5e-9 Ha" / "-0.0282, +0.0015, +0.0001 kcal/mol" | 6 数 | `20260929T_step_i_gridrepr.out:3,8,13`（同网格）与 `:4,9,14`（换网格） | 一致 | — |
| 316–317 | "the same three levels integrate the electron number to -1.6e-2, +3.0e-4 and -6.6e-6 electrons **away from the exact value**" | 3 数 | `20260929T_step_i_gridrepr.out:5,10,15`：这三个数是「分区网格 ∫ρ − 参照网格 ∫ρ」（如 lvl0：19.99285272−20.00898781=−1.61e-2），对真值 20 的偏离其实是 +8.99e-3/−7.15e-3、−5.3e-5/+2.4e-4、−3.5e-6/−1.0e-5 | **口径混用** | 见 R6 |
| 332–341 | Table 1 全 8 行 × 5 列（atoms / dE_int / dE_xc / dE_NLC / 占比） | 40 数 | `step_h.json` 逐行 `natm,dtot,dxc,dnlc`（氨、甲烷、苯-水、苯-氨、苯-甲烷五位小数被 CentOS 批次截成 3 位）；占比为上表已复核值 | 一致（正文按 ≤3 位有效小数呈现，未越权主张更高精度） | — |
| 343 | "moving them to level 1 shifts dE_NLC by 0.081 (A) and 0.013 (B)" | 0.081 / 0.013 | `20260928T193520Z_centos-step_h_benz_l0.out:5,9`（−4.448 / −2.401）对 `step_h.json`（−4.3668128 / −2.3880344） | 一致 | — |
| 343 | "levels 1 and 2 agree to the last digit" | — | `20260928T193520Z_centos-step_h_l1.out:5`（−0.593）与 `evidence/l2cp/...step_h_l2cp.out:6`（−0.593），两者都三位 | 一致（但"last digit"只在三位口径下成立） | — |
| 353–356 | "six of the eight; only the two benzene-dimer geometries stay at level 1, and benzene...methane needed a separate run after its first attempt was cut off by a four-hour wall-clock budget" | 6 / 2 / 4 h | `step_h_l2cp.json` `systems:6` + 6 行；`evidence/l2cp/MANIFEST.txt:10`（`20260928T213839Z step_h_l2cp rc=124`＝timeout 截断）、`PROGRESS-agent-l2.md:5-7`（`timeout 14400`）、苯-甲烷补跑 `wall_s:4136` | 一致（这条**已**与侧车同步，就是曾经过期那条） | — |
| 358–361 | "the water dimer, **-0.5935 to -0.5930** and **-0.6012 to -0.6010** kcal/mol" | 4 数 | level 1 全精度 ✓（`step_h.json` −0.5934947874882619 / −0.6012148492993636）；level 2 侧 **−0.593 / −0.601（三位）**（`evidence/l2cp/...l2cp.out:6`、`step_h_l2cp.json` `dnlc`/`p_frz_becke`）——尾那个 0 在工件里不存在 | **精度不匹配**＋**不一致** | 见 R7 |
| 361 | "1.0e-3 is the rounding floor rather than a measured change ... other five ... three decimals" | — | `step_h.json` 五行 CentOS 行（`run_batch:20260928T193520Z_centos-step_h_l1`）确实三位 | 一致 | — |
| 362–365 | "-6.129 ... BSSE of 1.687, 1.491, 0.196, 1.075, 0.760 and 0.578" | 7 数 | `step_h_l2cp.json` 各行 `dtot`−`dcp`：−7.816−(−6.129)=1.687、−5.166+3.675=1.491、−0.662+0.466=0.196、−4.341+3.266=1.075、−2.929+2.169=0.760、−1.780+1.202=0.578（`evidence/l2cp/...l2cp.out:6,11,16,21,26` 与 `20260929T051912Z_...:6` 同值） | 一致 | — |
| 373–374 | "Their ratio falls in 0.92-1.08 **across the eight systems**" | 0.92–1.08 / 8 | 只有 6 个体系有该比值（`step_h_l2cp.json` `p_over_ds`）；`step_h.json` 与 `step_h_benz_l1_remote.json` **无此字段**；苯二聚体只有 level-0 stdout 的 `P/CP 0.91 / 1.02`（`20260928T193520Z_centos-step_h_benz_l0.out:5,9`，**分母是 CP 不是 Δsup**）；0.92/0.99 只出现在 `MAIN-skeleton.md:175-176` | **口径混用**＋**找不到出处**（苯两行） | 见 R8 |
| 375–377 | "for the water dimer we also reproduce it at three different geometries (constructed initial, official S22, omegaB97X-V-optimised) with **0.915**-1.025" | 0.915 / 1.025 / 三几何 | `evidence/centos/20260928T165857Z_centos-step_c.out`：水初始 **1.017**(:6)、水优化后 **1.025**(:24)、**0.915 属于第 15 行的"苯 sandwich"**；水在 step_c 里只有两个几何 | **不一致**（把苯的比值安到水第三个几何上）＋分母是 `P_frz/CP` | 见 R9 |
| 388–392 | "our **-4.448** is the same kind of quantity ... not comparable to the **net interaction energy of -3.8** kcal/mol in the same row" | −4.448 / −3.8 | −4.448 = `20260928T193520Z_centos-step_h_benz_l0.out:5`（**已被本文 §3.2 行 343 判为 level 0 不适用的旧值**），当前值 −4.367（`step_h.json`）；外部色散分量 −3.34…−3.80 ✓ `RESEARCH-20260929-lit.md:94-99`；净能"2–3 kcal/mol"✓ 同文件 `:108-110`（§6.3），**没有任何工件把 −3.8 记为净相互作用能** | **口径混用**（−4.448）＋**不一致/找不到出处**（−3.8 当净能） | 见 R10 |
| 397 | "absolute spans of 0.004-0.247 ... relative spans ... 0.8-18.2%" | — | `step_h.json` 八行 span 与 pint.becke（逐一算过：0.84/0.79/4.47/7.23/9.23/14.77/16.08/18.16 %） | 一致 | — |
| 399–401 | "24-atom ... span (0.032, below the 6-atom water dimer at 0.043) ... 15-atom benzene...water gives the largest (0.247)" | 0.032/0.043/0.247 | `step_h.json` `span` 0.03196568 / 0.04347249 / 0.247 | 一致 | — |
| 405–413 | 表 2 全 8 行（P_frz / span / relative） | 24 数 | `step_h.json` `pint.becke`、`span`；三位小数的行与正文呈现位数一致 | 一致 | — |
| 418–420 | "misstate the methane dimer by more than twenty-fold" | 20× | 18.2/0.8 = 22.75（同上） | 一致 | — |
| 422–426 | "re-running the four schemes at level 1 across five basis sets gives spans of 0.0400, 0.0382, 0.0390 and 0.0398 ... while P_frz moves from -0.386 to -0.554 ... scheme spread stays put at ~0.04" | 4 span / 0.04 | `20260929T003144Z_stepg-recompute.out:4-8`（五档 span 齐全，第五档 sto-3g = **0.0249**）；−0.3857→−0.5537 ✓ | **不一致**（"five basis sets"只列四个 span，且漏掉的那档恰好打破 0.038–0.040） | 见 R11 |
| 426 | "the quantity of interest drifts by 0.17 kcal/mol across the basis ladder" | 0.17 | `20260929T003144Z_stepg-recompute.out:10-14`（最大绝对漂移 0.1680） | 一致 | — |
| 428–429 | "grid convergence ... 0.0081 kcal/mol over level 0 to 2 at 6-31G\* and 0.0002 over level 1 to 2 [S13]" | 0.0081 / 0.0002 | `evidence/centos/20260928T165857Z_centos-step2.out:19`（6-31g\* 跨网格散布 0.0081）、`:8,9`（−0.5237 vs −0.5235 ⇒ 0.0002） | 一致（注：这是**水二聚体单体系**、初始 S22 几何，正文附录已声明） | — |
| 435–436 | "beta = 3.0415 kcal/mol per electron" | 3.0415 | `20260929T_step_i_gridrepr.out:17` | 一致 | — |
| 437–438 | "at grid level 3 the four schemes spread N_A over **9.870-9.969** electrons, which is 0.300 kcal/mol" | 9.870/9.969/0.300 | 实测的是**差**：`PROGRESS-nlcsplit.md:698-700`（ΔN_A = 9.865e-2 e，ωB97X-V/6-31G\*，官方几何，**level 3，N=66532**，`scratch/check_abs_nlc.py` 未入库）；:704 只给 Becke 一侧 9.869898；9.969 = 9.8699+0.0987 的**推导体**，无任何工件印出它 | **精度不匹配**（把推导区间当实测区间）＋**找不到出处** | 见 R12 |
| 446–449 | "changes these numbers by at most 8.7e-7 electrons (2.6e-6 kcal/mol)" | 8.7e-7 / 2.6e-6 | `PROGRESS-nlcsplit.md:704`（软/硬列差 8.7e-07）＋`MAIN-skeleton.md:93-94`；`logs/V2_soft.out:1` 只印"偏离 1 的最大值 = 0.00e+00"，是另一件事；`20260929T050035Z_ide-s5full.out:6` 写"探针 [A] 实测 dev=0" | **找不到出处**（无归档 stdout，仅散文表） | 要么把探针 stdout 落进 `nlcsplit/logs/`（需解除 gitignore）后再引，要么改成"at most 1e-6 electrons (β·Δ ≤ 3e-6 kcal/mol), measured in a probe whose stdout is not yet archived" |

### §4 Limitations（行 455–564）

| 行 | 摘录 | 该数 | 真值源 | 判定 | 应改成 |
|---|---|---|---|---|---|
| 462 | "Counterpoise-corrected interaction energies are reported in section 3.2 for six of the eight systems" | 6/8 | `step_h_l2cp.json` `systems:6` ✓；但 **§1 行 194–196 声明"we do not apply a basis-set superposition-error correction to interaction energies"**，与 §3.2/§4 自己发的六个 CP 值互相打脸 | **正文自相矛盾** | 见 R13 |
| 469–470 | "16% to 223% ... 97% and 52%" | — | 同 abstract 行 42 | 一致 | — |
| 481–482 | "the control ... `ref/h2o_wb97x.out`, an ωB97X run with no -V, which contains no such line" | 0 命中 | 实测：文件存在，`grep -c "NL Energy, E(C,NL)"` = **0** ✓；但 `ref/` 被 .gitignore:5 排除，公开树里查不到 | 一致（内容）＋**找不到出处**（交付） | 把该对照 `.out` 提升到 `evidence/orca_run/` 并补 `MANIFEST.sha256` |
| 483–484 | "Six serial runs ... each terminating normally ... exactly one `NL Energy` line" | 6 | `evidence/orca_run/*.out`：6 个文件，`NL Energy` 计数各 1、`ORCA TERMINATED NORMALLY` 各 1；`orca_anchor.json:19-20,204`（串行 %pal nprocs 1、basis 函数 18→36、96→192 可加） | 一致 | — |
| 487–490 | Table: water −0.5931/−0.5935/0.0004(0.07%)；benzene A −4.3252/−4.3668/0.0416(0.95%) | 8 数 | `orca_anchor.json:162-179`（−0.593094309/−0.593494787/0.00040048/0.0675%；−4.325230445/−4.366812838/0.041582393/0.9522%） | 一致 | — |
| 495–496 | "The benzene gap, 0.042 kcal/mol, is **~17x larger than the 0.0024 kcal/mol attribution span** reported for that same system" | 0.0024 / 17× | 全仓 grep `0.0024` 只命中 `paper/main.md:496` 本行；同系统实测 span = **0.03196568**（`step_h.json` 苯A，正文行 407 自己写的就是 0.032）⇒ 0.0416/0.032 = **1.3×** | **找不到出处**＋**不一致** | 见 R14 |
| 499–503 | "donor r_OH 0.9639/0.9571 vs acceptor 0.9590/0.9590 ... ~0.0004 ... 1.6e-11 Eh" | 5 数 | `scratch/lit/s22/S22_02.xyz` 实算 0.9639/0.9571/0.9590/0.9590 ✓；`orca_anchor.json:193`（6.96241e-7 Ha = 4.37e-4 kcal）✓；`:195`（1.59999e-11 Ha）✓ | 一致 | — |
| 508–511 | "water-dimer nonlocal term of +52.9345 against ORCA's +0.084358235 Eh = +52.9356, and monomers +26.7635/+26.7644 against +26.7646/+26.7641 - agreement at the 1e-3 level" | 6 数 | `step_h_l2cp.json` 水行 `terms[].E_NLC_kcal` 52.9345/26.7635/26.7644 ✓；`orca_anchor.json:66-67,26-27,46-47`（0.084358235133→52.9355918；26.7645615；26.7641246）；差 0.0011/0.0011/0.0003 | 一致（注：ΔE 表用 **level 1**、绝对值核对用 **level 2**，两句同段并排，属可控但建议点明档位） | — |
| 512–516 | "We have not re-established what that 0.14 was" | 0.14 | 历史条目；现存偏移实测 `20260929T012238Z_ide-s4l1nobz.out:10`（+0.1379）与 `s4selftest2:18`（+0.1384）；正文只说"未重建诊断" | 一致（措辞已降级） | — |
| 519–521 | "a known paper title was retrieved exactly (1 record), a broad concept query returned 3,317 records, and a topical AND query ... returned 33" | 1/3317/33 | `RESEARCH-20260929-lit.md:337-339,395-397` | 一致 | — |
| 522–525 | "OpenAlex and Crossref each ... missed that same known, on-topic paper for **2 of 3 and 3 of 3** legitimate topical phrasings respectively" | 2/3 与 3/3 | OpenAlex：两条主题式各 0/4（`RESEARCH-20260929-lit.md:303-305`）＝missed **2 of 2**；Crossref：三条式召回 1/3（`:215`）＝missed **2 of 3**；"3 of 3"只出现在**已被否证的 429 混计那轮**（`:293`"第一轮 1/3；第二轮 0/3"，随后判定为限流假阴性） | **不一致** | 见 R15 |
| 533–535 | "batches of 20 ... on a 33-record query that reads as 13 ... assert len(records)==RecordsFound" | 20/33/13 | `RESEARCH-20260929-lit.md:385-387`（batches:[20,13]、n:33） | 一致 | — |
| 537–541 | "0.004-0.247 ... wrong by more than twenty-fold" | — | 同 §3.4 | 一致 | — |
| 544–546 | "a 0.099-electron spread ... is a 0.300 kcal/mol spread" | 0.099/0.300 | `PROGRESS-nlcsplit.md:698`（9.865e-2 ⇒ 0.3000）；0.099 是把 0.0987 往粗里圆 | 一致（建议写 0.0987） | — |
| 552–553 | "point-value kernel ... accurate to ~1e-8 Ha on its own grid" | 1e-8 | `20260929T_step_i_gridrepr.out:8` | 一致 | — |
| 553–554 | "JuNoLo ran the same N² sum over massively parallel hardware" | — | `RESEARCH-20260929-lit.md:251-253`（原文 "scales as N^2"） | 一致 | — |

### §5–§6 + 附录（行 566–687）

| 行 | 摘录 | 该数 | 真值源 | 判定 | 应改成 |
|---|---|---|---|---|---|
| 574–575 | "three of the bugs this measure was added to catch are described in the supplementary notes" | 3 个 bug / 补充说明 | `paper/` 里没有"补充说明"工件（`paper/notes/` 本次才建）；`paper/software.md:163-183` 讲的是 5 个导出闸门，不是几何断言抓到的 bug；可数的只有 `PROGRESS-nlcsplit.md:121,157`（单位错等 2 个）与 `:651`（`nh3()` 半角 53.35°） | **找不到出处**（交付物不存在） | 见 R16 |
| 576 | "Grid, basis and scheme sensitivity are separate functions (`step2_convergence.py`, `step_g_basis.py`, `step_h_s22.py`)" | 3 脚本 | 三个文件均存在且 tracked（`git ls-files` ✓） | 一致 | — |
| 577–578 | "`partition_factors()` verifies its own output against PySCF's partition weights" | — | `nlcsplit/tests/test_partition_factors.py:31-34`（`abs(soft - w_ref).max() < 1e-11`） | 一致 | — |
| 591–592 | "16% for water, 223% for methane, 97% and 52%" | — | 同上 | 一致 | — |
| 595–596 | "frozen-density pair term accounts for 0.92-1.08 of the superposition difference" | 0.92–1.08 | 同 abstract 行 46（6 体系） | 一致 | — |
| 597–599 | "0.004-0.247 absolute, 0.8-18.2% relative, unchanged across five basis sets and across grid levels" | — | 同 abstract 行 49（五基组那条不成立）；"across grid levels"仅 level1→2 成立（`step_h.json` vs `step_h_l2cp.json` 的 span 差 ≤0.001），level 0 的同类跨度是 0.0490（`20260929T050035Z_ide-s5full.out:15`） | **不一致**＋**口径混用** | "unchanged across grid levels 1 and 2 and across the four basis sets beyond STO-3G" |
| 607–609 | "six ORCA 6.0.1 single points that agree to 0.0004 ... and 0.0416" | 2 数 | `orca_anchor.json` | 一致 | — |
| 612 | "we searched for the words 'nonlocal' and 'VV10' in an output file that labels the quantity `NL Energy, E(C,NL)`" | — | `orca_anchor.json:212`（audit_trail 根因段） | 一致 | — |
| 613 | "the absolute per-fragment values are still unrefereed" | — | 与 §4 行 507–508"That flag is now retired"**互斥**（该 ORCA 锚就是整单体绝对值） | **正文自相矛盾** | 见 R17 |
| 617–619 | "reproduced every attributed quantity to within **4e-4** kcal/mol but the counterpoise interaction energy only to 0.139" | 4e-4 | `PROGRESS-nlcsplit.md:1444-1448`：ΔE_xc 4.1e-4、P_frz **4.2e-4** 已越界；且 3 位小数一侧的舍入半格就是 5e-4 | **精度不匹配**＋**不一致** | 见 R5 |
| 621–623 | "its level-1 column agrees with the post-fix recompute to four decimals for every base the two runs share" | 4 位小数 / 三个共有基 | `evidence/centos/20260928T165857Z_centos-step2.out:3,8,13`（−0.3857/−0.5237/−0.5537）＝`20260929T003144Z_stepg-recompute.out:4-6` 逐字相同 ✓（sto-3g/6-31g\*/aug 三档共有） | 一致 | — |
| 630 | "Six queries in the first round covered the decomposition vocabulary" | 6 | `RESEARCH-20260929-lit.md:346-351` | 一致（与行 187 的 "five" 冲突，改行 187） | — |
| 651 | "those stdout files are tracked, hash-listed under evidence/*/MANIFEST.sha256" | — | `git ls-files nlcsplit/logs` = **3**（只有 step_h.json / step_h_l2cp.json / orca_anchor.json）；.gitignore:5 `nlcsplit/logs/*` 把全部 `*.out` 排除；本审计用到的 S9/S12/S8 三个 stdout（`20260929T_step_i_gridrepr.out`、`20260929T003144Z_stepg-recompute.out`、`20260929T010500Z_step1_geomfix.out`）**本地存在但未被 git 跟踪** | **不一致**（交付声明与实际不符） | 见 R18 |
| 666 | S12 行："five-basis ladder of P_frz at level 1 **on the current geometry**" | — | 与本文行 422 "On the constructed water-dimer geometry"、行 681–683"其 level-1 一列…但整条阶梯仍需在弛豫几何上重跑"**互斥**；工件侧 `20260929T003144Z_stepg-recompute.out:2` 只写"水二聚体"，几何要靠 `MAIN-skeleton.md:134`（"构造几何"）判定 | **正文自相矛盾** | 附录 S12 改成 "on the constructed water-dimer geometry (levels and P_frz reproduce CentOS step2.out exactly)" |
| 671 | S17 行："complete readings of the two 4-record and **three** broad strings" | 3 | `RESEARCH-20260929-lit.md:428-431`（式 B=7、C=8、D=33、E=33 ⇒ **四条**宽式）；本文行 9 自己写的是 "four broad strings of 33, 33, 7 and 8 records" | **不一致** | "the two 4-record and four broad strings" |
| 681–683 | "the level-0 6-31G\* value -0.5316 appears in S13's ladder, while the -0.5975 of the relaxed structure does not" | −0.5316 / −0.5975 | `centos-step2.out:7`（6-31g\* lvl0 E_AB −0.5316）✓；`step_c.out:23`（优化后 P_frz −0.5975）✓ | 一致 | — |

---

## 2. 最危险五条（按审稿人抽查翻车概率排序）

1. **行 496 的"0.0024 kcal/mol attribution span / ~17x"**。全仓 `grep -rn "0\.0024"` 只命中这一行——一个数在正文、骨架、侧车、stdout 里都不存在，而**同一篇正文的表 2（行 407）写着同一个体系的跨度是 0.032**。这是本次审计里唯一"凭空数字 + 与自己正文冲突"的双料问题，而且它出现在 §4 的 ORCA 段落，恰好是被撤回过的那条断言的隔壁。审稿人只要把表 2 和 §4 并排读就能抓到；抓到的印象是"作者在跨程序段落里编了一个数来放大安全边际"（真实比值只有 1.3×，等于把警示方向反过来说）。
2. **行 287–288 的"18368 vs 20248"**。它把 §3.1（`step_i_gridrepr.py` 同版本的参照网格点数）搬进 §2.5 当跨版本证据，正是任务书点名的第 2 类坑：**同一名不同网格路径**。实测跨版本可比分组是 18336（WSL 2.12.1）对 20248（CentOS 2.14.0），而同版本内 scf_grid/atom_partition 是 18368 对 19936。这条一旦被复算，被质疑的不是数字而是"作者分不清自己两条网格路径"，连带 §3.1 整段的两行对照都失去可信度。
3. **行 358–361 的"-0.5935 to -0.5930 / -0.6012 to -0.6010"**。level-2 侧工件里根本没有第四位（stdout 与 json 都是 `-0.593`/`-0.601`），正文却给出带尾零的四位小数并宣称 1.0e-3 是"舍入下限"。这正是本仓已栽过的第 1 类坑（CentOS 批次三位小数）的复发形态：**用一个不存在的第四位去支撑一个精度主张**。同时它还把"六位 level-1 行里只有一位是全精度"的例外说成"唯一全精度的一行"。
4. **行 289–292 + 行 617–619 的整段跨版本"agree to X"**。五个差值（3.3e-4 / 4e-4 / 4.5e-5 / 1.6e-4 / 4.2e-4）里四个小于比较值的舍入半格 5e-4，全精度一侧只活在 `PROGRESS-nlcsplit.md:1444-1448`（散文表，WSL 侧车落在仓库外的 `/home/haangyeon/agent_l2_work/`）；结论 §6 又把它们收紧成"within 4e-4"——而实测 P_frz 差 4.2e-4、ΔE_xc 差 4.1e-4 已经在界外。这一条同时踩三个坑（精度不匹配 + 出处不入库 + 上界自造），且是本文"版本可移植性"卖点的全部支撑。
5. **行 373–377 的比值段："across the eight systems" 与 "0.915-1.025"**。0.915 在 `evidence/centos/...step_c.out:15` 是**苯 sandwich** 的 `P_frz/CP`，正文把它当成"水的第三个几何"；而 step_c 里水的两个几何实为 1.017 和 1.025。加上"八体系"里两行苯二聚体的比值只有骨架 `MAIN-skeleton.md:175-176` 的 0.92/0.99（level-0 stdout 印的是 P/**CP** 0.91/1.02，分母就不是同一个量），这等于本文的**第二条主结论**（0.92–1.08 ⇒ 结合时非局域关联几乎全由片间对承载）有两处体系数虚增和一处指认错误；而摘要与结论（行 46、595）都各重复了一次这个区间。

---

## 3. 替换句清单（申请修改，全部只动 `paper/main.md`；我未落笔）

- **R1（行 36–37 / 222 / 279–280，三处同一件事）**
  行 36–37 改为："A check against a second *program* now exists for the quantity Table 1 reports: ORCA 6.0.1 single points agree to 0.0004 kcal/mol on the water dimer and 0.0416 on benzene dimer A (§4). It does not yet extend to the attributed per-fragment blocks, and that is stated as a limitation, not as future work."
  行 222 改为："Cross-program agreement is established for ΔE_NLC itself (§4); it has not been established for the per-fragment blocks."
  行 279–280 改为："These are independent implementations of the kernel but share a library; the second-program anchor in §4 covers the reported ΔE_NLC, not the attributed blocks."
- **R2（行 49–51）** 改为："0.004-0.247 kcal/mol absolute, 0.8-18.2% relative to the Becke-scheme value, stable to within ±5% across the four basis sets beyond STO-3G and across grid levels 1 and 2 (at STO-3G the same spread is 0.025 kcal/mol), and without any pattern by interaction type".
- **R3（行 220–221）** 改为："...agrees to 2×10⁻³ kcal/mol with an independently written script that evaluates the same quantity over a ten-level grid sweep (levels 0–9, `ref/agentB/sweep_631gstar.txt`, promoted to `evidence/` for the submission)".
- **R4（行 257）** 改为："`S22/NN/struc.xyz`), downloaded by the fetch script that ships with the package (to be added at `tools/get_s22.sh`; today it exists only as `scratch/lit/get_s22.sh`, which is gitignored)"——或者先补 `tools/get_s22.sh` 再保留原句。
- **R5（行 289–292 与行 617–619）** 行 289–292 改为："ΔE_NLC, ΔE_xc, ΔE_int, the attribution span and P_frz[becke] all reproduce to within the 5×10⁻⁴ kcal/mol rounding half-step of the second run's three-decimal printout (level-2 values -1.405 / -2.325 / -1.780 / 0.213 / -1.441); no cross-version difference below 5×10⁻⁴ is measurable from the archived stdout. The one quantity that does not agree is the counterpoise interaction energy itself: -1.341 vs -1.202 kcal/mol, a difference of 0.139..."
  行 618 改为："reproduced every attributed quantity to within the 5e-4 kcal/mol printing floor of the archived run but the counterpoise interaction energy only to 0.139 kcal/mol".
- **R6（行 316–317）** 改为："...the two grids' electron-number integrals differ at the same three levels by -1.6e-2, +3.0e-4 and -6.6e-6 electrons (against the exact 20, the unpartitioned grid is off by +9.0e-3, -5.3e-5 and -3.5e-6 and the partitioned grid by -7.1e-3, +2.4e-4 and -1.0e-5)".
- **R7（行 358–361）** 改为："That bound is set by the one system whose level-1 row is stored at full precision - the water dimer, -0.5935 (level 1) against -0.593 as printed at level 2, and -0.6012 against -0.601 - so even there the level-1 to level-2 change can only be bounded by the 5e-4 rounding half-step of the level-2 printout; for the other five systems both rows carry only three decimals, so 1.0e-3 is the floor of what is measurable rather than a measured change."
- **R8（行 373–374）** 改为："Their ratio falls in 0.92-1.08 across the six systems evaluated at level 2 (`step_h_l2cp.json`, key `p_over_ds`); the two benzene-dimer geometries were not run at level 2, and their level-1 column is a different denominator (`P/CP` 0.91 and 1.02 in `20260928T193520Z_centos-step_h_benz_l0.out`), so they are not included."（摘要行 46 与结论行 595 的 "0.92-1.08" 保留但补 "for the six systems at level 2"。）
- **R9（行 375–377）** 改为："and for the water dimer we also reproduce it at the two geometries checked in `evidence/centos/...step_c.out` - the initial S22 structure (1.017) and the ωB97X-V-optimised one (1.025) - with the level-2 official-geometry value 1.01 between them."（0.915 不属于水，属该文件第 15 行的苯 sandwich；不得写"三个几何 / 0.915"。）
- **R10（行 388–392）** 改为："...and -3.69 at omegaB97M-V [S11]; our -4.367 (Table 1, level 1; the earlier level-0 value was -4.448) is the same kind of quantity to within functional-generation and basis-set differences, and it is *not* comparable with the 2-3 kcal/mol net interaction energy that study quotes for the same dimer, which is smaller because Pauli repulsion cancels most of it."
- **R11（行 422–426）** 改为："...across five basis sets gives spans of 0.0249 (STO-3G), 0.0400 (6-31G\*), 0.0382 (aug-cc-pVDZ), 0.0390 (def2-SVP) and 0.0398 (def2-TZVP) kcal/mol while P_frz itself moves from -0.386 to -0.554 [S12]: the quantity drifts by 0.17 kcal/mol across the basis ladder and the scheme spread stays at ~0.04 for every basis beyond the minimal one, where it is 0.025."
- **R12（行 437–438）** 改为："the four schemes spread N_A over 9.865e-2 electrons (Becke N_A = 9.870 at level 3, N = 66532), which is 0.300 kcal/mol" —— 并把该探针 stdout 归档后再引用（现在只有 `PROGRESS-nlcsplit.md:698-704`）。
- **R13（行 194–196）** 改为："and we do not use a basis-set superposition-error correction anywhere in the reported ΔE_NLC; counterpoise-corrected interaction energies are tabulated in §3.2 only as a convergence diagnostic (§4)."
- **R14（行 495–496）** 改为："The benzene gap, 0.042 kcal/mol, is ~1.3x the 0.032 kcal/mol attribution span reported for that same system (Table 2), which is a useful warning that cross-program noise is of the same order as the quantity being studied; it must never be folded into the attribution uncertainty."
- **R15（行 522–525）** 改为："OpenAlex retrieved a known title 4/4 times at rank 0 when queried by title, but missed that same on-topic paper for 0 of 2 legitimate topical phrasings (each repeated four times); Crossref retrieved four known titles 4/4 at rank 0 but recalled the same target for only 1 of 3 topical phrasings. We therefore report hit counts only from the instrument that passed."
- **R16（行 574–575）** 改为："...assert internal coordinates at construction time - the two unit-ordering bugs and the half-width ammonia angle that this measure caught are recorded in the repository work log (`PROGRESS-nlcsplit.md` 121/157/651), pending a real supplementary-notes file."（现在 `paper/notes/` 除本审计外是空的。）
- **R17（行 613）** 改为："Two items remain open there: the anchor covers 2 of the 8 systems, and the *intra-fragment* absolute blocks are still unrefereed (the §4 anchor referees whole-monomer and whole-complex totals, not per-fragment partitions)."
- **R18（行 651）** 改为："Each tag used above resolves to a file in this repository. Values tagged 'line N' can be read literally at that line of the archived standard output. The `evidence/**` stdout files are tracked and hash-listed under `evidence/*/MANIFEST.sha256`; the `nlcsplit/logs/*.out` stdout files are currently **gitignored** (`nlcsplit/logs/*` in `.gitignore`, only `step_h.json`, `step_h_l2cp.json` and `orca_anchor.json` are tracked) and must be promoted to `evidence/` before submission, together with `ref/h2o_wb97x.out` and `ref/agentB/sweep_631gstar.txt`."
- **R19（行 236 / 附录 666 / 671 / 187 的小项）**：3.5e-18 → 1.1e-16 Ha（两处：行 33 与行 234）；9×10⁻¹² → 1.1×10⁻¹⁰ kcal/mol（行 284）；"between floors of 10⁻⁸ and 10⁻¹⁶" → "over floors 10⁻¹⁰–10⁻¹⁴"（行 247，全档差另写 1×10⁻⁸）；"five keyword-shaped queries" → "six"（行 187）；S17 的 "three broad strings" → "four"（行 671）；S12 的 "on the current geometry" → "on the constructed water-dimer geometry"（行 666）；A 检索式补 `"pair resolved"`（行 160–162）；aromatic C–C 1.397 → 1.394（行 266，或注明 1.397 来自构造几何）。

---

## 4. 计数复核（全部为本次实测，命令随附）

| 计数项 | 实测 | 命令（在仓库根） |
|---|---|---|
| main.md 行数 | **687**（不是 684） | `wc -l paper/main.md` |
| 正文体系数（Table 1 / Table 2 / 摘要） | **8**（level 1，全部 `cpcorr:false`）；level-2+CP 体系数 **6**（另有 `step_h_l2cp.json` 顶层 `systems:6`，与 6 行实测一致） | `python -c "import json;d=json.load(open('nlcsplit/logs/step_h.json'));print(len(d['rows']),sorted(set(r['level'] for r in d['rows'])))"`；同法读 `step_h_l2cp.json` |
| 原子数 | 八体系 `natm` = 24, 24, 6, 8, 10, 15, 16, 17（合计 **120**）；与 `scratch/lit/s22/S22_02.xyz` n=6、`S22_11.xyz` n=24 等逐文件首行数一致；GMTKN55 本地副本共 **22** 个 xyz | 同上用 `print(sum(r['natm'] for r in d['rows']))`；`for f in scratch/lit/s22/*.xyz; do head -1 $f; done \| paste -sd, -` |
| 档位口径 | `step_h.json` 头级 `level:1` 与 8 行行级 `level:1` **一致**（本次没有头/行冲突）；但头级 `cpcorr:false` 对 6 个 level-2 体系不成立 ⇒ 档位一律以**行级**为准，正文引用档位时需带 `basis`+`cpcorr` | `python -c "import json;d=json.load(open('nlcsplit/logs/step_h.json'));print(d['level'],[r['level'] for r in d['rows']])"` |
| ORCA run 数 | **6** 个 `.out`（2 复合物 + 4 单体）；`NL Energy, E(C,NL)` 每文件 **1** 次、`ORCA TERMINATED NORMALLY` 每文件 **1** 次；`orca_anchor.json` 记录 **4** 条被否证的说法（保留为 audit_trail） | `for f in evidence/orca_run/*.out; do echo $f $(grep -c "NL Energy, E(C,NL)" $f) $(grep -c "ORCA TERMINATED NORMALLY" $f); done` |
| 测试条数 | 工作树 `def test_` = **49**（7 个模块）；其中 `test_fastpair.py`(10)、`test_fastpair_ide.py`(20) **尚未 git add**（`git ls-files --others` 实测）。已跟踪 = **19** defs（geometry 6 / kernel 5 / partition_factors 4 / regression 3 / tolerance_probe 1）。**发布树**（`tools/make_public_repo.js:30` TESTS = geometry+kernel+partition_factors+regression）= **18 defs，展开 parametrize 后 collect 32 例（22 fast + 10 slow）**。⚠ 18 与 32 是"定义数"和"收集数"两种口径，**不可相加、不可互换**；`paper/software.md:164-165` 现在写"collects 18 tests (15 fast, 3 marked slow)"——用 collect 动词配定义数，属口径误配（`PROGRESS-nlcsplit.md:1144-1158` 那次更正记的就是这类） | `python -c "import re,glob;[print(f,len(re.findall(r'^def test_',open(f,encoding='utf-8').read(),re.M))) for f in sorted(glob.glob('nlcsplit/tests/test_*.py'))]"`；parametrize 展开：partition_factors = 2 mol × 4 scheme + 4 scheme × 2 level + 2 = 18 |
| bib 条数 | **16**（key 唯一，16/16；与正文"bib 13 → 16"及 `RESEARCH-20260929-lit.md:456` 三条补入一致） | `grep -c '^@' paper/references.bib` |
| `[S#]` 标签数 | 定义 **17**（附录 S1–S17，无缺号）；正文使用 **17** 个不同标签，出现 **23** 次；正文用了未定义的：**0**；定义了正文没用的：**0** | `python -c "import re,collections;m=open('paper/main.md',encoding='utf-8').read();b=m.split('## Appendix')[0];print(len(set(re.findall(r'\[S(\d+)\]',b))),len(re.findall(r'\[S(\d+)\]',m)),sorted(set(int(x) for x in re.findall(r'^\| S(\d+) \|',m,re.M))))"` |
| 闸门 / 导出 | `tools/make_public_repo.js` 实列 **5** 个闸门（A–E），发布树测试清单 **6** 个文件（含 `__init__/conftest`） | `grep -n "const TESTS" tools/make_public_repo.js` |
| 交付性缺口 | 被正文点名的工件里 **5 个未入库**：`ref/h2o_wb97x.out`、`ref/agentB/sweep_631gstar.txt`、`nlcsplit/logs/20260929T_step_i_gridrepr.out`、`...20260929T003144Z_stepg-recompute.out`、`...20260929T010500Z_step1_geomfix.out`；`tools/get_s22.sh` **本地也不存在** | `git ls-files --error-unmatch <path>` / `git check-ignore -v <path>` 逐个实测 |
