# Attribution referee — an exact, partition-free reference for VV10 fragment attribution

Model density: two normalised Gaussians, `rho = rhoA + rhoB`, 4 electrons each,
centres on the z axis at +/- sep/2.  VV10 parameters: `b = 6.0`, `C = 0.01`, taken
at run time from PySCF `nlc_coeff('wb97x_v')` — the same route `nlcsplit` uses.
No SCF is run anywhere here; PySCF contributes only the parameters, its atomic
grids and its Becke partition machinery.

Re-run everything from the repository root:

```
wsl -e bash -lc 'cd <REPO> && PYTHONPATH=. python3 -u evidence/attribution_referee/run.py'
```

A fast plumbing check with shrunken grids (same comparisons, worse numbers):
prefix the command with `ATTR_REFEREE_TINY=1`.

---

## 1. Why this directory exists

P1's external anchor is a cross-program referee on the **superposition difference**
of the VV10 term (ORCA 6.0.1 vs PySCF over the S22 set, all residuals < 1%).  That
referee checks *differences of the quantity*.  It does not referee **attribution** —
"how much of the term belongs to fragment A versus the A-B pair" — which is what
`nlcsplit` actually reports.  P1 says so itself: the anchor checks differences, so
the absolute per-fragment values remain unrefereed.

This directory moves to a system where an exact reference exists **by
construction**, and measures the attribution against it.

## 2. The convention that is being refereed

Read off `nlcsplit/nlc.py` and `paper/main.md` section 2, and re-checked at run
time by the script (`validation.md`, item 1a):

```
rho(r)   = rhoA(r) + rhoB(r)                     (each a normalised Gaussian)
sigma(r) = |grad rho(r)|^2                        (of the TOTAL density)
w0(r)    = sqrt( C sigma^2 / rho^4 + (4 pi/3) rho )
kappa(r) = b (3 pi/2) (rho / 9 pi)^(1/6)
g = w0(r) R^2 + kappa(r),   g' = w0(r') R^2 + kappa(r'),   R = |r - r'|
                                                   (same-centre pairing)
Phi(r,r') = -3 / (2 g g' (g + g'))
E_NL   = 1/2 int int rho(r) Phi(r,r') rho(r') d3r d3r'
E_NLC  = E_NL + beta int rho ,   beta = (1/32)(3/b^2)^(3/4)
```

Two asymmetries between the referee and the package are measured rather than
assumed:

* the package drops grid points below `rho_floor = 1e-12` (and clamps `rho` there),
  the reference does not; the effect is quantified by the floor study in
  `convergence.md`;
* the package sums over a PySCF molecular grid, the reference over its own nodes.
  The reference is *also* evaluated through the package's own summation code (see
  section 4), which removes the grid as a variable.

## 3. Why bilinearity does not hand us the split (requirement R1)

`Phi` is a functional of the **total** density.  So the map `rho -> E_NL[rho]` is
not quadratic with a fixed kernel, and

```
E_NL[rhoA + rhoB] - E_NL[rhoA] - E_NL[rhoB]
```

is **not** "the A-B term": subtracting the two isolated-Gaussian calculations also
collects the response of `w0` and `kappa` inside region A to B's tail and vice
versa.  An exact three-way split obtained by monomer subtraction does not exist.
That is why the reference below is built at the level of the *pair assignment*,
and it is also why the ORCA/PySCF anchor (which compares exactly this kind of
superposition difference) cannot referee attribution.

## 4. The exact reference: pair assignment, not space assignment

Pick the electron pair `(r, r')` and ask which fragment each electron's **density
factor** belongs to.  With `rho = rhoA + rhoB` each factor expands, so define, for
`X, Y` in `{A, B}`,

```
I_XY = int int rhoX(r) Phi[rho_total](r,r') rhoY(r') d3r d3r'
```

This is an unambiguous number: `Phi` is built **once**, from the total density, and
no real-space partition, no Becke weight and no grid assignment occurs anywhere in
the definition.  Because `Phi(r,r') = Phi(r',r)` (swapping the arguments swaps
`g <-> g'` and `-3/(2 g g'(g+g'))` is symmetric),

```
I_AB = I_BA        and        E_NL = 1/2 (I_AA + I_BB) + I_AB      (exact)
```

**The bookkeeping against the package (the half factors, derived not guessed).**
`nlcsplit.nlc.pair_energy(A,B)` returns the *half* block
`1/2 sum_{i in A} sum_{j in B} w_i w_j Phi_ij`, and `fragment_decomposition`
reports `intra[A] = blk(A,A)` and `inter[(A,B)] = 2 blk(A,B)` so that
`E_NL = sum_A intra[A] + sum_{A<B} inter[(A,B)]`.  Substituting the density-factor
weights `w_i -> w_i rhoX(r_i)` gives, term by term,

```
blk(X,Y)  ->  1/2 I_XY
intra[A]  ->  1/2 I_AA
inter[(A,B)]  ->  I_AB          ( = 1/2 (I_AB + I_BA), using I_AB = I_BA )
```

so the referee number is `inter[0,1] - I_AB`, **not** `inter[0,1] - 2 I_AB`, and
the intra-fragment reference is `0.5 * I_AA`.  Both are asserted in the tables.

**The density-factor split is also expressible inside the package.**  `f_A =
rhoA/rho`, `f_B = 1 - f_A` sums to exactly 1 at every point, so it is a legal
`soft=` argument for `fragment_decomposition`.  Handing it the density factors
makes the package's own summation code evaluate the **exact** decomposition on
whatever node set it is given.  Subtracting that from the Becke block on the *same*
nodes isolates the partition from the grid — `d_partition` in `table.md`.

**The local term carries no attribution.**  `beta int rho` is a one-body functional;
under the density-factor split it is `beta N_A + beta N_B` with **no** cross term,
and the package does not pair-resolve it either.  `table.md` shows the grid value
against `beta * 8` so the reader can see the node sets integrate the density once.

## 5. Independent computations of the reference

Three implementations, none of which uses `nlcsplit` for the summation
(`referee_lib.py`; it forms `|r - r'|` by direct subtraction, where the package
uses the polarisation identity in a blocked gemm, so an arithmetic error cannot be
mirrored):

1. **3-D x 3-D Cartesian** tensor Gauss-Legendre, one cube per density factor
   (`integral_box3d`);
2. **5-D cylindrical** reduction about the internuclear axis (`integral_cyl5d`):
   azimuthal symmetry folds the 6-D integral to 5-D with weights carrying
   `4 pi s s'`, a different node set, a different domain shape and a different
   Jacobian;
3. **Monte-Carlo** with the density factor itself as the importance
   (`mc_integral`), giving an unbiased estimate and a standard error.

Each factor's domain is the cube/cylinder of half-side `f_trunc/sqrt(alpha)` about
its own centre, i.e. the factor is cut at `exp(-25)` of its peak; the truncation
itself is measured (`convergence.md`).  The integrand is bounded everywhere: on the
diagonal `rho^2 Phi ~ rho^(3/2) -> 0`, and off it the kernel falls off like `R^-6`.

The undecomposed total (`which="TOT"`) is integrated on a **single** coaxial
cylinder that contains both factors' domains, never through the four-way split —
that is the closure test `E_NL = 1/2 sum I_XY` against an independent route.
(The Cartesian variant of this test was removed on purpose: concatenating two
*overlapping* cubes counts the overlap twice — measured as a 17.7% inflation of the
total at `sep = 6, alpha = 1`.)

## 6. Configurations

`alpha` in {0.5, 1.0, 2.0} bohr^-2 (1/e half-width `1/sqrt(alpha)` = 2.00, 1.00,
0.71 bohr), `sep` in {2.5, 4.0, 6.0, 10.0} bohr, 4 electrons per Gaussian (8 total;
peak density of the pair at `alpha = 1` is 0.72 a.u., inside the range VV10 is
parameterised for).  Larger separations are used for the asymptotic check.

These are **synthetic** densities: no nuclei, no cusps, no orbital structure.  The
statement being measured is about the real-space attribution machinery as a
mathematical operation on a density, not about chemistry.

## 7. Files

| file | content |
|---|---|
| `referee_lib.py` | the model density, the transcribed VV10 fields, the three independent quadratures, the analytic anchors, the node builders |
| `run.py` | the whole comparison; writes `outputs/` |
| `probe_quadrature.py` | standalone numerical QA (weights and kernels against exact integrals, order ladders, truncation scan, timings) |
| `outputs/results.json` | every number, machine-readable |
| `outputs/table.md` | per-configuration table (reference, package blocks, differences, MC, normalisation) |
| `outputs/validation.md` | the falsification suite |
| `outputs/convergence.md` | order ladders, truncation scan, grid-level ladder, density-floor study |
| `outputs/headline.md` | the numbers to quote |
| `outputs/summary.md` | the reference's combined error bar `U` and, per configuration, whether `d_headline` exceeds it (`summarize.py`, no re-quadrature) |
| `outputs/results_run1_20261001.json`, `outputs/table_run1_20261001.md` | the first run, kept beside the second so section 11.1 is a file comparison and not a claim |
| `outputs/rerun_verify_20261001.log` | the second run's full stdout, including its `EXIT=0` line |
| `outputs/run_log.txt`, `outputs/run_log_stdout.txt` | the run transcript |

## 8. Falsification suite (requirement R6)

`validation.md` is generated; the design intent of each item:

* **1a transcription check** — this referee's `w0`/`kappa` against
  `nlcsplit.nlc.vv10_fields` on the same inputs.
* **1b/1c/1d known answers** — node weights against the exact Gaussian
  normalisation over a cube and over a cylinder; the double integral against a
  closed-form 6-D Gaussian integral (`exp(-lambda R^2)`) and against the textbook
  `erf` mutual energy of two Gaussians (`1/R`), whose two analytic routes are
  themselves cross-checked to each other.  These exercise the nodes, weights,
  Jacobians, domain truncation and `|r-r'|` geometry — everything except the VV10
  kernel itself, which P1 already referees against a second program.
* **1e positive control** — the pairing that `nlcsplit/step_e_kernel.py` proves
  wrong (`nlc.pair_energy(..., pairing="cross")`, kept in the package as an
  auditable control) is fed to both sides.  If the referee cannot see that error it
  is not refereeing anything.
* **1f Monte-Carlo** — third method, with its own standard error, per
  configuration in `table.md`.
* **1g asymptotics** — at large separation the cross term must follow the kernel's
  own `R^-6` expansion; the fitted log-log slope is compared with -6.
* **1h measurement-massage guard** — the node-set normalisation trap described in
  section 9.3, recorded as a number so the guard is demonstrably not always-true.

## 9. What failed, and what surprised me

### 9.1 The cylindrical radial nodes were mapped to +/- radius, not [0, radius]
Gauss-Legendre nodes live on `[-1,1]`; mapping `s = radius * x` integrates over a
symmetric interval in which the Jacobian `s` cancels the integrand exactly, so
every cylindrical integral returned `0.000000000000` and no error was raised.  It
was caught only because the weights were checked against the **exact** Gaussian
normalisation over a cylinder (`integral_norm_check`).  Both node mappings are now
anchored that way.

### 9.2 "Union of the two boxes" double counts the overlap
The first version of the undecomposed total concatenated the two per-centre cubes.
For `sep = 6, alpha = 1` the cubes overlap heavily, so the overlap region was
counted twice and the "closure" residual was 17.7% of the value — and the closure
test was the thing that screamed.  Fixed by a single coaxial cylinder (5-D) and,
for the referee's own node set, by two boxes **split at the midplane**
(`half_box_pair`), which covers the same region exactly once.

### 9.3 `partition.partition_factors` returns a measure that is not an integral
`partition_factors` hands back `base_w`, each atom subgrid's raw volume element.
Every point of space is covered by *every* atomic subgrid whose sphere reaches it,
so `sum(base_w * f)` integrates `f` once per atom.  Measured here at
`sep = 6, alpha = 1`, PySCF grid level 3, an 8-electron model density:

* `sum(partition_factors base_w * rho)` = **16.000003** electrons,
* `sum(atom_partition weights * rho)` = **8.000003** electrons (expected 8).

Every block built on `base_w` is therefore inflated by `natm` in the
weights, i.e. the pair blocks by `natm^2 = 4` (observed ratio 4.0007 on `E_NL`).
**Corrected 2026-10-01, after measuring the factor on a real molecule: it is not
exactly `natm` at usable grid levels, so it is not a constant that can be divided
out.**  On H2O2/6-31g\* (`natm = 6`) with `h = exp(-|r-(0,0,0.2)|^2)`, whose integral
is the closed form `pi^{3/2} = 5.568328`, `sum(base_w * h)` = 35.874 / 33.827 / 33.308
at grid levels 1/2/3, i.e. 1.0738 / 1.0125 / 0.9969 times `natm * pi^{3/2}`.  The recipe
that *is* anchored is the owner-masked one,

```
int s_a h  ~=  sum_{i: owner(i)=a} base_w_i * S[i,a] * h(r_i)
```

whose sum over `a` reproduces `pi^{3/2}` to 1.5e-05 / 1.8e-06 / 1.0e-07 relative at those
three levels, with per-fragment values stable to six digits between levels 2 and 3; the
`base_w / natm` patch misses it per fragment by 7-13%.  This is pinned by
`nlcsplit/tests/test_partition_factors.py::test_soft_attribution_owner_masked_matches_analytic_gaussian`,
itself checked two-sided — swapping the unmasked recipe into that test makes it fail with
`35.874 != 5.568`, so the assertion is not always-true.
`nlcsplit`'s production path (`step_h_s22.py`, `step1_validate.py`, ...) uses
`atom_partition`, whose weights already carry the Becke factor, and is **not**
affected — but `nlcsplit/tests/test_fastpair_ide.py` (the `partition_factors` +
`soft=S.T` branch, around its lines 378-395) does use that combination, and it cannot
see the factor: it feeds the *same* `base_w` to the screened path and to its own
reference, so `natm` cancels in the ratio being asserted.  That is the general lesson —
an assertion that compares two implementations on one shared measure is not a check of
the measure.  Nothing in this directory quotes a number off that branch, and every node
set used here is normalisation-guarded, so no number in these outputs carries the factor.

### 9.4 The half-factor question was not free
`inter[(A,B)]` corresponds to `I_AB` and `intra[A]` to `0.5 * I_AA` (section 4).
Assuming `2 I_AB` or `I_AA` would have produced a discrepancy of the order of the
quantity itself.  The tables print both the block and its reference.

### 9.5 The positive control is weaker on these densities than on water
The wrong pairing shifts `E_NL` here by an order of magnitude less than the
`+0.138 kcal/mol` the package documents for the water monomer, because a diffuse
Gaussian pair has small `|grad rho|/rho^2` where the two pairings differ.  The
measured shift and the measured attribution discrepancy are of comparable size, so
this referee resolves the attribution question only **relative to its own
uncertainty**, which is reported alongside; it is not a high-resolution kernel
spectroscope on synthetic densities.

### 9.6 What I could not falsify
The quadrature machinery was falsified three times (9.1, 9.2, and an early
`pts`/weights axis-order bug that made the Cartesian and cylindrical codes
disagree with the closed forms).  After those fixes I could not construct a test
that breaks it: every deliberately wrong variant I could think of (wrong pairing,
wrong node mapping, double-counted domain) is caught by one of the anchors above,
and each anchor has a denominator reported in `validation.md` (how many points,
which kernel, which closed form) so a vacuous "0 deviations" cannot hide.

## 10. Limits of this referee

* It referees the **attribution rule** (Becke/nearest-atom region assignment)
  against the density-factor assignment, on a density where the latter is exact.
  It does not certify `b`, `C`, or the kernel algebra — P1's cross-program anchor
  does that for differences.
* Homonuclear, equal-exponent, 4+4 electrons **in the two archived runs**.  An earlier
  version of this bullet stopped there and gave a reason for not going heteronuclear:
  the package side is evaluated on a PySCF grid whose Becke radii come from the atom types
  in `mk_mol` (two `He`), so making the centres unequal forces a choice of element - a
  choice of the partition convention under test - before any number means anything.
  **That reason was wrong in its magnitude and the referee now covers the case anyway**
  (section 12): two of the three compared quantities need no element at all - the exact
  reference is a six-dimensional integral of an analytic density pair, and the
  density-factor soft partition is defined from the density - and the radii table that the
  third one does read turns out to move the offset by at most 0.24% of itself.
* What is still not refereed here: a chemically realistic density (nuclei, cusps, orbital
  structure).  These are still synthetic Gaussian pairs, and the statement is about the
  attribution machinery as a mathematical operation on a density.
* The reference is a quadrature, not a closed form.  Its error bar is measured
  (order ladder, truncation scan, 3-D vs 5-D, Monte-Carlo), and any claim about the
  discrepancy smaller than that error bar would be unsupported.
* Literature anchor: **TODO** — a published per-fragment VV10 attribution for a
  two-centre model density would be a third, external opinion.  None was fetched
  or cited here (requirement R5: no network lookups, no invented citations).

## 11. Results

`outputs/summary.md` is the table to read: it carries the reference's own combined
error bar and, per configuration, whether the discrepancy exceeds it.  Regenerate it
without re-quadrating anything:

```
wsl -e bash -lc 'cd <REPO> && PYTHONPATH=. python3 -u evidence/attribution_referee/summarize.py'
```

Adopted reference uncertainty, all three components measured (worst over the six
ladder configurations): order-ladder last change 6.134e-07 Ha, domain-truncation
shift 2.026e-06 Ha, Cartesian-3D vs cylindrical-5D disagreement 7.965e-06 Ha, giving
**U = 1.060e-05 Ha = 0.00665 kcal/mol**.

* `d_headline` (package `inter[0,1]` on the PySCF production grid minus exact `I_AB`):
  min-abs 1.682e-08, median 5.576e-06, max-abs **1.256e-04 Ha** = 0.0788 kcal/mol.
* `d_partition` (same node set, Becke block minus density-factor block, grid cancels):
  agrees with `d_headline` to 8e-07 Ha everywhere ⇒ the discrepancy is the attribution
  rule, not the grid.  `d_grid` (density-factor block minus the exact reference) stays
  below U at every configuration, worst 7.96e-07 Ha: **the package's own summation code
  reproduces the partition-free reference when handed the exact density factors.**
* Resolved against U: **5 of 12 configurations** have |d_headline| > U (2x, 3x, 4x, 3x,
  12x).  The other 7 are smaller than the reference's own error bar, so this referee
  does not say the convention is right there — it says it cannot tell.  U is bounded by
  the 3-D Cartesian versus 5-D cylindrical disagreement (7.97e-06 Ha) — two deterministic
  node sets differing in shape and Jacobian — not by a lack of order in either ladder.
* **A second, independent and much tighter bar resolves all 12.** `mc_tighten.py` re-runs
  the Monte-Carlo route at 4,000,000 draws per configuration and writes a separate sidecar
  (`outputs/mc_tight.json`), so neither archived `results.json` is disturbed by it.  The
  bar is `max(2 s.e., |MC − 5-D|)`: the estimator's own scatter, plus the observed gap
  between the Monte-Carlo and the 5-D value, which is where any systematic they share
  would surface.  Worst over the 12 configurations: 1.819e-06 Ha = 0.00114 kcal/mol,
  **5.8x tighter than U**, and every offset clears it.  `summarize.py` prints the two
  counts side by side (12 of 12 against the Monte-Carlo bar, 5 of 12 against U) because
  they answer different questions; neither is quietly substituted for the other.
  The sidecar is deterministic apart from one field: two consecutive runs of
  `mc_tighten.py` differ in `meta.runtime_s` and in no other key of `meta` or of the 12
  rows, checked field by field. It was regenerated once after the script's sibling import
  was switched from `evidence.attribution_referee.referee_lib` to the plain
  `import referee_lib` the other scripts in this directory use (the dotted form made the
  export gate read `evidence` as an undeclared distribution); that regeneration is why the
  sidecar's hash moved while 1.819e-06 Ha, 9.09e-07 Ha and 12/12 did not.
* Relative sizes where resolved: 0.74-1.84% of the whole VV10 term, 2.5-5.2% of the
  cross term; the single largest relative offset, 11.79% of `I_AB`, sits at
  `alpha = 0.5, sep = 10.0` where the absolute difference (3.7e-06 Ha) is below U.
* `E_NL = 1/2 (I_AA + I_BB) + I_AB` closes against an independently integrated
  undecomposed total to 7.9e-06 Ha worst; `I_AB - I_BA` and `I_BB - I_AA` are
  2.7e-18 / 2.3e-17 Ha; the package's own block additivity residual is 1.7e-18 Ha.
* Monte-Carlo (third method, own standard error) agrees with the 5-D quadrature on
  `I_AB` at worst |z| = 2.23 over the 12 configurations.
* Node-set normalisation, the trap in 9.3, is asserted before use: production grid
  7.99999483..8.00000425 electrons, referee nodes 7.99997757..7.99999823 (expected 8).

### 11.1 Two runs, same numbers

The directory holds both runs, so the comparison is re-doable from the shipped files:

| file | which run | wall clock | workers |
|---|---|---|---|
| `results_run1_20261001.json`, `table_run1_20261001.md` | run 1 | 771 s | 12 |
| `results.json`, `table.md`, `run_log.txt`, `rerun_verify_20261001.log` | run 2 | 730 s | 10 |

* `cmp table.md table_run1_20261001.md` — identical.
* Field-by-field diff of the two `results.json`: **14 mismatches, and every one is a
  `runtime_s` field or `meta.nproc`.**  No scientific quantity moved, not in the last
  digit — including the Monte-Carlo block, which is seeded.
* Diffing the two transcripts ignoring timing lines: one difference, the worker count
  printed in the header.

Run 2 was deliberately run *alongside* other jobs on this box (the test suite and two
numerical probes were executing at the same time), which is why its per-row timings
differ by up to 2.7x while its numbers do not differ at all.  That is the reproducibility
claim this directory makes about itself, and it is stated as a file comparison rather
than as a sentence.


## 12. Heteronuclear extension (`hetero.py`, `outputs/hetero.json`)

Run 2026-10-01, Monte-Carlo m = 1,000,000 per configuration, same orders and truncation
as the main table, same production-grid call (`partition.atom_partition`, level 3,
`scheme="becke"`).  Full stdout: `outputs/hetero_run_20261001.log`.

**The falsification first.**  Row 0 is homonuclear and labelled `He/He`, exactly as
`run.py` labels its centres, so its numbers must equal the archived
`(alpha = 1.0, sep = 4.0)` row or this script is a divergent copy.  Measured:
`I_AB` differs by **0.000e+00** and the package cross term by **0.000e+00**.  Bit-exact,
not within tolerance.

**What the element choice is actually worth.**  Each density is run twice, with different
atom labels at the *same* analytic density, so the radii table is the only thing that
moved:

| density (n_A, n_B) | labels | d_headline (Ha) | fraction of I_AB | label sensitivity |
|---|---|---|---|---|
| (4, 4) control | He/He vs Be/Be | -3.1406e-05 vs -3.1332e-05 | -6.41% / -6.39% | 7.4e-08 = 0.24% of the offset |
| (2, 4) | He/Be vs He/Ne | -9.1915e-06 vs -9.1951e-06 | -6.18% / -6.18% | 3.6e-09 = 0.04% |
| (2, 6) | He/C vs He/Be | -5.7651e-05 vs -5.7671e-05 | -35.93% / -35.94% | 2.0e-08 = 0.03% |
| (4, 6) | Be/C vs He/C | -2.5276e-04 vs -2.5276e-04 | -15.33% / -15.33% | below the printed digits |

So the objection written into section 10 yesterday - that making the centres unequal
forces a choice of the convention under test - is empirically worth at most a quarter of
one percent of the quantity being measured.  It was not a reason to stop.

**What the heteronuclear case adds, and it is not reassuring.**  The symmetries that the
homonuclear table checks for free become real tests here: `|I_BA - I_AB|` = 3.5e-19,
2.7e-20 and 3.7e-18 Ha on densities where the two centres share nothing but the kernel,
and `|I_BB - I_AA|` is 1.1e-03, 7.4e-03 and 5.8e-03 Ha - i.e. non-zero, as it must be.
Block additivity still closes to 2.2e-19 - 1.7e-18 Ha, and the undecomposed-total closure
to 4.3e-06 Ha worst.

But the **attribution offset grows**: against the same exact reference, the owner/Becke
cross term sits 6.2-35.9% of `I_AB` on the heteronuclear pairs, where the homonuclear
scan put it at 2.5-5.2%.  The worst case here (alpha = 1.0 against 0.5, 2 electrons
against 6, sep = 6 bohr) is **-5.77e-05 Ha = 36% of the cross term**, resolved against an
error bar of 8.5e-07 Ha.  Every configuration is resolved against its own bar, so this is
not noise being read as signal - it is the non-uniqueness of grid-point attribution being
larger where the two fragments' densities are dissimilar, which is exactly the regime an
EDA is asked to work in.  The homonuclear table understated it.
