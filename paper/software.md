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
0.329 kcal/mol for the water dimer on the official S22 geometry and 0.300 on the
constructed one (`nlcsplit/step_k_population.py`, whose two runs both assert that the
fragment populations sum to the electron number).

**Attribution.** Four real-space partitions reachable through the PySCF grid
machinery - Becke, Becke with the atomic-radius adjustment, Becke-Treutler and
Stratmann - plus a nearest-atom hard assignment on a common grid. A point may be
shared by more than one fragment; the factor matrix is exposed as
`partition_factors(mol, level, scheme) -> (coords, base_w, S[N, natm])`,
normalised so that `Σ_a S[i,a] = 1` pointwise. The function refuses to return
unless two internal assertions pass: normalisation, and `base_w · S[i, owner(i)]`
reproducing the weights that PySCF's own `get_partition` produces - an external
anchor against the same C kernel PySCF uses, not against a re-implementation in
this package. The two checks it enforces are pointwise normalisation
`|Σ_a S[i,a] - 1| < 1e-12` and agreement with PySCF's own weights
`max|base_w·S[i,owner(i)] - w_ref| < 1e-11`, with a normalised mean deviation below
1e-14; the tolerances are the assertion thresholds in the published test, not residuals
we are claiming to have measured [S17].

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

Representative output, produced by `nlcsplit/examples/quickstart.py` (ωB97X-V/6-31G*,
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
number for how much of the nonlocal correlation is inter-fragment, which on the
six S22 complexes that carry a counterpoise reference at grid level 2 accounts for
0.92-1.08 of the frozen-density superposition difference - association-time
nonlocal correlation is almost entirely carried by point pairs straddling the
fragments [S2, S10]. It supplies the per-system uncertainty that the attribution
choice contributes (0.004-0.247 kcal/mol absolute, 0.8-18.2% relative, with no
ordering by interaction type or by system size), which is the error bar any future
use of such numbers must carry [S12]. That span is not basis-set invariant: on the
water dimer it is 0.0249 kcal/mol in STO-3G against 0.0382-0.0400 in the four larger
sets, so the number moves by ~38% between STO-3G and 6-31G* while the four sets
beyond STO-3G agree with each other within 5% [S12]. Nor is it grid-converged to
better than it is printed: level-2 values are stored to three decimals, so a
level-1 to level-2 change below 5e-4 kcal/mol is not resolvable in the archived
table, and the one four-decimal ladder we ran gives 0.0002 kcal/mol between levels
1 and 2 - small, but not zero. And it produces evidence about the quantity
itself: ΔE_NLC ranges from 16% to 223% of ΔE_xc across the eight systems in our
table (seven distinct S22 members plus a second benzene-dimer geometry), and
97% versus 52% for those two geometries of the benzene dimer, so the VV10 term
cannot be reported as "the dispersion energy" without qualification [S2].

## 5. Availability and quality assurance

Apache-2.0; no GAMESS source is included, linked or required. That claim is checked by
scanning the published tree for GAMESS *source artefacts* specifically - `find` over
`*.src`, `*.f`, `*.for` and `GAMESS*` returns 0 - and not for the word. An earlier version
of this sentence asserted that the word appears only in the package docstring, and that
assertion was false: 13 files contained it, 8 of them as part of a working-machine path
(`/root/gamess_work/...`, `/mnt/e/Project/GAMESS/...`) including inside the shipped
`step_h.json` and `run_all.sh`, which is how a repository name that reads as "this is the
GAMESS project" got into a release that claims not to contain it. Two defects were behind
that: the gate's patterns covered artefact extensions but not path forms, and it iterated
the list of copied names rather than the directory tree, so 13 `.pyc` files that pytest had
left inside the release directory were never opened at all. Both are now fixed - the gate
walks the tree and fails by default on path forms, bare cluster addresses and account
names - and the published copies are scrubbed of those paths while the numbers are left
untouched, with a byte-level ledger of every replacement kept beside the release and the
archived stdout in this repository still hashing to what was recorded for it. After the fix
the word appears in 5 published files, all of them the disclaimer or prose about it, and the
path forms in 0. Two further defects were found while re-checking this section on
2026-09-29, and both were of the kind a source-tree reading cannot see. The first: an
earlier build was reported fixed and still shipped two script-style `test_*.py` modules at
package top level; the wheel now has 36 members and none of them is a script-style test - it grew again when
`step_l_sweep_compare.py` was added to the whitelist, see below.
The second is worse and was found only by looking at the artefact: **`fastpair.py` was not in
the package at all**, while the shipped `step_j_scaling.py` imports it - so a reader
installing the wheel could not run a single number from the companion algorithm paper, and
gate E (which checks that every import is *declared*) stayed silent because the import is
intra-package. `fastpair.py` and its test module are now in the manifest. In the same pass
`test_tolerance_probe.py` was published too, because a tolerance tightened from 0.10 to
1e-4 kcal/mol is a claim about measured spread and the measurement belongs beside it.

A third omission of the same kind was found by asking the question the other way round:
`run_all.sh` - the advertised one-command reproduction path - knew four of the thirteen
`step_*.py` scripts, and `step_l_sweep_compare.py` was missing from the shipped step list
altogether. That script is the only producer of the "agrees to 2e-3 kcal/mol with an
independently written script" sentence in section 2.1, so until now the published tree
contained neither that script nor any artefact carrying the comparison column. The driver
now lists all thirteen with each one's precondition (which need an argument, which need a
geometry download, which need an unloaded machine), derives the repository root from its own
location instead of a hard-coded working path, and refuses to run the argument-taking ones
rather than silently running them at their defaults.

The suite collects 63 tests in the working repository - 43 under `-m "not slow"` and 20
under `-m slow`, a partition of the same collection and not two numbers to be added. The
published wheel ships six test modules plus `__init__.py` and `conftest.py`, which collect
43, and the 20 that stay behind are exactly `test_fastpair_ide.py`'s - the peer's frozen
control module, whose `fastpair_ide.py` is deliberately not distributed, since shipping the
test without the module would be a collection-time ImportError. Two different out-of-tree
runs must not be quoted as one: `pip install .` from the source directory in a clean
environment passes 62 with one skipped (the S22 geometry fetch, by design), because that
install pulls in the whole tree including the control module, whereas `pytest --pyargs
nlcsplit` against the built wheel, run from a directory that is not the source tree,
exercises only the 43 published tests - 42 passed and one skipped in 581 s, or 24 passed and
one skipped under `-m "not slow"`. Both are recorded with the wheel's SHA-256, together with
the shell-quoting bug that left the hash field blank in one of the two logs, in
`evidence/release_qa/` [S19]. Tables map to one `step_*.py` each;
the archived stdout a claim cites lives under `evidence/**` with a UTC-stamped filename and
a hash manifest, while working logs under `nlcsplit/logs/` are gitignored scratch and are
not cited as evidence. Including a naive triple-loop versus BLAS
comparison of the kernel, per-scheme additivity checks, and geometry guards that
assert bond lengths and angles at construction time.

Eleven export gates run locally on every rebuild (`node tools/make_public_repo.js`). They are
not all of equal standing, and the difference matters: some exist because they caught a real
defect, others only because we could not otherwise show the earlier ones were not vacuous.
The last column says which, and "planted" means the gate has never fired on real input - it
fires on a fault we put in deliberately to prove it would.

| gate | what it checks | standing |
|---|---|---|
| R | walks the **published tree** and fails by default on working-machine paths, bare cluster addresses and account names | real defect: 13 `.pyc` files pytest had left inside the release directory, never opened by the old word-only check |
| A | no GAMESS source artefacts (matched on source patterns, not on the word "gamess", which the disclaimer itself contains) | real defect: a permanent false positive on our own disclaimer, which is why it matches patterns and not the word |
| B | no credentials or internal network strings | real defect: a scrub that re-injected a proxy address into a comment |
| C | every `evidence/*/MANIFEST.sha256` reproduces byte-for-byte | real defect: a Windows path making `sha256sum` report six mismatches that were not there |
| C2 | the scrubbing changed no digit in any number, **and** every file in a published evidence directory is registered in that directory's own source manifest | the second half fired on real input the day it was written: a comparison JSON produced by a step script landed in `evidence/agentb_sweep/` with no manifest entry, and the build refused to ship it (`shipped: false`) |
| D | every path cited by the companion text's provenance appendix is actually shipped | real defect: three citations that resolved to nothing in the published tree |
| E | every import in a shipped module is declared in `pyproject.toml` | real defect: `figures.py` importing matplotlib, which no dependency listed |
| F | the wheel and sdist member lists are what we think they are | real defect: two script-style tests that survived a build already reported fixed |
| G | `LICENSE` in the **source** file carries the real copyright line, not the Apache placeholder | real defect: the legal statement existed only in the generated copy; fires today on a restored placeholder |
| T | nothing in the export tree is missing from the export manifest | added as a belt-and-braces check; no firing on real input is recorded in this repository, only on the faults we planted |
| U | every module a shipped file imports from `nlcsplit` (absolute, dotted or package-relative) is itself in the shipped tree; the gate also self-tests against a planted missing sibling, and a build where that self-test does not fire does not ship | real defect: it was written for `fastpair.py`, which gate E could not see because an intra-package import is not a declared dependency |

Gate D exists because the first three could only fail in one direction. A, B, C
catch material that should not be present; what actually went wrong repeatedly was
material that should have been present and was not - a cited stdout living only on a
remote machine, calibration scripts inside a gitignored directory. Those produce a
clean export and a reader holding a citation to nothing. Gate E has the same blind spot
in the other direction and we hit it: it checks that an import is *declared*, so it
says nothing when a shipped module imports a sibling that was never packaged - the
`fastpair.py` defect above.

Release hygiene is now executed rather than specified: a clean-environment install of the
source tree, and an out-of-tree `pytest --pyargs nlcsplit` against the built wheel from a
directory outside the repository, both recorded with the wheel hash. Writing the
specification down is what produced two of the fixes: script-style `test_*.py` modules were
removed from the package (pytest collects and executes them at import), and the `slow`
marker was registered in package configuration rather than only in repository
configuration. An earlier out-of-tree import by path - weaker, since it read the exported
tree rather than an installed distribution - found that `step_i_gridrepr.py` ran a full
self-consistent-field sweep at import time because it had no `__main__` guard, since fixed.

The continuous-integration workflow is written but has **never executed**, because
there is no remote repository yet. Reviewers should read it as intent. Writing it down
did produce one real fix: its PySCF version matrix interpolated as
`pip install "pyscf==>=2.13"`, which is not a valid requirement, so the second job
would have died at the install step.

Independent verification of the arithmetic now has a second program behind it. An
earlier version of this documentation withdrew an ORCA agreement because re-reading
the archived output found no separately reported nonlocal term - and that withdrawal
was itself wrong: the quantity is printed, under the label
`NL Energy, E(C,NL)`. Grepping the same output for "nonlocal" or "VV10" is not a way to
find it, but not for the reason we first gave: the words are there, in the run banner's
feature list (`NL-DFT gradient (VV10)`, line 116 of `evidence/orca_run/h2o_dimer.out`),
which prints on every run and reports no number. The `E(VV10-nl)` column that does match
belongs to the PT2 correlation of double-hybrid functionals, which is a different physical
quantity. With the label known, six ORCA 6.0.1 single points agree with the reported
ΔE_NLC to 0.0004 kcal/mol on the water dimer and 0.0416 kcal/mol on the benzene dimer
A, with the outputs and their SHA-256 manifest in the repository [S18]. A third, fully
independent implementation (Psi4, or libxc's `xc_nlc_vxc` through its own bindings)
is still outstanding, as is extending the anchor beyond 2 of the 8 systems.


## 6. Limitations

Quadratic cost in retained grid points, with no sub-quadratic approximation. One
attempt at a certified screening was built and measured, and rejected - not on the
weak version of the argument we first wrote here. The earlier sentence claimed the bound
prunes nothing "at the tolerance the companion text needs (1e-8 Ha absolute)"; that
mis-states both sides. `1e-8 Ha` is a per-node-pair acceptance constant, and the companion
text needs 1e-6 kcal/mol on a fragment-pair term, which is 1.6e-9 Ha - so the constant and
the requirement were never the same kind of quantity. Measured properly, three things hold:
at atom-block granularity the *smallest* block-pair bound in a real water dimer is 197.96 Ha
against a quantity of -8.3e-4 Ha, so nothing is prunable at that granularity whatever the
tolerance (0 of 21 pairs, and 0 of 300 on the 24-atom sandwich); refining below the atom
block does fire, and at the accuracy the decomposition needs it still evaluates 84.4-95.4%
of the far-field point pairs; and on an unloaded machine the screened path is 1.08-10.28x
slower than the dense sum across the whole ladder, with no faster sample. The radius the
bound subtracts is set by the far tail of each atom's density, so the certified separation
comes out zero for every pair, including the ones facing each other across the
inter-fragment gap. That is a statement about this particular bound, not about screening in
general, and the measurements are in `paper/p2.md` with their artefacts under
`evidence/bound_forms/`, `evidence/fastpair_ab/` and `evidence/scaling/` rather than
quietly dropped.
Interpretation limited to the two-body and fragment-pair level. Results depend on
the choice of real-space partition to the extent quantified in section 4. VV10
only - the τ-dependent rVV10 form is not implemented. And it is not an energy
decomposition analysis: it does not separate electrostatics, exchange-repulsion,
polarisation or charge transfer.

---
### Sources
Paths are given relative to the repository root, because that is what the export gate
resolves them against. Three rows used to name `logs/<something>.out`, which is not a path
in this repository: `nlcsplit/logs/` is gitignored scratch, and the three files concerned are
tracked only as the hash-manifested copies under `evidence/**` (the build does place a
scrubbed copy of two of them inside the package, but the manifest and the citation should
point at one tracked original, not at a generated duplicate).

[S1] `RESEARCH-20260929-lit.md` · [S2] `nlcsplit/logs/step_h.json`,
`nlcsplit/logs/step_h_l2cp.json`, `MAIN-skeleton.md` 表 2 (uncertainty decomposition),
表 3 (P_frz against the superposition difference) and 表 4b (the S22 subset) ·
[S3] `nlcsplit/step_f_dispersion.py` · [S5] `nlcsplit/step_e_kernel.py` ·
[S7] `nlcsplit/step_d_floor.py` · [S9] `nlcsplit/step_i_gridrepr.py`,
`evidence/recompute/20260929T_step_i_gridrepr.out` ·
[S10] `evidence/l2cp/20260928T213839Z_centos-step_h_l2cp.out`,
`evidence/l2cp/20260929T051912Z_centos-l2_benzmeth_cp.out` ·
[S11] Mardirossian and Head-Gordon, PCCP 16, 9904 (2014), 10.1039/c3cp54374a
(DOI reverse-checked) ·
[S12] `evidence/recompute/20260929T003144Z_stepg-recompute.out` ·
[S17] `nlcsplit/tests/test_partition_factors.py` ·
[S18] `evidence/orca_run/`, `evidence/orca_control/` (six ORCA 6.0.1 outputs and their
`MANIFEST.sha256`) ·
[S19] `evidence/release_qa/` (clean-environment installs and out-of-tree runs, each with
the wheel's SHA-256) ·
[S20] `evidence/bound_forms/`, `evidence/fastpair_ab/`, `evidence/scaling/`,
`evidence/coretail/` (the certified-screening measurements summarised in section 6, in
full in `paper/p2.md`)
