# 交接文档 — VV10 非局域关联的片段归属（Qoder CN → Qoder 国际版）

> 交出方：本窗口（Qoder CN，`E:\Project\GAMESS`）。接收方：Qoder 国际版。
> 本文件自包含：读完就能动手，不需要再去别处找结论。写于 2026-10-10 18:4x（宿主时钟）。
> 位置说明：故意放在 `paper/notes/`——`paper/` 与 `PROGRESS-*.md` 都不进发布树，交接件不会被导出闸门扫进公开仓。

## 一、当前状态（一句话）

科学面已闭合：八格跨构造证据齐、14 处实质差错全部落地修正、出货链关账（`shipped:true`），
正文只卡**一个由作者决定的口径问题（A/B 写法）**和**只有他能做的发布动作**；HEAD `c6fb533`，工作树干净。

## 二、你必须读的文件（按优先级，全部绝对路径）

1. `C:\Users\Administrator\.qoder\projects\E--Project-GAMESS\memory\cn_snapshot_20261010\README.md` —
   我从 CN 侧复制进来的记忆快照入口（含优先级表与 `SHA256SUMS.txt` 自证方法）。
   最关键两篇：`project-nlc-decomposition-line.md`（科学线与全部读数，**看最后一节"补记 2026-10-10 午后"**）、
   `project-publishability-constraint.md`（投稿与出货，同样看最后一节）
2. `E:\Project\GAMESS\tools\hooks\README.md` — 闸门层说明（五个闸门、判据、失败动作）。
   三条硬规矩（认文件不认通知 / MANIFEST 最后重生成 / 集群日志 cat+sha256）由
   `tools\hooks\session_brief.js` 在每次开场打印。
   **本仓没有 `AGENTS.md`**（我核过：`find . -maxdepth 2 -iname AGENTS.md` 为空），别去找它。
3. `E:\Project\GAMESS\PROGRESS-nlcsplit.md` — 追加式工作日志；最后四节是本轮
   （B 路线开工 → 苯两格 → 八格补齐并撤回一句过头话 → 本次交接）
4. `E:\Project\GAMESS\paper\main.md` — 主篇（21,979 词 / 5 图 / 附录 33 行，下一行号 **S34**）
5. `E:\Project\GAMESS\paper\notes\decision_pack_20261009.md` — 投稿路线报价与"只有他能做"的清单
6. 你**不要**信你自己那份旧记忆：
   `C:\Users\Administrator\.qoder\projects\E--Project-GAMESS\memory\project-gamess-blw-wb97xv.md` 停在 2026-09-28，
   里面"无 git 仓库"已经错（现在是 git 仓，分支 `master`，实测 `git rev-list --count HEAD` = **220** 个提交），
   而且它完全不知道 NLC 分解这条线是当前主线。
   GAMESS-BLW/ωB97X-V 那条 Fortran 线的结论是**已作废**（`rhfuhf.src` 改动让多中心 RHF 收敛到错误解，全树能量不能用）。

## 三、已完成（截至本次交接，都可从仓内核验）

| 环节 | 状态 | 凭据 |
|---|---|---|
| 核心修正（same-centre 核、四方案=一个 Becke 家族两个开关） | 完成 | `nlcsplit/`，提交 293bdf9 起 |
| 归属 vs 求积分离（同一 SCF/网格/权重，只换归属因子） | 完成，八格 | `evidence/common_grid/20261006T085207Z*`、`20261009T083325Z*` |
| 家族外分区（Voronoi + Hirshfeld，自由原子基态多重度/UHF/不球平均） | 完成，八格 | `20261009T155508Z*`（三小体系）、`20261009T193232Z*`（苯二聚体两格）、`20261010T061455Z*`（苯-水/氨/甲烷） |
| 14 处实质差错 | 全部落地 | `PROGRESS-nlcsplit.md` 各节 + `decision_pack` |
| 出货链（发布树 56+3 文件、wheel 39 成员、树外 56 passed + 3 skipped、rc=0） | 关账 | `evidence/release_qa/` |
| 参考文献年份口径（判据 = Crossref published-print） | 25/25 | `evidence/bib_provenance/20261009T124738Z_bib_all25_issue_year_check_after_fix.out`（+.rc） |
| claim gate（正文数字出处，5 份稿） | 干净，`node tools/claim_gate.js` rc=0 | 本轮实测 |
| `evidence/common_grid/MANIFEST.sha256` | 19 行，`sha256sum -c` 全 OK | 本轮实测 |

**记忆同步**：`C:\Users\Administrator\.qoder\projects\E--Project-GAMESS\memory\cn_snapshot_20261010\` 内 9 份文件
（CN 原件的逐字节副本，源目录 `...\.qoder-cn\projects\E--Project-GAMESS\memory\` 与 `...\.qoder-cn\memory\`；
已逐个 `sha256sum` 与源比对全部相同，目录内 `SHA256SUMS.txt` 自证 `sha256sum -c` rc=0）：
`project-nlc-decomposition-line.md`、`project-publishability-constraint.md`、`reference-orca-referee-locations.md`、
`reference-github-publish-credential-path.md`、`reference-cluster-endpoints.md`、
`feedback-verify-stated-numbers.md`、`feedback-no-self-referential-validation.md`、
`cn-pool-outage-20261010.md`、`README.md`。
你原来的 `MEMORY.md` 索引里那一行 ωB97X-V 条目**文字原样保留**，只在前面加了 2026-10-10 的作废/过期标注，
并追加了指向本交接件与快照目录的索引行。你的用户级记忆目录今天 17:17 仍有写入（可能有活会话），我没有动它。

## 四、待做（按优先级）

| 优先级 | 事项 | 详情 |
|---|---|---|
| P0 | **A/B 口径落地**（唯一卡正文的事） | 见 §五，需要作者点头；建议 A |
| P1 | #29 三份稿"仓库日志→论文"文风收尾 | 下一处：`paper/main.md` §1 那句仍约 94 词（libxc/ORCA/Psi4 那句） |
| P2 | S34 附录行 | 把家族外八格写成出处行；**需要一份净化（`<CLUSTER_HOME>` 占位）的 sbatch 副本**才能进随包复现路径——原样含登录名会撞 `gateB_intranet` |
| P3 | #51 | 非 `@article` 型条目的年份口径 + U2 缺引（每条先查 Crossref） |
| P3 | #50（可选加固，约 12 min） | 归档 wheel 成员比对守卫的负控读数 |
| P4 | #31 | tcc 上苯 CCSD(T) 作业 **93285** 取回归档（LSF，非 Slurm） |
| 只有他能做 | 新 classic PAT → **最后再跑一次** `node tools/make_public_repo.js` → `push_manual` → 转 public；第二作者 ORCID/邮箱；审稿人名单；Zenodo DOI；ScholarOne **只 Save 不 Submit** |

## 五、A/B 到底是哪两句话

八格读数（level 1，同一公共网格，单位 kcal/mol，全部可在 `evidence/common_grid/` 三份档里逐位核）：

| 体系 | 家族内跨度 | 跨构造总跨度 | 比值 | Voronoi 越界 | Hirshfeld 越界 | 增量 |
|---|---|---|---|---|---|---|
| 甲烷 | 0.0034 | 0.0414 | 12.17 | 0.0028 | 0.0352 | 0.0380 |
| 水 | 0.0433 | 0.0650 | 1.50 | 带内 | 0.0217 | 0.0217 |
| 氨 | 0.0284 | 0.0609 | 2.15 | 带内 | 0.0325 | 0.0325 |
| 苯(A) | 0.0274 | 0.2208 | 8.06 | 0.0031 | 0.1934 | 0.1934 |
| 苯(B) | 0.2195 | 0.2373 | 1.08 | 0.0177 | 带内 | 0.0178 |
| 苯-甲烷 | 0.2143 | 0.2445 | 1.14 | 0.0303 | 带内 | 0.0302 |
| 苯-氨 | 0.2219 | 0.2792 | 1.26 | 0.0154 | 0.0573 | 0.0573 |
| 苯-水 | 0.2468 | **0.3898** | 1.58 | 0.0278 | **0.1430** | 0.1430 |

- **A（建议）**：标题/摘要保留家族带 `0.004–0.247`；§3 末补一句 + 附录加 S34 行：
  换掉 Becke 家族（Voronoi/Hirshfeld）后八格跨度为 `0.041–0.390`，带顶由苯-水的 Hirshfeld 一格撑起（+0.143），
  Voronoi 最大越界仅 0.030；增量按绝对量 `0.018–0.193` 报，比值列只作参考并注明分母不稳（家族跨度自身跨 65 倍）。
  理由：0.39 是"一格 × 一个构造"，写进标题会被审稿人追问为什么让 outlier 定 headline；且逐格披露反正要做。
- **B**：摘要/标题直接按跨构造带 `0.04–0.39` 写。数据有 8/8 资格，但结论不变、风险更高。
- 两种写法都不动摇结论："attribution uncertainty" 这个名字在家族外构造下依然成立（没有任何格子跨度缩小）。
- **预登记纪律**：运行前写死的判档是 ≤2 / 中间 / >10（比值列）。八格三档全落 ⇒ 该判档规则被分母打穿，
  必须如实承认"规则在这组数据上不可用"，不许挑一档说事。

## 六、关键路径与常量

| 项 | 值 |
|---|---|
| 核代码 | `E:\Project\GAMESS\nlcsplit\{partition.py,nlc.py,step_h_s22.py,figures.py,geomlib.py}` |
| 家族四方案 | `partition.SCHEMES` = becke / becke-becke-rad / becke-treutler / stratmann |
| 常量 | β = 3.0415 kcal/mol/e⁻，KCAL = 627.50947400，(b,C) = (6.0, 0.01)，RHO_FLOOR = 1e-12，正文带值 = grid level 1 |
| 闭合检查 | `nlc.fragment_decomposition(soft=S, closure_check=True)`；对任意逐点归一权重代数精确 |
| 工具链 | `tools/claim_gate.js`、`tools/md2tex.js`、`tools/build_pdf.sh [main|p2|software]`、`tools/make_public_repo.js`（15 道闸门）、`tools/hooks/precommit_gate.js` |
| MiKTeX | 在 `D:\Program Files\MiKTeX`（不在 PATH）；PySCF 只在 WSL；本机 20 核 / 64 GB |
| 集群 | `ssh snnu` = 101.132.159.118:51758（用户 haangyeon，Slurm，host `workstation`，分区 cpu1/cpu3/cpu4）；工作副本 `~/nlcgrid/{nlcsplit,evidence,scratch}`，S22 几何 `~/nlcgrid/scratch/lit/s22/*.xyz`（22 个） |
| tcc | `XAR@219.244.66.99:10011`，LSF，36 核 |

## 七、红线（🚫 一条都不能破）

- 🚫 投稿系统里**永不点 Submit / 不发**；只 Save。即席授权也要先给他看最终态并等一个明确的"发"。
- 🚫 凭据、ORCID、密码、token 值一律由他提供；不编造真人邮箱，不落盘密码，token 不进对话。
- 🚫 不作破坏性 git：不 `--force`、不改历史、不 `--no-verify`；只在闸门全绿后提交已验证文件。
- 🚫 集群上只排队计算：不 `pkill -u`、不动他或同行的作业；登录节点不跑重活；一次状态轮询用**一条**合并命令。
- 🚫 共享状态上不做写探测（`bmod` 无 dry-run，试一次就真改了别人作业）。
- 🚫 图像模型产物绝不当论文图。
- 🚫 **6 Pro 欠费，他说别送、等他充值**：期间判断题本地自答并说明理由，也别走 pool 的 first-run onboarding（那要他手输凭据）。
- 🚫 C 盘只放小文件；长活/大产物放 E: 或集群。
- 🟢 计算位置规矩（他定的）：分钟级小活本机直接做；**≥30 min 或独占多核直接排集群**，不用先问。

## 八、踩坑（都是本仓真实事故，别再踩）

1. **认文件不认通知**：后台任务说 exit 0 也要读它自己落盘的退出码；管道会吞退出码（`.out.rc` 曾被 `| tee` 后的 `$?` 写成 0，真值 1）。
2. **集群日志入库**：必须 `cat` 原文 + 本地/远端 `sha256sum` 比对，禁止用终端回显拼档案；退出码只认作业自写的 `# exit=` 行。
3. **MANIFEST 最后重生成**（顺序反了 gate C2 抓你自己）；改证据 → 归档 → `git add` → 清单 → `git commit` 五步**各一条命令**。
4. **`.gitattributes` 已把 `evidence/**` 标成 binary**，别改——清单是按原始字节算的，git 归一化会让审计链当场断。
5. **列标签比数值更容易搬错**：未反泊松那一列当物理写、同一版本两条建网格路径当版本差，都曾是实质差错。
6. **派生数必须有原件**；整数计数没有小数闸门保护（"6/6"无原件就别进 caption）；节号现取不凭记忆（§6 其实是 §3.6）；图号按 caption 语义号而非文件名。
7. **Slurm 缓冲 stdout**：`.out` 尾部能滞后几十分钟，判进度别只看它；`pam_slurm_adopt` 在作业结束后会拒绝 `ssh cpu1`——那不是故障。
8. **"结果恰好等于 1/2 这类整齐分数"是构造指纹**：自由原子建在原点曾让 Hirshfeld 块恒为 E_NL 的一半，靠这个线索才抓到。新构造要配一列退化对照（等权 1/natm，本项目已排除在判据外）。
9. **hook 语义**：PostToolUse 报 blocking 的编辑其实已落盘；注释里的 `1e-9` 会被判实测数字；附录行里反引号只包真路径，否则 md2tex 拒绝出稿。
10. **sbatch 从未进版本控制**：`scratch/` 被 `.gitignore` 排除，两份提交脚本只在集群和本机工作树（sha：`42637119…`、`3223d9e7…`）。写 S34 前须处理。

## 验证清单（接收方逐项确认后再接手）

- [ ] 读完本文件全部内容
- [ ] 读了 `C:\Users\Administrator\.qoder\projects\E--Project-GAMESS\memory\cn_snapshot_20261010\README.md`
      并按其优先级表读了那两篇 project 记忆的最后"补记（2026-10-10 午后）"一节；
      `cd` 进该目录跑 `sha256sum -c SHA256SUMS.txt` 应 rc=0
- [ ] `cd /e/Project/GAMESS && git log --oneline -1` 读到 `c6fb533`，`git status --porcelain` 为空
- [ ] `node tools/claim_gate.js` 返回 rc=0
- [ ] 能用自己的话复述：为什么比值列不能当 headline、为什么 0.3898 只由一格一个构造决定
- [ ] 知道 P0 是"等作者点头选 A/B"，**不擅改标题口径**
- [ ] 知道 §七红线，尤其永不 Submit、不送 6 Pro、集群不杀作业
- [ ] 向我报告"接手完毕，准备执行 §四 P0/P1 第 X 项"

## 给作者的转交话术（可直接粘给国际版窗口）

```
先读 E:\Project\GAMESS\paper\notes\QODER_INTL_HANDOFF_20261010.md 和
C:\Users\Administrator\.qoder\projects\E--Project-GAMESS\memory\MEMORY.md，
按里面的验证清单逐项确认，然后告诉我 §五 的 A/B 你打算怎么落笔——A/B 要我点头才动正文。
```
