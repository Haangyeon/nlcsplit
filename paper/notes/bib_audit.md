# 参考文献外部元数据核验（第二轮，独立复核）

对象：`paper/references.bib`（16 条，均为 `@article`）。目标期刊：JCTC。
本轮不复用上轮结论：每条重新按 DOI 反向取 Crossref 记录，并另取两个独立源交叉。

## 0. 方法与数据源（先看这个，再看结论）

| 源 | 用途 | 取得情况 |
|---|---|---|
| Crossref `https://api.crossref.org/works/<DOI>` | 主核（年/期刊/卷/页或文章号/作者逐字段） | **16/16 HTTP 200**，字段取自原始 JSON |
| Semantic Scholar Graph API `paper/DOI:<doi>` | 第二独立源（题名、作者数、年份、venue、externalIds） | 16/16 有记录 |
| OpenAlex `works/doi:<doi>` | 第三独立源（`biblio`、作者数、venue） | 16/16 有记录 |
| 出版方落地页 | 一手标题核对 | APS 成功 1 条（Hamada & Tsukada）；`pubs.acs.org` 403、`pubs.rsc.org` 403、`sciencedirect` 404 → **未能访问，非否证** |
| WebSearch（题名/作者交叉） | 本要求项 | **本机 WebSearch 走中文聚合镜像，精确串检索亦只返回无关条目，不可用**。故改用 Semantic Scholar + OpenAlex 两个 API 作交叉源；下文逐条注明。 |

需要记录的两件处置：

1. **429 不当作"查不到"**：`dion2004`、`goerigk2017gmtkn55` 首轮 WebFetch 并发请求返回 **429 RATE_LIMITED**；随后用顺序 curl（`User-Agent: bib-audit/1.0 (mailto:…)`，间隔 1 s）重取，两条均 HTTP 200 并取到完整字段。最终 **0 条处于 RATE_LIMITED 未解决状态**。
2. **工具摘要误差已纠正**：WebFetch 的模型摘要把 Calbo 那章第四作者读成 "Aragón"；Crossref **原始 JSON** 是 `"given":"Juan","family":"Aragó"`。本表一律以原始 JSON 为准（`bib` 现写法 `Juan Aragó` 是对的）。

复现命令（无副作用，只读；本轮未落盘原始 JSON）：

```bash
for d in <16 个 DOI>; do curl -sS -H "User-Agent: bib-audit/1.0 (mailto:…)" \
  "https://api.crossref.org/works/$d?mailto=…" ; sleep 1; done
```

**字段解析率自证（先给这个再给结论）**：年份 16/16、期刊 16/16、卷 15/16（`calbo2015vv10review` Crossref 无 volume）、页或文章号 16/16（其中 4 条 Crossref 只有 `article-number`、`page` 为 ABSENT）、作者名单 16/16（含逐人 given/family 比对，非只比人数）。比对是在**已确认 DOI 指向正确**之后才做的。

---

## 1. 逐条表

判定口径：**一致** = 五个字段全部与 Crossref 相符；**不一致** = 有实质出入（含 bib 字段为空）。
"Crossref 返回"里 `art=` 是 `article-number`；`page ABSENT` 指 Crossref 记录本身没有 `page` 字段（APS/AIP 用文章号）。

| # | bib key | 现有写法（year / journal / vol / pages / 作者数） | Crossref 返回（issued 年 / container / vol / page·art / 作者） | 一致？ |
|---|---|---|---|---|
| 1 | `kruse2019dna` | 2018 / J. Chem. Theory Comput. / 15 / 95-115 / 3 | issued **2018-11-29**，published-print **2019-01-08** / J. Chem. Theory Comput. / **15**, issue 1 / 95-115 / Holger Kruse, Pavel Banáš, Jiří Šponer（3） | 卷页作者全对；**年份属"online-first vs 卷期年"口径**（key 名 2019 与 year=2018 也不自洽）→ 见 §3 |
| 2 | `sinha2015fdevdw` | 2015 / The Journal of Chemical Physics / 143 / **`pages={}`** / 2 | 2015 / The Journal of Chemical Physics / 143, issue 8 / page ABSENT，**art=084120** / Debalina Sinha, Michele Pavanello（2） | **不一致（缺页/文章号）** |
| 3 | `hujo2011hbond` | 2011 / Phys. Chem. Chem. Phys. / 13 / 13942 / 2 | 2011 / PCCP / 13, issue 31 / **page=13942**（Crossref 只给起页）/ Waldemar Hujo, Stefan Grimme（2） | 一致（RSC 完整区间 13942–13950 未能从出版方核到，见 §4） |
| 4 | `hamada2011c60au` | 2011 / Physical Review B / 83 / **`pages={}`** / 2，title `Adsorption ofC60on Au(111)…` | 2011 / Physical Review B / 83, issue 24 / page ABSENT，**art=245437** / Ikutaro Hamada, Masaru Tsukada（2），title 含 MathML 下标（`C60`） | **不一致（缺文章号 + 题名空格损坏）**；APS 落地页一手标题 = *Adsorption of C₆₀ on Au(111) revisited: A van der Waals density functional study* |
| 5 | `becke1988` | 1988 / The Journal of Chemical Physics / 88 / 2547-2553 / 1 | 1988 / JCP / 88, issue 4 / 2547-2553 / A. D. Becke（1） | 一致 |
| 6 | `stratmann1996` | 1996 / Chemical Physics Letters / 257 / 213-223 / 3，`R.Eric Stratmann` | 1996 / Chemical Physics Letters / 257, issue 3-4 / 213-223 / given **"R.Eric"**（Crossref 原样，无空格）, Gustavo E. Scuseria, Michael J. Frisch（3） | 一致（"R.Eric" 与 Crossref 字面同；见 §4） |
| 7 | `dion2004` | 2004 / Physical Review Letters / 92 / **`pages={}`** / 5 | 2004 / PRL / 92, issue 24 / page ABSENT，**art=246401** / M. Dion, H. Rydberg, E. Schröder, D. C. Langreth, B. I. Lundqvist（5） | **不一致（缺文章号）**；首轮 429，已重取 200 |
| 8 | `mardirossian2014wb97xv` | 2014 / PCCP / 16 / 9904 / 2 | issued 2014（created 2013-12-18）/ PCCP / 16, issue 21 / **page=9904** / Narbe Mardirossian, Martin Head-Gordon（2） | 一致（OpenAlex 记 year=2013，系 online-first 口径差异，非 bib 错） |
| 9 | `mardirossian2016wb97mv` | 2016 / The Journal of Chemical Physics / 144 / **`pages={}`** / 2 | 2016 / JCP / 144, issue 21 / page ABSENT，**art=214110** / Mardirossian, Head-Gordon（2） | **不一致（缺文章号）** |
| 10 | `lazic2010junolo` | 2010 / Computer Physics Communications / 181 / 371-379 / 6 | issued [2010,2] / CPC / 181, issue 2 / 371-379 / Lazić, Atodiresei, Alaei, Caciuc, Blügel, Brako（6） | 一致（OpenAlex 记 2009 = created 日，同口径差异） |
| 11 | `dasgupta2023` | 2023 / J. Chem. Theory Comput. / 20 / 49-67 / 4 | issued **2023-12-27**，published-print **2024-01-09** / JCTC / **20**, issue 1 / 49-67 / Saswata Dasgupta, Etienne Palos, Yuanhui Pan, Francesco Paesani（4） | 卷页作者全对；**与 #1 同一"online-first vs 卷期年"问题**（卷 20 属 2024）→ 见 §3 |
| 12 | `calbo2015vv10review` | 2015 / Annual Reports in Computational Chemistry / **`volume={}`** / 37-102 / 4，`@article` | type **book-chapter** / 2015 / Annual Reports in Computational Chemistry / **volume ABSENT** / page 37-102 / Joaquín Calbo, Enrique Ortí, Juan C. Sancho-García, **Juan Aragó**（4） | **不一致（缺卷号 + 条目类型错）**；作者四人含 `Aragó` 拼写**已按原始 JSON 确认一致** |
| 13 | `goerigk2017gmtkn55` | 2017 / PCCP / 19 / 32184-32215 / 6 | 2017 / PCCP / 19, issue 48 / 32184-32215 / Goerigk, Hansen, Bauer, Ehrlich, Najibi, Grimme（6） | 一致（含首轮 429 已重取 200） |
| 14 | `vydrov2009vv10` | 2009 / PRL / 103 / 063004 / 2 | 2009 / PRL / 103, issue 6 / art=063004 / Oleg A. Vydrov, Troy **Van Voorhis**（2） | 一致 |
| 15 | `vydrov2010simple` | 2010 / JCP / 133 / 244103 / 2 | 2010 / JCP / 133, issue 24 / art=244103 / Vydrov, Van Voorhis（2） | 一致 |
| 16 | `hyldgaard2014interp` | 2014 / PRB / 90 / 075148 / 3 | 2014 / PRB / 90, issue 7 / art=075148 / Per Hyldgaard, Kristian Berland, Elsebeth Schröder（3） | 一致 |

**计数**：五字段全一致 **9 条**（#3 #5 #6 #8 #10 #13 #14 #15 #16）；实质不一致 **5 条**（#2 #4 #7 #9 #12）；年份口径待定 **2 条**（#1 #11，除年份外四字段全对）。合计 16。
第二/第三源补充：16 条的**题名与作者人数**在 Semantic Scholar 与 OpenAlex 上均与 Crossref 相符（无一条人数不符、无一条题名实质不符）；`#12` 的 S2 题名带副标题，见 §4。

---

## 2. DOI 缺失 / 字段缺失

- **DOI 缺失：0 条。** 16 条全部有 `doi` 字段，无空值。
- **DOI 重复：0。** 16 个 DOI 字符串（大小写归一后）**全部唯一**，无"同一文献两条不同 DOI"，也无两条目共用一个 DOI。
- **DOI 指向性：** 16 个 DOI 全部 `api.crossref.org/works/<DOI>` 返回 200 且 `type=journal-article`（仅 `calbo2015vv10review` 是 `book-chapter`），返回题名/作者与本条相符 → **没有一条指错**（`hamada2011c60au` 只是题名里带 MathML 噪声，仍是同一篇）。
- **预印本 DOI 混用：无。** 反向证据：S2 的 `externalIds` 显示 `dion2004` 有 arXiv `cond-mat/0402105`、`vydrov2010simple` 有 arXiv `1009.1421`、`hyldgaard2014interp` 有 arXiv `1408.2075`，三条 bib 里用的都是**正式版 DOI**（PRL/JCP/PRB），未混用 arXiv DOI；其余 13 条无 arXiv 记录。
- **真正缺的是页/卷，不是 DOI：5 处空字段**（这是投稿硬伤，Crossref 都有值或可补）：

| bib key | 空字段 | 应填值 | 依据 |
|---|---|---|---|
| `sinha2015fdevdw` | `pages` | `084120` | Crossref `article-number`（OpenAlex 同值） |
| `hamada2011c60au` | `pages` | `245437` | Crossref `article-number` + APS 落地页 + DOI 尾段自证 |
| `dion2004` | `pages` | `246401` | Crossref `article-number` + DOI 尾段自证 |
| `mardirossian2016wb97mv` | `pages` | `214110` | Crossref `article-number`（OpenAlex 同值） |
| `calbo2015vv10review` | `volume` | `11` | Crossref **无此字段**（book-chapter 不登记 volume）；由 (a) Semantic Scholar `journal.volume='11'`，(b) Crossref 同系列 2011 年某章标题自证 *"Annual Reports in Computational Chemistry Volume 7"* ⇒ 2011=v7、2015=v11 两条独立推得 |

注：4 个 APS/AIP 条目的文章号同时被 DOI 字符串本身编码（`PhysRevLett.92.246401`、`physrevb.83.245437`），属可 reconstruction 的内部自证，不依赖单一日志。

---

## 3. 必须修的（5 条，可直接粘贴的替换块）

以下替换块保持原文件的缩进与对齐风格；**只填缺失字段/修题名，不改任何已核对为正确的值**。

### 3.1 `sinha2015fdevdw` — 补文章号

```bibtex
@article{sinha2015fdevdw,
  author  = {Debalina Sinha and Michele Pavanello},
  title   = {Exact kinetic energy enables accurate evaluation of weak interactions by the FDE-vdW method},
  journal = {The Journal of Chemical Physics},
  volume  = {143},
  pages   = {084120},
  year    = {2015},
  doi     = {10.1063/1.4928531},
}
```

### 3.2 `hamada2011c60au` — 修题名空格 + 补文章号 + DOI 大小写统一

（现题名 `Adsorption ofC60on Au(111)` 会原样进 PDF 的参考文献页；`{$\mathrm{C}_{60}$}` 的外层大括号用于挡住 `unsrtnat.bst` 的标题小写化，与本文件 `{{$\omega$}B97X-V…}` 的既有写法同风格。）

```bibtex
@article{hamada2011c60au,
  author  = {Ikutaro Hamada and Masaru Tsukada},
  title   = {Adsorption of {$\mathrm{C}_{60}$} on {Au}(111) revisited: A van der Waals density functional study},
  journal = {Physical Review B},
  volume  = {83},
  pages   = {245437},
  year    = {2011},
  doi     = {10.1103/PhysRevB.83.245437},
}
```

### 3.3 `dion2004` — 补文章号

```bibtex
@article{dion2004,
  author  = {M. Dion and H. Rydberg and E. Schr{\"o}der and D. C. Langreth and B. I. Lundqvist},
  title   = {Van der Waals Density Functional for General Geometries},
  journal = {Physical Review Letters},
  volume  = {92},
  pages   = {246401},
  year    = {2004},
  doi     = {10.1103/PhysRevLett.92.246401},
}
```

### 3.4 `mardirossian2016wb97mv` — 补文章号

```bibtex
@article{mardirossian2016wb97mv,
  author  = {Narbe Mardirossian and Martin Head-Gordon},
  title   = {{$\omega$} B97M-V: A combinatorially optimized, range-separated hybrid, meta-GGA density functional with VV10 nonlocal correlation},
  journal = {The Journal of Chemical Physics},
  volume  = {144},
  pages   = {214110},
  year    = {2016},
  doi     = {10.1063/1.4952647},
}
```

### 3.5 `calbo2015vv10review` — 补卷号 + 条目类型（两处给出，二选一）

Crossref 把这条登记为 **`book-chapter`**，现用 `@article` + `journal=` 严格说是类型选错（印出来像期刊论文）。

推荐（最小改动，只补卷号，类型暂不动，便于你一次合入）：

```bibtex
@article{calbo2015vv10review,
  author  = {Joaquín Calbo and Enrique Ortí and Juan C. Sancho-García and Juan Aragó},
  title   = {The Nonlocal Correlation Density Functional VV10},
  journal = {Annual Reports in Computational Chemistry},
  volume  = {11},
  pages   = {37-102},
  year    = {2015},
  doi     = {10.1016/bs.arcc.2015.09.002},
}
```

规范版（按 Crossref `type=book-chapter`；`editor=` 留空位**未编造**，需从 ScienceDirect 丛书页人工补）：

```bibtex
@incollection{calbo2015vv10review,
  author    = {Joaquín Calbo and Enrique Ortí and Juan C. Sancho-García and Juan Aragó},
  title     = {The Nonlocal Correlation Density Functional VV10},
  booktitle = {Annual Reports in Computational Chemistry},
  editor    = {TO CONFIRM -- Elsevier ARCC vol.\ 11 volume editor},
  volume    = {11},
  pages     = {37-102},
  year      = {2015},
  publisher = {Elsevier},
  doi       = {10.1016/bs.arcc.2015.09.002},
}
```

> 合入后需重跑 `xelatex/pdflatex → bibtex → 2×pass`，并重新生成 `paper/tex_audit.md`（`tools/md2tex.js` 的产物）。我未运行编译（本轮只核元数据）。

---

## 4. 体例待用户/编辑确认的项（不是元数据错误）

1. **ACS 两条的年份口径（#1 `kruse2019dna`、#11 `dasgupta2023`）** —— 需要你定一次，两条要用同一个口径。
   - 事实：Crossref `issued` = online-first（2018-11-29 / 2023-12-27），`published-print` = 卷期年（2019-01-08 / 2024-01-09）；卷 15 属 2019、卷 20 属 2024。Semantic Scholar 与 OpenAlex 都取 online-first 年。
   - 现在 bib 印的是 **online-first 年配卷期页码**（`2018; 15, 95–115`、`2023; 20, 49–67`），这个"卷—年不成对"是审稿人随手可验的点。
   - 选项 A（改 `year={2019}` / `year={2024}`，与卷号成对；顺带 `kruse2019dna` 的 key 名也就自洽了）；选项 B（保持 2018/2023，则建议在 key 或内部记录里说明取 ASAP 年，且 `kruse2019dna` 这个 key 名与实际印出的 2018 长期不一致，属内部可读性问题，PDF 里不可见）。
   - 我不能替你断定 JCTC 模板会印哪一个，故列为待确认；**本轮不算"必须修"**。
2. **`journal=` 全名 vs ISO4 缩写（影响全部 16 条）——我不确认 JCTC 是否要求缩写体例。**
   - 现状：16 条全用长名（`The Journal of Chemical Physics`、`Physical Review B`…），`unsrtnat.bst` 原样印成 `\emph{长名}`。
   - 已知事实：Crossref 对 ACS/RSC/APS 期刊**同时**提供 `short-container-title`（`J. Chem. Theory Comput.`、`Phys. Chem. Chem. Phys.`、`Phys. Rev. B/Lett.`），对 AIP `JCP`、`Chem. Phys. Lett.`、`Comput. Phys. Commun.`、ARCC **不提供**（字段为空/与长名同），所以若改缩写体例，后四条得手写 ISO4 形式。
   - **未能取到 JCTC 官方 Guide for Authors 的第一手页面**（`pubs.acs.org` 403；本机 WebSearch 镜像不可用；Crossref 里那篇 JCTC 论文的 `reference` 只 dep 了 1 条 unstructured 项，取不到风格样本）。因此"JCTC 是否强制缩写、斜体、是否要 `number=`/DOI 位置"这三点我不能给结论，请以 JCTC 官方投稿模板（通常 `achemso` + 其 `.bst`）实测定：多数情况下期刊名缩写由**模板/`bst` 决定**，届时 bib 里写全名也可能被排成缩写形式。
   - 另外：现 preamble 是 `\documentclass[11pt]{article}` + `natbib[numbers,sort&compress]` + `unsrtnat`，**不是 ACS 模板**；换投时这是独立于本表的另一件事。
3. **RSC 两条只有起页（#3 `hujo2011hbond` 13942、#8 `mardirossian2014wb97xv` 9904）** —— 与 Crossref 字面完全一致，故判"一致"；但 PCCP 官方页码通常是区间（13942–13950、9904–9932）。`pubs.rsc.org` 403 使我未能一手核对，proof 阶段建议人工核对后再决定是否补成区间；**Crossref 不是否证**。
4. **`#6 stratmann1996` 的 `R.Eric Stratmann`** —— 与 Crossref 原始 given 字段字面相同（出版社存录就没有空格）；原文署名一般作 "R. Eric Stratmann"。改成 `R. Eric Stratmann` 会比 Crossref 字面更"正确"但不再逐字相同，请你选。
5. **`#12 calbo2015vv10review` 题名是否带副标题** —— Crossref 与 Elsevier `linkinghub` 落地页给短题名（=现 bib 写法）；Semantic Scholar 给长题名 *The Nonlocal Correlation Density Functional VV10: A Successful Attempt to Accurately Capture Noncovalent Interactions*。**未能定论**（ScienceDirect 章节页 404，进不去），现写法有 Crossref 支撑，暂不改。
6. **APS DOI 大小写不统一** —— `hamada2011c60au` 用小写 `10.1103/physrevb.83.245437`，另 4 条 APS 用规范混合大小写。DOI 不区分大小写、解析不受影响，纯体例；§3.2 的替换块已顺手统一为 `PhysRevB.83.245437`。相关：`paper/main.md:259` 正文里 GMTKN55 的 DOI 写成大写 `…/C7CP04913G`，bib 写小写，同一 DOI 的两种写法并存（无害）。
7. **`number=`（期号）与 `month=` 全部 16 条都缺** —— Crossref 有 `issue`（如 15(1)、143(8)、13(31)）。是否要补取决于目标模板的引用样式，同属第 2 条待确认范畴。

---

## 5. `main.tex` 实引键集 vs `.bib` 键集（独立复核，不采信 tex_audit 的 16/16）

用四种互斥选择条件分别数，**结论不因计数口径而变**：

| 口径 | 值 |
|---|---|
| `references.bib` 条目数 | 16（distinct 16） |
| `main.tex` 含 `\citep` 的**行数** | 7（**别用这个数当引用数**：一个 `\citep{}` 里可含多键，且第 42、56 行各有多次调用） |
| `main.tex` 的 `\citep` **命令数** | 16 |
| `main.tex` 展开逗号后的**键实例数** | 16（无多键合并写法，故 = 命令数） |
| `main.tex` **distinct 键数** | 16 |
| `main.aux` 的 `\citation` 键实例 / distinct | 16 / 16 |
| `main.bbl` 的 `\bibitem` 数 | 16 |
| `main.md` 的 `[[key]]` 引用数 / distinct | 16 / 16 |
| `main.md` 的 provenance 标签 `[S#]` | 23–26 处（视正则口径），distinct 17 个 —— **与 bib 引用数不可相加**，二者是两套东西（tex_audit 的"17 tags"就是这一列，不是 bib 列） |

集合比对：`bib` 键集 == `main.tex` == `main.aux` == `main.bbl` == `main.md`，**五个口径的集合完全相同**，未被引的 bib 条目 0 条、引用了但 bib 里没有的键 0 个（\nocite 不存在）。`main.blg` 报 `You've used 16 entries` 且 `warning$ -- 0`，与上表独立一致。
所以 `paper/tex_audit.md` 那句"bib entries cited: 16 of 16"**本轮独立复核成立**；真正的风险不在键集对齐，而在 §1/§2 的字段（4 个空 `pages` + 1 个空 `volume`）与 §4 的年份口径。

---

## 6. 一句话给合并动作

- 合入 §3 的 5 个替换块（4 个补页/文章号、1 个补卷号，`hamada2011c60au` 顺带修题名），重跑 bibtex 三步编译并让 `tools/md2tex.js` 重新生成 `tex_audit.md`。
- 你只需再拍两件事：**ACS 两条取 2018/2023 还是 2019/2024**（§4.1），以及**是否按 JCTC 模板改期刊名缩写体例**（§4.2，我未能取到官方规则的第一手，不编）。
