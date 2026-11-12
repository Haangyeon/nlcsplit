# 投稿前全量检查与润色记录（2026-11-12）

执行人：千问工作助理。本记录供作者预览与 Qoder 复核。所有改动均可用 git diff 追溯。

## 一、检查结论

| 项目 | 结果 |
|---|---|
| 正文 PDF | 37 页，0 LaTeX 错误，0 overfull，无越界文本，无乱码 |
| SI PDF | 22 页（原 23 页，孤页已消除），0 错误，0 overfull |
| 公式 (1)-(4) | 编号右对齐，公式完整（PDF 与 DOCX 均核验） |
| 图 1-7 / 表 1-4 | 逐页目检 + 程序化检查：无压线、截断、溢出 |
| 参考文献 | 92/92 Crossref 现取核验通过（作者/页码 92/92；元数据 91 通过 + mitoraj2009 超时后按其 DOI 10.1021/ct800503d 补验，标题相似度 1.000） |
| DOCX 结构 | 242 段、7 表、7 图、102 行内公式 + 4 编号公式；参考文献 Word 自动编号 [1]-[88] 正常 |
| TOC 图 | 当前 PDF 无 TOC 图——10-29 提交 5b86961 已有意移除，交接件描述过时；如 ACS 表单要求 TOC 图需另行准备 |

## 二、发现并修复的缺陷

### DOCX（原地修复，备份在 scratch/VV10-pair-attribution_prefix_20261112.docx）
1. 正文残留未解析交叉引用 `Fig.~\ref{fig:6}` → `Fig. 6`（1 处）
2. 参考文献 LaTeX 重音命令残留 → 正确 Unicode（约 30 处）：
   Ji\v r'i Klime\v s→Jiří Klimeš、He\sselmann→Heßelmann、J\orgensen→Jørgensen、
   \L. M. Mentel→Ł. M. Mentel、\v Rez'a\v c→Řezáč、Mori-S'anchez→Mori-Sánchez、
   Carb'o-Dorca→Carbó-Dorca、St'efan→Stéfan、Fern'andez del R'io→Fernández del Río、
   G'erard-Marchant→Gérard-Marchant、Pilm'e→Pilmé、Cern'y→Černý、Ban'as→Banás 等
3. LaTeX 连字符 `--`/`---` → en/em dash（页码区间、Becke–Treutler、atom–atom、Meta–Generalized、libxc 标题等，约 50 处）
4. LaTeX 引号 ``...'' → “...”（zhang1998comment 条目标题）
5. 原始标记 `evidence/**` → `evidence/`（1 处）
6. 第一轮规则误伤 Xi'an/Chang'an 为 Xián/Changán，第二轮已还原；所有格撇号（PySCF's 等）全部保留

### SI 孤页
- 原第 23 页只有一行孤句。根因：最后一个 longtable 后的 \normalsize 重新施加段间距，把末行挤过页边界。
- 修复：tools/md2tex.js 的 SI 前言加 \addtolength{\textheight}{\baselineskip}（仅 SI，正文不受影响）。SI 现为 22 页，末段完整。

## 三、润色（降 AIGC 感，11 处，只改措辞，未动任何数字/引用/结论）

| # | 位置 | 原文 | 改后 |
|---|---|---|---|
| 1 | §1 | Two things are not trivial, and they are the content of this paper. | What is not trivial, and what this paper is about, is the following. |
| 2 | §3.2 | Three things follow. | The comparison has three consequences. |
| 3 | §3.2 | Two things still cannot be concluded from these three ratios. | These three ratios still leave two questions open. |
| 4 | 图3说明 | The point is a comparison of two spans, and figures.py refuses to draw the figure unless | The figure compares two spans, and figures.py refuses to draw it unless |
| 5 | §4 开头 | This section keeps four things apart that are easy to read past one another: | This section separates four questions that are easy to conflate: |
| 6 | §4.1 | Two things that used to be said here are withdrawn. | Two earlier claims are withdrawn here. |
| 7 | §4.2 | Three things must be said about it rather than glossed. | Three caveats apply. |
| 8 | §5 | it is worth naming the trade honestly | the trade should be stated plainly |
| 9 | §6 | Three things follow from applying it to ... | Applying it to ... yields three findings. |
| 10 | §6 | What the method does not do is equally important, and we would rather the reader learn it here than in a review. | The method's limits deserve the same attention as its results. |
| 11 | Statements | The Supporting Information file carries three things: | The Supporting Information file contains the |

说明：正文此前已做过深度去 AI 味（无 delve/landscape/underscore 等套话，无 em-dash 滥用），本轮只清除残留的枚举式模板开头与自我标榜措辞。长句（平均 42 词）多为承载数字与限定从句所致，未强行拆分以免改变语义。PDF 与 DOCX 已同步这 11 处。

## 四、重建与验证
- sh tools/build_pdf.sh main：37 页，0 错，0 overfull，94 条 citation，md2tex 闸门 0 失败
- sh tools/build_pdf.sh si：22 页，0 错，0 overfull
- DOCX 修复后复扫：LaTeX 残留 0；11 处润色全部就位；公式/表/图数量不变
- 文献证据：evidence/bib_provenance/20261112T064840Z_bib_all92_authors_pages_v2_result.json（92/92）；
  20261108T0000Z_bib_all92_crossref_result.json（92/92，含 mitoraj2009 补验记录）

## 五、投稿前置事项（需作者本人）
1. ACS 登录：CN 侧曾触发密码重置邮件，先确认是否点过重置链接，再登录 publish.acs.org
2. ChronosHub 草稿 457354 上的 DOCX 落后于本版本，Submit 前必须替换为本目录最新 DOCX/PDF
3. 6 个法律勾选 + Submit 由作者本人执行（红线：不代按）
4. 如表单要求 TOC 图，需另行准备（当前稿件无 TOC 图）