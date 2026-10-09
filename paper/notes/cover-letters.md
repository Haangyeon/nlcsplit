# 投稿附函草稿（三份稿各一封）— 2026-10-01

本文件不随包发布（`paper/**` 在导出时排除）。里面**不填**任何我没有一手依据的东西：
编辑姓名、审稿人建议、二作的贡献分工、日期，全部留成 `PENDING` 由作者给。
红线不变：这些文件只写出来给作者过目，**任何投递/粘贴到投稿系统的动作都要作者当次说"发"**。

---

## 1. P1 → J. Chem. Theory. Comput.（Article）

Dear Editor,

We would like to submit our manuscript, **"Pair Attribution of the VV10
Nonlocal-Correlation Term, and the Grid-Partition Dependence It Inherits"**, for
consideration as an Article in the Journal of
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
- The pair index has a **measured price**, and we report it as a cost rather than a benefit.
  A certified block-pair screening scheme built on a proved upper bound was timed against the
  exact sum over 33 screened/exact pairs in two independent windows: none was faster, because
  the tightest certificate obtainable at atom-pair granularity in a real dimer is loose by a
  factor of 2.4e5 relative to the quantity it would have to decide on. We did not have a
  separate paper in it, and we did not fold it into a footnote either.

Because the claim is about a decomposition, we spent as much effort on making the parts
checkable as on the decomposition itself: the same quantity computed by ORCA 6.0.1 on all
eight systems, a partition-free exact reference for the attribution step, and a
CCSD(T)/6-31G* counterpoise anchor for the binding energies of all eight complexes,
computed in both PySCF and ORCA and agreeing to three decimal places in kcal/mol, with the
ghost-function construction itself checked part by part against the basis dimension each
program reports. The anchor also carried a correction we would rather you read here than
find in a review: an earlier version of the coupled-cluster script evaluated each monomer in
its own basis, so the column it labelled counterpoise held the uncorrected difference, while
the density-functional column beside it had always been corrected. Fixing that changed the
arithmetic of the whole comparison, and we can show the change is attributable to the fix
alone - every complex energy in the re-run matches the archived one to 0.0e+00 Ha across two
machines, so only the monomer side moved. A second mismatch of the same kind was found by the
same kind of device: a job that has to reproduce an archived value before it may spend cluster
time refused, because three cells of the density-functional column had been computed in PySCF
2.14.0 while the other five were in 2.12.1. Re-running one script on one machine with the release
as the only variable reproduces both sets and attributes the entire difference to how many
integration points a given release attaches to atoms that carry basis functions but no nuclear
charge. On the corrected anchor, and in one environment, the functional's deviation
from frozen-core CCSD(T) is negative on all eight complexes, -0.450 to -3.412 kcal/mol, and
the two things that stop it being read as a verdict are measured rather than asserted:
changing only the integration grid moves a deviation by up to 1.217 kcal/mol, and changing
only the basis moves the anchor by 0.081-0.547 kcal/mol, in directions that are not even
consistent from one complex to the next. Where a check failed we say so in the text; the manuscript
carries an appendix that maps every quoted number to an archived standard output in the
repository, and fifteen release gates re-verify that mapping on every rebuild.

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

## 2. P2 → J. Chem. Phys.（**已作废：2026-10-02 并入 P1 §3.6，不单独投**）

本节留档不投递。P2 的三组测量（两窗墙钟 33 对无一更快、最小块界 197.96 Ha 对 −8.34e-4 Ha
松 2.4e5 倍、达标精度下仍算 84.4-95.4% 远场点对）现在是 `paper/main.md` §3.6 的全部内容，
附函里也作为"我们把自己的负结果报出来"卖进 JCTC。同一批文字再投第二个期刊会在同一批审稿人
面前构成重叠投稿，所以这封信标记为作废；p2.md §4（哪种几何判据根本筛得动）与 §5（紧性从哪来）
没有被压缩进 §3.6，若将来真要第二篇算法文，从那两节重新起稿而不是复用这封信。

以下为作废前的原信正文，仅留档：

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
than asserting it: the suite collects 69 tests, of which the distributed wheel carries 49 -
the 20 that stay behind belong to a frozen control implementation that is deliberately not
shipped, and shipping their test without it would be a collection-time ImportError - a wheel
whose members are re-tested out of tree, fifteen release gates each with a bidirectional
self-test, and agreement with ORCA 6.0.1 on the reported quantity for eight systems.

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
