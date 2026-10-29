# 软件说明的去处：并入 JCTC 的 SI（2026-10-28）

结论：**不单独投软件文；把可用内容写进主稿的 Supporting Information。**
这是作者 2026-10-28 的决定（"那还不如与 JCTC 一起投呢"），本轮已落地并通过全部稿件闸门。

## §1 索引身份是实测的，不是记忆的

JOSS 不能当 SCI 用。今天（2026-10-28）核到的三条独立事实：

1. Clarivate 主刊列表申请被拒，2024-02 月底确认，官方 issue 原话
   "JOSS is not currently included in the Web of Science / Clarivate master list"；
   既不在 SCIE 也不在 ESCI，因此没有官方影响因子，也没有 Journal Citation Indicator。
   （<https://github.com/openjournals/joss/issues/1283>）
2. OpenAlex `sources/issn:2475-9066` 与第三方收录页今天回读一致：只有 **DOAJ**，
   WoS 子库与 Scopus 栏位为空。（<https://journalsearches.com/journal.php?title=journal%20of%20open%20source%20software>）
3. FZ Jülich 的软件期刊指南明写它不在 WoS Core Collection / Scopus，
   并且该单位的绩效统计"JOSS publications thus do not count"。
   （<https://www.fz-juelich.de/en/rse/the_latest/should-i-publish-in-the-journal-of-open-source-software>）

对照件：SoftwareX 确为 SCIE + EI（最新 IF 1.9，JCR Q3，中科院 4 区），但 12 页长软件文与主稿
内容重复，Opus 判它会 desk reject；国内认定以本单位期刊文件为准，本节只陈述索引事实。

## §2 落地形态

- 主稿 `paper/main.md` 末尾新增 SI 附录 **"The nlcsplit package"**（约 1,200 词），
  由 `tools/md2tex.js` 随 provenance 附录一起排进 `supporting_information.tex`；
  15 道出货闸门表进 SI 成为 **Table S3**（源码里标题写 **Table 7.**，与 Table S2 同一套编号约定）。
- 主文 §5 Code availability 增一段指向它，并用 **[S37]** 引出货记录；
  Statements 里的 "Supporting information" 改成三件（Table S1 出处表 / Table S2 满 S22 跨度 /
  Table S3 闸门表 + 包说明）。
- 新出处行 **S37** = `evidence/release_qa/` 的 quickstart 原样 stdout、shipping wheel census、
  test-count census、no-GAMESS 安装件扫描、该目录 MANIFEST + `nlcsplit/examples/quickstart.py` +
  `tools/make_public_repo.js` + `CITATION.cff`，全部是 git-tracked 件。
- `paper/software.md` 保留但顶部写 **Disposition：不投稿**，并点名两条已作废数字；
  `paper/joss/paper.md` 保留不投。

## §3 两条"照抄就会搬错"的（已经拦下，别再搬）

| 软件文原句 | 为什么不能搬进投稿载体 | 现在用什么 |
|---|---|---|
| block-additivity residual 1.73e-18 to 6.94e-18 Ha | 该区间来自**一个体系的一份归档**，主文 §2.2 已改为 13 行普查、跨度 0.000e+00 to 5.551e-17 Ha，并写明旧说法错在哪 | 引主文 §2.2 与 [S33]，SI 不另报数字 |
| "74 of the repository's 94 tests" | 94 这条出自 `evidence/release_qa/20261023T122250Z_ship_qa_plan.out`，**该归档尚未 git-tracked**；md2tex 路径闸门只认 tracked，引用它=引用读者查不到的件 | 只报 tracked 的 10-13 census：套件收 94 条（71 非 slow / 23 slow），逐模块相加自证，不随包模块点名 |

## §4 工具侧两处改动（都可回滚、都已实测）

1. `tools/md2tex.js`：SI 节标题原为**硬编码** `\section*{Provenance of every quoted number}`，
   任何第二段附录都会被印成同一标题。改为从 Markdown 标题派生
   （剥掉 `Appendix:` 前缀 + 首字母大写）。验证：改后重排出的 `supporting_information.tex`
   与改前 **逐字节相同**（`diff` 空），即旧产物未被扰动。
2. `tools/md2tex.js` 的 `siPre`：补 `\tolerance=2000` 与 `\emergencystretch=3em`（主文前导早有，
   SI 没有）。原因：SI 里长 `\texttt{}` 串（API 签名、方案名、quickstart 输出行）撑出 4 条
   overfull hbox；补参数后 **0 overfull**。

## §5 闸门 D 的一条硬约束（下次往附录表里塞路径前先看这条）

`tools/make_public_repo.js` 的闸门 D 只扫 **`| S\d+ |` 表格里**的反引号路径，并要求每一个都随包发布。
导出白名单 `TOOLS = ['make_public_repo.js', 'audit_no_gamess.js', 'audit_share_rule.js']`，
所以 `tools/run_ship_qa.sh` **进表就会被判"读者打不开的出处"**（已实测：它一度在 S37 行里，撤掉后干净）。
写法上的结论：十五道闸门归属 `tools/make_public_repo.js`（随包），
`run_ship_qa.sh` 只能在散句里称作母仓驱动器，不能进 S 行。

## §6 本轮复验（都是实跑）

- `sh tools/build_pdf.sh main` → **37 页 / 0 LaTeX 错 / 0 overfull / aux 里 93 条 \citation**。
- `sh tools/build_pdf.sh si` → **23 页 / 0 错 / 0 overfull**（并发生长 18 → 23）。
- md2tex 审计：tags cited in the body **37**、tables emitted **7 / 全部带编号**、
  appendix rows never cited **none**、artefact checks failed **0**、bib **88 of 92**
  （剩余四条 `barca2020gamess, peng2011repro, sabatini2013, smith2016software` 只由不再投稿的软件文引用）。
- `node tools/claim_gate.js --stop` → clean（2 carriers, 30079 indexed numbers）。
- `node tools/audit_share_rule.js` → PASS（并自带"判据 (2) 不构成担保"的免责声明）。
- `node tools/audit_p2.js` → PASS，0 findings。
- 过程中被闸门**真拦下两次**：我自己算出的 -7.8131 / 53.0173 两个和值（归档里没有，改成
  "最后一位差一个单位"的定性写法）；`partition.py` 少写目录导致路径闸门 FAIL（改 `nlcsplit/partition.py`）。

## §7 仍然悬着的

- 作者当次授权才投稿；**绝不代按 Submit**。
- 出货前 `.publish/nlcsplit/` 与 `dist/nlcsplit/` 必须重生成（现为 10-01 旧导出，任务 13）。
- Figure 3 版式 A/B/C 仍待作者选（任务 12）。
- 提交授权：本会话工作树未提交文件数继续增长（任务 11）。
- 软件作为"可被引用的软件"这条，靠的是仓库公开 + tagged release + Zenodo DOI + `CITATION.cff`，
  与 SI 里这段文字无关；SI 只解决"读者能查到包怎么用的"。
