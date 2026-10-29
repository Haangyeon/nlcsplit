---
title: 'nlcsplit: fragment and pair resolution of the VV10 nonlocal-correlation energy'
authors:
  - name: Angran Xia
    name_localized: 夏盎然   # 中文名记在这里：这份文件不进 md2tex/pdflatex 管线，CJK 不会撞字体
    orcid: 0009-0006-3366-6054
    affiliation: 1
    email: haangyeon@snnu.edu.cn   # 本人 2026-09-30 给的通讯邮箱（长安校区）
    corresponding: true
  - name: Changwei Wang       # 第二作者：本学院 王长崴（"崴"读 wei，据本人说明转写；名在前是 JOSS 惯例）
    name_localized: 王长崴
    orcid: 0000-0001-5685-2403  # Crossref 著录：SNNU 四篇论文同一 ORCID
    affiliation: 1
affiliations:
  # 院系英文全称取该学院自己的英文站措辞（chem.snnu.edu.cn/english/，2026-09-30 抓取核对：
  # "School of Chemistry & Chemical Engineering" + "Shaanxi Normal University"）。
  # 没有另造"College of Chemistry and Materials Science"那种在官网上查不到的写法。
  # 校区与邮编取自校方"联系我们"页 kexie.snnu.edu.cn/kxgk/lxwm.htm（2026-09-30 核对：
  # 西安市长安区西长安街620号 长安校区，邮编 710119）。门牌号不写进署名行：校内不同页面
  # 给的街道号并不完全一致，而期刊只需要城市+邮编，等本人指定挂哪个门牌再补。
  - name: 'School of Chemistry & Chemical Engineering, Shaanxi Normal University (Chang''an
      Campus), Xi''an 710119, Shaanxi, China'
    index: 1
date: 29 September 2026
bibliography: references.bib  # 39 条，DOI 逐条回查（2026-10-22 全表复核见 evidence/bib_provenance/20261022T1404Z_bib_all39_crossref_result.out）
keywords:
  - nonlocal correlation
  - VV10
  - density functional theory
  - energy decomposition
  - PySCF
---

# nlcsplit: fragment and pair resolution of the VV10 nonlocal-correlation energy

*SoftwareX / JOSS shape. Every numerical claim carries a `[S#]` tag into this paper's own
`## Appendix: sources`, which resolves each tag to a tracked artefact in this repository —
not to `paper/main.md`, whose tags number a different set. Archived stdout lives under
`evidence/**` with SHA-256 manifests; `nlcsplit/logs/` is gitignored scratch and is not a
source. **The front matter contains fields only the author can supply (ORCID,
corresponding status, co-author confirmation); they are marked rather than filled.**
`references.bib` is the shared list; the entries this paper cites were reverse-checked
against Crossref by DOI, not by title search (see `RESEARCH-20260929-lit.md` §9 for why
that distinction mattered, and `evidence/bib_provenance/G_s22_provenance_20260930.md` for
the queries behind the two software entries).*

**Disposition (2026-10-28): this manuscript is not submitted.** The external referee read it as a
duplicate of the companion paper - everything method-shaped repeats its section 2, everything
result-shaped repeats its section 3 - and the one venue that would take it in this shape (JOSS) is
not in the Web of Science Core Collection, so it cannot be scored as the kind of record the
authors' institution counts. Its usable content - the entry point, the six attributions, the
worked example, the fifteen release gates and the defect each was written for - was rewritten into
the Supporting Information appendix "The nlcsplit package" of `paper/main.md`, keyed to that
paper's own provenance tags rather than to the set below. Two statements in this file are **not**
repeated there, because both are superseded: the block-additivity residual quoted as 1.73e-18 to
6.94e-18 Ha came from one archive of one system, and the main text now quotes the 13-row census
from its section 2.2; and the shipped-test count of 74 of 94 is the split of an export run whose
log is not yet tracked, while the tracked census in `evidence/release_qa/` records 59 of 94 inside
the wheel with the remaining modules named. This file stays in the tree as the record of what was
written and why, not as a source of numbers.

## Abstract

VV10-type nonlocal correlation is evaluated in production electronic-structure
codes by collapsing a double sum over grid-point pairs into per-point values,
which discards the pair index. `nlcsplit` evaluates that double sum explicitly
and attributes each grid point to atoms and fragments through a real-space
partition, so the nonlocal contribution separates into intra-fragment and
inter-fragment pair blocks that sum back to the total to machine precision. The
package is pure Python and NumPy [[harris2020numpy]] on top of PySCF
[[sun2018pyscf]]; [[sun2020pyscf]], released under Apache-2.0,
contains no GAMESS source, and reproduces every number it documents from a
single named script.

## 1. Motivation and statement of need

Functionals that pair a range-separated hybrid with the VV10 nonlocal correlation
term [[vydrov2010simple]] - ωB97X-V [[mardirossian2014wb97xv]] and ωB97M-V
[[mardirossian2016wb97mv]] in particular - are a routine choice for
non-covalent interactions. Their nonlocal contribution,

    E_NL = ½ ∫∫ ρ(r) ρ(r') Φ(r, r') d³r d³r',

is a two-centre sum, but what users get back is one number per grid point, or one
total [[sabatini2013]]. When an interaction energy needs to be interpreted per fragment, the
available options stop at the semi-local part: electrostatics, exchange,
polarisation and charge transfer can be resolved by EDA schemes [[khaliullin2007]], whereas the
nonlocal term is carried as an undivided block. The closest published treatment
computes exactly that block as a whole and asks whether it is accurate
[[dasgupta2023]]; the closest published explicit evaluation, JuNoLo
[[lazic2010junolo]], sums the double sum directly but targets an improved total
energy and explicitly recommends itself for bonded systems "where one cannot tell
apart fragments". Neither resolves the term into fragment pairs, which is what the
literature screen of [S1] was run to find - and that screen's own record says the
open-index *subject* search behind it is unreliable, so this is a screen, not an
enumeration. That gap is what this package fills, and it is a capability gap
rather than an accuracy gap: on the same grid and density our sum agrees with the
native PySCF kernel to ~1e-8 Ha [S9].

## 2. Method overview

**Kernel and convention.** `w0 = sqrt(C|∇ρ|⁴/ρ⁴ + 4πρ/3)`,
`κ = b(3π/2)(ρ/9π)^(1/6)`, `g = w0(r_i)R² + κ(r_i)` with same-centre pairing,
`Φ = -3/(2 g g' (g + g'))`, and `E_NLC = ½∬ρρΦ + β∫ρ` with
`β = (1/32)(3/b²)^(3/4)`. Parameters are read from PySCF `nlc_coeff` rather than
hard-coded. Same-centre pairing is the convention that reproduces the native
kernel; the cross-pairing variant `g = w0(r_j)R² + κ(r_i)` is retained as a
definition-sensitivity control and raises monomer energies by +0.1379 (water), +0.4182
(argon) and +0.1346 (methane) kcal/mol at grid level 1, and +0.9057 for benzene at level 0
[S5]. The offset is not a constant and
it moves with the grid - the level-0 benzene figure is not the level-1 one - so these four
numbers are one batch at the levels the producing script itself selects, and must not be
mixed with another batch. [S5] now points at an archived run carrying all four, which it did
not: an earlier version of this sentence gave benzene as 0.914 kcal/mol and labelled the whole
list "at grid level 1", and neither value nor label was checkable, because the only carrier had
been a gitignored working log. The rerun that closed the gap reproduced water and argon to the
printed digit and gave benzene +0.9057 at level 0 - which is what the companion text already
said, so the two papers had been disagreeing with each other about one number while citing the
same source row - and added methane, which neither paper had mentioned.

**Blocks and additivity.** `pair_energy(A, B)` returns the half block
½ Σ_{i∈A} Σ_{j∈B}; the inter-fragment term is reported as twice that, so
`E_nl = Σ_A intra[A] + Σ_{A<B} inter[A,B]` holds as an identity. Measured
residual: 1.73e-18 to 6.94e-18 Ha, over the five partitions and two repeated schemes of the
archived level-1 water-dimer run [S2].

**Why decomposing only the double sum is exact.** β is a constant and ∫ρ is the
electron number, so the local term β∫ρ = βN cancels identically from any
superposition difference. Inter-fragment decomposition therefore needs no
convention for splitting a local energy density: it is a property of the double
sum alone [S3]. The flip side is reported as a limitation rather than hidden - the
absolute local term of one fragment is exactly β·N_A, so its scheme spread is β
times the spread of the Becke population, 3.0415 kcal/mol per electron, i.e.
0.329 kcal/mol for the water dimer on the official S22 geometry [[jurecka2006s22]] and 0.300 on the
constructed one (`nlcsplit/step_k_population.py`, whose two runs both assert that the
fragment populations sum to the electron number).

**Attribution.** Four real-space partitions reachable through the PySCF grid
machinery - Becke [[becke1988]], Becke with the atomic-radius adjustment, Becke-Treutler
[[treutler1995]] and Stratmann [[stratmann1996]] - plus a nearest-atom hard assignment on
a common grid. A point may be
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
sum. Sweeping 1e-8 … 1e-16 moves the inter-fragment term by at most 2.1e-11 Ha at grid level 1
and 4.2e-11 Ha at level 2 - 1.3e-8 and 2.6e-8 kcal/mol, which the run's own log prints as
0.000000 - while discarding 10.7-22.6% of points carrying ≤2.3e-6 electrons [S7], so the
threshold is an implementation detail rather than a parameter. An earlier version of this
sentence said "≤5e-11 kcal/mol": it had taken the archived figure, which is in hartree, and
put a kilocalorie unit on it, claiming the term was about 260 times less sensitive to the
floor than the archive shows. Both figures are negligible against the 1e-4 kcal/mol scale of
the quantities here, so the conclusion survives the error, but the number did not - corrected
against `evidence/recompute/20260928T150222Z_step_d_floor.out`, whose header already records
the units.

## 3. Software description

`nlcsplit` is pure Python on top of PySCF's grid and density machinery, with NumPy
for the pair sum; no compiled extension is built or required. Three modules carry the
physics - `nlc.py` (VV10 fields and the block pair sum), `partition.py` (the six
attribution schemes) and `geomlib.py` (geometries, fragment boundaries and the S22
loader). The `step_*.py` scripts reproduce one table of the companion paper each and
write a JSON sidecar; `figures.py` draws only from those sidecars, never from log text.

The public entry point is one function:

    res = nlc.fragment_decomposition(coords, weights, rho, sigma, fragments,
                                     b=b, C=C, owner=owner)      # hard assignment
    res = nlc.fragment_decomposition(coords, weights, rho, sigma, fragments,
                                     b=b, C=C, soft=S)           # soft assignment

`fragments` is a list of atom-index groups. `owner` gives the nearest-atom index of
each grid point; `soft` is an `(natm, ngrid)` weight matrix whose columns sum to one,
as returned by `partition.scheme_factors(mol, coords, scheme=...)`. The return value is
a dict with `E_loc`, `E_nl`, `E_total`, `intra` keyed by fragment, and `inter` keyed by
fragment pair. `inter[(A, B)]` is the full cross contribution, not a half, so
`E_nl = sum(intra) + sum(inter)`; `closure_check=True` compares the block sum against a
monolithic evaluation over the same points and raises if they differ.

The six schemes are selected by name: the four Becke-family constructions used in the
companion paper (`becke`, `becke-becke-rad`, `becke-treutler`, `stratmann`) and two
cross-family controls (`voronoi`, `hirshfeld` [[hirshfeld1977]]). `scheme_factors` returns the same shape
for all six, so a comparison changes one keyword and nothing else, and it refuses to
return a matrix whose columns do not sum to one within 1e-8.

A minimal run, condensed from `nlcsplit/examples/quickstart.py`:

    mol = gto.M(atom=geomlib.h2o_dimer(), basis="6-31g*", unit="Angstrom")
    mf, X0, W0, rho0, sig0 = partition.scf_grid(mol, xc="wb97x_v", level=1)
    coords, weights, owner = partition.atom_partition(mol, level=1, scheme="becke")
    res = nlc.fragment_decomposition(coords, weights, rho0, sig0,
                                     geomlib.FRAGS["(H2O)2"], owner=owner)

For the water dimer at omegaB97X-V/6-31G*, grid level 1, this prints the numbers below,
archived verbatim with its interpreter and module fingerprints as
`evidence/release_qa/20261003T1901Z_quickstart_readme_example.out`:

    inter[(0,1)] = -0.5237
    intra        = -3.5457 -3.7437
    E_nl         = -7.8130   E_loc = 60.8303   E_total = 53.0172

`E_nl` equals `intra + intra + inter` as required, and `E_total` may be compared with the
native kernel on its own reference grid, which gives 53.017 and 53.016 for this system and
level (difference +0.002 kcal/mol, the grid-representation difference of the companion
text's section 3.1 rather than an algorithmic one) [S9]. Figure 1 shows the same call over
all five partitions: what stays fixed and what does not.

![What one call returns over five partitions of the water dimer, and the cross-program check: the nonlocal total, the inter-fragment block, the block-sum residual, and ORCA against PySCF](figs/fig_sw_decomposition.png)

**Figure 1.** What one call returns, on the archived water-dimer run at grid level 1 [S2].
(a) The nonlocal total moves by 1.0×10⁻³ kcal/mol across the five partitions; points are
deviations from the value printed for the Becke row. (b) The inter-fragment block moves by
0.040 kcal/mol over the same five rows. (c) The block sum reproduces the monolithic
evaluation to 1.7–6.9×10⁻¹⁸ Ha. (d) The second external anchor: ORCA 6.0.1 against PySCF
for the same quantity on the eight complexes, 0.067–0.952% of |E_NL|, all below the dashed
1% line [S18]. The partitions in (a)–(c) are the four Becke-family constructions of
section 2 plus a nearest-atom hard assignment; (a) and (b) are as printed by the run (three
decimals), while (c) is its own additivity check. Axis units: (a) deviations in 10⁻³
kcal/mol from the value printed for the Becke row, (b) kcal/mol, (c) Ha, and (d) |Δ| =
|ORCA − PySCF| in per cent of |E_NL|. The figure is drawn by
`nlcsplit/figures.py --software-fig`, which parses the two archived sources and refuses to
plot if either fails to parse.

Dependencies are NumPy and PySCF. `partition.py` reaches `libdft.VXCgen_grid` through
ctypes deliberately: it is the entry point `gen_grid.get_partition` itself uses, which
makes the audit against PySCF's own partition external rather than circular. There is no
other compiled dependency and no build step.

## 4. Impact

The package makes three things checkable that previously were not. It gives a
number for how much of the nonlocal correlation is inter-fragment, which on the
six S22 complexes that carry a counterpoise reference [[boys1970]] at grid level 2 accounts for
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
itself: where the share is defined at all it ranges from 16% of ΔE_xc (water) to 97%
and 52% for the two geometries of the benzene dimer, and on the methane dimer the two
parts carry opposite signs so the package's own rule (|ΔE_NLC/ΔE_xc| > 2 ⇒ report the two
absolute terms, not a ratio) refuses to state a share at all. The VV10 term therefore
cannot be reported as "the dispersion energy" without qualification, and on one row of our
own table not even as a percentage [S2].

The per-system numbers behind these statements are tabulated in the companion paper;
this paper does not repeat them.

## 5. Availability and quality assurance

`nlcsplit` is released under Apache-2.0. It contains no GAMESS [[barca2020gamess]] source, and the claim is
checked by scanning the published tree for source artefacts (`*.src`, `*.f`, `*.for`,
`GAMESS*`) rather than for the word, and by installing the wheel into a throwaway target
and walking what lands in `site-packages`. The archived scan reports 45 installed files,
three named exemptions and no hit outside the exemption ledger at rc=0 [S19]. The package
ships a `CITATION.cff` so that it is citable as software on the terms the FORCE11
principles set out [[smith2016software]], and every number it prints is regenerated from a
tracked script rather than retyped [[peng2011repro]].

Correctness is guarded at three levels. The test suite pins the kernel against PySCF's
native one, regression-tests the archived numbers, and checks the geometry and
partition-factor invariants. The release script `tools/run_ship_qa.sh` enforces fifteen
export QA gates over the exported tree: build-residue and credential hygiene, no GAMESS source,
byte-for-byte reproduction of every `evidence/*/MANIFEST.sha256`, no digit changed by the
publishing scrub, import and wheel-member checks, and the provenance checks below. Each
gate carries a two-directional self-test that must fire on a planted fault and stay silent
on valid input, and the build refuses to ship when a self-test does not fire. The gates
and the real defect that motivated each are listed in Table 1.

Two checks ship with the package itself. The ORCA 6.0.1 [[neese2020orca]] comparison recomputes the
nonlocal term for the eight complexes in the companion paper, together with an omegaB97X
control that must not print the label [S18]. The partition-free referee re-evaluates the
cross term on a two-Gaussian model density with three independent methods and reports the
error bar [S21]. Both are archived with their own manifests, and every `[S#]` tag used in
this paper resolves to a tracked file in the provenance appendix (Table 2); the converter
re-checks each tag at build time and refuses to emit the PDF when one does not resolve.

The wheel census is part of the same script: members are counted by category (test
modules, helpers under `nlcsplit/tests/`, everything else) and the category counts are
printed beside their sum, so a silently dropped category cannot pass as a member count
[S19]. The published wheel carries 74 of the repository's 94 tests; the 20 that stay out
test `nlcsplit/fastpair_ide.py`, a peer's frozen reference implementation that is
deliberately not distributed, and the exclusion is named in the export tool's
`INTERNAL_ONLY_MODULES` rather than left silent [S19].

| gate | what it checks | standing |
|---|---|---|
| R | walks the **export tree** for build and pytest residue left inside it - `__pycache__` and `.pyc`, `.egg-info`, a stray `setup.cfg` - which is how a compiled docstring carries a repository path out even when every source file is clean | real defect: 13 `.pyc` files pytest had left inside the release directory, never opened by the old check, which iterated the list of copied names instead of walking the tree |
| A | no GAMESS source artefacts (matched on source patterns, not on the word "gamess", which the disclaimer itself contains) | real defect: a permanent false positive on our own disclaimer, which is why it matches patterns and not the word |
| B | walks the **published tree** and fails by default on credentials and internal-network strings - private-key blocks, password assignments, `ssh … @` targets, bare-IP users - and, through the ten named rules that stay out of the release, on working-machine paths, bare cluster addresses and account names | real defect: the 13 published files that carried `/root/gamess_work/...` and `/mnt/e/Project/GAMESS/...` while the gate reported every one of its arrays empty, because its patterns covered artefact extensions but not path forms |
| C | every `evidence/*/MANIFEST.sha256` reproduces byte-for-byte | real defect: a Windows path making `sha256sum` report six mismatches that were not there |
| C2 | the scrubbing changed no digit in any number, **and** every file in a published evidence directory is registered in that directory's own source manifest | the second half fired on real input the day it was written: a comparison JSON produced by a step script landed in `evidence/agentb_sweep/` with no manifest entry, and the build refused to ship it (`shipped: false`) |
| D | every path cited by the companion text's provenance appendix is actually shipped | real defect: three citations that resolved to nothing in the published tree |
| E | every import in a shipped module is declared in `pyproject.toml` | real defect: `figures.py` importing matplotlib, which no dependency listed |
| F | the wheel and sdist member lists are what we think they are | real defect: two script-style tests that survived a build already reported fixed |
| G | `LICENSE` in the **source** file carries the real copyright line, not the Apache placeholder | real defect: the legal statement existed only in the generated copy; fires today on a restored placeholder |
| T | nothing in the export tree is missing from the export manifest | added as a belt-and-braces check; no firing on real input is recorded in this repository, only on the faults we planted |
| U | every module a shipped file imports from `nlcsplit` (absolute, dotted or package-relative) is itself in the shipped tree; the gate also self-tests against a planted missing sibling, and a build where that self-test does not fire does not ship | real defect: it was written for `fastpair.py`, which gate E could not see because an intra-package import is not a declared dependency |
| V | every Python module inside a packaged directory is either in the export whitelist or named, with a reason, as an unreleased internal module - this is the set `pip install .` actually puts in `site-packages`, which the whitelist does not constrain; self-tests fire on a planted stray and stay silent on the named ones | real defect: found by the shipped licence scanner, which walked 45 installed files from a source-directory install and found the peer implementation among them |
| W | no manuscript or README quotes a *share* for a system whose denominator cancels, i.e. where `abs(dE_NLC/dE_xc) > 2` - the same rule `step_f_dispersion.py` applies to its own output, extended to the prose | real defect: three of them on the day it was written (the companion text's conclusion, this paper's section 4, and a line the author had just added to this README), all quoting a share equivalent to a ratio above 2 that section 3.2 of the same paper argues against - and the gate caught its own author reintroducing the number while documenting the gate |
| X | every `step_*.py` in the export tree appears in `run_all.sh`'s command table, so each table in the text has an entry point a reader can actually invoke | real defect: `step_m_ccsdt.py` reached the release on 2026-09-30 without ever being registered, which is the same omission the driver had been rewritten to fix - that rewrite left no guard, and this gate is the guard it lacked. The self-test truncates the command table to the four entries of the original bug and must then report ten missing scripts, and must go silent on a table completed by construction |
| Y | every image and link target in `paper/joss/paper.md` resolves to a file the export actually carries — the gate walks the copied-file set, not the filesystem, so a figure that exists on the working machine but was never listed is a broken citation for the reader | planted only: it has not fired on real input, its two-directional self-test must fire on exactly the planted target and stay silent on a valid one, and it goes quiet when `paper/joss/` is absent from the tree |

**Table 1.** The release gates: what each checks, and the real defect that put it there. A letter identifies a gate in `tools/run_ship_qa.sh`; rows marked "planted only" have fired in self-test but not yet on real input.


## 6. Limitations

Quadratic cost in retained grid points, with no sub-quadratic approximation. One
attempt at a certified screening was built and measured, and rejected - not on the
weak version of the argument we first wrote here. The earlier sentence claimed the bound
prunes nothing "at the tolerance the companion text needs (1e-8 Ha absolute)"; that
mis-states both sides. `1e-8 Ha` is a per-node-pair acceptance constant, and the companion
text needs 1e-6 kcal/mol on a fragment-pair term, i.e. 1e-6/627.509474 Ha in the same unit -
so the constant and the requirement were never the same kind of quantity. Measured properly, three things hold:
at atom-block granularity the *smallest* block-pair bound in a real water dimer is 197.96 Ha
against a quantity of -8.3e-4 Ha, so nothing is prunable at that granularity whatever the
tolerance (0 of 21 pairs, and 0 of 300 on the 24-atom sandwich); refining below the atom
block does fire, and at the accuracy the decomposition needs it still evaluates 84.4-95.4%
of the far-field point pairs; and with no other runnable user task at the sampling instant
(a contention gate, not a claim that the machine was idle), the screened path is slower than
the dense sum in every one of 33 timed screened/exact pairs across two independent windows
on the same box - 1.08-10.28x in the archived window and 1.37-13.29x in the second (1.95-10.28x
and 2.63-13.29x at the tightest tolerance tested), with no
faster sample in either. The radius the
bound subtracts is set by the far tail of each atom's density, so the certified separation
comes out zero for every pair, including the ones facing each other across the
inter-fragment gap. That is a statement about this particular bound, not about screening in
general, and the measurements are in `paper/p2.md` with their artefacts under
`evidence/bound_forms/`, `evidence/fastpair_ab/` and `evidence/scaling/` rather than
quietly dropped [S20].
Interpretation limited to the two-body and fragment-pair level. Results depend on
the choice of real-space partition to the extent quantified in section 4. VV10
only - the τ-dependent rVV10 form is not implemented. And it is not an energy
decomposition analysis: it does not separate electrostatics, exchange-repulsion,
polarisation or charge transfer.

## Appendix: sources

Paths are relative to the repository root, because that is what the export gate resolves
them against. Every path below is tracked by git, and the build refuses to produce
`software.tex` if one is not. Three rows used to name `logs/<something>.out`, which is not
a path in this repository: `nlcsplit/logs/*.out` is gitignored scratch, and those files are
tracked only as the hash-manifested copies under `evidence/**` (the build does place a
scrubbed copy of two of them inside the package, but a citation should point at one tracked
original, not at a generated duplicate). The two `.json` logs in the S2 row are tracked in
place, and are cited as they are kept.

Literature is not in this table. Where a sentence needs a published work it uses a
`[[key]]` citation resolved against `paper/references.bib`, whose entries were
reverse-checked through Crossref by DOI; the queries for the software and benchmark
entries are archived in `evidence/bib_provenance/G_s22_provenance_20260930.md`.

### Artefact provenance

| Tag | Artefact | What it fixes |
|---|---|---|
| S1 | `RESEARCH-20260929-lit.md` §1, §6, §9 | the literature screen behind the statement-of-need comparison, together with that file's own measurement that open-index *subject* search recall is poor — which is why §1 calls the gap a screen and not an enumeration |
| S2 | `evidence/recompute/20260929T010500Z_step1_geomfix.out`, `evidence/recompute/MANIFEST.sha256`, `nlcsplit/logs/step_h.json`, `nlcsplit/logs/step_h_l2cp.json`, `MAIN-skeleton.md` (its uncertainty-decomposition, P_frz, and S22-subset tables) | the per-scheme block-sum residual - 1.73e-18 to 6.94e-18 Ha, printed for five partitions and two repeated schemes of the level-1 water dimer at lines 6-14 of the first artefact - the only measured additivity residual for a real system in this repository. The partition-free referee reports its own block-additivity residual on a two-Gaussian model density (worst 1.735e-18 Ha, row S21), which is a different object and not interchangeable with this one. Earlier versions of this row cited the two json logs for the residual: they carry the per-system tables and no additivity field at all |
| S3 | `nlcsplit/step_f_dispersion.py` | that `β∫ρ = βN` cancels identically from a superposition difference, so the inter-fragment term needs no local-density convention — and the denominator rule that refuses to quote a share when the sum cancels |
| S5 | `nlcsplit/step_e_kernel.py`, `evidence/recompute/20261001T083716Z_step_e_pairing_control.out`, `evidence/recompute/MANIFEST.sha256` | the definition-sensitivity control as both generator and record: the script compares same-centre with cross pairing on one grid and one density and prints the per-variant totals, and the archived stdout now carries the +0.1379/+0.4182/+0.1346 (level 1) and +0.9057 (benzene, level 0) kcal/mol of §2. Until 2026-10-01 this row pointed at a re-measurement only, because the stdout that recorded them lived in nlcsplit/logs, which is gitignored - and the unarchived benzene figure in this paper (0.914) did not match the archived one in the companion text (0.906); the run resolved it in favour of 0.906 |
| S7 | `nlcsplit/step_d_floor.py`, `evidence/recompute/20260928T150222Z_step_d_floor.out` | the `rho_floor = 1e-12` far-field cut, and the reported cost of it (10.7–22.6% of points dropped, carrying ≤ 2.3e-6 electrons) |
| S9 | `nlcsplit/step_i_gridrepr.py`, `evidence/recompute/20260929T_step_i_gridrepr.out` | agreement of the explicit pair sum with PySCF's native VV10 kernel on a fixed grid, and the grid-representation residual quoted in §1 and §2 |
| S10 | `evidence/l2cp/20260928T213839Z_centos-step_h_l2cp.out`, `evidence/l2cp/20260929T051912Z_centos-l2_benzmeth_cp.out` | the level-2 counterpoise numbers, computed on the cluster and archived with their stdout |
| S12 | `evidence/recompute/20260929T003144Z_stepg-recompute.out` | the basis-set and grid sensitivity of the attribution, including the ±5% agreement among the four basis sets beyond STO-3G |
| S17 | `nlcsplit/tests/test_partition_factors.py` | the two assertions `partition_factors()` enforces before returning (pointwise normalisation at 1e-12, agreement with PySCF's own `get_partition` weights at 1e-11) — assertion thresholds, not measured residuals |
| S18 | `evidence/orca_run/`, `evidence/orca_control/`, `evidence/orca_widen/`, `evidence/orca_widen/cross_program_table.txt` | the ORCA 6.0.1 outputs and their manifests (`evidence/orca_run/MANIFEST.sha256`, `evidence/orca_control/MANIFEST.sha256`, `evidence/orca_widen/MANIFEST.sha256`): six runs for the water and benzene-A anchors, the ωB97X control group, and eighteen more covering the remaining six systems, with the archived stdout for every one of the 24; plus the two generators that re-derive the comparison from those outputs and refuse if the system list or any row's definition disagrees |
| S19 | `evidence/release_qa/` | clean-environment installs and out-of-tree runs, each recorded with the SHA-256 of the wheel that was installed |
| S20 | `evidence/bound_forms/`, `evidence/fastpair_ab/`, `evidence/scaling/`, `evidence/coretail/` | the certified-screening measurements summarised in §6, reported in full in `paper/p2.md` |
| S21 | `evidence/attribution_referee/run.py`, `evidence/attribution_referee/referee_lib.py`, `evidence/attribution_referee/summarize.py`, `evidence/attribution_referee/README.md`, `evidence/attribution_referee/outputs/summary.md`, `evidence/attribution_referee/outputs/results.json`, `evidence/attribution_referee/outputs/results_run1_20261001.json`, `evidence/attribution_referee/outputs/table_run1_20261001.md`, `evidence/attribution_referee/MANIFEST.sha256` | the partition-free referee for attribution: the two-Gaussian model density, the three independent evaluations of the exact cross term, the measured error bar it is compared against, and the two shipped runs whose tables are byte-identical apart from recorded wall-clock fields. Re-running `evidence/attribution_referee/run.py` regenerates everything; `evidence/attribution_referee/summarize.py` re-quotes it with no re-quadrature |

**Table 2.** Provenance appendix: what each [S#] tag resolves to, and which claim in the text it fixes.
