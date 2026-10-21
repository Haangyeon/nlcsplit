# TASK-BRIEF-20261014 · E:\Project\GAMESS 交接调研书

生成 2026-10-14。代 Qoder 国际版会话 `3ebf621a-d14e-4155-bc25-29c8b985c43b` 导出（该会话最后一次有效产出 2026-10-14T06:19:24Z，此后只剩通道故障）。
仓库现状：HEAD = `df8ff66`（2026-10-10），分支 `master`，**未配置 git remote** ⇒ 222 个提交与全部未提交工作只存在于本机一份副本。
活跃 goal `1791903698223-dae5bf` 停在 100/120 轮（轮次上限会强制暂停），**未标 complete**。
接手读物优先级：`E:\Project\GAMESS\paper\notes\AUDIT-acceptance-20261014.md`（逐条凭据）→ `STATE-20261013-night.md §七` → `DECISION-BRIEF-20261014.md`（决策一页版）。

# 一、目标与验收标准

交付物：`nlcsplit` 包 + `E:\Project\GAMESS\paper\main.md` 达到"**审稿人一条命令能复现正文每一个数**"的投稿就绪态。四条验收全为机器可判、缺一不可；**四条目前一条未齐**。

论文当前的结论形状（单位修正 + 满表后已定稿的数据口径，措辞待 G2）：**归属歧义长在标准工具链内部，换到家族外构造（Voronoi / Hirshfeld）既不消除也不放大**。Table 1 的三列口径要认清：第 3 列"span, own grids"里 PySCF 的"换归属方案"会连积分网格一起换，一列同时装了两个效应；第 5 列"attribution only, one grid"（同一 SCF、同一网格）才是纯归属跨度，第 6 列是纯求积。参数量级差是整带的 8–11 倍，正文应主动引用它给自己设上限。

1. **数据面**：正文每张表每一格都有可复查 `.out` 原件（含脚本自写的 `# exit=` 行 + 同名 `.rc`），且表由脚本从原件现算、零手抄。缺口项 W4 = 满 S22 十四格 + 至少一类异质体系（候选 X40 或 ion-pair / H-bond 主导子集），每格有原件。
2. **发布链**：由 `node tools/make_public_repo.js` **从导出树**出货的 wheel 满足——`nlcsplit/certificate.py` 与测试模块随包（含家族外构造测试，和"故意给退化构造必须报警"的负控）；装进一次性 `--target` 目录、在树外 cwd 跑 pytest 全绿；`evidence/release_qa/` 下 census / member-diff / 树外 pytest 三份归档齐。此件未成立前 `paper/main.md:1232-1233` 那句 "implements … every table" 不成立。**从工作树直建是禁用路径**（会把 6 个 `INTERNAL_ONLY_MODULES` 装进包，且过不了自家泄漏闸门）。
3. **口径**：所有现在时计数由新 census 改口、不手抄；A/B 标题口径按定稿数据落（B 写法失支撑、A 撤"带顶 0.39"半句）。
4. **卫生与收口**：`node tools/claim_gate.js` 与 `node tools/hooks/precommit_gate.js` 均 rc=0；`tools/hooks/lib.js` 的 `staleManifests()=0`，且逐目录相对上一版无条目消失（`tools/make_evidence_manifest.sh` 带拒绝替换闸，`attribution_referee/outputs/` 那 16 条子目录登记不得被静默删）；未提交条目归零——**只能 Windows 侧提交**（WSL 侧 `core.autocrlf` 未设会把 26 个文本文件判成整文件已改）。

数值门槛（不可自行放宽）：确定性归属方案（家族内四 + Voronoi）逐列认证门 **1e-4**（旧档打印分辨率）；Hirshfeld 列门 **1e-3**。
终止 / 降级判据：四条齐 = 达成；W4 集群排期 >2 天 ⇒ 先交"S22 满 + 一类异质"，rVV10 全量退到 SI。
复现纪律（针对"复现已归档读数"的任何新脚本）：几何 / 基组 / 网格档 / 片段索引必须从原件用的**同一构造函数**取，并带一条与归属方案无关的总量对照（`E_nl`）——否则整列同号同幅的残差会被误读成实现有系统性偏差。
本仓硬规矩三条：① 认文件不认通知（后台任务报 exit 0 也要读它自己落盘的 `# exit=`）；② MANIFEST 在所有证据编辑定稿之后**最后**重生成；③ 集群原始日志必须 `cat` 原文 + 比 sha256 才算入库，禁止用终端回显拼档案。
决策门（不自行扩权）：G1 路线、G2 措辞、提交授权、出货与发布动作（PAT / `push_manual` / 转 public / 二作 ORCID / Zenodo / ScholarOne 只 Save 不 Submit）。W4 一律不动别人作业，提交前先查配额。

# 二、已完成

## 已提交（HEAD `df8ff66`，2026-10-10；共 222 commits）

- `E:\Project\GAMESS\evidence\common_grid\`（20 个受控文件）：家族外分区测量脚本入库（`0d40520`）、家族外第一版作废留档 + 等权对照列（`3962a53`）、修正版 level-1 三体系（`214f7be`，跨构造偏移 0.02–0.04 kcal/mol）、苯二聚体两格入库（`70b36fc`，sha 逐字节相符）、八格跨构造补齐与**"全落在带内"的撤回**（`c6fb533`）、苯二聚体 A/B level-1 归属/求积分列（`04f40b1`）。
- `E:\Project\GAMESS\paper\main.md` Table 1（第 817–824 行，8 行）：第 5 列 "attribution only, one grid" 甲烷 `0.0034`、苯-水 `0.2468`、苯-甲烷 `0.2143`、苯-氨 `0.2219`、苯二聚体(B) `0.2195`，与工作树内 `20261013T141002Z_after_unitfix_summary_table.out` 的"家族内跨度"列逐格一致。§3.4 已把 0.004–0.247 拆成"归属 / 求积"两列（`05de98d`）。
- `E:\Project\GAMESS\evidence\release_qa\`：测试普查 79 = 58 非慢 + 21 慢接入正文（`2802b66`）；最终 wheel 树外读数与 `dist/` 命名整改（`483de28`、`570dc48`）；README 里 wheel 哈希的自指问题写成机制（`570dc48`）。
- `E:\Project\GAMESS\paper\references.bib`：25 条文献年份统一到纸质卷期年（`03bae3a`）；`c2ba20f` 把三份档案里的登录名换成运行时取源指针。
- 文风与图件三轮：fig3 接进 §3.6（`8583294`）、摘要去日志腔（`5c6c3d3`）、引言 121 词分号链拆开（`1699e1e`）；`c169b2f` 撤回"空载机器"在摘要与 §6 的残留。
- 编号勘误（`65c16a2`：commit message 里"十四处"应为"十三处"，历史不改、勘误入库）与决策包状态（`2afce34`：P1/P2 全清，差错 13 处）。
- 发布链三轮收口：`39bba48` 补上公开仓缺件两处、并修掉"清点脚本被归档命名毒掉"（留住错的那份读数）；`483de28` 把最终 wheel 的树外读数接入正文、改掉 `dist/` 里"替别人作证"的文件名；`cfbba60` / `1dac4d1` 导出 `shipped:true` 的闭环读数与出货顺序模板。
- 受版本控制文件分布：`evidence/` 312 · `paper/` 67 · `nlcsplit/` 52 · `tools/` 34 · `figs/` 6。交接件与逐字节记忆快照（`65f9214`、`df8ff66`）。

## 未提交（工作区 296 条 = 14 个 M + 282 个 ??，覆盖 2026-10-11 → 10-14 四个工作日）

- **满 S22 批已齐**：`E:\Project\GAMESS\evidence\common_grid\` 206 个未跟踪文件；22/22 格 `..._s22_full_certificate_S22_NN_l1_small.out` + `.rc=0`；批日志自落 `# exit=0 at 2026-10-14T02:55:43Z`，墙钟 **11 h 32 m 37 s**（`15:23:06Z` 起），22 格全 `VERDICT DONE`、0 格 flagged、六方案全 usable。并发 6/5/3/2、线程 3/4/6/10，全在本机 20 核，未占集群。
- 满表读数（`20261014T030330Z_summarize_s22_full_table.out`，`# exit=1`）：家族内带 **0.0034–0.3030**（22 格）、含家族外总跨度带 **0.0088–0.3586**；按片段分层 **同核 12 格 / 异质 10 格**（同核家族内 0.0034–0.2342、增量中位 0.0051 / 最大 0.0781；异质家族内 0.0381–0.3030、增量中位 0.0216 / 最大 0.1079）。
- 逐列交叉认证 8 行：**4 格六列全 OK**（水 / 氨 / 甲烷 / 苯-水，最大 +0.0001），**4 格只错 Hirshfeld 一列**（`S22_11` 0.0064、`S22_20` 0.0079、`S22_18` 0.0130、`S22_10` 0.0093，门 1e-3）；确定性五方案 + Voronoi 在 8 格全 ≤1e-4。
- 线程 A/B 三小格（同一格只差 BLAS 线程数）：`20261013T192727Z_..._methanedimer_th4.out` = **REFUSED**（2.3e-4 > 门 1e-4）；`20261013T200051Z_..._methanedimer_th1.out` = **DONE**（3.9e-05）；`20261013T194514Z_..._waterdimer_th1.out` = DONE（水格 4 线程本来就过，**不能**当 A/B 用）；`20261013T202326Z_..._ammoniadimer_th1.out` = DONE（1.36e-05）。代码漂移已排除：对比档 `20261013T053243Z_crossfamily_inpackage_check` 抬头自报 `git HEAD df8ff66`、`partition.py ec6c0c56…`、`nlc.py 2817acd6…` 与工作树逐一相同。
- **`E:\Project\GAMESS\nlcsplit\certificate.py`（162 行）整模块未跟踪**，连同 `nlcsplit\tests\test_certificate.py`（10 条）、`test_crossfamily_schemes.py`（5 条）。证书入口水格复现（`20261013T145505Z_certificate_reproduction_l1_waterdimer.out`，rc=0）：逐方案最大残差 3.6e-05、`argmin/argmax` 同向、`E_NLC` 跨方案极差 2.7e-15 且与旧档 `E_NL` 在 0.005 门内相等；第一次 REFUSED 那份保留 + sidecar 记因（几何不同源）。
- `E:\Project\GAMESS\nlcsplit\partition.py` 未提交 +118/−2：新增 `CROSS_FAMILY_SCHEMES=("voronoi","hirshfeld")`、`ALL_SCHEMES`（六个方案一个入口，家族内四的既有调用点不受影响）、`voronoi_factors()`（护栏：one-hot argmax 必须与 `nearest_partition` 逐点一致）、`hirshfeld_factors()`、`FREE_ATOM_MULT={"H":2,"C":3,"N":4,"O":3,"F":2}`、`_NORM_TOL=1e-12` 每点权重和归一化护栏；`__init__.py`/`geomlib.py` 各 ±6。
- `E:\Project\GAMESS\tools\` **11 个新脚本全部未跟踪**：`run_w4_closeout.sh`（**8 步 = 编号 1…7 加 1b，顺序写死不可换**）、`run_ship_qa.sh`（不带参数只打印计划，已实测 `dist` 条目 6→6 无变化；`--yes` 才执行出货）、`preflight_ship_check.js`（预飞随包测试模块 **= 10**）、`check_table1_transcription.py`、`check_manifest_regression.sh`、`make_evidence_manifest.sh`（拒绝替换闸）、`selftest_manifest_gate.sh`（四向演示）、`selftest_manifest_regression.sh`、`audit_table_row_provenance.js`、`audit_original_exitcodes.js`、`run_preflight_ship_check.sh`。
- `E:\Project\GAMESS\paper\notes\` 11 份决策件/台账未跟踪：`AUDIT-acceptance-20261014.md`、`DECISION-BRIEF-20261014.md`、`STATE-20261013-night.md`、`DECISION-G2-20261013.md`、`DECISION-G3-exitcode-coverage-20261013.md`、`DECISION-G4-table1-pfrz-source-20261013.md`、`FINDING-20261011-hirshfeld-unit-and-determinism.md`、`PLAN-20261011-next-steps.md`、`PLAN-20261012-JCTC-route.md`、`PLAN-20261012-rvv10-kernel.md`、`P0a-precedents-draft-20261011.md`。
- `E:\Project\GAMESS\evidence\rvv10_referee\`（W0 / ORCA / CP2K / libxc 全部裁判档，含 `r4_cp2k_form_test.py`、`probe_nlc_parameter_authority.py`）与 `evidence\claims_audit\`（`A_nlc_share_vs_dx_c.md`…`F_p2_cite_apply.txt` 六份）**整目录未跟踪，且 HEAD 里没有这两个目录的 MANIFEST ⇒ `check_manifest_regression.sh` 对它们无基线可比**（工具如实报出，没伪装成已通过）。
- 已跟踪文件的未提交增量：`PROGRESS-nlcsplit.md` +484 行；`paper/references.bib` +28；7 份 `MANIFEST.sha256`（`common_grid` 2301→7728 B、`release_qa` 7060→9655 B、`bib_provenance` 1573→2049 B、`retrieval_calibration` 325→404 B、`agentb_sweep`/`l2cp` 亦变）；`tools/hooks/GATE-OVERRIDES.log` +1065 行；`tools/make_public_repo.js` +13；`evidence/common_grid/hirshfeld_crossfamily.py`（单位修正 + 判读口径写死在脚本头）。
- 收口第 1 步实测 STOP 且清单未被触碰：`20261014T025620Z_w4_closeout.out`（`# exit=1 at 2026-10-14T02:56:25Z`）+ `20261014T025620Z_summarize_s22_full_table_closeout.out`（rc=1，满表全文在内）。
- 22 格定名核对：`20261013T220452Z_verify_s22_official_names.out` rc=0 —— 22/22 与 GMTKN55 官方 `.res`（sha256 `a43c93f5…c888bd7`，落 `scratch/lit/gmtkn55_S22.res`）化学式逐格一致、四对同式兄弟指纹可分、官方 `##` 7/8/7 分块边界与几何氢键指纹边界一格不差；22 份几何与上游 tag v1 逐字节相同。判据说明与两处踩坑见 `evidence/common_grid/NOTE_s22_official_names_20261013.md`。
- 发布清单只读核对：`make_public_repo.js` 白名单 37 条、具名不发的内部件 6 条、白名单里盘上缺的 0 条。对照件（工作树直建）实测 48 成员 / 随包 11 个测试模块 / 树外装跑 69 passed + 2 skipped + 23 deselected，但**装了 6 个 internal 且自家泄漏闸门 rc=1** ⇒ 禁用的正是这条路。三个"随包模块数"分属三件不同工件，引用时别混：旧 `dist/` 规范名 wheel = 8 模块 / 59 条（`20261013T153804Z_test_count_census.out`），工作树直建对照件 = 11，导出树预飞 = 10。
- 本次核实（2026-10-14，只读）：`node tools/claim_gate.js` → **rc=0**；`tools/hooks/lib.js` 的 `staleManifests(root)` → **180 条**；`git status --porcelain` → **296 条**；`ps -W` 无 python/pyscf 进程 ⇒ 无在跑作业。

## 关键数字速查（每个都指回原件，路径默认在 `E:\Project\GAMESS\evidence\common_grid\`）

| 数 | 值 | 原件与行位 |
|---|---|---|
| 满 S22 家族内带 | 0.0034–0.3030（22 格） | `20261014T030330Z_summarize_s22_full_table.out` 第 34 行 |
| 满 S22 含家族外总跨度带 | 0.0088–0.3586 | 同上 第 35 行 |
| 片段分层 | 同核 12 格 / 异质 10 格 / 未分类 0 | 同上 第 38–40 行 |
| 八格家族内带 / 跨构造带 / 绝对增量 | 0.0034–0.2468 / 0.0088–0.2746 / 0.0000–0.0393 | `20261013T141002Z_after_unitfix_summary_table.out` 第 15–17 行，`VERDICT OK` 第 19 行 |
| 逐列认证门 | 确定性 1e-4、Hirshfeld 1e-3 | 满表档内 `##` 注释（第 43–46 行） |
| 超门四格（全在 Hirshfeld 列） | 0.0064 / 0.0079 / 0.0130 / 0.0093 | 满表 `!!` 行：`S22_11`、`S22_20`、`S22_18`、`S22_10` |
| 满批墙钟 | 11 h 32 m 37 s | `20261014T025620Z_w4_closeout.out` + `AUDIT` 第 17 行 |
| 线程扫描自差 T=1/2/4/8 | 0.000e+00 / 8.509e-02 / 7.103e-01 / 7.107e-01 | `20261013T181611Z_thread_sweep_summary.out`；表在 `DECISION-BRIEF-20261014.md` §1 |
| 权重抖动覆盖面 | 58448 个网格点中 38119 个（65%）差 >1e-3 | 会话 2026-10-13T18:36:17Z 汇报（`NOTE_hirshfeld_two_implementations_20261013.md`） |
| 甲烷线程 A/B | `th4` REFUSED 2.3e-4 / `th1` DONE 3.9e-05 | `20261013T192727Z_..._methanedimer_th4.out` / `20261013T200051Z_..._methanedimer_th1.out` |
| 单线程价签锚点 | `S22_18`（16 原子）4 线程 = 3714 s | `DECISION-BRIEF-20261014.md` §1 更正节 |
| 测试全量 | 94 = 非慢 71 + 慢 23 | `evidence/release_qa/20261013T153804Z_test_count_census.out` |
| 随包测试模块 | 8（旧 `dist/` 规范名 wheel，59 条）/ 10（导出树预飞）/ 11（工作树直建对照件，禁用） | 同一 census；`tools/preflight_ship_check.js` |
| 孤儿档 | `20261013T152010Z_..._S22_03_l1_small.out`（无 `.rc`，被表自动排除） | 满表"被排除在外的档（1 个）"节 |
| 当前收口状态 | `staleManifests` 180 条 · 未提交 296 条 · `claim_gate` rc=0 | 2026-10-14 本次实测 |

# 三、已撤回或修正的结论及原因

1. **带顶 0.3898 / 苯-水 +0.1430 / 甲烷比值 12.17 / 苯二聚体(A) 比值 8.06 全部作废**。原说：跨构造带 0.0414–0.3898，带顶由苯-水的 Hirshfeld 撑起。现说：新跨构造带 0.0088–0.2746，苯-水 0.2746、甲烷比值 2.60、苯二聚体(A) 2.43。原因：`evidence/common_grid/hirshfeld_crossfamily.py:87` 拿 `atom_coord(a, unit="Angstrom")` 的坐标去减 Bohr 网格坐标，是真实单位口径错；水那格 Hirshfeld 增量 0.0214 → **0.0000**。出处 `FINDING-20261011-...md` 第 18/30/36 行 + `20261013T141002Z_after_unitfix_summary_table.out` 的"旧跨构造(Å)/旧比值"两列（旧值故意留在同一行做对照）。
2. **"包内路径已复现跨构造列"由 MET（范围有限）降为 NOT MET**。原判断只建立在水二聚体一格上；甲烷格 `th4` = `REFUSED`（2.3e-4 > 门 1e-4）当场否掉外推。没有靠放宽门让它变绿。
3. **`HIR_TOL=1e-3` 与 `TOL=1e-4` 两个门都作废**——同一个错犯了两次：按单格（水）的成功标定容差再外推全表。
4. **Hirshfeld 列不可逐位复现的病因，前两次解释都被实测否掉**。① "两份实现分叉"——互比 1.47e-1 比自比 6.6e-1 还小，该问题在此尺度上无意义；② "自由原子基态 UHF 近简并换解"——重复 5 次，H/C/N 的 ΔE 与 Δ1-RDM **精确为 0**，`n_zero` 恒 0、兜底也没参与。现说：病因 = **BLAS 线程数**（`20261013T181611Z_thread_sweep_summary.out`）：T=1 自差 `0.000e+00`（IDENTICAL）、T=2 `8.509e-02`、T=4 `7.103e-01`、T=8 `7.107e-01` ⇒ 是"1 与 >1"的阶跃，不是"越多越抖"的连续量。能量只差 1e-14 但 **1-RDM 哈希会变**，只看 `e_tot` 会漏判。
5. **"给分母加下溢阈值就能让权重与线程无关" 不成立**：T=1 vs T=8 下 58448 个网格点中 **38119 个（65%）** 权重差 >1e-3，抖的不是尾部少数点。该出路已删。
6. **"全部单线程出货"（方案 A）从推荐里撤掉**：实测锚点 `S22_18`（苯-氨，16 原子）4 线程 = 3714 s ⇒ 单线程每格数小时、22 格几天；24 原子格已耗 CPU 8 h 17 m（4.6 核 × 1 h 43 m）。
7. **"八格重叠给出一次新旧交叉认证"是过头话，实际只有 7 格**：`summarize_s22_full.py` 用**文件名**当旧档键，而苯-水那格档名是拉丁 `benzwater`、其余七格是中文 ⇒ 被**静默丢掉**。改成取档内自报体系名当键后覆盖面 8/8（`20261014T030330Z`）。过程中把正则写成 `^##`（真实是 `==`），被脚本自己的报警分支当场抓到。
8. **"同式不同几何三对" → 四对**：漏了 `S22_11/20`（苯二聚体 A/B，正文本来就用 (A)/(B) 标着）。四对 `05/13`(dmin 1.77/2.71)、`11/20`(3.37/2.80)、`14/21`(3.20/2.59)、`07/15`；前三对已成对落档且分得开，`07/15` 落档后四对全测到。出处 `20261013T193551Z_verify_s22_folder_identity.out`。
9. **"PySCF 把 rVV10 做成 VV10 是实现缺陷"被 W0 证伪**（两档残差同量级；是把 `-rV` 的参数记错，`WB97M_V` 给 (6.0, 0.01) 是对的）。R4 又查明 CP2K 的 `&NON_LOCAL TYPE` 枚举里没有 VV10 核形 ⇒ JCTC Article 的 C3 两条腿都没了。裁判另两条判死：libxc 7.1.2 只导出 `xc_nlc_coef`（`xc_nlc_vxc`/`xc_nld_vxc`/`xc_vdwnl_kernel`/`xc_setup_kernel`/`xc_run` 全不存在，当不了任何一臂的裁判，但 `SCAN-VV10`(584) 与 `SCAN-RVV10`(292) 是不同功能号）；libvdwxc 里 `vv10` 字样零命中。CP2K 线按自定停机判据砍掉（能算 rVV10 但算不了 VV10 核 ⇒ A−B 同码对照不成立），留档可复跑。
10. **甲烷"相对%"正文 `0.9%` 复现不出来**：`check_table1_transcription.py` 的 `check_span_cols()` 由未舍入值（span ÷ |becke|）重算 ⇒ 8 行第 3 列逐字命中、第 4 列 **7/8 一致**，唯一不符是甲烷：机读源 `nlcsplit/logs/step_h.json` 给 **0.84% → 0.8%**，而 `main.md:817` 写 `0.9%`。这条已从"两文档互相打架"升级为有判据指哪边对。
11. **"published wheel ships eight test modules / those 79 / 留在树外的 20 条全是 `test_fastpair_ide.py`" 现在时计数失效**：census（`evidence/release_qa/20261013T153804Z_test_count_census.out`，自报 `git HEAD df8ff66…`）实测全量 **94 = 非慢 71 + 慢 23**，留在树外的是 **3 个模块 / 35 条**（证书 10 + 家族外 5 + ide 20）；随包 8 模块收 59 条对**当前规范名 wheel** 仍成立。`README.md:29-30` 的 58/79 同步过期。
12. **ETA 外推两处修正**：① "整批 7–8 h" 偏低（从 3–6 原子小格外推，没料到 24–30 原子的二次增长，光剩余就要 9 h 以上）；② 末次外推剩余 2 格中位 3.2 h、区间 [2.3, 4.3] h，实测 2 h 14 m 32 s = 8072 s，**比下沿 8280 s 还低 208 s** ⇒ 区间没盖住实测（低 2.5%）。教训：拟合残差 ±38% 是单格散布，两格并发跑同一 barrier 组时误差相消而非相加 ⇒ **剩余格数少时区间该按组给**。
13. **"先提交再出货"是我自己加的假依赖**：grep `tools/make_public_repo.js` 全文无 `git status --porcelain`、无 uncommitted 检查，出货不触网不用 token ⇒ 两者互相独立。真正有先后的只有"证据定稿→重生成清单→提交"与"计数只能在出货之后改口"。
14. **"Table 1 第 2 列 `P_frz` 找不到出处"是错的**（只 grep 了两个目录），已撤回并查明在 `E:\Project\GAMESS\MAIN-skeleton.md` 表 4b。
15. **"两张零机器验证的表本来无数可比" 对 `paper/p2.md:242` 是错的**：那两行有真数字 `53,983`、`18.0%`、`0`，正确说法是"不在共现级覆盖内"（判据要求每行 ≥3 个带小数值，整数按设计当噪声丢）。同一份审计把"空载机"收口为"方向成立、措辞过强"（24/24 样本外部 R=0 但同工件 `load1` 记到 0.99–4.24），并把比值端点从 1.08–10.28× 收到纳入被丢弃复现后的 **1.03–12.8×**。出处 `evidence/claims_audit/C_p2_refutation.md`。
16. **工具层的自我更正（会让下一个读数的人踩同一个坑，逐条已落档）**：① 固定宽度 `"%.4f"` 当键 ⇒ 8 行全部误报"无对应值"；② 逗号千分位切分 ⇒ 假覆盖，总数从 51/35 改为 **50/34** 并如实报出；③ `except: return 0` 掩盖了 `No module named 'nlcsplit'` ⇒ 现在打印原因并 `return -1`；④ `ROOT` 浅一层使 glob 匹配 0 文件；⑤ WSL 缺 `pgrep` 给出假的 0；⑥ 内联 `wsl bash -lc '...$T...'` 的 `$T` 被外层吃掉 ⇒ 三档"不同线程"其实同一设置，"结论看着齐全全是假的"，改成盘上脚本；⑦ 用 naive 正则数随包模块 ⇒ 产出乱码名字，已撤回改用 `preflight_ship_check.js` / `test_count_census.py`；⑧ `\[([\s\S]*?)\]` 在注释里就截断 ⇒ 假警报"白名单缺 `test_nlc_closure.py`"，且 `INTERNAL_ONLY_MODULES` 是 `{路径: 理由}` 对象不是数组 ⇒ 误报要静默少发 `test_fastpair_ide.py`；⑨ 判据初版"单份档必须全包"使 Table 1 八行全部误报 ⇒ 改成分级 FULL/PARTIAL/WEAK/NONE，只有 NONE 算真问题；⑩ 一次 `in "HO"` 子串判断把 H···H 当氢键 ⇒ 那是 **rc=0 的假绿**，已留档说明。
17. **四次表格行被覆盖**（anchor 在已有行标签上）与**一次 `$?` 穿过 WSL 不可信**（同一 `main()` 返回 1，经 `wsl bash -lc` 回到 Windows 侧显示 0）记为流程结论：这套双层 shell 里别拿 `$?` 当判据，只认脚本自落的 `.rc` 或 `VERDICT` 行。

# 四、当前卡点

- **收口链 STOP（外部决策卡点，不是代码缺陷）**：`tools/run_w4_closeout.sh` 第 1 步 rc=1，因逐列交叉认证拒 Hirshfeld 那 4 格（0.0064 / 0.0079 / 0.0130 / 0.0093 > 门 1e-3）。病因已闭合 = BLAS 线程数。门未放宽、判据代码未改。放行前置 = 作者拍 G5/G6。恢复只要两步：拍完 G5/G6 → 按处置改判据或重取，再 `bash tools/run_w4_closeout.sh`。
- **外部异质体系一格没有（代码 + 数据 + 账号三重）**：① 代码缺口——`s22_full_certificate.py` 建 `gto.M(...)` 时**没有 `charge` 参数**，电离对/离子液体那类会被按中性算电子数（静默错）；② 数据缺口——盘上除 `scratch/lit/s22/` 的 22 个官方 xyz 外无任何一手 `.xyz/.pdb/.cif`；③ 外部——未认证 GitHub API 已 **403 rate limit**（60 次/小时，那轮用掉了），`AL2X6/01/struc.xyz` 实测 404 ⇒ 不要照 S22 的两位数字猜别的库路径。"批还在跑时不改生产脚本"的约束已解除（批 02:55Z 完成）。
- **提交授权（外部，人）**：296 条未提交 + `staleManifests` 180 条，是**故意**留的——收口第 2 步（重生成清单）在第 1 步 STOP 之下没执行，且提前重生成会把半份 `.out` 锁进 MANIFEST。必须 Windows 侧。**风险叠加**：无 remote ⇒ `certificate.py`、11 个 tools 脚本、22 格 S22 原件、11 份决策件、`rvv10_referee/` + `claims_audit/` 两个证据目录只存在于工作树，任何一次误 `checkout`/`clean` 就没了。
- **出货与发布授权（外部，人）**：`make_public_repo.js`、PAT、`push_manual`、转 public、ORCID、Zenodo、ScholarOne 只 Save 不 Submit——全在作者那五件里，未动。
- **会话通道故障（外部，中转代理）**：转录内 9 条 `isApiErrorMessage`，最早 2026-10-14T09:26:47Z，文本均为 "Unable to connect to the service, or the connection was interrupted. Check your network, VPN, or proxy" 与 "Sorry, something went wrong"；2026-10-14T06:19:24Z 之后该会话零有效产出。这是本文件存在的直接原因。
- **定名结果尚未回流到满表（本次核实的观察；是否有意为之：未核实）**：`20261014T030330Z_summarize_s22_full_table.out` 的体系名列仍有 14 格写"（待核）"（表头自述"只有已独立核对过的才填"），而 `20261013T220452Z_verify_s22_official_names.out` 已 rc=0 定名 22/22。引用纪律已知：标签 `uracil` 在 05/13 **重复**、`indolebz`/`indolbz` 只差字母顺序 ⇒ 正文必须带文件夹号或几何描述。
- **集群（外部资源，本轮未使用）**：满批全在本机跑。历史坑：10-12 SNNU CPU 配额曾被另一项目长作业挤满、`51335` 曾 PENDING 在 `QOSMaxCpuPerUserLimit`；集群提交仍需授权，一律不动别人作业。`sbatch` 脚本本身从未进过版本控制（`c62e01a` 自己记下这个缺口）。
- **必须认得的孤儿档**：`20261013T152010Z_s22_full_certificate_S22_03_l1_small.out` 只有抬头没有判语、**没有 `.rc`**（为"先定价再开批"起、出数前主动停掉）。它不是证据；`summarize_s22_full.py` 只取 `rc=0` 档所以自动排除，表尾"被排除在外的档（1 个）"就是它。留档不删。
- **未核实项**：本文件没找到任何记录说明目标原文的"至少一类异质体系（候选 X40…）"与 `AUDIT` 第 27 行"改道 MET（不等 X40）"（靠 S22 内部同核/异质分层 7/5→12/10）是否算同一判据；两处措辞不一致，需作者或 Claude 明确"分层是否满足 W4 后半"。

# 五、下一步（按优先级）

| # | 动作 | 预计工作量 | 依赖 |
|---|---|---|---|
| P0 | 拍 **G6**（带顶换确定性 Voronoi、Hirshfeld 退 SI）或 **G5**（单线程重取超门那 4 格） | 决策 10 分钟；G6(c) **0 算力**；(a) ≈ **16 核·小时**（本机空闲，由 `S22_18` 4 线程 3714 s 推得） | 只需作者点头 |
| P1 | `bash tools/run_w4_closeout.sh` 跑完 8 步（满表 → 线程记录 → 重生成清单 → 无丢条目 → stale=0 → 两闸门 → 全稿零手抄 → 体系列唯一性） | 20–40 分钟机器时 | P0；22/22 已齐（已满足） |
| P2 | 把已核定的 22 个官方标签接进 `summarize_s22_full.py` 体系名列并重出满表（保留"未核对不填名"分支） | 1–2 小时（含正则自检与 rc 判据回归） | P0/P1；先确认这条是遗漏还是有意留（未核实） |
| P3 | 外部异质体系二选一：(甲) 给 `s22_full_certificate.py` 加 `charge` 入口 + 重新认证，做 ion-pair 子集；(乙) 先做**中性且元素异质**小体系（GMTKN55 alane/borane 类、carbohydrate 氢键类），不改代码 | 甲 ≈ 1 天 + 若干核·小时；乙 ≈ 1 天（含取几何与批跑） | 网络可用 + 路线判断（与 G1 同级，归作者）；P3 的"不改生产脚本"前置已解除 |
| P4 | 重生成 `evidence/*/MANIFEST.sha256` → **Windows 侧** `git add` / `commit`（清单生成、`add`、`commit` 三者必须各一条命令） | 1–2 小时（含 180 条陈旧逐目录核对） | P1 通过 + 作者提交授权 |
| P5 | `bash tools/run_ship_qa.sh --yes`：从导出树建 wheel → census / member-diff → `pip install --no-deps --target 临时目录` → 树外 cwd `pytest -m "not slow"` → 三份归档，并核对装的 `test_*.py` == 预飞说的 10 | 30–60 分钟 | 作者出货授权 |
| P6 | G2 八处现在时计数改口 + G4 的 `P_frz` 列键 + G3 的退出码口径措辞 | 2–3 小时 + `claim_gate` 回归 | P5 出的 census 数（之前只能留占位符）+ G2 点头 |
| P7 | G1 路线定稿（JCP / JCTC）；若走 JCP，§5 与 cover letter 里 C3 相关表述一并收 | 决策半小时；改文 2–4 小时 | 作者 |
| P8 | 起任何新长批前先 `setsid bash ... > log 2>&1 &`，并在脚本抬头打印 `OMP/OPENBLAS/MKL`（本批曾与启动 shell 同会话，PPID=7010 / SID=1135，无 nohup，有被 SIGHUP 带走的风险） | 每次 5 分钟 | 无 |

# 六、需要他或 Claude 决策的问题

- **G1 主投期刊**：JCP（推荐）/ 继续 JCTC。代价：W0 证伪 + R4 查明 CP2K 无 VV10 核形 ⇒ JCTC Article 的 C3 已无内容支撑，硬冲必须自建 rVV10 阻尼核再找第三方裁判（本机没有），是纯增量风险；走 JCP 不丢任何已做出来的东西。JCTC 可留作拒稿后的升级路线。
- **G6 带顶口径**：(c) 带顶只用确定性 Voronoi、Hirshfeld 移进 SI 作敏感性对照（推荐，可把 G5 的 16 核·小时整笔省掉）/ (a) 整表单线程重跑（最干净，几天）/ (b) 表注挂线程条件。代价：(c) 要把"含家族外总跨度带"从 0.0088–0.3586 换成不含 Hirshfeld 的口径，§3.4 与相关图必须同步改；(b) 的线程记录是**派生自批日志**、不是原件自报，引用时须说明。(c) 现在有满表级支撑：4 格六列全过、超门的只有 Hirshfeld 一列。
- **G5 Hirshfeld 列处置**：只重取超门 4 格 ≈16 核·小时 / 整列降级进 SI / 保留但加"随线程变"表注。代价：任何"换定义"（占据平均、球平均闭壳层参考、分母下溢阈值）都已实测否掉或需整列重算 + §2.3 重写、旧读数全作废。
- **G2 八处措辞**：`main.md:1232-1233`（"four attribution schemes" 包内实为六个；"every table" 待出货）、`software.md:154`（模块地图整行缺 `certificate.py`）、`software.md:330-331`、`software.md:507`（讲历史事故却用现在时形）、`README.md:30`、`README.md:33-38`、`README.md:148`/`:151`，加 §4b 甲烷 `0.9%→0.8%`。代价：只改正文会让 README 成为全仓唯一还错着的文件，而它比正文先被读者打开；`README:33` 那句 "not typed here from memory" 现在等于"靠一份过期档案"。
- **G3 退出码覆盖面**：23 份**被引**原件既无 `# exit=` 也无 `.rc`（Table 1 所引 3 份实测 0/3 有自报行；`.rc` 2/3 有，其中一份还是旧写法 `rc=0`）。方案：以改措辞为主（"自 2026-10-13 起用 `# exit=`+`.rc`；更早的档由同名 `.rc`（两代写法）或档内 `EXIT=` 记录"），只补跑其中 1 份（`test_count_census`，秒级，正是 `README:36` 的凭据）。代价：**16 份是测量档，重跑可能给出略不同的数、制造"两份档互相矛盾、正文引哪份"的新问题**（比缺一个退出码行严重一个量级）；只有 7 份可安全补跑。判据：这份档的用途是"某个数"还是"某个过程发生过"，前者不许重跑。没有从档内已有的 `EXIT=0` 反推 `.rc`（那等于事后制造证据）。
- **G4**：Table 1 第 2 列 `P_frz` 是否纳入逐字核（出处 `MAIN-skeleton.md` 表 4b，检查器已就位只差这一列的键）。代价：不纳入则第 2 列仍是全稿唯一没被"零手抄"覆盖的正文数。
- **提交授权 与 出货授权**：两者互相独立、谁先都行（"先提交再出货"是假依赖，已撤）。代价：一直不提交 ⇒ 2026-10-11→10-14 的全部新工件只存在于一块磁盘的一份副本上，且无 remote 备份；一直不出货 ⇒ 正文那两处现在时计数只能继续留占位符，`main.md:1232-1233` 的 "every table" 持续不成立。
- **异质体系选哪一类**（带电需先补 `charge` 入口 / 中性不需改代码）：属研究路线判断，与 G1 同级，归作者。
- **"分层是否算满足 W4 后半"**：见 §四 最后一条未核实项。代价：若判"不算"，P3 从可选变必需（1 天起）；若判"算"，需要把 `AUDIT` 第 27 行的分层口径同时写进正文，否则读者看不出这一半是怎么满足的。
