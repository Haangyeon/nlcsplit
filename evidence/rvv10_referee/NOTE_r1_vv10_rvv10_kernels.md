# R1 · VV10 与 rVV10 的核形转写（来源一，闸门未过）

> 目的：方案书 `paper/notes/PLAN-20261012-rvv10-kernel.md` 的 R1 要求**同一公式在两个独立来源逐字一致**
> 才允许进 R2 写代码。本件是**来源一**的转写与出处登记。**R1 门未过，本件不构成可写进正文的依据。**

## 一、来源一是什么

- 文件（本机已下载）：`scratch/lit/fulltext/mardirossian2017_b97m_rv.pdf`，208120 字节，PDF 1.5。
- 抓取地址：`https://eprints.soton.ac.uk/id/eprint/403871/1/paper_accepted_manuscript.pdf`（接受稿，OA）。
- 题名（按检索结果登记，**卷/页/DOI 待 Crossref 逐条核**，本仓规矩：bib 条目必须过 Crossref）：
  *Use of the rVV10 Nonlocal Correlation Functional in the B97M-V Density Functional:
  Defining B97M-rV and Related Functionals*，Mardirossian, Pestana, Head-Gordon 等，2017。
- 关键参考文献（同一 PDF 末尾原文行，可直接复查）：
  - ref 19 = Vydrov, Wu, Van Voorhis, *Self-Consistent Implementation of a Nonlocal van der Waals
    Density Functional with a Gaussian Basis Set*, J. Chem. Phys. **129**, 014106 (2008)
    ⇒ 与本项目同一 regime（**高斯基组**下的 VV10 自洽实现）。
  - ref 20 = Sabatini, Gorni, de Gironcoli, *Nonlocal van der Waals Density Functional Made Simple
    and Efficient*, Phys. Rev. B **87**, 041108 (2013) ⇒ VASP 的 rVV10 引的就是它。
  - ref 16 = Q-Chem 4（本文所有数都是 Q-Chem 开发版算的 ⇒ Q-Chem 是这一族的参照实现）。
  - ref 23 = ONETEP 已实现 B97M-rV（周期性线性标度码，另一个潜在裁判）。

## 二、转写下来的公式（PDF 第 2 页，式 (1)–(7)）

VV10 的非局域关联能与其核：

```
E^VV10 = ∫ dr ρ(r) [ (1/32)(3/b²)^{3/4} + (1/2) ∫ dr' ρ(r') Φ(r,r') ]      (1)
Φ      = -(3/2) ( g g' (g+g') )^{-1}                                       (2)
g      = ω₀ R² + κ ,   R = |r - r'|                                        (3)
ω₀     = ( C |∇ρ/ρ|⁴ + (4π/3) ρ )^{1/2}                                    (4)
κ      = ( 3πb / (576π)^{1/6} ) ρ^{1/6}                                    (5)
```

⇒ 式 (2)(3) 与本仓 `nlcsplit/nlc.py:6-8` 文档串里的
`Phi = -3/(2 g g'(g+g'))`、`g = w0(r) R² + kappa(r)` **逐字同形**；
`nlc.py:39-40` 的 `w0 = sqrt(C σ²/ρ⁴ + 4πρ/3)`、`kap = b(3π/2)(ρ/9π)^{1/6}` 对应 (4)(5)。

rVV10：**差别在核本身**，原文两句是关键（逐字引）：

> "The difference between the VV10 and rVV10 NLCFs **originates in the nonlocal correlation kernel**."
> "Sabatini and coworkers **retained the value of C**, as well the exchange and correlation functionals,
> switched -V with -rV, and **optimized b = 6.3** on the S22 dataset, to define the rVV10 density functional."

并给出改写式与简化核：

```
Φ  = -(3/2) κ^{-2} κ'^{-3/2} ( (g g'/κκ')^{-1} ( sqrt(κ/κ') + sqrt(κ'/κ) )^{-1} ...   (6)
Φ* = -(3/2) κ^{-3/2} κ'^{-3/2} ( (g g'/κκ') + (g+g')/κκ' )^{-1}                        (7)
```

⚠️ **式 (6)(7) 的括号结构是从渲染页图像里读的，我没有把握逐字正确。**
实现前必须用来源二（CP2K/GPAW/ONETEP 源码里的 rVV10 kernel，或 Sabatini PRB B 87, 041108 原文式）
逐字核对。**这条没做完之前，R2 一行代码都不写。**

## 三、这份来源顺手给的外部锚点（将来验实现用）

PDF 表 IV：S22 结合能（kcal/mol，Ref = S22B 参考值）

| 复合物 | Ref | rPW86PBE | VV10 | rVV10 | rVV10* | B97M-V | B97M-rV |
|---|---|---|---|---|---|---|---|
| CH₄ 二聚体 | −0.53 | 0.07 | −0.45 | −1.50 | −1.39 | −0.44 | −0.46 |
| 苯–H₂O (C_s) | −3.28 | −1.85 | −3.34 | −3.41 | −3.29 | −3.14 | −3.21 |
| 苯–NH₃ (C_s) | −2.31 | −0.80 | −2.32 | −2.40 | −2.27 | −2.18 | −2.25 |
| NH₃ 二聚体 | −3.13 | −2.72 | −3.45 | −3.48 | −3.41 | −3.11 | −3.14 |

⇒ 同一半局域泛函下 VV10 与 rVV10 的**总结合能差**是可查的（苯–H₂O 差 0.07，CH₄ 差 1.05）
⇒ 将来实现 rVV10 后，可以拿这类 published 数做**总量级**的外部校验（不是 E(C,NL) 分项，弱一些但独立）。

## 四、一个改变施工顺序的发现（省掉一整块工作）

**CP2K 同时内置 VV10 与 rVV10 两种核**（手册 `NON_LOCAL` 段把 rVV10 明列为允许值）。
⇒ **"PySCF 的 SCAN_RVV10 是不是真 rVV10"这个缺陷判定，不需要我先实现核**：
   同一套 CP2K 里跑 VV10 与 rVV10 两档，再与 PySCF 的 `scan_rvv10` 对，就能把"形式差"与"参数差"分开。
⇒ 我自己实现 rVV10 核（R2）真正的用途是**方法普适性**那一档（JCTC 的 C1：把归属机器套到 rVV10 族上），
   它是"要不要做 JCTC"的问题，不是"有没有缺陷"的问题。施工顺序按这个改：**R4 先行，R2 随后按需。**

## 五、R1 还缺什么

1. **来源二**：式 (7) 的逐字核对（CP2K 源码 / Sabatini 原文 / GPAW 源码，任一）。
2. Crossref 核：这份 PDF 的 DOI/卷/页，以及 ref 19/20 的条目（要进 `paper/references.bib` 的话）。
3. 若将来要写"某程序实现不一致"：仍需两家用**同一密度同一基组**同向 + 原始定义式逐式核（红线不变）。
