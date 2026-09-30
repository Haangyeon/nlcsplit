# D — P2 裸串 → BibTeX 映射与核实登记表

**文档目的**：`paper/p2.md` 的先例引用至今是正文里的裸串（形如 `[Vydrov & Van Voorhis 2009, PRL 103, 063004]`），
没有进任何 bib 文件。本表把每一处裸串原文照抄，登记它对应的 bib key、DOI 与核实状态。
新建的文献库是 **`paper/references-p2.bib`**（24 条）。

**本表不改动 `paper/p2.md`**（该文件正由另一代理审计，任何字符级改动都会与它冲突）。
表中"稿件原文"列就是唯一事实来源；需要落稿时由 p2 的作者按本表自行替换。

| 项 | 值 |
|---|---|
| 登记日期 | 2026-09-30（UTC） |
| `paper/p2.md` 快照 | 25732 字节，MD5 `44679158f51286f47fb3f5eacec5037f`，mtime 2026-09-30 12:49 |
| `paper/references-p2.bib` | 24 条（18 条来自 p2 §1 裸串 + 6 条 p2/主篇共用），键名风格与 `paper/references.bib` 一致（姓+年份+短词；同一文献已存在于 references.bib 时复用同键） |
| 元数据核验途径 | Crossref `https://api.crossref.org/works/<doi>`（逐条 DOI 精确回查）；arXiv `https://export.arxiv.org/api/query?id_list=<id>`（仅 Laikov 预印本）。UA `refcheck/1.0 (mailto:haangyeon@snnu.edu.cn)`，请求间隔 0.25 s |
| 未使用的手段 | 没有用开放索引的主题检索来判"存在/不存在"（召回实测不合格，见 `RESEARCH-20260929-lit.md` §9）；条目字段一律取 DOI 回查所得 |

状态图例：
- **VERIFIED** —— DOI 回查成功，且 作者/年份/期刊/卷/页 与委托单或稿件裸串一致。
- **VERIFIED / 稿件字段不符** —— 文献本身核实无误，但 p2 裸串里某一字段（页码、版本日期）与 API 记录不一致。**这是稿子要改的地方，不是 bib 的问题。**
- **VERIFIED (arXiv)** —— Crossref 无此记录（预印本未进 Crossref），元数据来自 arXiv API。
- **查无此文（已删，勿复原）** —— 见 §C。

---

## A. p2.md 里的裸串（原文照抄）→ bib key → DOI → 状态

> 换行：p2.md 用约 90 列硬换行，下表把跨行裸串合并成单行照抄，合并只删换行符、不改任何字符。
> 行号是本快照（MD5 见上）的行号；p2.md 被另一代理改动后行号会漂，**以原文串为准**。

| # | 稿件原文（照抄） | 行 | bib key | DOI | 状态 |
|---|---|---|---|---|---|
| A1 | `[Vydrov & Van Voorhis 2009, PRL 103, 063004]` | 64 | `vydrov2009vv10` | 10.1103/physrevlett.103.063004 | VERIFIED |
| A2 | `[same authors 2010, JCP 133, 244103; Sabatini, Gorni & de Gironcoli 2013, PRB 87, 041108]` 之前半 | 65 | `vydrov2010simple` | 10.1063/1.3521275 | VERIFIED（"same authors" 不是可引用串，须换成显式 key） |
| A3 | 同上之后半 | 65 | `sabatini2013efficient` | 10.1103/physrevb.87.041108 | VERIFIED |
| A4 | `[Lazić et al. 2010, CPC 181, 371-379, doi:10.1016/j.cpc.2009.09.016, JuNoLo]` | 66–67 | `lazic2010junolo` | 10.1016/j.cpc.2009.09.016 | VERIFIED（6 名作者，`et al.` 对应 Lazić 等；卷/页/DOI 全对） |
| A5 | `Laikov's preprint "Nonlocal van der Waals density functional made faster" [arXiv:2511.04169, v2 of 2026-09-30]` | 68–69 | `laikov2026faster` | 无 DOI（arXiv:2511.04169） | VERIFIED (arXiv) / **稿件字段不符**：v1 = 2025-11-06，**v2 = 2026-01-19**，API 无 v3（2026-09-30 查询）⇒ "v2 of 2026-09-30" 里的日期不是 v2 的日期 |
| A6 | `[noloco, Nabok, Puschnig & Ambrosch-Draxl 2011, CPC 182, 1657-1670]` | 81–82 | `nabok2011noloco` | 10.1016/j.cpc.2011.04.015 | VERIFIED / **稿件字段不符**：Crossref 记 182, **1657-1662**，稿写 1657-1670（bib 按 API 写 1657-1662） |
| A7 | `[Schwegler, Challacombe & Head-Gordon 1998, J. Chem. Phys. 109, 8764-8769, doi:10.1063/1.477546; …]` 之前半 | 84–85 | `schwegler1998multipole` | 10.1063/1.477546 | VERIFIED |
| A8 | 同上之后半 `Dehnen 2002, J. Comput. Phys. 179, 27-42, doi:10.1006/jcph.2002.7026` | 85–86 | `dehnen2002hierarchical` | 10.1006/jcph.2002.7026 | VERIFIED（卷/页/年全对）。⚠ 题名按 Crossref 存录是 `A Hierarchical (N) Force Calculation Algorithm`，返回的 title 字段里没有 "log"；bib 未凭记忆补字，proof 时对出版页再确认一次 |
| A9 | `the "Linear Scaling Hierarchical Integration Scheme for the Exchange-Correlation Term" of Burow & Sierka [JCTC 7, 3097-3104, 2011]` | 89–91 | `burow2011hierarchical` | 10.1021/ct200412r | VERIFIED（稿中引号内题名是 API 全题名的**前缀截断**，全题名为 "…Exchange-Correlation Term **in Molecular and Periodic Systems**"；不算错，但加引用后建议写全） |
| A10 | `[Lambrecht & Ochsenfeld 2005, JCP 123, 184101, and Lambrecht, Doser & Ochsenfeld, same volume 184102; Doser et al. 2008, PCCP 10, 3335]` 第一 | 94 | `lambrecht2005estimates` | 10.1063/1.2079967 | VERIFIED |
| A11 | 同上第二（"same volume 184102"） | 94–95 | `lambrecht2005screening` | 10.1063/1.2079987 | VERIFIED（123 卷确认，"same volume" 成立） |
| A12 | 同上第三 `Doser et al. 2008, PCCP 10, 3335` | 95 | `doser2008tighter` | 10.1039/b804110e | VERIFIED（作者实为 Doser, Lambrecht, Ochsenfeld；`et al.` 成立。Crossref 的 page 字段只有起始页 3335，bib 未自行补末页） |
| A13 | `[Engblom 2011, Appl. Numer. Math. 61, 1096-1102, doi:10.1016/j.apnum.2011.06.011]` | 96–97 | `engblom2011wellseparated` | 10.1016/j.apnum.2011.06.011 | VERIFIED |
| A14 | `[Luty et al. 1994, Mol. Simul. 14, 11-20, doi:10.1080/08927029408022004; …]` | 102–103 | `luty1994pppmesh` | 10.1080/08927029408022004 | VERIFIED |
| A15 | `Petersen 1995, J. Chem. Phys. 103, 3668-3679, doi:10.1063/1.470043` | 103 | `petersen1995pmesh` | 10.1063/1.470043 | VERIFIED |
| A16 | `Deserno & Holm 1998, J. Chem. Phys. 109, 7678-7693, doi:10.1063/1.477414` | 104 | `deserno1998meshup` | 10.1063/1.477414 | VERIFIED |
| A17 | `Gumerov & Duraiswami 2008, J. Comput. Phys. 227, 8290-8313, doi:10.1016/j.jcp.2008.05.023` | 105 | `gumerov2008fmmgpu` | 10.1016/j.jcp.2008.05.023 | VERIFIED |
| A18 | `Kohnke, Kutzner & Grubmüller 2020, JCTC 16, 6938-6949, doi:10.1021/acs.jctc.0c00744` | 106 | `kohnke2020gmxfmm` | 10.1021/acs.jctc.0c00744 | VERIFIED |

委托单给的 17 条 DOI：**17/17 全部回查成功**，作者/年份/期刊/卷与委托单一致；
唯一的字段级冲突是 A6 的页码（稿 1657-1670 → API 1657-1662），另有 A5 的版本日期（稿 2026-09-30 → arXiv v2 = 2026-01-19）。
17 条里 **5 条** Crossref 的 `page` 为空，`pages` 取自 `article-number`（A1、A2、A3、A10、A11），其余 12 条用 `page` 字段；
这与 references.bib 现有做法一致。

---

## B. p2 里只点名、没有裸串的条目（本轮补建，P2 与主篇共用）

| 稿件原文（照抄） | 行 | bib key | DOI | 状态 |
|---|---|---|---|---|
| `PySCF 2.12.1, OMP_NUM_THREADS=4`（原句含反引号包裹的 `OMP_NUM_THREADS=4`） | 276 | `sun2020pyscf` | 10.1063/5.0006074 | VERIFIED（Crossref 里**不存在** 2.12 版专属论文；按 title 检索 PySCF、限 2024 年以后共 5 条命中，其中没有一条是以 2.12 为对象的软件论文，最接近的只有 `pu2025pyscf`（硬件/算法篇）。软件版本号只能写进正文/软件表，bib 里没有为它编造 DOI） |
| 同上（`§7 Condition 1 is structural for VV10 as implemented in PySCF`） | 360 | `sun2018pyscf` | 10.1002/wcms.1340 | VERIFIED（原始框架论文；Crossref issued=2017 网络首发、published-print=2018-01，bib 取 2018） |
| 同上（可选第三条） | — | `pu2025pyscf` | 10.1063/5.0285025 | VERIFIED（APL Comput. Phys. 1, 016101 (2025)，PySCF 硬件/算法增补篇；是否引用由作者定，P2 现文不需要它） |
| 主篇 `libxc … exports \`xc_nlc_coef\` and nothing else`（p2 未点名 libxc） | — | `lehtola2018libxc` | 10.1016/j.softx.2017.11.002 | VERIFIED（SoftwareX **7** (2018) **1-5**，与委托单给的卷/页/DOI 完全一致） |
| 主篇 `eight S22 complexes at official GMTKN55 geometries` | — | `goerigk2017gmtkn55` | 10.1039/c7cp04913g | VERIFIED（PCCP 19, 32184-32215, 2017；键与 references.bib 已有条目同名同 DOI，未另起新键） |
| `compact dimers (S22) have no inter-block region that is both distant and negligible.` | 356 | `jurecka2006s22` | 10.1039/b600027d | VERIFIED（PCCP 8, 1985-1993, 2006 —— S22/S22c/S66 数据库的正式出处） |

---

## C. 查无此文 / 已被否证（防"复原"记录）

| 条目 | 状态 | 处置与依据 |
|---|---|---|
| **"Dehnen 2014"**（曾出现在 p2.md §1 分层方法那句里） | **该句引用无依据 —— 已删，勿复原** | 判定依据不是本轮做的：2026-09-30 主线逐条回查时确认此串系凭记忆造出，已删（本轮只复核稿件现状：`paper/p2.md` 本快照里 "Dehnen 2014" 出现 **0 次**，"Dehnen 2002" 出现 **1 次** = 本表 A8）。**但要注意一个反向坑**：本轮补查发现 Crossref 上**确有** Walter Dehnen 的 2014 年 FMM 论文 —— 10.1186/s40668-014-0001-7, *Computational Astrophysics and Cosmology* **1**, art. 1 (2014，issued 2014-09-11，单作者 Walter Dehnen；Crossref 的 page 字段为空，article-number = 1，所以本轮不写页码范围)，"A fast multipole method for stellar dynamics"。它是天体 N-body 的 FMM，**不是** p2 那句的对象（分子库仑积分/精确交换的分层多极可接受性判据），所以不能拿它把原句补回来；要以它为引，必须先改写句子语境。本轮另按 author=Dehnen+Frommer / title 截断式检索，未能在 Crossref 里定位任何 Dehnen 的 2014 年电子结构积分论文 |
| 委托单给的 S22 定位符 `JCP 2005, 123, 054103 前后` | **定位符指向别的论文，不能用来当 S22 引** | 走 Crossref 期刊路由（ISSN 0021-9606，vol 123 issue 5，日期 2005-08-01）逐条比对 article-number：123 卷 054103 = **10.1063/1.1992483，D. Wu & D. A. Kofke, "Phase-space overlap measures. I. Fail-safe bias detection in free energies calculated by molecular simulation"**，与非共价基准集无关。S22 用 B 表最后一行（10.1039/b600027d） |
| 委托单里 "PySCF 2.12 版相关论文" | **Crossref 无此文** | 已按 title/bibliographic 两种检索 + 2024 年起时间过滤查证：没有任何一条以 2.12 为对象的软件论文。可作软件引用的只有 2018（框架）、2020（近期发展）、2025（APL 硬件/算法篇）三篇，其余命中都是模块论文（PyQMC、可微分量子化学等）。版本号写进正文/软件表（`PySCF 2.12.1`），bib 里不给它编 DOI |
| GMTKN55 的作者猜测（"Keen & …？Kozarieva/Kardas？"） | **猜测不成立** | 标题含 GMTKN55 的原始数据库论文是 **Goerigk, Hansen, Bauer, Ehrlich, Najibi & Grimme, PCCP 19, 32184-32215 (2017)**，10.1039/c7cp04913g（回查命中，作者与委托单的两种猜测都不同）。检索里出现的 Kesharwani/Karton/Sylvetsky/Martin、Gould、Bryenton/Johnson 都是**后续再评估/子集篇**，不是 GMTKN55 本身 |
| p2.md §1 末尾 "Four method names carried in our own earlier notes could not be located in any of five indexes" | 与本轮无关，无需 bib | 那四个方法名在现文里已不出现（p2.md 全文检索：0 次），保持现状即可 |

---

## D. 交给 p2 作者的待办（本表不代做）

1. A6 页码：`1657-1670` → 按 Crossref 改 `1657-1662`（或核对纸刊后指出 API 有误，二选一，不能并存）。
2. A5 版本日期：`v2 of 2026-09-30` → arXiv 记录是 **v2, 2026-01-19**；2026-09-30 是取回日期。另外记忆条目里"2026-09-30 出 v2"同样与 API 不符，一并纠正。
3. A5 正文那两个数（103.6 µEh 的 XeXe 势阱偏差、"below 18 %" 的键能）：arXiv 摘要里**两个都不存在**（摘要没有任何数值），它们只能来自正文表格。引之前必须回原文重读，元数据核验覆盖不到这一点。
4. A2 的 "same authors"、A8/A9 的 "JCP" 撞名说明句：换成 bib key 之后，§1 里那句"两个 JCP 是不同期刊所以特意拼全"的说明需要重新看一眼是否还成立（*J. Chem. Phys.* 与 *J. Comput. Phys.* 的区分在参考文献表里由 `journal` 字段承担）。
5. 替换裸串时 `paper/references-p2.bib` 与 `paper/references.bib` 有 4 个键同名同 DOI（`vydrov2009vv10`、`vydrov2010simple`、`lazic2010junolo`、`goerigk2017gmtkn55`）；P2 单独编译只喂 references-p2.bib 即可自洽，若两库同时进同一工程需去重。

## E. 复核命令（本表全部结论可重跑）

```bash
UA='refcheck/1.0 (mailto:haangyeon@snnu.edu.cn)'
# A 表 17 条 DOI + B 表 6 条
for d in 10.1103/physrevlett.103.063004 10.1063/1.3521275 10.1103/physrevb.87.041108 \
         10.1016/j.cpc.2009.09.016 10.1016/j.cpc.2011.04.015 10.1063/1.477546 \
         10.1006/jcph.2002.7026 10.1021/ct200412r 10.1063/1.2079967 10.1063/1.2079987 \
         10.1039/b804110e 10.1016/j.apnum.2011.06.011 10.1080/08927029408022004 \
         10.1063/1.470043 10.1063/1.477414 10.1016/j.jcp.2008.05.023 10.1021/acs.jctc.0c00744 \
         10.1063/5.0006074 10.1002/wcms.1340 10.1063/5.0285025 10.1016/j.softx.2017.11.002 \
         10.1039/c7cp04913g 10.1039/b600027d; do
  curl -s -H "User-Agent: $UA" "https://api.crossref.org/works/$d" \
    | python -c "import json,sys;m=json.load(sys.stdin)['message'];print(m['DOI'],(m['issued']['date-parts'][0][0]),(m.get('title') or [''])[0][:60],'|',m.get('volume'),m.get('page'),m.get('article-number'))"
  sleep 0.25
done
# A5（Laikov 预印本；v1/v2/不存在的 v3 各查一次）
curl -s -H "User-Agent: $UA" "https://export.arxiv.org/api/query?id_list=2511.04169v1,2511.04169v2,2511.04169v3"
# C 表（JCP 123 卷 054103 到底是哪篇）
curl -s -H "User-Agent: $UA" "https://api.crossref.org/journals/0021-9606/works?rows=1000&select=DOI,title,volume,issue,article-number,issued,author&filter=from-pub-date:2005-06-01,until-pub-date:2005-09-30"
```

原始 JSON 响应落在临时目录（`%LOCALAPPDATA%\Temp\p2_bib_batch1.json` 等），**临时目录会被清，不作为存档**；
可复核的存档就是本表 D/E 两节 + `paper/references-p2.bib` 头注里的来源说明。
