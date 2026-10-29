# SCIENTIFIC_AUDIT — paper/main.md（2026-10-29）

对象冻结：`audit_round0/FREEZE-20261029.txt`（main.md / main.tex / SI.tex / bib / 两份 PDF / 7 张图，
路径 + 字节数 + mtime + SHA-256）。
方法：`scientific-correctness-audit` 技能，三条独立审计线并行（图表 vs 正文、数字与派生算术、
引文语境＋对抗性审稿），findings 只报不改，由主代理逐条复核后修。
**第三条线（数字与派生算术）截稿时仍未返回**，其结论不在本文件内。

## 1 本轮已修（每条都改了正文，并重跑过构建）

| ID | 严重度 | 问题 | 修法 |
|---|---|---|---|
| C-F1 | BLOCKER | §3.4 把两个苯二聚体几何的**互片段非局域块之差**（1.667）当成总能量差，据此宣称"平行位移结构低 1.5 kcal/mol 以上、任何方案都不反转"。实际总相互作用能 Table 1 是 -3.580 vs -3.188（A 低），Table 2 反泊松后是 -1.9403 vs -2.4297（B 低）——**排序在两张表之间反向** | 整段重写：删掉排序主张，改成"两个取向在未校正/反泊松两张表里排序相反，互片段块不是结合能的代理"，并注明旧版误读 |
| C-F2 | MAJOR | 摘要最后一句重复同一错误（"total-energy ranking is stable"） | 改成"百分比相差七倍，而总相互作用能在反泊松前后排序相反" |
| C-F17 | MAJOR | CCSD(T) 基组阶梯第一级用了**全电子值** -3.7035，后三级是冻核值；"cc-pVDZ→aug-cc-pVTZ 跨度 1.18" 实为 1.03（1.18 是 6-31G*→cc-pVDZ 那一步） | 改为 -3.6986、跨度 1.03 并补一句说明两个列的差别 |
| C-F4 | MAJOR | 58,664,816 与零命中串标成 [S16]（§8.1 = 访问前提），实际在 [S17]（§13） | 改 [S17]，并在 §4.4 的访问前提句补回 [S16]（否则 S16 成孤儿行，md2tex 当场拦下） |
| C-F3 | MAJOR | PBE0-VV10 / revPBE-D3 的 ALMO-EDA 色散数值没有引到那篇研究 | 在 "ALMO-EDA study" 后补 [[dasgupta2023]]，三个泛函引用留在名称处 |
| C-F7 | MAJOR | 开放索引召回数三处互相矛盾（§1 写 0/4 each；§4.4 写 2 of 3 / 3 of 3；S15 行写 0/4 与 1/3） | 以检索记录为准统一：OpenAlex 0/4、Crossref 1/3（§1 与 §4.4 两处都改） |
| C-F5 | MAJOR | "every record returned by every query was read" 与检索记录不符（33 条那两批只读题名） | 改为"逐条枚举、逐条读题名；摘要只读了 4 条的两批与 33 条里的 8 条" |
| C-F6 | MAJOR | 三处写"local part cancels identically / every dE_NLC is free of it"，与实测残差 -0.0013…+0.0011 冲突 | 三处都改成"连续极限下精确抵消；网格上只到电子数求积误差，残差见 §3.3" |
| C-F9 | MINOR | 摘要把 0.92–1.08 的分母说成 counterpoise 差，实际是**未校正**的 frozen-density 差 | 改为 "uncorrected … for which a counterpoise reference is also available" |
| C-F10 | MINOR | 摘要说 ORCA 锚在全部八体系"低于 1%"，但平行位移苯二聚体那行残差是跨度的 1.3 倍 | 摘要补上这个例外 |
| C-F11 | MINOR | §6 写"level 1 到 2 在 0.001 以内"，§4.5 是 0.0013 | 改为 0.0013 |
| G-F7 | MAJOR | **PDF 里所有 "6-31G\*" 的星号被吞掉**，印成 "6-31G"（另一个基组名） | 根因在 `tools/md2tex.js`：markdown 的转义星号原样送出 `\*`，文本模式下 LaTeX 不排版它。改为在 inline() 里还原成 `*`；重建后 PDF 已显示 6-31G* |
| G-F18 | MAJOR | 两份 PDF 都比源文件旧 | 重建：main 37 页、SI 23 页，均 0 LaTeX 错 0 overfull |

## 2 未修（已复核、按优先级）

| ID | 严重度 | 问题 | 建议 |
|---|---|---|---|
| G-F1 | MAJOR | Figure 4 **全文从未被正文引用** | 在 §4.2 引出 Table 4 的句子后加 "Figure 4" |
| G-F2 | MAJOR | §4.4 那句 "Error bars must be reported per system (Fig.~\ref{fig:2})" 指的是 Figure 6（Figure 2 是能量图） | 改 fig:6 |
| G-F3 | MAJOR | §3.5 用 `Fig.~\ref{fig:1}` 引 16%/97% 两个数，那是 Table 1 的值（Figure 1 是八个体系的结构图） | 改引 Table 1 |
| G-F5 | MAJOR | Figure 7 的空心/实心图例与实际画法不符（空心只标了 archived 窗口的 exact 系列，screened 全是实心） | 改图注措辞或改编码 |
| G-F6 | MAJOR | Figure 7(a) 画的是 11 条连接线（1e-12 子集），图注说"33 对的图形化" | 改图注为"最严容差子集"或补画 |
| G-F4 | MINOR | Figures 3 与 5 在正文里没有被引用 | §3.2/§3.4 各加一处 |
| G-F8 | MINOR | "five of the eight are larger than 1.217"，按 Table 2 数是六个 | 改 six（或 five of the other seven） |
| G-F9 | MINOR | "Table 1 的 release split is stated row by row"，Table 1 没有 release 列 | 改"stated in the text"或加列 |
| G-F10 | MINOR | Table 3 把跨度叫 "variance"，代码算的是 max-min | 改 range/spread |
| G-F11 | MINOR | Table 5 的 S33 行引 Table 1 的 0.0435，该值在 Table 4 | 改引 Table 4 |
| G-F12 | MINOR | SI 的 S1 表提到 "Figure 5's lower panel"、"Tables 1-3"，SI 里没有这些浮动体 | 加"of the main text" |
| G-F13 | MINOR | SI 说明承诺"line-number record behind every quoted value"，实际只有 S6 带行号 | 改措辞或补行号 |
| G-F14 | MINOR | Figure 6 标 methane 0.8%，Table 3 印 0.9%（正文解释了舍入，图注没解释） | 图注加一句 |
| G-F15 | NIT | Table 5 题注缺 "numbered Table S1" 的桥接句 | 补一句 |
| G-F16 | NIT | Figure 5(d) 的 "x0.1" 掩盖了 0.07 那个点 | 改两位有效数字 |
| G-F17 | MINOR | 七张图里四张的 PNG 比生成脚本旧（内容是否变未验） | 投稿前统一重生成并比哈希 |
| C-F8 | MAJOR | 摘要第一句"Production kernels … fold the double sum"超出所审范围（只审了 PySCF 内核） | 改成"the production kernel we audited (PySCF's)"，并写明 ORCA/Psi4/Gaussian 未审 |
| C-F12 | MINOR | "second-generation ALMO-EDA [[khaliullin2007]]" 引的是第一代 | 补 Horn 2016；khaliullin2007 只覆盖 E_Frz+E_Pol+E_CT |
| C-F13 | MINOR | §4.3 标题"which no other program can supply"无软件普查支撑 | 改成"which the second program we used cannot supply" |
| C-F14 | MINOR | "no quantity in Table 1 rests on…" 过宽；Table 4 只核 ΔE_NLC | 限定到 ΔE_NLC 列 |
| C-F15 | MINOR | 4 条 bib 条目无人引用（barca2020gamess / peng2011repro / sabatini2013 / smith2016software） | 删掉，或在 §1 "explicit evaluation is not itself new" 处引 sabatini2013 |
| C-F16 | MINOR | §4.5 写"No charge-transfer … complex is tested"，同段却报了 dative H3N-BH3 控制 | 改为"no donor-acceptor case beyond the dative control" |

## 3 修复后的复验

- `sh tools/build_pdf.sh main` → **37 页 / 0 LaTeX 错 / 0 overfull / 94 \citation**。
- `sh tools/build_pdf.sh si` → **23 页 / 0 错 / 0 overfull**。
- `claim_gate --stop` → clean（1 carrier, 33766 indexed numbers）。
- md2tex 出处审计：37 标签全落地、7 张表全带编号、无孤儿行。
- 6-31G* 星号：`pdftotext -f 16` 现在读到 "6-31G*"，修复前读到 "6-31G"。

## 4 未闭合的风险

1. 第二条审计线（数字与派生算术）结果未到，本文件不含它。
2. §3.4 那段"化学决策"已按事实删除：原判词（Opus 第三轮 REVISE）部分建立在这个错误前提上，
   **REVISE 的效力需要重估**；JCTC 适配度评估要按"化学增量更薄"的新事实重做一次。
3. G-F5/G-F6 是图本身的问题（Figure 7），只改图注能遮住症状、不改图像与数据的对应关系。
