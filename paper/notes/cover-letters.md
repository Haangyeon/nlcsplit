# 投稿附函草稿（三份稿各一封）— 2026-10-01

本文件不随包发布（`paper/**` 在导出时排除）。里面**不填**任何我没有一手依据的东西：
编辑姓名、审稿人建议、二作的贡献分工、日期，全部留成 `PENDING` 由作者给。
红线不变：这些文件只写出来给作者过目，**任何投递/粘贴到投稿系统的动作都要作者当次说"发"**。

---

## 1. P1 → J. Chem. Theory. Comput.（Article）

Dear Editor,

We would like to submit our manuscript, **"Fragment-Resolved Nonlocal Correlation:
Pair Attribution of the VV10 Term"**, for consideration as an Article in the Journal of
Chemical Theory and Computation.

The VV10 nonlocal-correlation term is evaluated by production codes as a folded
per-point quantity, so the pair index that defines it is gone by the time the energy is
returned. The manuscript reports an explicit pair-resolved evaluation of the same double
sum, attributed to fragments through a real-space partition, and three things that follow
from measuring it rather than defining it:

- The nonlocal term is **not** a fixed fraction of the exchange-correlation change. It is
  16% of it for the water dimer, 97% and 52% for the two structures of the same benzene
  dimer, and on the methane dimer the nonlocal and semi-local parts carry opposite signs.
  Reporting the term as "the dispersion" is therefore unsupported at the level of the
  complexes most people use these functionals on.
- Association-time nonlocal correlation is carried almost entirely by grid-point pairs
  that straddle the fragments (0.92-1.08 of the frozen-density superposition difference).
- The residual uncertainty is the **choice of attribution scheme**, and it is per-system
  (0.004-0.247 kcal/mol absolute, 0.8-18.2% of the Becke value) with no pattern by
  interaction type. This is the number we would ask a reader to carry away.

Because the claim is about a decomposition, we spent as much effort on making the parts
checkable as on the decomposition itself: the same quantity computed by ORCA 6.0.1 on all
eight systems, a partition-free exact reference for the attribution step, and a
CCSD(T)/6-31G* anchor for the binding energies of three of them, computed in both PySCF and
ORCA and agreeing to three decimal places in kcal/mol. Where a check failed we say so in
the text; the manuscript carries an appendix that maps every quoted number to an archived
standard output in the repository.

The code is a standalone Apache-2.0 Python package (`nlcsplit`) built on PySCF and NumPy.
It contains no GAMESS source, despite the institution of our starting point. Repository:
PENDING (to be made public before acceptance). Archive DOI: PENDING.

The manuscript is original, has not been published, and is not under consideration
elsewhere. All authors have approved the submission. Suggested and excluded reviewers:
PENDING (author-supplied).

With regards,
Angran Xia (corresponding author) on behalf of both authors
School of Chemistry & Chemical Engineering, Shaanxi Normal University, Xi'an 710119, China

---

## 2. P2 → J. Chem. Phys.（或 JCTC，二选一，见 `PLAN-next.md` §3.5）

Dear Editor,

We submit **"Certified screening of the VV10 nonlocal-correlation double sum: what the
bound buys, and what it costs"** for consideration in the Journal of Chemical Physics.

This is a negative result, and it is the kind of negative result that is easy to get wrong
in one's own favour. We implemented a certified screening scheme for the quadratic double
sum that defines the VV10 nonlocal term - every pair of grid-point blocks either evaluated
exactly or replaced by a proved upper bound accumulated into one pre-declared error - and
then measured it. At the accuracy a fragment-pair decomposition requires, the bound is too
loose to skip work: 84.4-95.4% of far-field point pairs are still evaluated, and of 33
screened-versus-exact pairs sampled in two independent timing windows, none was faster than
the dense sum.

Three measurements explain it, and they are the reason we think the paper is worth a
reviewer's time rather than a footnote: the smallest block-pair bound in a real dimer
exceeds the quantity it is meant to judge by a factor of 2.4e5; every root box separation
is 0.0000 A, which puts a 0.0% ceiling on any geometric accept/reject rule; and refining
the bound by a dense-core/sparse-tail split moves the droppable fraction from 12.349% to
13.650%. We also record a criterion that looks monotone under refinement and is not - a
mass-weighted ball loses monotonicity on 18% of refinements - which we only know because we
counted. The screening ships off by default.

We were told in advance that a negative result is a hard sell, and we have tried to write
one that is at least falsifiable in both directions: every number above comes from an
archived run in the repository, and the four conditions under which certified screening
*could* win are stated so a reader can check that none of them holds here.

Code: `nlcsplit` (Apache-2.0, PySCF-based, no GAMESS source). Repository: PENDING.
Original work, not published or under consideration elsewhere; all authors approved.

With regards,
Angran Xia (corresponding author)

---

## 3. P3 → JOSS（软件投稿走 `paper.md`，本节是给人看的说明）

Dear Editors,

We submit **`nlcsplit`: fragment and pair resolution of the VV10 nonlocal-correlation
energy** as a JOSS submission.

Scope for the reviewer: the package evaluates the VV10 nonlocal-correlation double sum
with the grid-point pair index retained and attributes the result to atoms and fragments
through a real-space partition - something the production path (fold to per-point values)
cannot report. It is pure Python and NumPy on top of PySCF, Apache-2.0, and contains no
GAMESS source.

The `paper.md` we will generate from `paper/software.md` states the verification rather
than asserting it: 69 tests (49 fast, 20 slow), a published wheel whose members are
re-tested out of tree, thirteen release gates, and agreement with ORCA 6.0.1 on the
reported quantity for eight systems.

Repository URL: PENDING (public). Archive DOI: PENDING. Authorship and ORCIDs: PENDING.
No concurrent submission; both authors have approved.

Angran Xia (corresponding author)

---

## 投稿前必须补的空格（逐条对应 `PLAN-next.md` §3）

| 位置 | 缺什么 | 谁能给 |
|---|---|---|
| 三封信的 Repository | 仓库转公开后的 URL | 作者（§3.1） |
| 三封信的 Archive DOI | Zenodo 联动发布 | 作者（§3.3） |
| P1/P2 的 reviewer 栏 | 建议/回避审稿人 | 作者 |
| 三封信的署名块 | 两个 ORCID、二作邮箱、通讯标注 | 作者（§3.2） |
| P3 的 `paper.md` | JOSS 的 YAML front matter | 公开仓之后由我生成 |
