---
title: 'nlcsplit: fragment and pair resolution of the VV10 nonlocal-correlation energy'
authors:
  - name: Angran Xia
    orcid: TBD  # 需本人提供，禁止代填
    affiliation: 1
    corresponding: true  # 待本人确认
  - name: TBD  # 若有第二作者（含 IDE 侧贡献者），由本人指定署名与贡献
    orcid:
    affiliation: 1
affiliations:
  - name: 'Shaanxi Normal University, Xi'an, China  # 院系与官方英文全称由本人补，此处刻意不猜'
    index: 1
date: 29 September 2026
bibliography: references.bib  # 尚未生成；DOI 已在 §Sources 逐条回查
keywords:
  - nonlocal correlation
  - VV10
  - density functional theory
  - energy decomposition
  - PySCF
---

*SoftwareX / JOSS shape. Numerical claims carry a `[S#]` tag into
`paper/main.md` and `MAIN-skeleton.md`; scripts named here are in the repository
and their archived stdout under `nlcsplit/logs/` is the source. **The front matter
above contains fields only the author can supply (ORCID, corresponding status, exact
affiliation string, co-author list); they are marked rather than filled.**
`references.bib` now exists (16 entries, up from 13 today: VV10's own two papers and
the Hyldgaard-Berland-Schroeder xc-hole interpretation were missing), and every DOI in
it has been reverse-checked against Crossref by DOI and against Web of Science, not by
title search (see `RESEARCH-20260929-lit.md` §9 for why that distinction mattered
here).*

## Abstract

VV10-type nonlocal correlation is evaluated in production electronic-structure
codes by collapsing a double sum over grid-point pairs into per-point values,
which discards the pair index. `nlcsplit` evaluates that double sum explicitly
and attributes each grid point to atoms and fragments through a real-space
partition, so the nonlocal contribution separates into intra-fragment and
inter-fragment pair blocks that sum back to the total to machine precision. The
package is pure Python and NumPy on top of PySCF, released under Apache-2.0,
contains no GAMESS source, and reproduces every number it documents from a
single named script.

## 1. Motivation and statement of need

Functionals that pair a range-separated hybrid with the VV10 nonlocal correlation
term - ωB97X-V and ωB97M-V in particular [S11] - are a routine choice for
non-covalent interactions. Their nonlocal contribution,

    E_NL = ½ ∫∫ ρ(r) ρ(r') Φ(r, r') d³r d³r',

is a two-centre sum, but what users get back is one number per grid point, or one
total. When an interaction energy needs to be interpreted per fragment, the
available options stop at the semi-local part: electrostatics, exchange,
polarisation and charge transfer can be resolved by EDA schemes, whereas the
nonlocal term is carried as an undivided block. The closest published treatment
computes exactly that block as a whole and asks whether it is accurate
(Dasgupta, Palos, Pan, J. Chem. Theory Comput. 2023, 10.1021/acs.jctc.3c00903);
the closest published explicit evaluation, JuNoLo (Lazić et al, Comput. Phys.
Commun. 181, 371 (2010), 10.1016/j.cpc.2009.09.016), sums the double sum directly
but targets an improved total energy and explicitly recommends itself for bonded
systems "where one cannot tell apart fragments". Neither resolves the term into
fragment pairs. That gap is what this package fills, and it is a capability gap
rather than an accuracy gap: on the same grid and density our sum agrees with the
native PySCF kernel to ~1e-8 Ha [S9].

## 2. Method overview

**Kernel and convention.** `w0 = sqrt(C|∇ρ|⁴/ρ⁴ + 4πρ/3)`,
`κ = b(3π/2)(ρ/9π)^(1/6)`, `g = w0(r_i)R² + κ(r_i)` with same-centre pairing,
`Φ = -3/(2 g g' (g + g'))`, and `E_NLC = ½∬ρρΦ + β∫ρ` with
`β = (1/32)(3/b²)^(3/4)`. Parameters are read from PySCF `nlc_coeff` rather than
hard-coded. Same-centre pairing is the convention that reproduces the native
kernel; the cross-pairing variant `g = w0(r_j)R² + κ(r_i)` is retained as a
definition-sensitivity control and raises monomer energies by 0.138 (water), 0.418
(argon) and 0.914 (benzene) kcal/mol [S5].

**Blocks and additivity.** `pair_energy(A, B)` returns the half block
½ Σ_{i∈A} Σ_{j∈B}; the inter-fragment term is reported as twice that, so
`E_nl = Σ_A intra[A] + Σ_{A<B} inter[A,B]` holds as an identity. Measured
residual: 0.0 to 3.5e-18 Ha [S2].

**Why decomposing only the double sum is exact.** β is a constant and ∫ρ is the
electron number, so the local term β∫ρ = βN cancels identically from any
superposition difference. Inter-fragment decomposition therefore needs no
convention for splitting a local energy density: it is a property of the double
sum alone [S3]. The flip side is reported as a limitation rather than hidden - the
absolute local term of one fragment is exactly β·N_A, so its scheme spread is β
times the spread of the Becke population, 3.0415 kcal/mol per electron, i.e.
0.300 kcal/mol for the water dimer [S12].

**Attribution.** Four real-space partitions reachable through the PySCF grid
machinery - Becke, Becke with the atomic-radius adjustment, Becke-Treutler and
Stratmann - plus a nearest-atom hard assignment on a common grid. A point may be
shared by more than one fragment; the factor matrix is exposed as
`partition_factors(mol, level, scheme) -> (coords, base_w, S[N, natm])`,
normalised so that `Σ_a S[i,a] = 1` pointwise. The function refuses to return
unless two internal assertions pass: normalisation, and `base_w · S[i, owner(i)]`
reproducing the weights that PySCF's own `get_partition` produces - an external
anchor against the same C kernel PySCF uses, not against a re-implementation in
this package. Measured: 4.4e-16 and 8e-13 respectively across four schemes and
three grid levels [S17].

**Far-field cut.** Points below `rho_floor = 1e-12` are dropped from the double
sum. Sweeping 1e-8 … 1e-16 changes the inter-fragment term by ≤5e-11 kcal/mol
while discarding 10.7-22.6% of points carrying ≤2.3e-6 electrons [S7], so the
threshold is an implementation detail rather than a parameter.

## 3. Software description

    nlcsplit/
      nlc.py           VV10 fields, pair_energy (gemm path), fragment_decomposition
      partition.py     four attribution schemes, partition_matrix, partition_factors
      geomlib.py       single source of geometry truth; internal-coordinate
                       assertions at construction; covalent-connectivity fragment
                       splitting; official GMTKN55/S22 loader
      step*.py         one script per table in the paper; stdout archived UTC-stamped
      figures.py       figures built from the JSON sidecar, never from log text
      tests/           kernel, regression, geometry and partition-factor suites
      examples/        quickstart plus two comparison checks

Dependencies: NumPy and PySCF. `partition.py` reaches into
`libdft.VXCgen_grid` through ctypes deliberately - it is the entry point that
`gen_grid.get_partition` itself uses, which is what makes the audit above external
rather than circular.

Representative output, produced by `examples/quickstart.py` (ωB97X-V/6-31G*,
water dimer, grid level 1, kcal/mol):

    inter[(0,1)] = -0.5237
    intra        = -3.5457 -3.7437
    E_nl         = -7.8130   E_loc = 60.8303   E_total = 53.0172

`E_nl` equals intra + intra + inter as required, and `E_total` may be compared
with the native kernel evaluated on its own reference grid, which gives 53.017
and 53.016 for this system and level (difference +0.002 kcal/mol, which is the
grid representation difference of section 3.1 of the companion text rather than
an algorithmic one) [S9].

## 4. Impact

The package makes three things checkable that previously were not. It gives a
number for how much of the nonlocal correlation is inter-fragment, which on eight
S22 complexes accounts for 0.92-1.08 of the frozen-density superposition
difference - association-time nonlocal correlation is almost entirely carried by
point pairs straddling the fragments [S2, S10]. It supplies the per-system
uncertainty that the attribution choice contributes (0.004-0.247 kcal/mol
absolute, 0.8-18.2% relative, unchanged across five basis sets and across grid
levels, with no ordering by interaction type or by system size), which is the error bar any future
use of such numbers must carry [S12]. And it produces evidence about the quantity
itself: ΔE_NLC ranges from 16% to 223% of ΔE_xc across one benchmark set, and
100% versus 54% for two geometries of the same benzene dimer, so the VV10 term
cannot be reported as "the dispersion energy" without qualification [S2].

## 5. Availability and quality assurance

Apache-2.0; no GAMESS source is included, linked or required - a claim checked by
scanning every file of the published tree (61 files at the time of writing) for
GAMESS source artefacts specifically, not for the word, which appears only in the
disclaimer. Every table in the companion text maps to one `step_*.py`, and archived
stdout is kept under a UTC-stamped filename. The test suite collects 18 tests in the
published tree (15 fast, 3 marked slow), including a naive triple-loop versus BLAS
comparison of the kernel, per-scheme additivity checks, and geometry guards that
assert bond lengths and angles at construction time.

Five export gates run locally on every rebuild (`node tools/make_public_repo.js`),
and each has fired at least once on a real defect rather than sitting idle:

| gate | what it checks | what it caught first |
|---|---|---|
| A | no GAMESS source artefacts (matched on source patterns, not on the word "gamess", which the disclaimer itself contains) | a permanent false positive on our own disclaimer |
| B | no credentials or internal network strings | a scrub that re-injected a proxy address into a comment |
| C | every `evidence/*/MANIFEST.sha256` reproduces byte-for-byte | a Windows path making `sha256sum` report six mismatches that were not there |
| D | every path cited by the companion text's provenance appendix is actually shipped | three citations that resolved to nothing in the published tree |
| E | every import in a shipped module is declared in `pyproject.toml` | `figures.py` importing matplotlib, which no dependency listed |

Gate D exists because the first three could only fail in one direction. A, B and C
catch material that should not be present; what actually went wrong repeatedly was
material that should have been present and was not - a cited stdout living only on a
remote machine, calibration scripts inside a gitignored directory. Those produce a
clean export and a reader holding a citation to nothing.

Release hygiene is specified end to end but **not yet fully executed**: the intended
procedure is a pip install into a separate environment followed by running the tests
from outside the source tree with `pytest --pyargs nlcsplit`. That procedure has
already earned its place - as a *specification* it led us to remove script-style
`test_*.py` modules from the package (which pytest collects and executes at import)
and to register the `slow` marker in package configuration rather than only in
repository configuration - but the clean-install run itself is still open, and so is
the check that `pip install .` leaves no undeclared import. What has been verified
locally is an out-of-tree import of the exported tree by path, which is weaker: it
found that `step_i_gridrepr.py` ran a full self-consistent-field sweep at import time
because it had no `__main__` guard, since fixed.

The continuous-integration workflow is written but has **never executed**, because
there is no remote repository yet. Reviewers should read it as intent. Writing it down
did produce one real fix: its PySCF version matrix interpolated as
`pip install "pyscf==>=2.13"`, which is not a valid requirement, so the second job
would have died at the install step.

Independent verification of the arithmetic now has a second program behind it. An
earlier version of this documentation withdrew an ORCA agreement because re-reading
the archived output found no separately reported nonlocal term - and that withdrawal
was itself wrong: the quantity is printed, under the label
`NL Energy, E(C,NL)`; searching for the words "nonlocal", "nloc" or "VV10" finds
nothing in an ωB97X-V output, and the `E(VV10-nl)` column that does match belongs to
the PT2 correlation of double-hybrid functionals, which is a different physical
quantity. With the label known, six ORCA 6.0.1 single points agree with the reported
ΔE_NLC to 0.0004 kcal/mol on the water dimer and 0.0416 kcal/mol on the benzene dimer
A, with the outputs and their SHA-256 manifest in the repository. A third, fully
independent implementation (Psi4, or libxc's `xc_nlc_vxc` through its own bindings)
is still outstanding, as is extending the anchor beyond 2 of the 8 systems.


## 6. Limitations

Quadratic cost in retained grid points, with no sub-quadratic approximation. One
attempt at a certified screening was built and measured this round, and rejected: at
the tolerance the companion text needs (1e-8 Ha absolute), the triangle-inequality
atomic-block bound prunes nothing on a 24-atom system - 0 of 300 atom-block pairs -
because the radius the bound subtracts is set by the far tail of each atom's density,
so the certified separation comes out zero for every pair, including the ones facing
each other across the inter-fragment gap. That is a statement about this particular bound, not about screening in
general, and it is recorded in `PROGRESS-nlcsplit.md` rather than quietly dropped.
Interpretation limited to the two-body and fragment-pair level. Results depend on
the choice of real-space partition to the extent quantified in section 4. VV10
only - the τ-dependent rVV10 form is not implemented. And it is not an energy
decomposition analysis: it does not separate electrostatics, exchange-repulsion,
polarisation or charge transfer.

---
### Sources
[S1] `RESEARCH-20260929-lit.md` · [S2] `nlcsplit/logs/step_h.json`,
`MAIN-skeleton.md` tables 2-3 · [S3] `step_f_dispersion.py` · [S5]
`step_e_kernel.py` · [S7] `step_d_floor.py` · [S9] `step_i_gridrepr.py`,
`logs/20260929T_step_i_gridrepr.out` · [S10] CentOS
`logs/20260928T213839Z_centos-step_h_l2cp.out` · [S11] Mardirossian and
Head-Gordon, PCCP 16, 9904 (2014), 10.1039/c3cp54374a (DOI reverse-checked) ·
[S12] `logs/20260929T003144Z_stepg-recompute.out` · [S17]
`tests/test_partition_factors.py`
