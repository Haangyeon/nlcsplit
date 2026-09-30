# 技能盘点 × 本项目 4 个瓶颈 — 侦察报告

日期：2026-09-30 作业者：只读侦察子代理 交付物：本文件（未改动任何其他文件）

---

## 0. 范围、方法与去重

### 0.1 扫描到的技能存放位置（全部实际存在）

| 位置 | 性质 | 数量 |
|---|---|---|
| `C:\Users\Administrator\.agents\skills\` | **JUNCTION → `D:\AgentData\shared-skills`**（本机唯一物理技能库） | 899 个目录，其中 893 个含 `SKILL.md` |
| `C:\Users\Administrator\.claude\skills` | 符号链接 → 同一 `D:\AgentData\shared-skills` | 与上同源 |
| `C:\Users\Administrator\.agents\skills\.system\` | CLI 内置技能 | 6 个：`imagegen` `openai-docs` `plugin-creator` `review-agent` `skill-creator` `skill-installer` |
| `C:\Users\Administrator\.qoder-cn\` | **无用户技能目录** | 只有 `extensions\vscjava.migrate-java-to-azure-1.15.3-win32-x64\skills`（Java 迁移扩展自带，与本项目无关）；`plugins\` 下仅 `cache/ data/ installed_plugins*.json` |
| `E:\Project\GAMESS\` | **本项目没有 skills 目录** | `.qoder\` 下只有 `better-harness\2026-09-28\` |
| 其他项目级 | 冗余副本 | `E:\Project\perovskite\.trae\skills`（429，内容与全局库同名，无独门技能）、`E:\Project\mace_tensorflow\.trae\skills`（1）、`E:\Project\挖漏洞\skills`（4，全是漏洞提交类）、`E:\Project\alloyDesign*\.codex\skills`（空） |

### 0.2 去重结论

899 个目录里 **370 个是 `source-command-*` 前缀的镜像副本**（同一份 SKILL.md 的第二次安装痕迹）。真实可用技能面 = **527 个唯一技能 + 6 个内置**。

### 0.3 本次纪律

只用了 `ls / find / grep / head / read` + 本地端口与路径探测。未修改任何既有文件、未安装任何东西、未联网、未调用任何云端模型、未向集群提交作业。下列判断全部来自 SKILL.md 原文与文件系统实测，不是推测。

---

## 1. 技能清单：确实存在且与本项目相关的（路径 + SKILL.md 自述用途）

### Tier A — 直接命中瓶颈

| 技能 | 绝对路径 | SKILL.md 自述用途要点 | 前置条件 |
|---|---|---|---|
| `tcc-cluster-access` | `C:\Users\Administrator\.agents\skills\tcc-cluster-access\SKILL.md` | 外部 "tcc" 服务器（XAR@219.244.66.99:10011，CentOS 7，72 核单机，**LSF 10.1，是 bsub 不是 PBS**）的访问与调度纪律。**§4 软件盘点实测记录：`/share/BackUp/XAR/xar/Program/` 下装有 `orca-6.0.1`，另有 Gaussian g09/g16、ABCluster、LAMMPS；`ProgramFiles/` 下是 vasp.6.5.1。** 含硬规则：一切计算（含编译）必须走 `bsub`；`bsub` 不在 PATH，必须 `. /share/lsf/conf/profile.lsf`；`#BSUB` 走 stdin 不用 `#!`；LSF 只暴露 36 slot（nproc 显示 72）；`/` 盘 99% 满，一切落 `/share`；**该机上不了网**（pypi/github 全 `000`）。附 `templates/bsub_job.sh` | 需 SSH 到远端（本次禁止） |
| `snnu-hpc-safety` | `...\skills\snnu-hpc-safety\SKILL.md` | SNNU 集群（`snnu` = 10.8.51.23:20019，frp 备用口 101.132.159.118:51758）强制安全流程：登录节点禁 CPU/GPU 重活、禁并发 SSH 轮询环与子代理、禁 `pkill -u`、禁未授权开工；一轮状态只允许**一条合并 SSH 命令**；给了白名单命令（`squeue -u haangyeon -o ...`、轻量 `ps`）。这是"守夜而不打爆登录节点"的纪律来源 | 需 SSH（本次禁止） |
| `slurm-job-script-generator` | `...\skills\slurm-job-script-generator\SKILL.md` | 生成可粘贴的 SLURM `sbatch` 脚本并对资源请求做自洽检查：节点/MPI task/OpenMP 线程/内存（per-node vs per-cpu）/GPU/walltime/partition/modules 冲突与超额订阅自动报警。纯标准库 Python，无外部依赖 | 本地即可跑（生成脚本），不涉网 |
| `reference-metadata-crossref-check` | `...\skills\reference-metadata-crossref-check\SKILL.md` | 用 Crossref API **逐条核验 LaTeX 稿件参考文献外部元数据**（作者/年份/标题/期刊/卷/页），投稿前 bibliography QA。核心铁律来自真实返工：**先自证字段解析率再谈比对结论**——第一版把 `Adv. Mater. 36 2301854` 整串读进 journal 字段，118 条只解析出 3 条卷 1 条页，却报"0 mismatch"。要求每次跑完先打印"解析出 year/volume/pages 各多少条"。含 IOP/RSC `thebibliography` 条目的真实解析结构 | 需联网打 Crossref（本次禁止）。**注意：目录内只有 SKILL.md，无 bundled 脚本** |
| `citation-management` | `...\skills\citation-management\SKILL.md` | LaTeX 论文 BibTeX 全生命周期：`harvest`（从草稿用 Semantic Scholar 补引文）/`validate`/`add`/`format`。**实有 8 个可执行脚本**：`validate_citations.py`（查缺失引用、未用 bib 条目、重复 key、重复 section、重复 label、未定义引用、缺图，支持 `--check-figures --figures-dir`）、`doi_to_bibtex.py`、`harvest_citations.py`、`extract_metadata.py`、`format_bibtex.py`、`search_pubmed.py`、`search_google_scholar.py` | ⚠️ 三个坑：(1) SKILL.md 示例路径写 `~/.claude/skills/...`，实测该 junction **可达**，但第二调 `deep-research/scripts/bibtex_manager.py` 所在的 **`deep-research` 技能在本机不存在** ⇒ 该命令是死链；(2) `validate_citations.py` 只认 `\cite{}/\citep{}/\citet{}` 与 `.bib`，**不认 markdown 里的 `[[key]]`**；(3) `doi_to_bibtex.py`/`harvest_citations.py` 需联网 |
| `biblatex` | `...\skills\biblatex\SKILL.md` | biblatex/biber 现代书目管理：`style=authoryear`、`sorting=nyt`、`maxbibnames`，编译链 `pdflatex → biber → pdflatex ×2`。**注意本项目用的是 `bibtex`**（实存 `paper/bibtex.log`、`main.bbl`），二者 backend 不同 | 纯知识参考，无外部依赖 |
| `latex` | `...\skills\latex\SKILL.md` | LaTeX 综合参考：排版/数学/表格/图/书目/编译。目录里**只有 SKILL.md 一个文件**（无模板无脚本），定位是查表而非产物生成 | 无 |

### Tier B — 图件与稿件 QA（瓶颈 4）

| 技能 | 绝对路径 | 用途要点 |
|---|---|---|
| `manuscript-layout-qa` | `...\skills\manuscript-layout-qa\SKILL.md` | Word/LaTeX 交付前**三道扫描**：图族宽高统一（关键坑：`bbox_inches="tight"` 让裁剪框各异 ⇒ 同宽嵌入后高不齐；解法是 tight 后统一补白，PNG 用 PIL 居中 paste、PDF 用 fitz `show_pdf_page` 且**先 close 源文档再 save**）、边缘 2px 非白像素 `edge_ink` 出界自检、**LaTeX 浮动体三修（孤页/空页/大空隙根因）** |
| `journal-figure-typography-unify` | `...\skills\journal-figure-typography-unify\SKILL.md` | 把全稿带字图件统一到**目标期刊官方条款**（字体族/最小字号/字重/斜体/图幅/栏宽），并数值证明"只改排版没改内容"。铁律：基准是期刊官方条文而不是"图与图互相对齐"；**先复现基线再改**，不能复现的图＝provenance 缺口要单独登记，不许静默替换；冻结目录用全树 SHA 快照前后比对 |
| `figure-font-unification` | `...\skills\figure-font-unification\SKILL.md` | 一组异构工具产出的图统一到同字体族，几何不变。三条路线按风险排序：A 改 SVG `font-family` 重导出（首选）／B 改 rcParams 重跑脚本／C PyMuPDF redact+重插。**最大坑：不要假设"重跑原脚本＝复现交付图"**（实例：重跑得 `S/R/Rac` 而交付图是 `S-3BrMBA/...`，页宽 417→501 pt） |
| `docx-svg-figure-qc-backfill` | `...\skills\docx-svg-figure-qc-backfill\SKILL.md` | 验收外部交付图件并回填 Word：施工前逐格数字核对＋硬约束合规扫描、热图 WCAG 文字对比度逐格扫描、**Word 内 SVG+PNG 双存储按内容 md5 指纹定位替换**（媒体文件名与图号不对应这个静默错位坑）。自身明确写了与 `docx-figure-batch-replace`/`journal-figure-typography-unify` 的分工表 |
| `manuscript-figure-polish` | `...\skills\manuscript-figure-polish\SKILL.md` | matplotlib 图件修订规则与作者审美：科学正确性绝对优先（不许为好看改数据/统计/结论）、轴首尾刻度压角取整值、无物理零点的量（**如 E_R 能量**）y 下限不必从 0 起、边界 marker 被 spines 裁半要加负边距 |

### Tier C — 长任务守夜 / 浏览器 / 投稿 / 检索

| 技能 | 绝对路径 | 结论 |
|---|---|---|
| `qoder-inwindow-timer` | `...\skills\qoder-inwindow-timer\SKILL.md` | **本会话窗口内**定时投喂：靠 `Bash run_in_background` 结束时 harness 向**同一会话**投递 task-notification 唤醒 idle 会话。实测 50/120/700 s 零误差；并明确 `qoder_cron` 做不到（在自己独立会话执行），`send_message_to_chat_session` 有防自指限制；文档里的 600000 ms 上限对 `run_in_background` 不生效。脚本 `scripts/until.sh` |
| `unattended-automation-continuity` | `...\skills\unattended-automation-continuity\SKILL.md` | 无人值守续跑的状态机：实测确认每次 automation 触发都是**全新 thread_id、零记忆** ⇒ 连续性必须活在文件里。给出 `AUTOMATION_STATE.json` + `run_next.py` driver + append-only run log + 带 singleton guard 的后台 patrol daemon + watchdog 的配方，并列出四类失败模式（状态回滚／空转验证轮／做了没记／双 daemon） |
| `scholarone-upload` | `...\skills\scholarone-upload\SKILL.md` | 投稿系统（ScholarOne/Editorial Manager）全流程自动化：常驻浏览器 + CDP 保登录态（session cookie 不落盘）、dump 页面识别必填项、上传槽机制、**只 Save 不 Submit 红线**。属于写操作，需用户授权 |
| `playwright-browser-automation` / `agent-browser` / `browser-use:browser-use` | `...\skills\...` | 通用浏览器操作/截图取证。注意项目记忆 `browser-session-per-window`：用户登录的窗口 ≠ 被驱动的会话，2FA/PAT/密码不代办 |
| `academic-db-retrieval` | `...\skills\academic-db-retrieval\SKILL.md` | CNKI / Web of Science / Scopus 的 Playwright 检索 + 全文回捞 + 批量题录导出 + known-item 检索式校准，**前提是机构网络内** |
| `review-method-closure` | `...\skills\review-method-closure\SKILL.md` | 综述方法关账：PRISMA 闭合、把"诚实分母"近似换成基于内容的三态编码、逐篇审计表、所有数字单一真值源可复现 |
| `paper-lookup` / `database-lookup` | `...\skills\...` | `paper-lookup`：10 个文献库 REST（PubMed/PMC/bioRxiv/medRxiv/arXiv/**OpenAlex/Crossref/Semantic Scholar**/CORE/Unpaywall）。`database-lookup`：78 个库，实查 `references/` 目录**全是生医/天文/经济库（含 cod.md 晶体学库），没有任何软件/代码注册库** |
| `pyzotero` | `...\skills\pyzotero\SKILL.md` | Zotero Web API v3 程序化管理书目。需 `ZOTERO_LIBRARY_ID`/`ZOTERO_API_KEY` 凭据 |
| `abacus-dft-guardrails` / `hea-mainline-monitor` / `restoration-server-usage` / `snuu-hpc-vasp-ops` | `...\skills\...` | 同族计算纪律：ABACUS 只认 `!FINAL_ETOT_IS` 收敛标志、Rydberg/eV 双打印陷阱、init_chg 暖启动合法条件、结构生成器强制 round-trip 验证。`hea-mainline-monitor` 是**只读**监视技能（绝不启停模拟），示范了"每轮一次合并查询 + 全量记日志"的守夜形态 |
| `get-available-resources` | `...\skills\get-available-resources\SKILL.md` | 重算任务开局探测 CPU/GPU/内存/磁盘并产出 JSON + 策略建议（并行 vs out-of-core）。本地可跑 |
| `venue-templates` | `...\skills\venue-templates\SKILL.md` | 期刊/会议 LaTeX 模板与投稿规范。实查覆盖 Nature 系/Science/PLOS/IEEE/ACM/NeurIPS/ICML/CVPR/CHI/NSF/NIH/DOE/DARPA——**没有 JOSS，没有 SoftwareX**，而本项目目标刊正是这两个 |

### Tier D — 已核实但当前不可用（重要负面发现）

| 技能 | 实测状态 |
|---|---|
| `clawsgo-science` + `science_router` | SKILL.md 写服务在 `http://127.0.0.1:8001`、启动脚本在 `E:/Project/deepmdkit/clawsgo-science/start_clawsgo.sh`。**实查：`E:\Project\deepmdkit` 不存在，8001 端口没有监听**；真实位置是 `E:\Project\EAM\clawsgo-science\start_clawsgo.sh` ⇒ **SKILL.md 里的路径是过期错链**。读 `server.py` 确认两条通道：`task_type=auto` 会打 `ANTHROPIC_API_KEY`/`OPENAI_API_KEY` 云端模型（本次纪律禁止）；`task_type=latex_compile` 只是 `subprocess` 调本地 `LATEX_BIN`（默认 `pdflatex`，两遍编译处理交叉引用）——**这条不碰模型，理论可用，但需要拉起服务（属写/起进程动作，本次未做）** |
| `markdown-to-html` | 该技能是 md→tex 唯一"直接配方"（`pandoc input.md -s -o output.tex`）。**实查 `pandoc` 与 `tectonic` 均不在 PATH**（与项目记忆 `local-toolchain-windows-box` 一致）。禁止安装 ⇒ 当前不可用 |
| `markdown-long-doc-to-docx` | 长 md → 投稿 docx，但**依赖本机 `editor_sdk` MCP**，且产物是 Word 不是 tex/pdf，不解决瓶颈 3 |
| `what-if-oracle`、`council`、`llm-council`、`consciousness-council`、`multi-agent-brainstorming` | 多视角评议类，会调用云端模型，且不提供科学判据 |
| `skill-installer` / `find-skills` / `qoder-find-extensions` / `skillhub-preference` | 装技能本身＝安装动作，本次禁止；且 `find-skills`/`qoder-find-extensions` 要联网检索市场 |

---

## 2. 逐瓶颈对照表

### 瓶颈 1 — 外部裁判覆盖太窄（ORCA 6.0.1 只锚了水、苯，需扩到 ≥6 个二聚体）

| 技能 | 判定 | 依据 |
|---|---|---|
| `tcc-cluster-access` | **能用，且是唯一能让 ORCA 6.0.1 真的跑起来的那个** | 它不是"通用 HPC 知识"，而是**实测的机器台账**：白纸黑字记着 `/share/BackUp/XAR/xar/Program/orca-6.0.1` 存在（job 93238，2026-09-06 验证）、调度器是 LSF 而非 PBS、`bsub` 必须先 `. /share/lsf/conf/profile.lsf`、`#BSUB` 从 stdin 读、**36 slot 上限**、`/` 盘 99% 满是陷阱、该机上不了网。这套坑靠猜猜不出来，而"扩锚点到 6 个体系"正是 repeatedly 卡在这里 |
| `snnu-hpc-safety` | **能用（另一台）** | 提供 SNNU 侧 SSH 主/备地址与登录节点保护、白名单查询命令、"一轮一条合并 SSH"、禁并发轮询。锚点批量跑时的安全外壳 |
| `slurm-job-script-generator` | **部分能用** | 只对 SNNU（Slurm）有效；**tcc 是 LSF，本技能产的 `#SBATCH` 用不上**。价值在 MPI/OpenMP/内存冲突自检 |
| `abacus-dft-guardrails` / `restoration-server-usage` / `snuu-hpc-vasp-ops` / `hea-mainline-monitor` | **不能用** | 全是周期性固体/ABACUS/VASP/HEA 那套路（`FINAL_ETOT_IS`、OUTCAR、赝势、KPOINTS）。本项目是分子二聚体 + 非局域相关泛函，basis/收敛/裁判口径完全不同。**唯一可借的抽象**是"只认一个明确的收敛标志、不拿迭代数当收敛"和 `hea-mainline-monitor` 的只读守夜形态 |
| `get-available-resources` | **能用（辅助）** | 本地 WSL 20 核跑 PySCF 批量单点前先探资源，避免 18 分钟 0 字节日志那种事故 |
| **任何 PySCF / Psi4 / ORCA / 二聚体 / BSSE-反算 / SAPT 领域的技能** | **没有** | 全库关键词扫描（`pyscf psi4 orca gamess counterpoise dimer basis-set coupled-cluster`）命中 17 个文件，逐个查证全是 `pymatgen`/`transformers`/`seaborn`/`scikit-learn`/`statsmodels` 里的偶然词撞库，**没有一个是量子化学计算技能**。`deepchem`/`medchem`/`rdkit`/`molecular-dynamics`/`rowan` 是药物化学与 MD，不做 wave-function 级二聚体相互作用能 |

> 直接后果：锚点扩容这件事**没有现成技能可以端上桌**，能拿到的只有"怎么把作业安全打到有 ORCA 的那台机上"。计算方案本身（哪 6 个二聚体、哪个 basis、`E(C,NL)` 标签怎么对齐、ghost/orbital-collapse 陷阱）仍是本地代码 + 项目记忆的事。

### 瓶颈 2 — 稿件引证层缺失（p2.md 引文 0 条；software.md 有 [S#] 无定义表、从未过出处闸门）

| 技能 | 判定 | 依据 |
|---|---|---|
| `citation-management` | **能用，但只覆盖后半段** | `validate_citations.py` 实测接口是 `--tex <.tex> --bib <.bib> [--check-figures --figures-dir]`，只做 `\cite{}` 与 `.bib` 的对账 ⇒ **它能验"tex 挂上 [[key]] 之后"的键一致性，验不了 p2.md 现在这个"正文裸串"阶段**。`doi_to_bibtex.py`（走 `https://doi.org/`）与 `harvest_citations.py`（Semantic Scholar）需要联网。SKILL.md 里第二条命令引用的 `deep-research/scripts/bibtex_manager.py` **本机不存在**＝死链 |
| `reference-metadata-crossref-check` | **能用，正中要害（瓶颈 2 与 4 共用）** | 它专治本项目刚踩过的账：**"0 mismatch" 可能是空转出来的**。要求先打印解析出 year/vol/pages 各多少条再下结论，正是记忆里 "Dehnen 2014 是我造的" 那类事故所缺的那道闸门的自查规则。缺点：只有 SKILL.md，**没有 bundled 脚本**，得照它的步骤现写；且需联网 |
| `biblatex` | **部分能用** | 是 backend/样式知识参考。**本项目实际走的是 `bibtex`**（`paper/bibtex.log`、`main.bbl` 实存），照 biblatex 的 `backend=biber` 建议做会走错编译链 |
| `paper-lookup` / `database-lookup` | `paper-lookup` **能用**（含 Crossref/OpenAlex/Semantic Scholar，可补程序原始文献 DOI）；`database-lookup` **不能用** | 实查 `database-lookup/references/` 78 个库文件：全生医/天文/地球/经济，**没有任何软件注册库（无 asof/Zenodo/software-registry）**。我们要的是"程序对表"（哪个程序哪个版本实现了哪个 NLC 方案），它一条都覆盖不到 |
| `pyzotero` | **不能用（当前）** | 需要 Zotero 库与 API key；本项目书目是仓内 `paper/references.bib`（实查 17 条 `@`），引入外部文献管理软件只多一层同步不一致的风险 |
| `academic-db-retrieval` | **不能用** | 它只覆盖 **CNKI / WoS / Scopus**，产出是题录导出与 PRISMA 检索式校准；我们要的是**程序实现与版本对表 + 单条外部元数据核验**。领域不重叠，且它要求机构网内 + 真浏览器会话 |
| `review-method-closure` | **不能用（瓶颈 2）** | 它管的是系统综述的 PRISMA 分母闭合与逐篇编码，不是引文键/provenance |
| `scholarone-upload` | **不能用（瓶颈 2）** | 是投稿系统的文件上传/表单自动化，属于稿件已完备之后的环节，不产生引证层 |

> 实测基线（用于校准"缺什么"）：`paper/p2.md` 里 `[[` 出现 **0 次**、无 References 小节；`paper/software.md` 有 **27 处** `[S#]`、**13 个唯一标签**（S1,S2,S3,S5,S7,S9,S10,S11,S12,S17,S18,S19,S20 —— 编号本身有洞），且**没有 [S#] → 出处定义表**；`paper/references.bib` 17 条。

### 瓶颈 3 — P2/P3 没有 LaTeX 产物（md2tex 只服务 main.md）

| 技能 | 判定 | 依据 |
|---|---|---|
| `markdown-to-html` | **当前不能用** | 唯一给出 `pandoc input.md -s -o output.tex` 直接配方的技能，**但 pandoc 不在 PATH、tectonic 也不在**，本任务禁止安装 |
| `clawsgo-science`（`latex_compile` 通道） | **有条件可用，但文档已过期** | SKILL.md 写的启动路径 `E:/Project/deepmdkit/clawsgo-science/` 不存在，真实在 `E:/Project/EAM/clawsgo-science/`；8001 端口当前未监听。`server.py` 的 `latex_compile` 只 subprocess 本地 `pdflatex`（两遍），**这条不碰云端模型**；`auto` 通道碰模型，本次纪律禁止 |
| `latex` / `biblatex` | **能用（作为查表）** | 是写/修 preamble、数学转义、浮动体、书目标记的参考。但 `latex` 目录**只有一个 SKILL.md，零模板零脚本**，不会给你产物 |
| `venue-templates` | **不能用** | 实查覆盖 Nature/Science/PLOS/IEEE/ACM/NeurIPS/ICML/CVPR/CHI + NSF/NIH/DOE/DARPA，**无 JOSS、无 SoftwareX**——正是本项目两个目标刊。照它套模板会拿到错的排版约束 |
| `markdown-long-doc-to-docx` | **不能用于瓶颈 3** | 产物是 Word，且要 `editor_sdk` MCP |
| **专门的 Markdown→LaTeX 管线技能** | **没有** | 全库搜 `md2tex|markdown to latex|pandoc` 只落到上面几个。本项目已有的正确路径是仓内 `tools/md2tex.js`——实测第 12 行 `const SRC = 'paper/main.md';` 硬编码单文件，正是这个瓶颈的根因 |

> 有利条件（实测）：MiKTeX 24.1 在 `D:\Program Files\MiKTeX\miktex\bin\x64\`，`pdflatex.exe`/`xelatex.exe`/`latexmk.exe`/`bibtex.exe` 逐个在盘上确认存在；只是不在 Git Bash 默认 PATH 上。**"本机没有 LaTeX" 是已经写进稿件并被推翻过的假结论，不要复现它。**

### 瓶颈 4 — 图件与元数据 QA、参考文献外部元数据核验

| 技能 | 判定 | 依据 |
|---|---|---|
| `reference-metadata-crossref-check` | **能用（本瓶颈唯一直接命中）** | 见瓶颈 2 的分析；它的"先报解析率再报结论"规则正好补上本项目闸门缺分母的那块 |
| `manuscript-layout-qa` | **能用** | LaTeX float 三修 + 孤页/空页扫描 + 图出界 `edge_ink` 自检，是 tex 出来后那一步的验收 |
| `journal-figure-typography-unify` | **能用（有前提）** | 铁律"先复现基线，不能复现的图＝provenance 缺口单独登记"与"全树 SHA 快照前后比对"跟本项目 `evidence/**` 的 SHA 清单口径天然对得上。前提是要有期刊官方条款 + 图的生成脚本 |
| `figure-font-unification` | **部分能用** | 只在"多张图字体族不一致"时上。路线 B（重跑原脚本）的坑它自己写明了，本项目 `nlcsplit/figures.py` 实测字节确定，反而比该技能的经验更安全 |
| `docx-svg-figure-qc-backfill` / `docx-figure-batch-replace` / `docx-table-surgery` / `pdf-docx-signature-stamp` | **不能用** | 全部面向 **Word `.docx` 母稿**（`wp:extent`/`a:ext` 成对改、SVG+PNG 双存储、Word COM 渲 PDF）。本项目交付是 md→tex→pdf，docx 管线整族无关 |
| `manuscript-figure-polish` / `scientific-visualization` / `plot-from-data` / `matplotlib` / `seaborn` | **部分能用** | 图件生成侧的规则库（审美与科学性优先级、轴刻度取整、无物理零点不从 0 起）。属"改图时读一遍"的参考，不是 QA 闸门 |
| `exploratory-data-analysis` / `markitdown` / `pdf` | **辅助可用** | `markitdown` 实测已安装可 import（读 PDF/DOCX/图像为 md，本地）；`pdf`/`exploratory-data-analysis` 可做产物体检。都非瓶颈的直接解 |

### 跨瓶颈：守夜 / 长任务

| 技能 | 判定 |
|---|---|
| `qoder-inwindow-timer` | **能用** — 锚点批量跑在远端时，用它挂到本窗口按时唤醒复查，是实测零误差的机制；`scripts/until.sh` 在位 |
| `unattended-automation-continuity` | **能用（方法论）** — "每次触发都是新会话零记忆 ⇒ 连续性必须活在 `AUTOMATION_STATE.json` + driver + append-only log 里" 正好治本项目反复重跑验证轮的病 |
| `snnu-hpc-safety` | **能用（约束）** — 它明令禁止高频轮询与并发 SSH 轮询环，等于给守夜定了频率上限 |
| `cron-jobs` / `render-monitor` / `lark-event` / `sentry` / `investigation-mode` | **不能用** — 分别是 Vercel 定时、Render 云部署监控、飞书事件、Sentry、部署排障，与集群作业无关 |

---

## 3. 建议的实际使用顺序

**注意：本次任务禁止联网/禁止提交集群作业/禁止起服务，所以下面是"下一步开工时的顺序"，不是本次已执行的顺序。**

### 先上两个：瓶颈 3（`tools/md2tex.js` 泛化 + MiKTeX 编译）与瓶颈 2（引证层）

**第 1 位 — 瓶颈 3 的 tex 产物。**
理由：它是**唯一完全本地、零外部依赖、零科学风险**的一步，而且是瓶颈 2 后半段和瓶颈 4 的**入场券**——`citation-management/validate_citations.py` 只吃 `.tex`+`.bib`，`reference-metadata-crossref-check` 只吃 `thebibliography`/bib 结构，`manuscript-layout-qa` 的浮动体扫描只对 `.tex` 有意义。**P2/P3 没有 tex，这三个技能全部在门外等着。** 反过来，一旦 p2.tex 能编，瓶颈 2/4 立刻可闸。
需要的技能：`latex`（preamble/数学转义查表）+ `biblatex`（**只用它辨别 backend 差异，别照抄 biber**，本项目是 bibtex）。
不要指望的技能：`pandoc`（不在盘上）、`venue-templates`（无 JOSS/SoftwareX）、`clawsgo-science`（服务未起、SKILL.md 路径过期）。
动手点：`E:\Project\GAMESS\tools\md2tex.js` 第 12 行 `const SRC = 'paper/main.md';` 是唯一硬编码；编译用绝对路径 `D:\Program Files\MiKTeX\miktex\bin\x64\pdflatex.exe`（PATH 上没有）。

**第 2 位 — 瓶颈 2 的引证层，且与第 1 位并行准备。**
理由：`paper/p2.md` 实测 `[[` 出现 0 次、无 References 节；`paper/software.md` 实测 27 处 / 13 个唯一 `[S#]` 且无定义表（编号还带洞：S4/S6/S8 缺席）。这两件事都不依赖任何外部资源，纯本地就能补；而"没挂 `[[key]]` 就生成 tex"只会产出一个引用为空的稿子。
需要的技能：`reference-metadata-crossref-check`（联网后跑，**且先落它的"自证解析率"规则再谈 mismatch**）+ `citation-management` 的 `validate_citations.py`（tex 出来后当键一致性闸门）。
明确不要用：`academic-db-retrieval`（只 CNKI/WoS/Scopus）、`database-lookup`（78 库无软件库）、`pyzotero`（无 Zotero 库）。

### 第 3 位 — 瓶颈 1 的锚点扩容（最需要技能、也最不可能自动化）

排在第 3 不是因为它次要——它是最严重的瓶颈——而是因为：
1. 它必须**你授权**才能提交集群作业（`tcc-cluster-access` 规则 2：不能表达成 batch job 就停下等指示）；
2. 它**没有对应领域技能**：全库没有任何 PySCF/Psi4/ORCA/二聚体/counterpoise 技能，技能能给的只有"怎么把作业安全打到装有 ORCA 6.0.1 的那台机"；
3. 它的价值周期长（跑作业 + 收 `E(C,NL)` 标签），适合和第 1、2 位交叠进行，不适合占第一个时段。
用：`tcc-cluster-access`（ORCA 6.0.1 位置、LSF `bsub` 用法与 36 slot、`/share` 路径纪律、该机无网）＋ `snnu-hpc-safety`（SNNU 侧登录节点保护）＋ `slurm-job-script-generator`（仅 SNNU/Slurm 侧自检）＋ `qoder-inwindow-timer`（本窗口按时复查）＋ `unattended-automation-continuity`（跨轮状态落文件）。
本地侧：`get-available-resources` 先探 WSL，再用 `python3 -u` 跑 PySCF（记忆已载：不带 `-u` 曾 18 分钟 0 字节日志）。Psi4 本机是否有**未经验证**，别当既有事实用。

### 第 4 位 — 瓶颈 4 的图件/元数据 QA

排在最后，因为它的前提是"已经有 tex/pdf"。届时：`reference-metadata-crossref-check`（元数据）→ `manuscript-layout-qa`（浮动体/孤页/图出界）→ 若图字体不齐才上 `journal-figure-typography-unify` / `figure-font-unification`。**`docx-*` 一族全部跳过**（Word 专用）。

---

## 4. 空白清单（没有对应技能的）

1. **量子化学外部裁判/锚点本身**：无 PySCF、Psi4、ORCA、GAMESS 技能；无二聚体相互作用能、counterpoise/BSSE、`E(C,NL)` 标签提取、orbital collapse/ghost 陷阱的技能。**瓶颈 1 的核心计算内容没有技能覆盖**，只有集群运维技能覆盖。
2. **Markdown→LaTeX 管线**：无可用技能。`markdown-to-html` 靠 pandoc（缺），`clawsgo-science` 服务未起且文档路径过期，`venue-templates` 不含 JOSS/SoftwareX。正确资产是仓内自有的 `tools/md2tex.js`。
3. **`[S#]` 出处标签闸门**：全库没有任何技能处理"裸串出处标签 → 定义表 → 出处核验"这套私有标记体系（`review-method-closure` 管 PRISMA 分母，`citation-management` 只认 `\cite{}`）。**瓶颈 2 的 software.md 那一半没有技能**。
4. **JOSS / SoftwareX 投稿规范**：无技能含这两个刊的模板或条款。
5. ** Psi4 可用性探测/安装**：无技能，且本机状态未验证。

---

## 5. 交付前自检（本报告的数字与结论怎么来的）

| 声称 | 来源 | 是否实测 |
|---|---|---|
| 899 目录 / 893 个 SKILL.md / 370 个 `source-command-*` 镜像 | `ls`+`find` 计数 | 是 |
| `.agents\skills` 是 junction → `D:\AgentData\shared-skills`；`.claude\skills` 同源 | `cmd dir /AL` + `readlink` | 是 |
| `deep-research` 技能不存在 ⇒ citation-management 示例命令死链 | `ls -d` 返回不存在 | 是 |
| `validate_citations.py` 只吃 `--tex/--bib`，不认 `[[key]]` | 读脚本 argparse 段 + `extract_cite_keys` 正则 | 是 |
| p2.md `[[` 0 次、无 References 节；software.md 27 处 / 13 唯一 `[S#]` 无定义表；references.bib 17 条；只有 main.tex/main.pdf | `grep -c` / `grep -o | sort -u` / `ls` | 是 |
| md2tex.js 第 12 行硬编码 `paper/main.md` | `grep` | 是 |
| MiKTeX 在 D 盘、pandoc/tectonic 缺 | 列目录 + `which` | 是 |
| clawsgo 服务 8001 未监听、SKILL.md 路径 `E:/Project/deepmdkit` 不存在、真实在 `E:/Project/EAM`；`latex_compile` 走本地 pdflatex、`auto` 走云端 | `netstat` + `ls` + 读 `server.py` | 是（未拉起服务、未调用） |
| venue-templates 无 JOSS/SoftwareX；database-lookup 78 库无软件库 | `grep` + 列 `references/` | 是 |
| tcc 上有 orca-6.0.1、LSF 非 PBS、36 slot、无网 | **仅读 SKILL.md 所载验证记录（job 93238，2026-09-06）** | 否——本次未连远端，按文档为"待复核" |

未做（受纪律约束）：联网、提交集群作业、起本地服务、调用云端模型、修改任何既有文件、安装任何东西。
