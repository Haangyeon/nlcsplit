# P0-a 先例接住段（草稿·台账）— 2026-10-11

> 第零波产物。放这里是因为它**还没进 `paper/main.md` 正文**。
> 出处核验：`evidence/bib_provenance/20261011T114318Z_p0a_precedents_crossref_summary.out`（+.rc=0、
> 原始 JSON `..._crossref_result.json`）。三条进了 `paper/references.bib`（25 → 28 条），第四条**没进**。

---

## 一、四条先例的核验状态

| # | 计划里的写法 | 核验结果 | 能不能引 |
|---|---|---|---|
| 1 | Chem. Rev. 2016 "atomic contributions **is not well-defined**" | 按卷页 116, 5038–5071 定位到 **Řezáč & Hobza**, *Benchmark Calculations of Interaction Energies in Noncovalent Complexes and Their Applications*, DOI 10.1021/acs.chemrev.5b00526（Crossref 有记录，无摘要） | 对象可引（`rezac2016bench`）。**逐字引用不可**——本机没有 ACS 全文，无法证实那句话是不是原文。要么作者翻 PDF 确认，要么改写成不帶引号的说法 |
| 2 | Lehtola & Marques 2022 "numerically ill-behaved" | DOI 10.1063/5.0121187，JCP 157, 174114（article-number），print=issued=2022，Crossref 有摘要 | 可引（`lehtola2022illbehaved`）。摘要自证了它讲的是"泛函在常用数值求积/求和规则下收敛不良"，**不是**分解不唯一 |
| 3 | Andrés 2019 "Nine questions on EDA" | DOI 10.1002/jcc.26003，JCC 40, 2248–2283，print=2019，30 位作者，Crossref 有摘要 | 可引（`andres2019ninequestions`）。摘要自证了"概念定义不精确 ⇒ 分区方案多元并存"这条 |
| 4 | Keller 2025 JCP "cannot be decomposed into atom-pair" | **Crossref 未定位**：四条主题检索 + 两条 author 检索（`Keller`、`Keller, Stefan`，限 2023-06 之后的 journal-article）全部命中不上同一对象，最佳题名相似度 0.057–0.247，且都不是这个主题 | **不建条目、不进正文**。要引它必须由作者给出可核对的出处（卷/页/DOI 之一）。计划里那句"审稿人会拿这条毙我们"目前是我方无法证实的说法，不能当依据写 |

计划 §五 待核那条"Lehtola 2022 被引 63"：Crossref 本次 `is-referenced-by-count = 44`（读数日期 2026-10-11T11:43Z）。
两个数口径不同（Google Scholar / WoS / Crossref 各自一套），**正文不许出现"被引 N 次"**，除非把口径与日期一起写。

---

## 二、草稿段落（英文，正文候选）

### A 段（放 §1 引入之后，接住"分区不唯一早就是常识"）

> That a decomposition into atom or fragment contributions is not uniquely defined is
> routinely stated rather than measured: it motivates the thirty-author interrogation of
> energy decomposition analysis, whose first question is precisely whether the imprecision
> of the underlying chemical concepts is what makes partition schemes proliferate
> [@andres2019ninequestions], and it recurs in benchmark reviews of interaction energies
> when atomic contributions are discussed [@rezac2016bench]. What has been missing is the
> number. Statements of non-uniqueness leave the size of the effect unspecified, and an
> unspecified effect can be dismissed as a matter of taste. Here we measure it for one
> term of one functional, on a fixed quadrature grid, across every attribution scheme that
> a practitioner can reach without leaving the standard tool chain.

### B 段（放 §3 末或 §4，把"求积"那条先例接进"归属"这条线）

> A related body of work warns that recent density functionals are numerically ill-behaved:
> total energies computed from tabulated atomic Hartree–Fock densities converge extremely
> slowly under the quadrature rules in common use [@lehtola2022illbehaved]. That failure is
> in the *quadrature*, and it is diagnosed by increasing the grid. Ours is in the
> *attribution*, and increasing the grid does not remove it: at every grid level we report,
> the inter-fragment term keeps a finite spread because the schemes disagree about which
> atom a grid point belongs to, not about how many points there are. The two defects are
> therefore complementary, and only the first has a cure that is already standard practice.

**这两段的可辩护性边界**：
- A 段只在 #2、#3 上做逐字可查的断言；#1 只作为"这类说法在综述里出现过"的指针，没引号、没复述原句。
- B 段最后一句（"increasing the grid does not remove it"）需要与正文既有的 level 扫描数据对上号——
  落笔前要把这一句的出处指到具体的表/图，不许凭本段的说法进正文。
- 两句都**不引用** Keller 那条，也不写"学界断言了十年、第一次有人给数"这种无原件的说法
  （"第一次"是全称否定，Crossref 的主题召回本来就测不出它，见 RESEARCH-20260929-lit §9/§11）。

## 三、要作者做的两件事

1. #1 那句话要不要当逐字引用：手边有 ACS 全文，翻 §里讲 atomic contribution 的那一段，
   原句贴回来（页码 + 原句），我再把它从"指针"升成"引用"。
2. #4 Keller：给出处，或者接受它不进正文。
