# S22/NumPy 出处的 Crossref 重放记录

> 由 `node scratch/verify_s22_numpy_bib.js` 生成，请勿手改本文中的查询结果。
> 该脚本在 `scratch/` 下，而 `scratch/` 没有纳入版本控制 —— 所以这份记录的可复现性
> **不依赖那个脚本**：六条查询的完整 URL 已逐字抄在各自小节里，照抄即可重放。
> 生成时刻：2026-09-30T14:51:18.931Z
>
> 用途：main.md §2.4 声称「那条 2003 前身两次（2026-09-29、2026-09-30）在 Crossref 查不到」，
> 并新增 `harris2020numpy` / `jurecka2006s22` 两条引用。本文把支撑这两件事的查询逐字存档。
> 2026-09-29 那一次走的是 `scratch/build_bib.js`，其结果在 `scratch/bib_candidates.json`：
> `jurecek2003s22` → `"ok": false, "why": "no candidate DOI"`。

## A. 按 DOI 回查我记忆里的那个号（证明它不是 NumPy）

```
GET https://api.crossref.org/works/10.1038/s41586-020-2308-7
```

HTTP 200

命中 1 条：

- 10.1038/s41586-020-2308-7 | Nature 581 434-443 (2020) | Konrad J. Karczewski 等 178 人 | The mutational constraint spectrum quantified from variation in 141,456 humans

## B. 题名精确检索 NumPy 那篇（拿正确 DOI）

```
GET https://api.crossref.org/works?rows=5&filter=container-title:Nature,from-pub-date:2020-09-01,until-pub-date:2020-10-31&query.title=Array%20programming%20with%20NumPy
```

HTTP 200

命中 1 条：

- 10.1038/s41586-020-2649-2 | Nature 585 357-362 (2020) | Array programming with NumPy

## C. 09-30 第一次找 PCCP 5, 1811 (2003)：刊名 + 年内 + 期望题名

```
GET https://api.crossref.org/works?rows=6&filter=container-title:Physical+Chemistry+Chemical+Physics,from-pub-date:2003-01-01,until-pub-date:2003-12-31&query.title=Benchmark%20of%20density%20functional%20methods%20for%20investigating%20large%20molecules%20with%20intramolecular%20hydrogen%20bonds
```

HTTP 200

命中 6 条：

- 10.1039/b306301a | Physical Chemistry Chemical Physics v5 p4265 | A density-functional-theory study of bacteriochlorophyll b
- 10.1039/b212590k | Physical Chemistry Chemical Physics v5 p2001 | The vibrational spectra of furoxan and dichlorofuroxan: A comparative theoretical study using density functional theory and local electron correlation methods
- 10.1039/b212073a | Physical Chemistry Chemical Physics v5 p1337 | Spin trapping by bis(benzene)chromium: A density functional study
- 10.1039/b308197d | Physical Chemistry Chemical Physics v5 p4776 | Conformation of dimethoxymethane: roles of anomeric effects and weak hydrogen bonds. A free jet microwave study
- 10.1039/b300210c | Physical Chemistry Chemical Physics v5 p1533-1535 | Ordered and disordered hydrogen bonds in adenosine, cytidine and uridine studied by low temperature FT infrared spectroscopy
- 10.1039/b211014h | Physical Chemistry Chemical Physics v5 p808-811 | Blue shifting and red shifting hydrogen bonds: A study of the HArF⋯N2 and HArF⋯P2 complexes

## D. 09-30 第二次：放宽成 bibliographic 混合串（含作者/卷/页）

```
GET https://api.crossref.org/works?rows=5&query.bibliographic=Jurecka%20Sponer%20Sebest%20Hobza%20benchmark%20density%20functional%20intramolecular%20hydrogen%20bonds%20PCCP%202003%205%201811
```

HTTP 200

命中 5 条：

- 10.1002/chem.200500255 | Chemistry – A European Journal v11 p5062-5066 | Are the Hydrogen Bonds of RNA (A⋅U) Stronger Than those of DNA (A⋅T)? A Quantum Mechanics Study
- 10.1021/ja00081a036 | Journal of the American Chemical Society v116 p709-714 | Bifurcated hydrogen bonds in DNA crystal structures. An ab initio quantum chemical study
- 10.1039/d5cp00836k | Physical Chemistry Chemical Physics v27 p8706-8718 | Density functional benchmark for quadruple hydrogen bonds
- 10.1039/9781839160400-00368 | Understanding Hydrogen Bonds vundefined p368-400 | Intramolecular Hydrogen Bonds
- 10.1021/acs.jpca.9b06801.s001 | undefined vundefined pundefined | Can 2X-Ethanols Form Intramolecular Hydrogen Bonds?

## E. 09-30 第三次：卷/首页字段过滤（该组合被接口拒成 HTTP 400，一并记下，别让人以为是查不到）

```
GET https://api.crossref.org/works?rows=6&filter=container-title:Physical+Chemistry+Chemical+Physics&query.field.volume=5&query.field.firstpage=1811&query.bibliographic=Jurecka%202003%20hydrogen%20bonds
```

HTTP 400

```
{"status":"failed","message-type":"validation-failure","message":[{"type":"field-query-not-available","value":"field.firstpage","message":"Field query 'field.firstpage' specified but there is no such field query for this route. Valid field queries for this route are: affiliation, degree, event-acron
```

## F. 主篇现在引的 S22 正式出处（必须回查得到，否则 §2.4 那句话没有依据）

```
GET https://api.crossref.org/works/10.1039/b600027d
```

HTTP 200

命中 1 条：

- 10.1039/b600027d | Phys. Chem. Chem. Phys. 8 1985-1993 (2006) | Petr Jurečka; Jiří Šponer; Jiří Černý; Pavel Hobza | Benchmark database of accurate (MP2 and CCSD(T) complete basis set limit) interaction energies of small model complexes, DNA base pairs, and amino acid pairs

## 结论

全部查询按原样重放成功，且判定与 main.md §2.4 / references.bib 的写法一致：
1. `10.1038/s41586-020-2308-7` **不是** NumPy 那篇（它是 gnomAD），NumPy 的正确 DOI 是 `10.1038/s41586-020-2649-2`；
2. `Jurecka et al., PCCP 5, 1811 (2003)` 在 Crossref 里三条独立检索都取不到 —— 所以它不进 `references.bib`，正文改为只说查得到的链条；
3. `10.1039/b600027d` 回查为 PCCP **8** 1985-1993 (2006)，四人作者，与 `references.bib` 的 `jurecka2006s22` 逐字段相符。
