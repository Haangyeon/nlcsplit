# Pair Attribution of the VV10 Nonlocal-Correlation Term, and the Grid-Partition Dependence It Inherits

Angran Xia\* and Changwei Wang

School of Chemistry & Chemical Engineering, Shaanxi Normal University, Chang'an Campus,
Xi'an 710119, Shaanxi, China

\* Corresponding author. E-mail: `haangyeon@snnu.edu.cn`; ORCID 0009-0006-3366-6054. The
second author's ORCID and e-mail are still to be supplied by him and are not guessed here.
Both names, the institution and the campus postcode were supplied by the authors on
2026-09-30; the school's English wording is taken from the school's own English site rather
than translated by us. The Chinese forms of both names are recorded in `CITATION.cff` and in
`paper/software.md` and are deliberately not typeset here: this file goes through a pdflatex
with no CJK font, and `tools/md2tex.js` refuses characters it cannot map rather than dropping
them silently.

Number provenance is tagged `[S#]`; the tag-to-artefact table is the appendix at the end of
this file, mirrored in `paper/tex_audit.md`. The literature search behind the no-precedent
claim is described where its own limits are stated (§1 and §6).

---

## Abstract

The VV10 nonlocal-correlation term [[vydrov2009vv10]] of range-separated hybrid
functionals is a double sum over pairs of grid points, and the kernel we audited
folds that sum into per-point values before returning it, which destroys the pair
index. We evaluate the double sum explicitly, keep the (i, j) index, and attribute each
grid point to atoms and fragments through a real-space partition, so the term resolves
into intra-fragment and inter-fragment pair blocks. The split loses nothing in the
continuum: the term's local part is beta times the electron number, which cancels in
any superposition difference. On a grid that cancellation is a measured residual rather
than an identity, 0.0000 to 0.0011 kcal/mol over the six cells checked at grid level 1
on one common grid [S33]. On a fixed density the explicit sum reproduces PySCF's own
kernel to 5.7e-06 kcal/mol, and its superposition differences agree with ORCA 6.0.1's
independently computed `NL Energy, E(C,NL)` to under 1% of the term for all
eight complexes examined. Applied at omegaB97X-V/6-31G* to the eight S22 complexes,
association-time nonlocal correlation is carried almost entirely by point pairs straddling
the fragments - the inter-fragment block is 0.92-1.08 of the frozen-density superposition
difference in the six systems checked against a counterpoise reference - while the
nonlocal and semi-local parts of the exchange-correlation change are not locked in a
fixed ratio. The attribution choice does not collapse either: 0.004-0.247
kcal/mol absolute, with no pattern by interaction type, so a fragment-resolved nonlocal
energy needs a per-system error bar. We found no published
implementation that resolves this term into fragment pairs, and the index is not free: of
33 timed screened/exact pairs on an unloaded machine none beat the exact sum, because the
tightest provable block bound found in a real dimer is loose by a factor of 2.4e5
[S25].

## 1. Introduction

Range-separated hybrid functionals with the VV10 nonlocal-correlation
functional — ωB97X-V [[mardirossian2014wb97xv]] and ωB97M-V
[[mardirossian2016wb97mv]] in particular [[calbo2015vv10review]] — have become a default choice
for non-covalent interactions. The nonlocal term is a two-electron-density
double integral over all pairs of grid points,

E_NL = ½ ∫∫ ρ(r) ρ(r′) Φ(r, r′) d³r d³r′,

and every production quantum-chemistry package we have examined evaluates it in a
way that destroys the pair index: PySCF's `nr_nlc_vxc` calls its own C kernel
`libdft.VXC_vv10nlc`, which bins the kernel and returns only point-folded values.
We have not audited the equivalent paths inside libxc [[lehtola2018libxc]], ORCA, Psi4 or Gaussian -
libxc is not one of them and cannot be made into a numerical referee: the two
libxc shared objects on this machine (conda-forge 5.2.3 and the 7.0.0 bundled with
PySCF) export `xc_nlc_coef` and nothing else among thirteen probed nonlocal entry
points - no `xc_nlc_vxc`, no `xc_run` - which matches libxc's own statement that this
class of van der Waals term "cannot be evaluated with the local density information
provided to Libxc, and must be handled by the calling program". libxc therefore
supplies the parameters (b, C) keyed by functional name, not an independent value of
the integral, so an agreement claim against it would be a category error (see §4,
`RESEARCH-20260929-lit.md` §8.3, and `evidence/recompute/20260929T110830Z_libxc_referee.out`
for the symbol audit). PySCF's nonlocal term comes from its own `nr_nlc_vxc`
implementation, not from libxc. The consequence we do demonstrate is
structural rather than numerical: once the double sum has been folded into a
per-point energy density, as ours does not, the question "how much of this
nonlocal correlation belongs to the interaction between fragment A and fragment
B?" has no answer inside that evaluation.

We provide that answer. `nlcsplit` evaluates the same double sum explicitly,
keeping the (i, j) pair index, and attributes each grid point to a fragment
through a real-space partition, so that E_NL decomposes into intra-fragment
blocks E_AA and inter-fragment pair blocks E_AB. Evaluating the sum explicitly is
not itself new: JuNoLo post-processed a converged density from another code with
the nonlocal term, at the same N² cost, in order to obtain an improved *total*
energy on massively parallel hardware [S14]. What is absent from that work - and
from the production kernels - is the attribution. JuNoLo in fact recommends
against fragment-style treatments for the weakly-bound cases where fragments are
distinguishable, reserving itself for chemisorption "where one cannot tell apart
fragments of the bonded system" [S14]; the present paper works precisely in the
regime where they are. The decomposition is exact by
construction — the sum of the blocks reproduces the total to machine precision
— but exactness is not the point and we do not sell it as such: grouping the
summation indices is trivially additive. Two things are not trivial, and they
are the content of this paper.

The first is **attribution**. The non-uniqueness lives in which fragment owns
each grid point (and, in the same spirit, how the local term β∫ρ is assigned),
not in how the sum is grouped. We therefore quantify the spread over four
published real-space partitions — Becke, Becke with the radius adjustment,
Becke–Treutler, and Stratmann's — on eight S22 complexes, and report it as a
per-system uncertainty rather than asserting one scheme as correct. The spread
is 0.004–0.247 kcal/mol in absolute terms and 0.8–18.2% relative to |E_AB|,
and it shows no systematic ordering by interaction type: the parallel-displaced benzene dimer
sits at 0.8% while benzene–water sits at 18.2% [S2]. Nor does a better
one-electron basis remove it: on the official water-dimer geometry the spread
stays 0.041-0.044 kcal/mol across the four basis sets beyond STO-3G (0.030 in STO-3G
itself, where the quantity is smaller too) while the quantity itself
drifts by 0.18 kcal/mol along the same ladder (section 3.4, [S12]). A single
blanket uncertainty figure would misrepresent the data; we
report it system by system.

The second, and chemically the more consequential, is **what the term actually
is**. Within a hybrid functional the exchange-correlation contribution to an
interaction energy splits as ΔE_xc = ΔE_xc^rest + ΔE_NLC, where "rest" collects
the semi-local exchange-correlation and the fraction of exact exchange, and the
local piece β∫ρ drops out of any superposition difference identically — β is a
constant and ∫ρ equals the electron count, so Δβ∫ρ vanishes to 3.7×10⁻⁵
kcal/mol in our level-1 test [S3]. That leaves the double sum as the only part
of the nonlocal term that can carry inter-fragment structure, and measuring it
shows that treating it as "the dispersion" is unsafe. For the water dimer it
supplies 16% of ΔE_xc. For the two benzene dimer configurations of S22 the
same quantity ranges from 52% to 97% [S4] — and those two structures differ
only in the relative orientation of the same pair of molecules, so the failure
of the identification is visible within one chemical system, without any
cross-system comparison. In the methane dimer the nonlocal term exceeds the
whole of ΔE_xc (ΔE_NLC = −0.517 against ΔE_xc = −0.232), i.e. the rest of the
exchange-correlation is net repulsive there.

Our positioning relative to the closest prior work is specific, and the title is
written to be specific rather than to sound broader: this is one already-parameterised VV10
double sum, in one implementation, asked where its own grid says the pieces belong.
Dasgupta and Paesani [[dasgupta2023]] decompose interaction
energies of dispersion-corrected functionals with second-generation ALMO-EDA
(E_Int = E_Pol + E_Frz + E_CT + E_Disp) and obtain E_Disp as a difference against a
dispersion-free reference: they treat the VV10 correction as one undivided block and ask
whether that block is accurate. We work inside that block. Heßelmann
[[hesselmann2013nldft]] partitions his own nonlocal scheme's correlation energy into
atom-atom contributions - the abstract of that paper says so in as many words - so
attributing a nonlocal correlation term to atoms is not ours and is not claimed here.
JuNoLo [[lazic2010junolo]] [S14] evaluates the nonlocal double sum explicitly, at the same
N² cost, but post-processes a converged density into an improved *total* energy, and
recommends itself for bonded systems "where one cannot tell apart fragments", directing
separable cases elsewhere. Hyldgaard, Berland and Schröder [[hyldgaard2014interp]] read the
same quantity as a coupling of zero-point energies of semilocal exchange-correlation holes:
a real-space *interpretation*, and the strongest available objection to calling the term
unanalyzable, so we keep the distinction explicit - they interpret the kernel and the holes,
we take an already-evaluated E_NLC and *bookkeep* it against named fragments and atom pairs,
then report how much the bookkeeping itself moves the answer.

What survives that comparison is specific: taking an existing, already-parameterised VV10
double sum on a numerical integration grid, resolving it into named fragment and atom pairs
without changing the total, and measuring how much the attribution itself - not the energy -
moves when the partition scheme is changed. A formal Web of Science search over the Core
Collection (58,664,816 records, 2026-09-29) found no precedent for that [S16]: the two
strings written closest to our own claim both return zero records, and the non-zero strings
were enumerated in full through the database's own record endpoint, so every returned record
was read rather than the top one. The nearest neighbours are each attributable in one
clause. Kruse, Banáš and Sponer [[kruse2019dna]] benchmark VV10 among 29 functionals and
decompose the *total* interaction energy by SAPT; Hujo and Grimme [[hujo2011hbond]]
benchmark VV10 for hydrogen bonds; Sinha and Pavanello [[sinha2015fdevdw]] construct a
*new* subsystem-based nonlocal functional rather than resolving an existing one; Hamada and
Tsukada [[hamada2011c60au]] attribute an *adsorption energy* to the term, the opposite
direction; Vydrov and Van Voorhis [[vydrov2010simple]] re-derive the nonlocal construction
itself; and two further result lists of 33 records each - one spanning the whole "van der
Waals density functional" [[dion2004]] x "nonlocal correlation" topic, one crossing
"nonlocal correlation" with the partition schemes themselves (Becke, Hirshfeld, Mulliken,
atoms-in-molecules) - contain, on reading every title, no application of an atomic partition
to the VV10 double sum.

Two cautions about that instrument belong with the claim, because a reader who does not know
them will over-read the zeros. A keyword-shaped novelty query is narrower than the claim it
is meant to test: the first round of the search [S1] covered the decomposition vocabulary and
missed Hyldgaard et al. entirely, a paper whose abstract shares no term with any of our
keywords, and the broadest topical query available is what surfaced it. And the open indexes
tried first - OpenAlex and Crossref - retrieve a known title reliably when the query
resembles its title but miss that same exactly-on-topic paper for legitimate topical
phrasings, at 0/4 each [S15]; they are known-item lookup tools here, not topical search, and
their zeros are not read as absence. The calibration behind both statements, and the
single-index coverage limit of the search, are in section 4.4.


Two limits are stated here rather than in a closing section, because both
bound what the numbers may be used for. First, this is not an energy
decomposition analysis: we do not separate electrostatics, exchange-repulsion,
polarization or charge transfer. Counterpoise-corrected interaction energies are
reported for all eight systems (§3.2), so on the total interaction energy basis-set
superposition error is measured rather than assumed away. The VV10 column of Table 1
is not one of those corrections: it is the uncorrected superposition difference, and
its own superposition error has been measured on three of the eight cells, where it
comes out 0.17, 0.11 and 1.87 times that cell's attribution span (§4.1, [S32]) - so
the second number is the one place the attribution uncertainty is not the largest
numerical effect we have quantified. Second, the explicit
sum is not more accurate than the production kernels it is compared against —
the interpolation residual of PySCF's native kernel is of order 4×10⁻⁶
kcal/mol, far below any chemical interest, and the ≈0.1–0.9 kcal/mol offsets
that an earlier version of this work attributed to interpolation were in fact
a pairing error in our own kernel. The value of the explicit implementation is
that it retains the pair index, nothing more.

## 2. Method

### 2.1 The VV10 kernel and the pairing convention

With ρ the electron density and σ = |∇ρ|²,

w0(r) = √( C σ²/ρ⁴ + (4π/3) ρ ),  κ(r) = b (3π/2) (ρ/9π)^{1/6},
g = w0(r_i) R² + κ(r_i),  g′ = w0(r_j) R² + κ(r_j),  Φ = −3 / (2 g g′ (g+g′)),

with (b, C) = (6.0, 0.01) for ωB97X-V, and E_NLC = E_NL + β∫ρ,
β = (1/32)(3/b²)^{3/4}. The pairing of ω and κ in g and g′ is a genuine choice,
and the cross pairing g = w0(r_j) R² + κ(r_i) — which an earlier implementation
of ours used — is wrong: it raises monomer energies by +0.1379 kcal/mol for water,
+0.4182 for argon and +0.1346 for methane at grid level 1, and +0.9057 for benzene at
level 0, and the offset is itself
grid-dependent, so it cannot be subtracted as a constant [S1, S5]. The
same-centre pairing above reproduces PySCF's native kernel to 5.7e-06 kcal/mol on the water
dimer's complex - the two monomer rows of the same archive give 4.1e-06 and 3.8e-06
[`evidence/centos/20260928T193520Z_centos-step_h_l1.out`], and this sentence said "on the water
monomer" while quoting the complex's row until a 2026-10-05 re-derivation caught it - and agrees with an independently written script that evaluates the
same quantity by a different code path to 1.24×10⁻⁴ kcal/mol worst case: against the
script's self-consistent column the difference runs from -1.058×10⁻⁴ (level 0) to
-1.242×10⁻⁴ (level 8) and back to -1.230×10⁻⁴ (level 9), same sign at all ten levels and
no drift with grid density (level 9 carries 430,768 integration points, of which 428,920
survive the density floor); its fixed-density column differs only at level 0
(-1.056×10⁻³), where that column is itself the outlier [S21]. A
second program has since been brought to bear on the same quantity - ORCA 6.0.1, on all
eight systems, with every residual below 1% of the term - but its grids are not
matched to
ours, so that anchor is quoted as a joint grid-plus-kernel difference in §4 rather than
as a kernel-only check here.

### 2.2 Blocks, half-blocks and additivity

`pair_energy(A, B)` returns the half block ½ Σ_{i∈A} Σ_{j∈B} w_i w_j Φ_ij, so
that the inter-fragment term reported by `fragment_decomposition` is
E_AB = 2·pair_energy(A,B) and

E_NL = Σ_A E_AA + Σ_{A<B} E_AB

holds by construction. That identity is why the check quoted here is not the package's own
assert: comparing a block sum against the total the sum defines would be a guard with no way
to fail, and until 2026-10-06 that is what the in-package assert was. The published residuals
come from an archive that re-evaluates all kept points in one monolithic double sum and
compares the block sum against that independent number, and `closure_check=True` now does the
same inside the package - off by default, because the reference doubles the summation and the
production sweep does not pay for it. The test suite keeps the guard honest: one cross term is
counted twice, then dropped, and the check must fire both times [S33]. What the check still
cannot see has to be stated with it, because it shares its inputs with the quantity it audits
- the pair kernel, the density floor that decides which points are kept, and the owner array
itself are common mode, so a wrong far-field kernel or a mis-assigned owner moves both sides
together and leaves the residual at zero. Those are attacked where they are not shared: the
kernel against PySCF's own and against ORCA (§4.2), the assignment against a partition
reference built outside the package (§4.3). The census itself is generated rather than
asserted: `evidence/recompute/additivity_census.py` re-runs
the check on the water dimer at level 1 (four schemes plus the nearest-atom control on the common
grid) and on both benzene-dimer geometries at level 0 - the parallel-displaced S22_11 entry and
the constructed sandwich - giving 13 rows over three systems, with the residual spanning
0.000e+00 to 5.551e-17 Ha, the largest from the Becke--Treutler row of S22_11
[`evidence/recompute/20261005T0410Z_additivity_census.out`]. An earlier version of this paragraph
claimed 0.00-6.94e-18 Ha "across all systems and partitions reported here": that interval came
from one archive of one system, its lower bound was not any run's reading, and no benzene row was
in it. Every row stays below the check's own 1e-10 Ha threshold. The same archive records that
the level-0 grids integrate the electron number to 2.1e-04-7.2e-04 relative on the 24-atom
systems - a property of the benchmark's coarsest grid, not of the decomposition - which is why
the residual is quoted against 1e-10 Ha rather than against machine zero. R² is evaluated through the polarisation identity
|a|²+|b|²−2a·b in blocked gemm operations rather than through an explicit
displacement tensor, which reduces peak memory by roughly a factor of five at
this system size.

### 2.3 Attribution schemes and the far-field cut

Grid points are assigned to atoms by PySCF's own partition machinery
(`gen_grid.get_partition` with `radi.BRAGG_RADII`), in four variants — Becke
[[becke1988]] with the bare interatomic-distance exchange function, the same function with
Becke's own radial adjustment (`radi.becke_atomic_radii_adjust`), the same function with the
radial adjustment of Treutler and Ahlrichs (`radi.treutler_atomic_radii_adjust`)
[[treutler1995]], and Stratmann's variant [[stratmann1996]] — plus a nearest-atom hard
partition on the common grid as a control. Naming four variants makes this sound like four
independent schemes, and it is not: three of the four are one product formula of Becke's
with a different radius table, so the sweep turns two switches (which radial mapping, which
partition kernel), and only the second of them is a different published method. What that
costs in diversity is visible in the side-by-side run of §3.4: on one grid, one weight set
and one density, the four variants give E_AB = -1.3598, -1.1129, -1.1962 and -1.3595
kcal/mol on benzene...water, and the whole term is -31.4256 kcal/mol in every one of those
four rows [S33]. The last part is the structural point rather than a coincidence: on a fixed
grid an ownership choice redistributes the double sum between blocks, it cannot move the
total. The totals that §2.5's Table 1 varies between schemes move because each scheme is
also regenerating its own grid - which is the second of the two switches, and the reason the
published spread is now reported as attribution and quadrature separately (§3.4). Points with ρ below
`rho_floor` (default 10⁻¹²) are excluded from the double sum; across the sweep this
drops 10.7–22.6% of the points, and the points it drops carry at most 2.3×10⁻⁶
electrons. Over the floor interval the sweep accepts (10⁻¹⁰ to 10⁻¹⁴) E_AB moves by
2.1×10⁻¹¹ Ha at grid level 1 and 4.2×10⁻¹¹ Ha at level 2; adding the two outer rungs
at 10⁻⁸ and 10⁻¹⁶ still leaves the reported value unchanged at six decimals in
kcal/mol [S7]. The local term β∫ρ is a one-body functional of the density and is not
pair-resolved; as noted above it cancels identically from superposition
differences, which is what makes it legitimate to decompose only the double
sum.

### 2.4 Geometries and fragment boundaries

All dimer geometries are taken verbatim from the official GMTKN55 repository
(github.com/grimme-lab/GMTKN55, `S22/<NN>/struc.xyz`), fetched by `nlcsplit/tools/get_s22.sh`;
the repository's own citation instruction is Goerigk et al. [[goerigk2017gmtkn55]], PCCP 19, 32184-32215
(2017), DOI 10.1039/C7CP04913G, which we verified by reverse DOI lookup. The S22
database itself is Jurečka et al., PCCP 8, 1985-1993 (2006) [[jurecka2006s22]],
also confirmed by reverse DOI lookup. We do not trace these twenty-two complexes back
beyond that: an attribution to a still earlier hydrogen-bonded benchmark
(PCCP 5, 1811 (2003)) resolves to no Crossref record on two separate attempts
(2026-09-29 and 2026-09-30, queries archived in `evidence/bib_provenance/G_s22_provenance_20260930.md`),
so we cite only the chain that could be pinned. The geometry files we used come from
the GMTKN55 distribution, so our numbers depend on that, not on any earlier compilation.
Fragment boundaries are derived from covalent connectivity with a 1.65 Å cutoff — longer than the longest covalent bond appearing in these
systems (aromatic C–C, 1.397 Å; a general C–C single bond is 1.54 Å) and shorter
than the shortest hydrogen bond (O···H 1.95 Å) — and the code refuses to proceed
unless exactly two fragments result. This is not a formality: in the official
S22 water-dimer file the atoms are ordered so that the fragments interleave,
and a hard-coded index split would mix the two molecules silently. For the
water dimer we additionally report ωB97X-V/6-31G* optimised geometry
(R(O···O) = 2.901 Å, 0.009 Å from the reference value) [S6].

### 2.5 Verification

Two routes to E_NLC are computed and compared at run time, with a hard failure if
they disagree: our explicit pair sum, and PySCF's native kernel
(`numint.nr_nlc_vxc`). These are independent implementations of the kernel but
share a library, so agreement between them validates the arithmetic and not the
functional parameters. A second-program anchor now exists for all eight systems (§4), so
no quantity in Table 1 rests on agreement between two implementations of the same kernel
alone. Energy
accounting is checked independently: for a hybrid functional the exact-exchange
energy is folded into `vhf.exc` by `get_veff` and is absent from `nr_rks`, so
we close e_tot = e_nuc + e₁ + e_coul + e_xc to ≤1.1×10⁻¹⁰ kcal/mol rather than
assuming any particular partition of the XC terms.

Cross-version reproducibility was first checked on one system run twice:
benzene-methane at grid level 2 with
counterpoise, on PySCF 2.12.1 on one machine and PySCF 2.14.0 on another - which is why the
comparison at first looked like a cross-machine one. It is not: the release is now isolated as a
variable by running the same script twice on a single machine with nothing but `PYTHONPATH`
different, and both numbers reproduce (§3.2), so the machine was never the factor. The release
matters enough to state plainly what is in which one: Table 1 carries one row computed on PySCF
2.12.1 (the water dimer, the only row its sidecar records at full precision) and seven rows from
the PySCF 2.14.0 batch, so the table is a cross-release table, and it is defensible only because
the quantities it reports are the ones measured below to agree across releases. The counterpoise
energy is the exception - it is the one reported quantity that does not - which is why §3.2's
functional column is stated in one release.
The same molecule carries three different level-1 point counts across this paper's
archives, and the three must not be read as one another: the grid the self-consistent
field actually builds is 18336 points on the official water-dimer geometry, and that is
the grid every common-grid number of §3.4 sits on [S33]; the four schemes' own
partitioned grid on the same geometry is 19936
(`evidence/recompute/20261005T0410Z_additivity_census.out`); and an explicit grid build on the
same release and geometry returns 20248, which is the unpartitioned reference count the
cross-release probe records [S8]. A sentence used to sit here reading the difference
between the first and third of those as a disagreement between PySCF 2.12.1 and 2.14.0.
It is not: both counts are on 2.12.1, and the same probe prints 20248 for the complex on
*both* releases - the only grid difference it records between them is on the ghost
monomers (16752 against 20248), which is the thing §3.2's release statement is actually
about.

The energies themselves are what the comparison is about: on that official geometry the two releases print E_NLC = +52.9345 and E_xc - E_NLC =
-11757.5276 kcal/mol identically, with a 5.7e-06 discrepancy between the two implementations
of the kernel on each side. That is why the agreement is stated quantity by quantity rather
than as a blanket "digit for digit". ΔE_NLC agrees to 3.3e-4 kcal/mol (-1.404667 vs -1.405),
ΔE_xc to 4e-4 (-2.324590 vs -2.325), ΔE_int to 4.5e-5 (-1.780045 vs -1.780), the attribution span
to 2e-4 (0.213163 vs 0.213) and P_frz[becke] to 1e-3 (-1.441416 vs -1.441), each inside the
0.001 kcal/mol to which the second run prints. Those five full-precision pairs are not transcribed:
`evidence/l2cp/cross_version_pair.py` reads the two harvest sidecars and prints the table, which is
archived as `evidence/l2cp/20261004T0100Z_cross_version_pair_benzmeth.out` [S8]. The one quantity that does not agree is the
counterpoise interaction energy itself: -1.341 vs -1.202 kcal/mol, a difference of 0.139 that
is two thirds of the level-2 attribution span of the same complex. That last split is no longer
an unexplained one. It has since been reproduced with the version as the *only* variable - the
same script on the same machine under both releases, three systems and both grid levels - and the
answer is the grid attached to the ghost atoms: 2.14.0 gives a monomer whose partner is present
only as basis functions the same number of points it gives the full complex, while 2.12.1 gives it
17-21% fewer. Everything else, including every uncorrected quantity, is point-for-point and
digit-for-digit identical [S31, §3.2]. What remains untested is the other half of the original
sentence - whether an attributed pair term can escape the grid its density was integrated on.

What the observation does settle is a constraint on usage: the attributed quantities are the version-stable ones, and a counterpoise energy is not
a safe denominator for them [S8].

---

## 3. Results and discussion

### 3.1 Two different things previously reported as one number

Comparing our explicit pair sum against PySCF's native kernel produces a
discrepancy whose size depends entirely on *which grid* the comparison is made
on, and the two cases must not be quoted side by side. Holding the density and
the grid fixed and varying only the evaluation of the kernel, the difference is
+1.5e-8, +1.0e-8 and +8.5e-9 Ha at grid levels 0, 1 and 2 — flat in level,
because it is a discretisation property of the interpolated kernel itself.
Moving the same sum onto the Becke-partitioned grid of `gen_grid.get_partition`
instead gives -0.0282, +0.0015 and +0.0001 kcal/mol, which tracks the ability of
the grid to represent the density at all: the same three levels integrate the
electron number to -1.6e-2, +3.0e-4 and -6.6e-6 electrons away from the exact
value. The second row is a property of the grid, not of our algorithm, and it
disappears as the grid is refined [S9]. A residual of the size of the first row
is what a reference implementation should look like; a residual of the size of
the second row is what a coarse grid looks like from the inside.

### 3.2 The nonlocal term is not a fixed fraction of the exchange-correlation term

Table 1 reports omegaB97X-V/6-31G* results for eight S22 systems at the official
GMTKN55 geometries. The quantity of interest is dE_NLC, the change in the
nonlocal correlation energy on bringing two fragments together from infinity at
fixed density, and its ratio to the total dE_xc for the same process. The
remainder, dE_xc^rest = dE_xc - dE_NLC, is the semi-local exchange-correlation plus
the fraction of exact exchange; it is tabulated explicitly in
`MAIN-skeleton.md` table 4b and is recoverable from these two columns by subtraction.

![Per-system split of the superposition exchange-correlation change into the VV10 term and the rest of ΔE_xc minus ΔE_NLC](figs/fig1_xc_split.png)

**Figure 1.** The same quantity two ways, per system: the VV10 term ΔE_NLC and the remainder ΔE_xc - ΔE_NLC (semilocal exchange-correlation plus the exact-exchange fraction), both for the superposition difference at grid level 1 and uncorrected density. The remainder is negative for seven of the eight systems but positive for the methane dimer (+0.285 against a VV10 term of -0.517 kcal/mol), the one case where the semi-local remainder is itself repulsive and the nonlocal term alone provides the binding. The other seven span -0.119 to -3.115 kcal/mol, so no single fraction of ΔE_xc belongs to the VV10 term. Data: `nlcsplit/logs/step_h.json`, produced by `nlcsplit/step_h_s22.py`; drawn by `nlcsplit/figures.py` [S2].


| System | atoms | dE_int | dE_xc (total) | dE_NLC | share of dE_xc (only where it is defined) |
|---|---|---|---|---|---|
| benzene dimer (A, parallel-displaced) | 24 | -3.580 | -4.486 | -4.367 | 97% |
| benzene dimer (B, T-shaped) | 24 | -3.188 | -4.555 | -2.388 | 52% |
| benzene...water | 15 | -4.342 | -4.012 | -1.259 | 31% |
| benzene...ammonia | 16 | -2.928 | -2.915 | -1.327 | 46% |
| benzene...methane | 17 | -1.785 | -2.322 | -1.404 | 60% |
| water dimer | 6 | -7.816 | -3.708 | -0.593 | 16% |
| ammonia dimer | 8 | -5.167 | -0.881 | -0.678 | 77% |
| methane dimer | 10 | -0.664 | -0.232 | -0.517 | n/a (see note) |

All entries in kcal/mol, all at grid level 1. The two benzene rows were tabulated at level 0 in an earlier version of this table; moving them to level 1 shifts dE_NLC by 0.081 (A) and 0.013 (B) kcal/mol. Level 0 is therefore not adequate for a 24-atom aromatic dimer, unlike the six-atom water dimer where levels 1 and 2 agree to the last digit (section 3.2).

**Why the methane row has no share.** Its ratio is |dE_NLC|/|dE_xc| = 2.2, which trips the
cancellation test that ships with the code (`nlcsplit/step_f_dispersion.py`: above 2, the
denominator is reported as two signed terms, never as a percentage - here -0.517 plus a
semi-local remainder of +0.285). Quoting that ratio as a share - it is 2.2, so more than
twice the whole change - would have advertised a figure whose
divisor is an accident of two larger numbers. What that row does support, without any
forbidden ratio, is a comparison against a physical quantity: at level 2 with a
counterpoise correction the whole interaction energy is -0.376
(`evidence/l2cp/20261003T0907Z_wsl2121-cp_levels.out`) while the nonlocal term
alone is -0.517 [`evidence/l2cp/20260928T213839Z_centos-step_h_l2cp.out`, whose
nonlocal column is what the version test of §3.2 found to be version-insensitive],
i.e. the VV10 term exceeds the net binding by 37% of it. That excess is 0.141 kcal/mol - it was
0.051 while this cell still carried the other release's counterpoise value, which is what a
one-environment column changes - and it is 141x the cross-program residual
of the nonlocal term for this very system (0.0010
kcal/mol, `evidence/orca_widen/cross_program_table.txt`) and about 3x10^3 the
cross-release reproducibility of the *uncorrected* interaction energy (4.5e-5 kcal/mol, §2.5) - so the
excess is a measurement rather than noise, even though the ratio of the two numbers
behind it is still not something we may print as a share. It is, however, only 1.6x the
cross-release sensitivity of this same counterpoise cell (0.089 kcal/mol, §3.2), which is the reason the
37% is stated to two figures and not four.
The final column is the reason this decomposition is worth having: the nonlocal
term ranges from one sixth to more than the whole of the rest of XC, and in the
methane dimer it exceeds it, so that the remainder of the XC contribution is
*repulsive* while the nonlocal term alone provides the binding. No single
fraction of dE_xc can be assigned to VV10 across a benchmark set, and the two
geometries of the same 24-atom benzene dimer (97% vs 52%) show that the ratio
is a property of the arrangement, not of the pair of molecules.

For the six systems with at most 17 atoms we
additionally re-ran the whole table at grid level 2 with a full counterpoise correction - six of
the eight; the two benzene-dimer geometries have no level-2 *row of this table*, and
benzene...methane needed a separate run after its first attempt was cut off by a
four-hour wall-clock budget [S10]. What does exist for the two benzene dimers at level 2 is
their counterpoise-corrected binding energy, computed for §3.2 [S28, S29]: a narrower quantity,
which is why the two statements are kept apart here rather than merged into one coverage count. Between levels 1 and 2 neither dE_NLC nor the
interfragment pair term moves by more than 1.0e-3 kcal/mol, but that number is a
statement about storage precision, not a measurement. Every level-2 row in the sidecar is
kept to three decimals, so no level-1 to level-2 difference below 5e-4 kcal/mol is
observable from these files at all. For the water dimer, whose level-1 row carries full
precision (-0.5934948 and -0.6012148 kcal/mol), level 2 prints -0.593 and -0.601 -
consistent to the printed digit, and nothing sharper can be claimed from this evidence.
For the other five systems both rows are three-decimal, so 1.0e-3 there is the rounding
floor rather than a measured change. The counterpoise-corrected interaction energy
comes out at -6.1526 kcal/mol for the water dimer, i.e. a basis-set superposition
error of 1.663, 1.438, 0.285, 1.074, 0.706, 0.439, 1.638 and 0.756 kcal/mol for water, ammonia,
methane, benzene...water, benzene...ammonia, benzene...methane, the parallel-displaced and the
T-shaped benzene dimer - eight systems, all of them the difference of a counterpoise
and an uncorrected interaction energy computed at the same grid level in the same PySCF, the
uncorrected side of the five aromatic systems measured for this purpose in
`evidence/l2cp/20261003T1025Z_wsl2121-dtot_aromatic.out` [S10, S31]. Until that file existed the
last three of those numbers were the difference of a 2.12.1 counterpoise value and a 2.14.0
uncorrected one, defended by the claim that the uncorrected side is version-insensitive - a claim
measured on three hydrogen-bonded dimers and then used to vouch for complexes it had never been
tested on. It holds (the three aromatic cells reproduce the older batch to the three decimals
that batch prints), but it now holds on its own evidence. Those numbers are also a revision in
themselves: the same three cells used to read 1.687, 1.491 and 0.196, taken from a batch computed
in a different PySCF, and §3.2's last paragraph gives the size and the cause of the difference. The core
quantities of this method are therefore converged
one grid level before the total binding energy is; a user who only wants dE_NLC
can stop at level 1.

**Is -6.1526 the right answer?** Not a question about the nonlocal term, but it is a
question the paper invited, and it now has a measurement instead of a caveat. At the same
official S22 geometry, the same 6-31g\* basis and the same counterpoise convention,
coupled cluster gives dE_int = -4.8789 kcal/mol at CCSD(T) with frozen oxygen 1s
(-4.8821 all-electron, so the frozen-core choice is worth 0.003 here), and -3.7035, -4.3316,
-4.3474 and -4.7287 at cc-pVDZ, aug-cc-pVDZ, cc-pVTZ and aug-cc-pVTZ respectively [S24, S30].
Three things follow. At fixed basis our functional binds 1.27 kcal/mol *more* strongly than
correlation does in the same basis - not less, which is what an earlier version of this
paragraph said, and the reason it said so is the subject of the next paragraph. As the
correlated calculation moves up its own basis ladder it becomes -4.73 at aug-cc-pVTZ, still
short of the -5.01 equilibrium-geometry CCSD(T)/CBS dissociation energy quoted by an
open-access coupled-cluster study [[altun2018dlpno]] (different geometry, and we have not read
the primary reference behind it), so the residual basis error of the anchor is of the order of
0.3 kcal/mol and the functional-vs-anchor gap of 1.27 is larger than it. And the ladder itself
now spans 1.18 kcal/mol from cc-pVDZ to aug-cc-pVTZ, which is comparable to - not twice the
size of - the deviation being judged: a verdict of the form "the functional overbinds" obtained
by comparing one small-basis density-functional number with one CBS reference remains
unsupportable, but for a different reason than this draft originally gave. That is a caution
about the total binding energy, not about dE_NLC, which is
what every claim in this paper is made of, and which is grid-converged a level earlier
(above) and agrees with a second program to 0.0004 kcal/mol on this same complex
[S18]. A related definitional point, learned from a retraction: the S22 tables report
*total* interaction energies [[jurecka2006s22]], and the revision that made them
basis-set-consistent keeps doing exactly that [[takatani2010s22]], so no
"CCSD(T) dispersion energy" can be read out of them, and an earlier version of this draft
quoted one.

**How this section was wrong before, and what the error is worth.** The paragraph immediately
above previously reported -6.856 for the 6-31g\* anchor and read the functional as 0.73
kcal/mol *too shallow*. Both numbers were computed in this repository; neither was a
counterpoise number. The coupled-cluster script built each monomer from that fragment's own
atoms, so the monomers were evaluated in a smaller one-particle basis than the complex, which
is the one thing a Boys-Bernardi correction must not do; the column heading said dE_CP and the
quantity underneath it was the uncorrected difference. The functional column it was being
subtracted from had always used ghost functions, so every deviation in this section was the
difference of two conventions. The size of that mismatch is now measured rather than assumed,
as the basis-set superposition error of the correlated ladder itself: 1.977 kcal/mol on the
water dimer at 6-31g\*, and 0.252 to 2.971 across the eight complexes [S30]. Two properties of
that error are why it survived: it is always of the sign that makes the complex look more
strongly bound, so it inflated the anchor instead of deflating it, and both sides of the
subtraction are individually plausible energies - only the difference is impossible. The
structural check that should have caught it on the day it was written (the monomer must have
the complex's basis dimension) had been in the density-functional script from the start and was
simply absent from the coupled-cluster one; it is now, together with the electron-count check,
and `nlcsplit/tests/test_cc_convention.py` pins the invariant across all four convention rungs
and rebuilds the broken pairing deliberately, so the guard is shown to be capable of failing
[S24]. The corrected ladder and the row-by-row proof that nothing else moved are
`evidence/ccsdt/20261003T0652Z_snnu_cp_rebuild_631.out` and
`evidence/ccsdt/20261003T0700Z_snnu_cp_rebuild_compare.out` [S30].

**Repeating it on the other seven complexes gives one sign, and a magnitude that ranks.** The
three hydrogen-bonded dimers above are not the whole set, and testing the rest required a second
cluster: the same ladder was run for benzene-water, benzene-ammonia and benzene-methane
(114-118 AO), for the parallel-displaced benzene dimer (192 AO) and for the T-shaped one
(192 AO), all at official S22 geometries, 6-31g\*, counterpoise, frozen core [S26, S28, S29, S30].
Set against the omegaB97X-V/6-31G\* level-2 counterpoise values - all eight now computed in
PySCF 2.12.1, the same version and the same grid level as the coupled-cluster side - the eight
deviations are:

| complex | CCSD(T) dE_CP | omegaB97X-V dE_CP | deviation | correlated BSSE |
|---|---|---|---|---|
| water | -4.8789 | -6.1526 | -1.2737 | 1.9770 |
| ammonia | -2.5380 | -3.7277 | -1.1897 | 1.9174 |
| methane | +0.0734 | -0.3765 | -0.4499 | 0.2518 |
| benzene-water | -1.9724 | -3.2671 | -1.2947 | 1.6812 |
| benzene-ammonia | -0.8882 | -2.2227 | -1.3345 | 1.3855 |
| benzene-methane | +0.0816 | -1.3406 | -1.4222 | 1.1399 |
| benzene dimer (parallel-displaced, S22 #11) | +1.4712 | -1.9403 | -3.4115 | 2.9711 |
| benzene dimer (T-shaped, S22 #20) | -0.5748 | -2.4297 | -1.8549 | 1.9758 |

kcal/mol, read from the archives by `evidence/ccsdt/cp_rebuild_compare.py` rather than
transcribed [S30, S31]. That print block is itself new. Until this revision the script printed
only the identity check and the grid step, so the four columns above were carried across by hand
from the archives - and the hand-carrying is exactly where three of the eight DFT rows had stayed
on PySCF 2.14.0 (the 2026-09-28 batch) while the other five rows, and the whole correlated side,
were on PySCF 2.12.1 (the cluster). The column above is 2.12.1 for all eight rows; what the
superseded rows were worth is measured in the last paragraph of this section rather than dropped.
Every one of the eight is negative: at this basis the functional binds more
strongly than the correlated anchor on every complex in the set, with no exception and no
sign flip - which is the opposite of what this section reported before the convention was fixed,
and the reason for the difference is the mismatch described above rather than a new calculation
scheme. The magnitudes rank roughly with size and dispersion content, from 0.45 on the methane
dimer to 3.41 on the parallel-displaced benzene dimer. Two entries are worth reading twice because they are not small
numbers of the same kind: on the methane dimer and on benzene-methane the counterpoise
CCSD(T)/6-31g\* interaction is *positive* (+0.0734 and +0.0816, i.e. unbound at this geometry and
basis) while omegaB97X-V binds them by 0.38 and 1.34. That is the regime in which the previous
version of this paragraph found "deeper by 0.29", and it is the reason a small-basis anchor of
this kind cannot carry a verdict about a dispersion functional by itself.

**The anchor is not a one-program number, and the check now runs on the corrected quantity.**
Across the water dimer at both bases and both frozen-core conventions, the counterpoise energies
recomputed in ORCA 6.0.1 agree with PySCF's to 0.0001-0.0003 kcal/mol, on the ghost-function
construction as well as on the uncorrected one, and ORCA's printed AO dimension equals the PySCF
nao for every part of every run - 36 against 36 for a monomer whose partner is present as basis
functions with no nuclear charge, 18 against 18 for the same monomer without them
[S24, S30]. The uncorrected construction is recomputed in the same execution as the corrected one
precisely so that the new numbers remain comparable to the archived record they replace: ORCA
reproduces -6.8560 against PySCF's -6.8559, which is the quantity the earlier version of this
paragraph subtracted from a counterpoise value. A d-shell convention difference between the two
programs would be worth 0.01-0.1 kcal/mol, one to two orders of magnitude above the largest
disagreement measured, and the basis-identity check is what excludes it [S30].

**What the second basis does to the comparison.** Re-running the correlated side in
aug-cc-pVDZ, with only the basis changed, moves the counterpoise anchor by 0.5473, 0.0808 and
0.4987 kcal/mol on water, ammonia and methane [S24, S30]. Against the deviations those anchors
are used to judge - 1.2737, 1.1897 and 0.4499 - the ratios are 0.43, 0.07 and 1.11. Six of the
seven systems measured this way fall between 0.43 and 1.11, so on them neither term is the
other's error bar; the exception is ammonia, where the anchor's own basis move is 14.7 times
*smaller* than the deviation being judged, and on the methane dimer the basis move is the larger
of the two. That is the opposite of what this paragraph reported before the convention
was fixed, when the same comparison gave ratios of 1.4
to 28 and the section could say the discrepancy was mostly the basis. It was not, and the reason
the old reading looked that way is measurable in the same tables: the correlated BSSE itself
changes with the basis (1.9770 kcal/mol on water at 6-31g\*, 0.9162 at aug-cc-pVDZ), so an
uncorrected two-point ladder was comparing two different amounts of the same error, and calling
the difference a basis effect. Two things still cannot be concluded from these three ratios.
Part of each deviation may be the anchor not being converged rather than the functional being
wrong - 6-31g\* has no diffuse functions - and on the corrected ladder the direction of that
deficiency is not even consistent: going from 6-31g\* to aug-cc-pVDZ makes the water anchor
0.5473 kcal/mol *less* bound while it makes the ammonia and methane anchors 0.0808 and 0.4987
more bound, so the three small dimers do not share a common basis bias whose size could be
subtracted. And the same comparison now extends past the hydrogen-bonded set: the three
pi complexes and the parallel-displaced benzene dimer have archived aug-cc-pVDZ counterpoise
anchors (`evidence/ccsdt/20261003T0758Z_snnu_pi_three_avdz_ghostcp.out`,
`evidence/ccsdt/20261003T1212Z_snnu_sandwich_avdz_ghostcp.out` - that file's name, and the
parenthetical in its own first line, carry the word we used for this geometry before we measured
it; what the archive ran is the S22_11 entry, named in that same line, and its bytes are frozen
because its hash is cited elsewhere in this draft. The label is now computed from the coordinates
rather than asserted (`evidence/recompute/20261005T0340Z_benzene_dimer_label_measure.out`: S22_11
interplanar angle 0.0 deg with 1.698 A of in-plane slip, so parallel-displaced; S22_20 at 90.0 deg,
so T-shaped; and the third geometry, the one built by the benzene_sandwich() constructor of `nlcsplit/geomlib.py` (slip 0.000 A), is not either S22 entry), and `nlcsplit/tests/test_geometry.py` pins those three apart), giving seven spans whose
ratios to the deviation run 0.07 to 1.11 - the parallel-displaced dimer's own is 1.02, computed in
`evidence/ccsdt/20261005T0414Z_cp_rebuild_compare_labels_fixed.out` rather than by hand (the
same script's 2026-10-04 output, `evidence/ccsdt/20261004T0135Z_cp_rebuild_compare_derived7.out`,
carries identical numbers but prints these two rows under the labels we used before the angle was
measured, and the row labels are the only thing that differs between them). The
T-shaped dimer is the one complex with no aug-cc-pVDZ anchor at all: that rung was
never run, so no ratio is claimed for it. The functional side has now been measured in the
matched basis for the three π complexes: at level 2 their aug-cc-pVDZ counterpoise values are
-3.3184 (benzene-water), -2.3353 (benzene-ammonia) and -1.5556 (benzene-methane) kcal/mol
[`evidence/l2cp/20261003T1747Z_snnu51052-dft_cp_avdz_pi.out`], computed with the same PySCF
release as the 6-31G\* column above (2.12.1, recorded with the module's SHA-256 in
`evidence/l2cp/20261003T1747Z_snnu51052-sbatch.out`), after that job's own pre-spend guard
reproduced the two archived small-basis values -6.1526 and -1.3406 digit for digit. So
benzene-methane is now quoted at both bases on the same side of the comparison - -1.3406 in
6-31G\*, -1.5556 in aug-cc-pVDZ - both ends archived, their difference deliberately not
printed here. That closes the matched-basis question on the functional side for six of the eight
complexes - the three hydrogen-bonded dimers and the three pi complexes - and the two it does
not close are worth naming rather than leaving to the reader: the benzene dimer in either
geometry has no functional-side aug-cc-pVDZ counterpoise value on record, so its row of the
deviation table remains a 6-31G\* number and no same-basis statement is made about it. The
three hydrogen-bonded dimers were re-run into a per-run directory after the first attempt was
found unusable, and they are now measured at -4.9601 (water), -3.0288 (ammonia) and -0.4646 (methane)
kcal/mol at level 2 [`evidence/l2cp/20261004T0328Z_snnu51083-dft_cp_avdz_small.out`], from a
job whose own pre-spend guard reproduced both archived 6-31G\* values to 0.0000 and whose
sbatch header records the same PySCF release as the π batch above
[`evidence/l2cp/20261004T0328Z_snnu51083-sbatch.out`]. Those three cells are also the one place
where machine-independence is checked rather than assumed: the same producer file, the same
release and the same official geometries were run again on an unrelated workstation (WSL,
20 cores), where the two guard values and all three aug-cc-pVDZ counterpoise values come back
identical line for line, and the only field that moves is the two-implementation closure
diagnostic - by up to 3.6e-11 kcal/mol, on four of the five rows
[`evidence/l2cp/20261004T0903Z_wsl2121-small_crosscheck.out`]. The
withheld first attempt is kept as the
reason this rerun exists, and what makes it unusable is in its own bytes: it opens with
`DFT_SET=pi` and ends with `DONE DFT_SET=small`, and its guard rows print 3.6e-11 and 7.1e-11
of closure where every other printed field on those same rows is identical to rows the clean
π archive prints as 0.0e+00 and 3.6e-11
[`evidence/l2cp/20261003T1721Z_snnu51050_dft_avdz_small_interleaved.out` against
`evidence/l2cp/20261003T1747Z_snnu51052-dft_cp_avdz_pi.out`].


The same runs exposed a second nuisance parameter of comparable size. Raising only the
integration grid from level 1 to level 2, with the reference untouched, moves the
benzene-water deviation from -1.4220 to -1.2947 and the benzene-ammonia one from -1.4373 to
-1.3345, while benzene-methane moves from -1.4205 to -1.4222 [S26, S30]. In
terms of the computed value rather than the difference, the grid step shifts the three complexes
by 0.127, 0.103 and 0.0017 kcal/mol - a 75-fold spread from one complex to the next, on the same
functional, the same basis and the same geometry. The seventh system makes the point without
needing an argument: on the parallel-displaced benzene dimer the same one-step grid change moves the deviation
from -2.1945 to -3.4115 kcal/mol, a step of 1.217 - of the same order as the deviations in the
table above, whose smallest is 0.4499 (methane) and whose largest is this dimer's own 3.4115
[S28]. An earlier version of this sentence claimed the step was larger than every deviation but
its own, which the same table refutes: five of the eight are larger than 1.217. The grid effect is
neither proportional to system size nor monotone in it - benzene-methane's 0.0017 against the
parallel-displaced dimer's 1.217 is a factor of 700 - and the level-2 value is not claimed to be converged,
only to be the level this paper uses. The eighth complex, the T-shaped benzene dimer,
was measured the same way and moves 0.266 kcal/mol [S29]. All eight systems now have both grid
levels on the corrected anchor: the three hydrogen-bonded dimers were added in this revision and
their steps are 0.298, 0.646 and 0.219 kcal/mol [S31], which is to say within a factor of 4.3 of
the deviations they qualify (the same three are 1.2737, 1.1897 and 0.4499). The step is smallest on benzene-methane (0.0017) and largest on the
parallel-displaced benzene dimer (1.217), and none of that orders by system size. One claim in this paragraph is a casualty of the
convention fix and is worth keeping anyway: before it, three of the five then-measured grid steps changed the
*sign* of the deviation, which is how the paragraph used to make its point. On the corrected
anchor every deviation is negative at both grid levels and no step flips a sign - the sign flips
were the mismatch, not the grid. What the grid still does is move quantities of the size that was
going to serve as evidence, by up to 1.217 kcal/mol against deviations of 0.45 to 3.41, without
anyone deciding anything. This is the third reason the section judges dE_NLC and not the
functional.

**A fourth nuisance parameter, found by a guard that refused to pass.** The eight DFT values in
the table above were not, until now, one measurement: five came from the cluster and three from a
2026-09-28 batch on another machine, and the two differ in one thing the paper had never treated
as a variable - the PySCF version, 2.12.1 against 2.14.0. The mismatch surfaced as a refused
guard, not as a diagnosis: the cluster job that was about to spend time on aug-cc-pVDZ first has
to reproduce a level-2 counterpoise value, and it reproduced -6.1526 where it was told to expect
-6.1290, so it stopped [S31]. Running the same script, same geometry, same thread count and same
Python on this machine under both versions attributes the whole difference: the uncorrected
interaction energies agree to 1e-6 kcal/mol in all six cells, and the complex and bare-monomer
integration grids are identical point-for-point, while the grid attached to the *ghost* atoms is
not - 2.14.0 gives a monomer whose partner is present only as basis functions the same 43904
points it gives the full complex, and 2.12.1 gives it 34864. The counterpoise energy is the only
quantity in this paper that puts zero-charge atoms into the integration grid, so it is the only
one that moves: 0.0232, 0.0526 and 0.0892 kcal/mol at level 2 for water, ammonia and methane, and
0.31 to 0.59 at level 1, where 2.12.1's sparser ghost grid has not yet been refined away. Two
consequences are stated rather than smoothed. The table above quotes 2.12.1 throughout, because
that is the version every other DFT number in the paper - Table 1, the figures, the sidecar, the
ORCA cross-check - was produced in; choosing consistency over the newer release is a decision,
and its cost is exactly the three numbers just given. And the paragraph above this one, which
says the level-2 counterpoise value is used but not claimed converged, now has a reason instead
of a hedge: in 2.12.1 the same one grid step moves the counterpoise energy of the three small
dimers by 0.298, 0.646 and 0.219 kcal/mol, while in 2.14.0 it moves by 0.0011, 0.0002 and 0.0038,
so whether a level-2 counterpoise value is converged is a property of the implementation, not of
the system.

![The correlated reference ladder per system against this work's value, and the two cross-program checks](figs/fig4_anchor_crosschecks.png)

**Figure 3.** Left three panels: the MP2/CCSD/CCSD(T) counterpoise ladder for the three
hydrogen-bonded systems of this section, at 6-31G\* (solid) and aug-cc-pVDZ
(dashed), with this work's
omegaB97X-V/6-31G\* level-2 counterpoise value (PySCF 2.12.1, [S31]) as the dotted rule. The point is a comparison
of two spans, and `nlcsplit/figures.py` refuses to draw the figure unless the two fall within two
decades of each other on every system - a side-by-side figure is claiming comparability, and that
is the claim it checks. Per system the correlated value's move between the two bases
(0.547 / 0.081 / 0.499 kcal/mol for water / ammonia / methane) against the functional's deviation
from the frozen-core CCSD(T) at the smaller basis (1.274 / 1.190 / 0.450) gives 0.43 / 0.07 /
1.11 - within a factor of 2.4 on water and methane, and 14.7 apart on ammonia, so the two
quantities are comparable on this figure's own terms but not ordered the same way twice. Both numbers are read from
the archived runs, not transcribed. The three π complexes of the paragraph above are drawn in
Figure 4 rather than here, so that this figure keeps one comparison per panel [S26, S27, S31]. Right
two panels: the same
quantity computed by two programs - (b) the nonlocal term for all eight systems, as a
percentage of the term, against
the 1% guide (§4.2), and (c) the anchor of the left panels recomputed in ORCA 6.0.1, against
the 0.001 kcal/mol bar [S24].

![The same two spans for six complexes, as bars and as a ratio plot](figs/fig5_six_system_spans.png)

**Figure 4.** Top: the counterpoise ladder of the three π complexes at both bases with this
work's level-2 value as the dotted rule; bottom: for all six complexes where both quantities
exist, the reference's basis move and the functional's deviation from it at 6-31G\*, as paired
bars and as their ratio. The ratios are 0.07 to 1.11: on five of the six systems the two
quantities are within a factor of 2.4, and the one system where they are not is ammonia, where
the reference's basis move is 14.7 times smaller than the functional's deviation. No system puts
either quantity two decades below the other - which is the bound the drawing script enforces -
and the ordering differs from system to system, so neither term is the other's error bar.
The two benzene dimers are outside this panel by
design - the figure carries six systems, three hydrogen-bonded and three pi - and their own
aug-cc-pVDZ anchors now exist for the parallel-displaced dimer (ratio 1.02, read from the same archive) but not
for the T-shaped geometry, which was never run at that basis. Same archives
as Figure 3, drawn by the same script, which refuses to draw if any ratio leaves the two-decade
window [S26, S27, S30, S31].



### 3.3 The interfragment pair term saturates the frozen-density limit

`inter[(A,B)]`, summed over the retained grid points, is directly comparable to
the superposition difference d_sup computed from the unrelaxed monomer densities,
because both hold the density fixed. Their ratio falls in 0.92-1.08 across the six
systems for which the level-2 sidecar carries a counterpoise reference [S8]. The two
benzene-dimer geometries are not in that set: no level-2 value of this ratio was computed for
them, and the level-1 ratio printed for them has a different denominator (their
counterpoise-corrected binding energies, which are a different quantity, are in §3.2). On the coarser level-0 grid the same ratio
is 1.017 for the water dimer at the official S22 geometry and 1.025 at the
omegaB97X-V-optimised one, while the constructed benzene sandwich - the benzene_sandwich() constructor of `nlcsplit/geomlib.py`,
the zero-slip geometry, not either S22 entry - falls below the band at 0.915
[S19] - the level-2 value of 1.01 for the official water geometry sitting between
those two [S8]. Those three level-0 readings are not the same measurement as the level-2
value they are set beside, and the archive says why: on the coarsest grid the electron number
is not integrated exactly - 19.992853 against 20 for the water dimer, 84.038083 against 84
for the sandwich - so each energy carries a discretisation offset in the local term beta*int_rho
before any physics is subtracted. That offset does not corrupt a ratio between two densities on
the *same* grid (the same archive prints 84.038083 and 84.038271 for the sandwich's
self-consistent and superposed densities, which agree to three decimals, so the local term is
common to both sides), but it does not cancel between grid *levels*, which is why the level-0
numbers are quoted here as the coarse-grid behaviour of this ratio and not as three further
measurements of relaxation. In every one of these ratios the denominator is the superposition
difference evaluated on the same grid at the same level, with the monomers in their own basis -
uncorrected for basis-set superposition. The counterpoise-corrected quantities are §3.2's and
are a different number; they are not what this ratio divides by.
The ratio being able to exceed unity matters: relaxation is a small
correction of *either* sign on top of the frozen-density interfragment term, not
an orthogonal contribution that adds to it. Physically this says that in these
complexes essentially all of the nonlocal correlation that changes on association
is carried by grid-point pairs straddling the two fragments, with the
intra-fragment nonlocal correlation of each relaxed monomer contributing the
balance [S2, S10].

This is where the explicit sum earns its cost. A point-value kernel evaluation
returns dE_NLC and nothing else; the (i, j) index structure retained by the
double sum is what makes 0.92-1.08 a statement that can be checked at all. The
corresponding dispersion component published for the benzene dimer is -3.34 to
-3.80 kcal/mol at the PBE0-VV10, revPBE-D3 and related levels of an ALMO-EDA
study, and -3.69 at omegaB97M-V [S11]; our -4.367 (Table 1, level 1; the level-0
value was -4.448) is the same kind of quantity to within functional-generation and
basis-set differences, and it is *not* comparable with our own uncorrected
interaction energy for that dimer, -3.580 at the same level, which is smaller
because Pauli repulsion cancels most of it.

### 3.4 Attribution-scheme sensitivity is system-dependent

Repeating dE_NLC for the four partition schemes of section 2.3 gives absolute spans
of 0.004-0.247 kcal/mol and relative spans - measured against the Becke-scheme
interfragment term - of 0.8-18.2%. Neither ordering follows system size: the
24-atom parallel-displaced benzene dimer has one of the smallest absolute spans
(0.032, below the 6-atom water dimer at 0.043), while the 15-atom benzene...water
gives the largest (0.247). What separates them is the arrangement, not the atom
count or the interaction class:

| System | P_frz (Becke) | span (4 schemes) | relative |
|---|---|---|---|
| methane dimer | -0.474 | 0.004 | 0.9% |
| benzene dimer (A) | -4.038 | 0.032 | 0.8% |
| ammonia dimer | -0.649 | 0.029 | 4.5% |
| water dimer | -0.601 | 0.043 | 7.2% |
| benzene dimer (B) | -2.371 | 0.219 | 9.2% |
| benzene...methane | -1.442 | 0.213 | 14.8% |
| benzene...ammonia | -1.393 | 0.224 | 16.1% |
| benzene...water | -1.360 | 0.247 | 18.2% |

![Attribution spread of the interfragment pair term over the four partition schemes, as a percentage of the Becke-scheme value](figs/fig2_scheme_sensitivity.png)

**Figure 2.** How much of the reported pair term is a choice about where grid points belong: the spread of P_frz over the four partition schemes of section 2.3, divided by the Becke-scheme value, per system, sorted. The two geometries of the same 24-atom benzene dimer sit at 0.8% and 9.2% and benzene...water at 18.2%, so the percentage is a property of the arrangement rather than of the pair of molecules and cannot be collapsed into one blanket error bar. Data as in Figure 1 [S2].


Two observations follow. First, the relative span has no pattern by interaction
type: hydrogen bonding spans 7.2% (water) and 4.5% (ammonia), dispersion-driven
complexes span 0.9% (methane) and 18.2% (benzene...water), and the two benzene
dimer geometries differ by a factor of eleven. The relative column is read from what
the run printed, not divided out of the sidecar afterwards: that file stores the
methane cell's span and pair term to three decimals, and the stored numbers divide
to 0.8% while the run, dividing before it rounded, printed 0.9% [S2]. A single blanket uncertainty
percentage for this class of method would misstate the methane dimer by more than
twenty-fold. Error bars must be reported per system (Fig.~\ref{fig:2}). Second, the span is an
attribution property rather than a one-particle-basis property. On the official
S22 water-dimer geometry - the same geometry the rest of this section's tables are
computed on - re-running the four schemes at level 1 across five basis sets gives
spans of 0.0299 (STO-3G), 0.0435 (6-31G\*), 0.0413 (aug-cc-pVDZ), 0.0421 (def2-SVP)
and 0.0423 (def2-TZVP) kcal/mol while P_frz itself moves from -0.458
(STO-3G) to -0.633 (aug-cc-pVDZ) [S12]: the quantity of interest drifts by
0.18 kcal/mol across the basis ladder while the scheme spread stays inside
0.0413-0.0435 for the four basis sets beyond the minimal one - a band no wider than 4% of
the 0.042 it is usually quoted against - at 0.030 in STO-3G. The last
two rungs move P_frz by 0.026 kcal/mol, below the 0.05 the ladder's own criterion
asks for, so the basis is near its limit while the span is not shrinking - the
drift and the spread are different phenomena. The same ladder on the constructed
geometry (0.0249/0.0400/0.0382/0.0390/0.0398, drift -0.386 to -0.554) reproduces
this to 5-8%, so the reading is not an artefact of which water dimer we sat down
with. No better basis set will remove the spread, which is why it - and not grid
convergence,
which is 0.0081 kcal/mol over level 0 to 2 at 6-31G\* and 0.0002 over level 1 to
2 [S13] - is the error bar this method has to carry.

### 3.5 A limit of fragment-resolved quantities

Because beta is a constant and the integral of rho is the electron number, the
local term attributed to a fragment is exactly beta*N_A where N_A is its Becke
population, and beta = 3.0415 kcal/mol per electron. Any scheme-induced spread in
the population is therefore amplified into the fragment-resolved local term by
that factor as an identity, not an estimate: for the water dimer at grid level 3
the four schemes give fragment-A populations of 10.1559 (Becke), 10.1537 (Stratmann),
10.0979 (Becke--Treutler) and 10.0478 (Becke--Rad) electrons on the official S22
geometry, a spread of 0.108 electrons which is 0.329 kcal/mol; on the constructed
geometry the same spread is 0.09865 electrons, i.e. 0.300 kcal/mol [S20].
Two consequences deserve stating explicitly. In a superposition difference the
term cancels identically — electron number is conserved — so every dE_NLC value
in this paper is free of it. But any table reporting *absolute* fragment energies
inherits an uncertainty of this size from a quantity (atomic population) that the
method does not control. This is a property of Becke partitioning that every EDA
scheme shares, and we state it rather than claim it as a contribution.

A related implementation note: attributing the local term softly, by evaluating
all fragment factors s_A at every grid point rather than assigning each point to
one owner, changes these numbers by at most 1.53e-6 electrons (4.6e-6 kcal/mol
after multiplication by beta) on the official geometry the tables use, and by
8.69e-7 electrons (2.64e-6 kcal/mol) on the constructed one - grid level 3, all four
partition schemes, both numbers now in [S23]. The soft and hard readings of the local
term are numerically the same thing, which is worth recording because the two are
sometimes discussed as if they competed. The distinction between the two geometries
is itself the lesson here: this sentence read "8.7e-7 electrons" for a week, which was
true of the constructed geometry and silently too small for the one we publish.

### 3.6 The pair index has a cost, and a provable bound does not pay it

Keeping the (i, j) index means the double sum is evaluated rather than folded, so the
optimisation every quadratic kernel eventually tries is the obvious one: bound each block,
discard the blocks whose bound cannot matter at the requested accuracy, and hope the arithmetic
saved outweighs the deciding. We built that path - box separation of the point sets, a leaf-pair
traversal with a monotone accept rule, and a per-block certificate - and timed it against the
exact sum twice, on an unloaded machine, with the load sampled before and after each rung so a
contended window cannot be read as a measurement. It is slower everywhere. Of 33 timed
screened/exact pairs, none ran faster: the ratio spans 1.08-10.28x in the archived window and
1.37-13.29x in the re-run window [S25].

The culprit is the bound rather than the traversal. At atom-pair granularity the smallest
block-pair certificate we found for a real dimer is 197.96 Ha, against the quantity it would
have to decide on, -8.34e-4 Ha - loose by a factor of 2.4e5 - and the corresponding run reports
zero pairs whose bound falls below the value and an empty drop list [S25]. A traversal cannot
recover from that: it can only descend, and descent is the work. The consequence stated in this
paper's own units: at the coarsest tolerance in the sweep that still reproduces the exact sum to
|dE| <= 1e-6 kcal/mol, the screened path evaluates 84.4-95.4% of the far-field point pairs, and
for two of the six systems no tolerance in the sweep meets that target at all, so their admissible
tolerance is finer still and the share smaller.

We report this as the price of the pair index, not as a defect to be smoothed over. A reader
deciding whether pair resolution is affordable on their own system needs the number, and the
mechanism behind it constrains any future claim: a distance-only bound of the kind we implemented
does not reach 1e-3 Ha at pair granularity for diffuse inter-fragment pairs, so screening on this
term has to begin from a tighter certificate than the one that makes MBD-style schemes pay, and
until such a certificate exists the exact double sum is the cheapest correct option we know of.
The kernel-specific bound for VV10 (which has no multipole expansion to exploit in the near
field, unlike a charge-charge kernel) remains an open problem; nothing in this paper depends on
solving it.

---

## 4. Scope, independent verification, and limitations

This section keeps four things apart that are easy to read past one another: what the
reported quantity is not (§4.1), the two checks that were run against something outside our
own library (§4.2 and §4.3), the instrument behind the novelty claim (§4.4), and the limits
that survive all of it (§4.5).

### 4.1 What this decomposition is not

**This is not an energy decomposition analysis.** We split dE_xc into the
nonlocal term and everything else, and we resolve the nonlocal term into
fragment pairs. We do not separate electrostatics, exchange-repulsion,
polarisation or charge transfer, and the resulting components are therefore not
comparable term-by-term with ALMO-EDA or SAPT(DFT) output. Counterpoise-corrected
interaction energies are reported in section 3.2 for all eight systems.
The nonlocal term is not among those corrections. Table 1's dE_NLC is a
superposition-position difference whose monomers were solved in their own basis,
because the production path sums total energies and never takes the nonlocal term
of a ghost monomer [S2]. That is a convention, not a theorem: the ghost
construction is available for this quantity - the partner's functions stay, its
charge does not - so we ran it, at level 1 and the same basis, on the three small
dimers. The correction comes out -0.0074 (water), -0.0031 (ammonia) and +0.0075
kcal/mol (methane) [S32], against those cells' own four-scheme attribution spans
of 0.0435, 0.0290 and 0.0040 kcal/mol: 0.17, 0.11 and 1.87 times the attribution
effect. Two things that used to be said here are withdrawn. Basis-set
flexisation does enter dE_NLC, measured on three systems rather than argued; and
its absence was not "precisely why" the term converges a grid level earlier than
dE_int does [S10] - on the methane dimer the basis-set effect is the *larger* of
the two uncertainties quantified for that cell, which is the one place in this
paper where the ordering of those two is not ours to claim. What makes the
nonlocal term settle a grid level earlier is not explained here.

**The nonlocal term is not the dispersion energy.** Section 3.2 is the evidence:
dE_NLC accounts for anywhere between 16% and 97% of dE_xc across the seven complexes
where that share is defined by our own cancellation test (Fig.~\ref{fig:1}) - and note that this
is not a smooth ladder: the two geometries of the same benzene dimer give 97% and 52%.
The eighth complex, the methane dimer, is the case a percentage cannot describe at all:
its two parts carry opposite signs, so the nonlocal term is not a fraction of the change
but the thing that has to overcome it. A quantity whose relation to another varies that
far - and in one case changes character - cannot be identified
with it. We use "dispersion" only when quoting external work, and the values in
Table 1 should be read as "the contribution of the VV10 term", not as a
dispersion energy.

### 4.2 Cross-program check: ORCA 6.0.1 agrees on the reported quantity, on all eight systems

Our
explicit sum had only ever been checked against PySCF's native kernel, and both live in
one library, so they could share an error in the functional parameters or in the kernel
convention. That check now exists against a second program, and on more than the two
systems we first reported. ORCA 6.0.1 prints the term
natively for `! WB97X-V` as `NL Energy, E(C,NL)`; the control showing that the label is
VV10-specific rather than a generic DFT printout is `evidence/orca_control/h2o_wb97x.out`, an ωB97X run
with no `-V`, which contains no such line [S18]. Twenty-four serial runs - the water dimer
and the parallel-displaced benzene dimer (S22 #2, #11) on the cluster, the other six systems on this machine,
all at S22 official complex geometries with 6-31G*, each
terminating normally with a converged SCF and carrying exactly one `NL Energy` line -
give, for the superposition difference that Table 1 reports. The last two columns compare
the residual with the partition-scheme span of the same row (§3.4), which is the
quantity a referee has to be smaller than to be informative:

| system | ΔE_NLC ORCA | ΔE_NLC PySCF | difference | span | residual/span |
|---|---|---|---|---|---|
| water dimer (S22 #2) | -0.5931 | -0.5935 | 0.0004 (0.07%) | 0.0435 | 0.009 |
| ammonia dimer (S22 #1) | -0.6745 | -0.6780 | 0.0035 (0.51%) | 0.0290 | 0.120 |
| methane dimer (S22 #8) | -0.5160 | -0.5170 | 0.0010 (0.19%) | 0.0040 | 0.242 |
| benzene...water (S22 #17) | -1.2522 | -1.2590 | 0.0068 (0.54%) | 0.2470 | 0.028 |
| benzene...ammonia (S22 #18) | -1.3189 | -1.3270 | 0.0081 (0.61%) | 0.2240 | 0.036 |
| benzene...methane (S22 #10) | -1.3912 | -1.4040 | 0.0128 (0.91%) | 0.2130 | 0.060 |
| benzene dimer B (S22 #20) | -2.3685 | -2.3880 | 0.0195 (0.82%) | 0.2189 | 0.089 |
| benzene dimer A (S22 #11) | -4.3252 | -4.3668 | 0.0416 (0.95%) | 0.0320 | **1.301** |

All eight agree to better than 1% of the term, and the residual tracks the magnitude of
ΔE_NLC rather than the size of the system, which is what a quadrature difference looks
like. Three things must be said about it rather than glossed. First, the grids are
not matched - ORCA uses its own nonlocal quadrature (Lebedev-110, IntAcc 4.004) against
PySCF's `grids.level=1` - so the residual is the joint grid-plus-implementation
difference and we do not attribute it to either side. Second, in seven of the eight systems
the cross-program residual is smaller than the attribution span it would have to resolve,
by 4.1 to 111 times (methane the tightest, water the loosest; that interval is printed by
`evidence/orca_widen/generator_cross_program_table.py` into `cross_program_table.txt` rather than
divided here, because the sentence this paragraph replaces quoted "8 to 100 times" and both ends
of it were wrong); the exception is the parallel-displaced benzene dimer, where 0.042 kcal/mol is
1.3x the 0.032 kcal/mol span for that same geometry. That single row is the warning this
comparison exists to provide: cross-program noise can be of the same order as the
quantity being resolved, so it must never be folded into the attribution uncertainty.
Third, the two water monomers
of S22 #2 are not equivalent (donor r_OH 0.9639/0.9571 vs acceptor 0.9590/0.9590), so the
monomer term had to be computed twice - using 2x one monomer would have introduced
~0.0004 kcal/mol, exactly the size of the residual. A repeat of one input inside the same
allocation reproduced its VV10 term to 1.6e-11 Eh, so the residual is not run-to-run
noise [S18]. The widened set was assembled after an audit of our own record found that
`evidence/orca_widen/orca_widen.json` marked all twelve of its first runs `converged: false`
while the archived outputs print `SCF CONVERGED AFTER n CYCLES` and `ORCA TERMINATED
NORMALLY`: the flag came from a criterion that looked for a different program's wording.
The flags were re-derived from the logs without re-running anything, with the assertion
that no energy value moves (`evidence/orca_widen/generator_rescan_convergence.py`), and
the table above is generated from the tracked artefacts by
`evidence/orca_widen/generator_cross_program_table.py`, which refuses to emit it if the
system list disagrees with the one it declares, or if any row's basis, grid level or
counterpoise setting disagrees. One operational note belongs with the row it affects: the
24-atom benzene dimer (B, S22 #20 - the T-shaped one, not the parallel-displaced (A))
is the only run that needed four times
the per-process memory allowance (%maxcore 4000 against 1000), which changes what ORCA can
hold in core and nothing about the numerical parameters; at 1000 it died in the SCF with
`CANNOT OPEN FILE dimer.opot2.tmp`, and that difference is recorded on the run rather than
left for a reader to rediscover.

What this also checks is the absolute value, not just the difference. An earlier log of
ours recorded a ~0.14 kcal/mol disagreement on the water monomer between our explicit sum
and the native kernel, and we flagged the absolute fragment energies as unrefereed. That
flag is now retired: the archived level-2 run gives a water-dimer nonlocal term of
+52.9345 kcal/mol against ORCA's +0.084358235 Eh = +52.9356, and monomers +26.7635/+26.7644
against ORCA's +26.7646/+26.7641 - agreement at the 1e-3 kcal/mol level on the absolute
quantity as well [S8, S18]. We have not re-established what that 0.14 was: the most likely cause is a
comparison made before the beta·∫rho counterterm was added back - `step_f_dispersion.terms`
now adds it before reporting, and the comment at that call site exists precisely because of
this confusion - but we are stating the present agreement, not a diagnosis of the old
number, so the section 3.5 identity is covered by this anchor without needing that story
to be true.

### 4.3 A referee for attribution, which no other program can supply

A second program checks
the value of the term; it cannot check how the term is *owned*, because it does not
attribute at all. So `evidence/attribution_referee/` moves to a system where an exact,
partition-free reference exists by construction: two normalised Gaussians, four electrons
each, centred at `+/- sep/2` on the z axis, with `Phi` built once from the total density
and `I_XY = int int rho_X Phi rho_Y` taken for each pair of density factors. No Becke weight,
no grid assignment and no fragment ownership appear anywhere in that definition, and
`E_NL = 1/2 (I_AA + I_BB) + I_AB` holds exactly, so `I_AB` is what the inter-fragment block
would have to be if attribution were a property of the density rather than of a convention.
It is computed three ways - a 3-D x 3-D Cartesian tensor product, a 5-D cylindrical
reduction about the internuclear axis (different nodes, domain shape and Jacobian), and
importance-sampled Monte-Carlo using the density factor itself as the importance - and the
Monte-Carlo agrees with the quadrature within its own standard error everywhere, worst
`|z| = 2.23`.

The outcome separates cleanly, and the two halves say different things. Handed the exact
density factors, the package's own summation code reproduces `I_AB` to `7.96e-07` Ha worst,
inside the reference's combined uncertainty `U = 1.060e-05` Ha (0.00665 kcal/mol, assembled
from three measured error bars: order-ladder last change, domain-truncation shift, and the
Cartesian-versus-cylindrical disagreement). The arithmetic is therefore refereed, and by a
route that does not share our library. Handed the production Becke/owner assignment, the
same code lands `1.68e-08` to `1.26e-04` Ha from `I_AB` (0.00001-0.0788 kcal/mol), and
because the same comparison is also run on a second, disjoint node set where the grid
cancels, that offset tracks the partition rule and not the grid: the grid's own cost in the
same quantity stays below `U` at every configuration. Reported as sizes, the offset is
0.0007-1.84% of the whole VV10 term and 0.32-11.79% of the cross term it is meant to be.

The resolution is stated rather than assumed, and it depends on which reference is
holding the bar. Against the deterministic reference and its combined uncertainty `U`,
the offset exceeds `U` in **5 of the 12 configurations** (2x, 3x, 3x, 4x and 12x `U`);
in the other 7 it is smaller than that error bar, and there this referee does not
certify the convention, it reports that it cannot distinguish it [S22]. Repeating the
comparison against the Monte-Carlo route instead - 4,000,000 draws per configuration,
scored against `max(2 s.e., |MC - 5-D|)`, whose worst value is 1.819e-06 Ha or
0.00114 kcal/mol, 5.8x tighter than `U` - resolves **12 of 12** [S22]. Both numbers are
reported because they answer different questions: the deterministic `U` is bounded by
how far the two quadratures disagree with each other, the Monte-Carlo bar by an
independent estimator's own scatter plus that disagreement, and neither is traded for
the other. Those five resolved offsets run 0.013-0.079 kcal/mol,
which is 0.55-1.84% of the whole VV10 term and 2.5-9.7% of the cross term, the same order as
the four-scheme spread of section 2.3 (0.004-0.247 kcal/mol) - the distance from one
convention to a partition-free reference is about the distance between conventions, which is
the consistency this section wanted.

Two limits travel with that result. The densities are synthetic (no nuclei, no cusps, no
orbital structure), so what is refereed is the attribution machinery as a mathematical
operation on a density, not a chemical statement. The positive control - the
documented-wrong pairing of section 3.5 - moves the whole term on these densities by
0.0052 kcal/mol, which is larger than most of the offsets tabulated above: it therefore
shows the referee can see a kernel-definition error, but it also shows that this apparatus
resolves attribution conventions, not kernels. Extending it to heteronuclear pairs is not a
parameter change: the reference itself needs no nuclei, but the package side is evaluated
on a grid whose Becke radii come from atomic numbers, so making the two centres unequal
forces a choice of radii - the very convention under test - and that has not been done here.
It does reproduce:
two independent executions of the whole pipeline give tables that are byte-identical except
in the recorded wall-clock fields, and both runs are shipped in that directory.

### 4.4 How we know the literature search means anything

The zeros in section 1 are
only as good as the instrument, so we calibrated it in the same session: a known
paper title was retrieved exactly (1 record), a broad concept query returned 3,317
records, and a topical AND query in the same vocabulary returned 33. By contrast
the two open indexes we tried first failed the same test - OpenAlex and Crossref
each retrieved a known title 4/4 times when queried by title but missed that same
known, on-topic paper for 2 of 3 and 3 of 3 legitimate topical phrasings
respectively. We therefore report hit counts only from the instrument that passed.
Its enumeration is complete rather than sampled, and that took a second round: the
result-page UI virtualises its list and gave us one record per list, and the first
attempt at working around it by excluding already-read titles backfired - the title we
excluded was the truncated form of the very record we were chasing (FDE-vdW's full title
begins "Exact kinetic energy enables..."), so we had removed our own nearest neighbour.
Going to the record endpoint instead returned every record of every list. One further
trap there is worth naming, because it fails silently: that endpoint streams records in
batches of 20, and a parser that overwrites rather than appends reports the tail batch as
the whole result set - on a 33-record query that reads as 13, and nothing in the response
says so. We now assert `len(records) == RecordsFound` on every query.

The search covers one index -
Web of Science Core Collection - because Scopus was measured as unsubscribed at our
institution and Embase and SciFinder were not searched at all. Within that one index,
though, the search is now a full enumeration rather than a sample: every record
returned by every query was read, which changed the conclusion in one place worth
reporting, since a keyword-shaped novelty query is narrower than the claim it is
meant to test. Six queries in the first round covered the decomposition vocabulary and
found nothing in the interpretive line; adding the broadest topical query available
(vdW-DF x "nonlocal correlation", 33 records, every title read) surfaced Hyldgaard,
Berland and Schröder's xc-hole interpretation of the same energy [S17], which no query
containing decompose, partition, fragment or pair would ever have returned. The open
indexes tried instead (OpenAlex, Crossref, Semantic Scholar, arXiv) are recorded as
supplementary and not as a second formal search, because their reachability was uneven and
measured: OpenAlex's search route returned 21 usable responses against 14 rate-limited and
10 server-error attempts, Semantic Scholar's search route was rate-limited throughout so its
keyword dimension was never actually queried, arXiv failed known-item calibration (its own
abstract field contains a term that its search does not retrieve) so its zeros are not read
as absence, and Scopus returned 401/403. Crossref and OpenAlex retrieve known titles reliably
but miss a known on-topic paper when asked topically. The round still changed this
paper: the nearest neighbour, and the reason the claim is narrower than it was written, came
from it rather than from the formal search.

### 4.5 The limits that remain

**The attribution uncertainty is intrinsic and per-system.** The 0.004-0.247
kcal/mol spread of section 3.4 does not shrink with a finer grid or a larger
basis; it is a property of how grid points are assigned to atoms. Any number
produced by this method carries it, and reporting a single percentage for the
whole method would be wrong by more than twenty-fold for individual systems.

**Absolute fragment energies inherit a population uncertainty.** As shown in
section 3.5, the local term of a fragment is exactly beta*N_A, so the
0.108-electron spread of the attributed population over the four schemes is a
0.329 kcal/mol spread in the
reported fragment energy - larger than the scheme spread of the pair term itself
for the water dimer. Differences are safe; absolutes are not, unless the
population convention is stated alongside them.

**Cost, and what it buys.** The explicit double sum is quadratic in the number of
retained grid points. A sub-quadratic route was built and measured, not merely
declined: section 3.6 times a screened traversal against the exact sum over 33
pairs and finds none faster, because the certificate available at pair granularity
is loose by a factor of 2.4e5 at its tightest real case. The point-value kernel
that PySCF ships remains both cheaper and accurate to ~1e-8 Ha on its own grid
(section 3.1). The cost is not prohibitive in itself - JuNoLo ran the same N² sum
over massively parallel hardware for surface calculations [S14] - but it is a real
constraint, and it is worth naming the trade honestly. We are therefore not claiming that this
method computes dE_NLC better. What it buys is the (i, j) index structure: the
0.92-1.08 frozen-density result of section 3.3, and the per-pair numbers behind
Table 1, are not recoverable from a scheme that collapses the pair sum to point
values first.

**Scope of functionals.** Everything here is the VV10 kernel with the (b, C)
parameters PySCF reports for omegaB97X-V, using the same-centre pairing
convention of section 2.1. Functionals whose nonlocal term uses the regularised
rVV10 form have not been tested and may not share the pairing convention.

## 5. Code availability

The package `nlcsplit` (Apache-2.0, containing no GAMESS source) implements the
kernel, the four attribution schemes, the fragment decomposition and every table
in this paper; it is built on PySCF [[sun2018pyscf]] [[sun2020pyscf]] and NumPy
[[harris2020numpy]], and each table is produced by exactly one `step_*.py` script whose
stdout is archived under a UTC-stamped filename. Fragment boundaries come from
covalent connectivity rather than hand-written atom lists, and both the geometry
constructors and the official-geometry loader assert internal coordinates at
construction time - three of the bugs this measure was added to catch are
described in the supplementary notes. Grid, basis and scheme sensitivity are
separate functions (`step2_convergence.py`, `step_g_basis.py`, `step_h_s22.py`)
rather than one combined uncertainty, and `partition_factors()` verifies its own
output against PySCF's partition weights before returning it.

## 6. Conclusions

We have shown that the VV10 nonlocal-correlation energy can be resolved into
fragment pairs without giving up the total: the double sum is evaluated
explicitly, the local part cancels identically from any superposition difference
because it is exactly beta times the electron number, and the resulting blocks
reproduce the total to machine precision while carrying an (i, j) index that the
point-value evaluation discards.

Three things follow from applying it to eight S22 complexes at official
geometries. The VV10 term is not a fixed share of the exchange-correlation
contribution - 16% for the water dimer, 97% and 52% for two geometries of the same
benzene dimer, and no quotable share at all for the methane dimer, where the two parts
carry opposite signs and the denominator is their small residue (the package refuses to
report one there by rule, §3.2) - so reporting it as "the dispersion
energy" is unsafe even within one benchmark set. The association-time change is
almost entirely inter-fragment: the frozen-density pair term accounts for
0.92-1.08 of the superposition difference in the six systems checked against a
counterpoise reference, with relaxation a small correction of
either sign rather than an additive channel. And the dominant uncertainty is the
attribution scheme, not the numerics - on the two numerical axes we checked, basis
set and grid: 0.004-0.247 kcal/mol absolute,
0.8-18.2% relative, confined to 0.0413-0.0435 across the four basis sets beyond STO-3G
and to within 0.001 kcal/mol between grid levels 1 and 2, with
no pattern by interaction type that would let a single percentage be quoted.
That ranking does not hold on a third axis: on the methane dimer the superposition
error of dE_NLC itself is +0.0075 kcal/mol, 1.87 times that cell's own attribution
span [S32], so among the three cells where both have been measured it holds on two,
and "dominant" is a counted result, not a property of the quantity.

What the method does not do is equally important, and we would rather the reader
learn it here than in a review. It is not an EDA: it does not separate
electrostatics, exchange-repulsion, polarisation or charge transfer. It is not
faster than the production kernels it could be compared against - it is
quadratic in the grid. Its arithmetic was for most of this project verified only
against a second implementation of the same kernel inside the same library; that
gap is now closed for the quantity Table 1 reports, by twenty-four ORCA 6.0.1 single points
covering all eight systems, every residual below 1% of the term
(0.0004 kcal/mol on the water dimer up to 0.0416 on the parallel-displaced benzene dimer,
S22 #11). An earlier
version of this draft claimed such an anchor and had
to withdraw it; what actually failed was not the check but our ability to find its
number, because we searched for the words "nonlocal" and "VV10" in an output file
that labels the quantity `NL Energy, E(C,NL)`. One scoping limit remains: the absolute
value, not only the difference, is checked on the water dimer and on both of its monomers
(§4, where the earlier "unrefereed" flag is retired); on the other seven systems the second
program checks the difference, which is what every claim in this paper is made of, and not
each absolute fragment value. Attribution has a referee of its own now (section 4), on a
two-Gaussian density where a partition-free value exists by construction: the summation code
reproduces that value to within the reference's own error bar, while the Becke/owner
convention sits 1.7e-08 to 1.26e-04 Ha (0.00001-0.0788 kcal/mol) from it - a difference
resolved in 5 of its 12 configurations against the conservative deterministic error bar
and in all 12 against an independent Monte-Carlo bar 5.8x tighter. The case that draft
excluded, unequal exponents and unequal electron numbers on the two centres, is now run too
[S22]: the exact reference needs no nuclei and the density-factor partition needs no radii,
so the only convention-dependent input is the element label, and swapping the label at a fixed
density moves the offset by at most 0.24% of itself. What the heteronuclear case actually
changes is the size of the effect - the owner/Becke cross term sits 6.2-35.9% of the exact
cross term there, against 2.5-9.7% for the five of twelve homonuclear scan rows that clear
their own error bar (the same five as §4.3, read off [S22]), every one of them resolved
against its own error bar. The homonuclear table understated the non-uniqueness, and it
understated it in the regime where an EDA is asked to work. What still does not carry a
referee is a chemically realistic density: nuclei, cusps and orbital structure remain outside
this check, which is about the attribution rule as a mathematical operation.

Two further items are open and stated as such rather than smoothed over. The first is a
number, not a missing run: re-running benzene-methane at level 2 with counterpoise on two
PySCF releases reproduced every attributed quantity to within 5e-4 kcal/mol - the
rounding half-step of the three-decimal printout on one side, the largest measured
difference being 4.2e-4 on the pair term - but reproduced the
counterpoise interaction energy only to 0.139 kcal/mol (section 2), so a counterpoise
denominator is not portable between versions while the pair term appears to be. The second
is a scope limit that has since been closed, and how it was closed matters more than the
number: the basis-set ladder of section 3.4 had been run on the constructed water-dimer
geometry while every other table in this paper is computed on the official S22 one. Re-running
the five-basis, four-scheme ladder on the official geometry (level 1, same script, spans
0.0299/0.0435/0.0413/0.0421/0.0423 kcal/mol against 0.0249/0.0400/0.0382/0.0390/0.0398 on the
constructed one) leaves every reading of the argument intact to 5-8%, so section 3.4 now quotes
the official geometry. An earlier version of this paragraph claimed instead that the ladder
predated the 2026-09-29 geometry fix and "has not been re-run" - which was not true: the fix
landed at 01:07 that morning (+08) and the re-run is stamped 08:31, and the provenance row for
that table already said it was on the constructed geometry. Declaring a task open is a claim
too, and it was checked against the artefacts only after the fact.

The package is released under Apache-2.0 with no GAMESS source in it, every
number in this paper is produced by a named script whose archived stdout is part
of the repository, and the two structural guards we added after finding bugs in
our own geometry builders - coordinate assertions at construction time, and
`partition_factors()` verifying its own output against PySCF's partition weights
before returning - are the part of this work we would most recommend copying.

---
## Statements

**Data availability.** Every number in this manuscript is produced by a named script in the
released repository, and the archived standard output of that script is committed beside it
under `evidence/`, one `MANIFEST.sha256` per directory. The package `nlcsplit` is Apache-2.0
and contains no GAMESS source. The dimer structures are the published S22 sets
[[jurecka2006s22]] [[takatani2010s22]] at their official GMTKN55 geometries
[[goerigk2017gmtkn55]] and are not redistributed
here; `nlcsplit/geomlib.py` reads them from the file names it ships with.

**Supporting information.** The provenance appendix at the end of this file - the tag-to-file
and line-number record behind every quoted value - is the material that will be carried as
the Supporting Information. It is left inside the manuscript while the work is under
revision so that a reviewer can resolve a tag without opening a second file.

**Conflicts of interest.** The authors declare no competing financial interest. *(To be
confirmed by both authors before submission.)*

**Acknowledgments.** *(Funding information and grant numbers to be supplied by the authors;
nothing is asserted here on their behalf.)*

---
## Appendix: provenance of every quoted number

Each tag used above resolves to a file in this repository. "line N" means the value can be
read literally at that line of the archived standard output; those stdout files live under
`evidence/**`, are tracked, and are hash-listed under `evidence/*/MANIFEST.sha256` — they were
not re-typed by hand. `nlcsplit/logs/` is a different case and is stated as such rather than
glossed: only three sidecar JSONs there are tracked (`step_h.json`, `step_h_l2cp.json`,
`orca_anchor.json`), the rest of that directory ignores `*.out` by its own `.gitignore`, so a
run log left there is a working note and not evidence.

| Tag | Artefact | What it fixes |
|---|---|---|
| S1 | `RESEARCH-20260929-lit.md` §1, §6 | first-round WoS/Scopus search record: strings, hit counts, search date |
| S2 | `MAIN-skeleton.md` tables 2 and 4b; `nlcsplit/logs/step_h.json` | the level-1 S22-subset table, incl. the 0.8% / 18.2% nonlocal fractions |
| S3 | `nlcsplit/step_f_dispersion.py` | the level-1 dispersion-scale check that leaves the double sum as the only unaccounted term |
| S4 | `MAIN-skeleton.md` table 4b | the 52%-97% range of the same quantity across the two archived geometries of one molecule pair (benzene dimer A parallel-displaced, B T-shaped) — the geometry axis, not the partition axis |
| S5 | `nlcsplit/step_e_kernel.py` | explicit pair sum vs PySCF's native VV10 kernel on a fixed grid |
| S6 | `evidence/centos/20260928T165857Z_centos-step_c.out` line 19 | relaxed O-O = 2.901 A |
| S7 | `nlcsplit/step_d_floor.py`, `evidence/recompute/20260928T150222Z_step_d_floor.out`, `nlcsplit/tests/test_kernel.py` | the local term is beta x electron number, so it cancels in any superposition difference; the archived stdout is the rho_floor sweep itself - dropped-point fractions, electrons carried by the dropped points, and the per-level Ha spans behind the sensitivity claim in §3 |
| S8 | `nlcsplit/logs/step_h.json`, `nlcsplit/logs/step_h_l2cp.json`, `evidence/l2cp/20260929T051912Z_centos-l2_benzmeth_cp.out`, `evidence/l2cp/20260929T051849Z_l2_benzmeth-wsl.out`, `evidence/centos/20260928T165857Z_centos-step_f_h2o2.out`, `evidence/recompute/20260929T010500Z_step1_geomfix.out`, `evidence/l2cp/20260929T051849Z_wsl2121-benzmeth-l2cp.json`, `evidence/l2cp/20260929T051912Z_centos2140-benzmeth-l2cp.json`, `evidence/l2cp/cross_version_pair.py`, `evidence/l2cp/20261004T0100Z_cross_version_pair_benzmeth.out` | cross-version pair (PySCF 2.12.1 vs 2.14.0) and the 19936 vs 20248 partitioned grid counts |
| S9 | `nlcsplit/step_i_gridrepr.py`, `evidence/recompute/20260929T_step_i_gridrepr.out` | the two discrepancies that were previously reported as one number |
| S10 | `evidence/l2cp/20260928T213839Z_centos-step_h_l2cp.out`, `evidence/l2cp/20260929T051912Z_centos-l2_benzmeth_cp.out`, `nlcsplit/logs/step_h_l2cp.json` | level-2 with counterpoise, all six S22 subsystems complete, including the `p_over_ds` column behind the 0.92-1.08 ratio |
| S11 | `RESEARCH-20260929-lit.md` §6.2-6.3 | published comparison value for JCTC 3c00903 (full text via ChemRxiv green OA 10.26434/chemrxiv-2023-nc64t) |
| S12 | `evidence/recompute/20260930T191014Z_stepg-official.out` (official S22 geometry, the numbers quoted in sections 2 and 3.4), `evidence/recompute/20260929T003144Z_stepg-recompute.out` (constructed geometry, quoted as the cross-check), both produced by `nlcsplit/step_g_basis.py`, cross-checked against `evidence/centos/20260928T165857Z_centos-step2.out` | five-basis ladder of P_frz and of the four-scheme span at level 1, run once per geometry by the same script (`NCOFF` selects the official one). The two ladders agree to 5-8% on every span and to within 0.008 kcal/mol on the STO-3G-to-aug-cc-pVDZ drift, so the reading is geometry-insensitive; the script's own criterion (last-two-rung drift < 0.05) is satisfied on both geometries, which is what licenses calling the basis near-converged while the scheme span is not shrinking |
| S13 | `evidence/centos/20260928T165857Z_centos-step2.out` lines 17-20, per-level values at lines 2-15 | cross-grid spread per basis (sto-3g 0.0010, 6-31G* 0.0081, aug-cc-pVDZ 0.0067); the 0.0002 for 6-31G\* over level 1 to 2 is the difference of lines 8 and 9 |
| S14 | Lazić, Atodiresei, Alaei, Caciuc, Blügel and Brako, *Comput. Phys. Commun.* **181**, 371-379 (2010), DOI 10.1016/j.cpc.2009.09.016; open preprint arXiv:0810.2273v1; judgement in `RESEARCH-20260929-lit.md` §10 | the closest published decomposition of a nonlocal term, read in full text |
| S15 | `evidence/retrieval_calibration/oa_stab.js`, `evidence/retrieval_calibration/openalex_stability.json`, `evidence/retrieval_calibration/xref_calib2.js`, `evidence/retrieval_calibration/xref_r3.js` | measured recall of the open indexes: 4/4 known titles at rank 0, 0/4 and 1/3 for legitimate topical strings |
| S16 | `RESEARCH-20260929-lit.md` §8.1 | the institutional-access precondition of the search, and why the first round was counted from the UI |
| S17 | `RESEARCH-20260929-lit.md` §13 | second round: full enumeration through WoS's own record endpoint (RecordsSearched = 58,664,816, search date 2026-09-29), the three calibration strings reproduced record-for-record, the two zero-hit strings, complete readings of the two 4-record and four broad strings, and the three added citations whose DOIs were checked against both Crossref and WoS |
| S18 | `nlcsplit/logs/orca_anchor.json`, `evidence/orca_run/h2o_dimer.out`, `evidence/orca_run/h2o_mono0.out`, `evidence/orca_run/h2o_mono1.out`, `evidence/orca_run/benz_dimer.out`, `evidence/orca_run/benz_mono0.out`, `evidence/orca_run/benz_mono1.out`, `evidence/orca_run/MANIFEST.sha256`, `evidence/orca_control/h2o_wb97x.out`, `evidence/orca_control/h2o_wb97xv.out`, `evidence/orca_control/MANIFEST.sha256`, `evidence/orca_widen/orca_widen.json`, `evidence/orca_widen/RECHECK_convergence.txt`, `evidence/orca_widen/generator_rescan_convergence.py`, `evidence/orca_widen/generator_merge_run.py`, `evidence/orca_widen/generator_cross_program_table.py`, `evidence/orca_widen/cross_program_table.txt`, `evidence/orca_widen/MANIFEST.sha256` | the cross-program referee: three ORCA 6.0.1 runs each (S22 official geometries, 6-31G\*, every run with a converged SCF and exactly one `NL Energy, E(C,NL)` line) — six for water and the benzene sandwich from `nlcsplit/logs/orca_anchor.json`, eighteen more archived under `evidence/orca_widen/` (one log per run, each listed with its sha256 in `evidence/orca_widen/MANIFEST.sha256`) covering ammonia, methane, benzene...water, benzene...ammonia, benzene...methane and the parallel-displaced benzene dimer; the per-file sha256 manifests; the omegaB97X (no `-V`) control that prints no such line; the re-scan that corrected twelve falsely-flagged `converged` fields without touching any energy; and the generator that emits the eight-row comparison and refuses if the system list disagrees with the one it declares, or if any row's basis, grid level or counterpoise setting disagrees |
| S19 | `evidence/centos/20260928T165857Z_centos-step_c.out` lines 6, 15 and 24 | the level-0 ratios of the inter-fragment pair term to the superposition difference: 1.017 for the water dimer at the official S22 geometry, 1.025 at its omegaB97X-V-optimised geometry, and 0.915 for the benzene sandwich - the third of these is a different system, which is why it is not folded into the 0.92-1.08 band |
| S20 | `nlcsplit/step_k_population.py`, `evidence/population/20260929T131530Z_stepk_pop-official.out`, `evidence/population/20260929T131055Z_stepk_pop-constructed.out` | the level-3 four-scheme population table for the water dimer, from which beta*N_A is read; both runs assert that the fragment populations sum to the electron number. Re-running them is also what showed that the earlier tabulation of this number in the work log was labelled "official geometry" but reproduces only on the constructed one |
| S21 | `evidence/agentb_sweep/20260928T071951Z_agentb-sweep_631gstar.txt`, `evidence/agentb_sweep/20260929T151414Z_step_l_sweep_compare_levels0-9.out`, `evidence/agentb_sweep/20260929T151414Z_step_l_sweep_compare_levels0-9.json`, `nlcsplit/step_l_sweep_compare.py` | the independent sweep (water-monomer nonlocal term at levels 0-9, self-consistent and again on one fixed density matrix, ending in a partial `atom_grid` scan that dies on an unsupported angular grid), and the archived stdout plus sidecar JSON of our comparison against it, which carry the per-level difference column behind section 2.1 - the sweep file alone has no comparison column. Produced by the shipped script; its level-9 row covers the point pairs among 428,920 kept grid points, which is why that one row took hours. The `levels0-8` snapshot taken mid-run is kept beside it, hashed, as the record of what was known before level 9 landed; its header announces the intended 0-9 range, which is why that filename says 0-8 and this one says 0-9. |
| S22 | `evidence/attribution_referee/run.py`, `evidence/attribution_referee/referee_lib.py`, `evidence/attribution_referee/summarize.py`, `evidence/attribution_referee/probe_quadrature.py`, `evidence/attribution_referee/README.md`, `evidence/attribution_referee/outputs/results.json`, `evidence/attribution_referee/outputs/table.md`, `evidence/attribution_referee/outputs/summary.md`, `evidence/attribution_referee/outputs/validation.md`, `evidence/attribution_referee/outputs/convergence.md`, `evidence/attribution_referee/outputs/headline.md`, `evidence/attribution_referee/outputs/run_log.txt`, `evidence/attribution_referee/outputs/results_run1_20261001.json`, `evidence/attribution_referee/outputs/table_run1_20261001.md`, `evidence/attribution_referee/outputs/rerun_verify_20261001.log`, `evidence/attribution_referee/MANIFEST.sha256`, `evidence/attribution_referee/hetero.py`, `evidence/attribution_referee/outputs/hetero.json`, `evidence/attribution_referee/outputs/hetero_run_20261001.log` | the partition-free referee: two-Gaussian model density, the cross term by three independent routes (3-D Cartesian tensor product, 5-D cylindrical reduction, importance-sampled Monte-Carlo), the measured combined uncertainty 1.060e-05 Ha, the column that cancels the grid, and the falsification suite (positive control on the documented-wrong pairing, closed-form Gaussian and Coulomb anchors, node-normalisation guard). The two shipped runs give a file-level reproducibility check rather than a sentence: the two tables compare byte-identical, and the field-by-field diff of the two machine-readable results is confined to the recorded wall-clock fields and the worker count. The Monte-Carlo error bar in the same file comes from
`evidence/attribution_referee/mc_tighten.py` (4,000,000 draws per configuration, its own
seed base) and is stored in
`evidence/attribution_referee/outputs/mc_tight.json`, a separate sidecar, so neither
archived run is disturbed by it. Re-running `evidence/attribution_referee/run.py` regenerates
every number; `evidence/attribution_referee/summarize.py` re-quotes them without
re-quadrating. `hetero.py` is the heteronuclear extension, and it is written as a sidecar for
the same reason `mc_tighten.py` is: it must not disturb the archived table. Row 0 is therefore
homonuclear and labelled as the archived run labels it, and it reproduces the reference cross
term and the package cross term with a difference of exactly 0.000e+00 - which is what licenses
the three unequal-centre rows. It skips the referee's own disjoint half-box node set, because
that construction assumes two congruent boxes, and it runs each density under two different
element labels so the radii table's contribution is measured instead of assumed |
| S23 | `evidence/population/20260930T200927Z_stepk_soft-vs-hard-official.out`, `evidence/population/20260930T201142Z_stepk_soft-vs-hard-constructed.out`, `nlcsplit/step_k_population.py`, `evidence/population/MANIFEST.sha256` | the soft-vs-hard reading of the local term, per partition scheme, on both water-dimer geometries at grid level 3: hard populations credit a point to its owner only, soft populations spread it over the fragment factors at that point, and both are computed on PySCF's own partition weights so the measure is the converged one. The two files give the largest soft-hard population difference (1.527e-06 electrons official, 8.686e-07 constructed) and its conversion through beta into kcal/mol. Before these runs existed, this sentence quoted 8.7e-7 electrons on the strength of a working log only - the number was real but its geometry was not the published one, which is why the scope is now stated in the sentence |
| S24 | `nlcsplit/step_m_ccsdt.py`, `evidence/ccsdt/20260930T224400Z_stepm_ladder_after_refactor.out`, `evidence/ccsdt/20260930T235900Z_stepm_three_systems_631g.out`, `evidence/ccsdt/20261001T000400Z_stepm_three_systems_avdz.out`, `evidence/ccsdt/20260930T212300Z_stepm_ladder.out`, `evidence/ccsdt/20261001T044833Z_orca_crosscheck.out`, `evidence/ccsdt/20261001T052943Z_orca_crosscheck_three_systems.out`, `evidence/ccsdt/orca_crosscheck.py`, `evidence/ccsdt/README.md`, `evidence/ccsdt/MANIFEST.sha256`, `nlcsplit/tests/test_cc_convention.py`, `evidence/ccsdt/20261003T0703Z_stepm_water_fivebases_ghostcp_local.out` | the coupled-cluster anchor for the water-dimer binding energy: same official S22 geometry, same basis, same counterpoise convention, RHF reference, MP2/CCSD/CCSD(T) from PySCF's own modules, each rung reported both frozen-core and all-electron. The archive also records the mixed-convention bug this run nearly shipped with: freezing the monomers while switching only the dimer's convention printed -23.16 kcal/mol for the water dimer, which is impossible, and the impossibility was 17 kcal of oxygen 1s correlation counted on one side of the difference only. Two runs are kept because the second one exists to prove the first is still valid: after the frozen-core selection was refactored into a single call feeding both sides of the difference, the ladder was re-run with the script as it now ships, and stripped of wall-clock columns the two files differ in five lines, all of them one print statement whose wording changed - no energy moved. `nlcsplit/tests/test_cc_convention.py` pins that invariant, and one of its seven tests rebuilds the broken pairing on purpose to show the guard can fail. `evidence/ccsdt/orca_crosscheck.py` is the third-program check: ORCA 6.0.1, same geometries, same basis, same convention, on three systems and both conventions (eight rows, 24 single points), worst difference 0.0002 kcal/mol on the interaction energy and 1.2e-07 Ha between executions on the absolute energies. **What that check validated has to be restated:** it built its monomers the way the script of the day built them, so both programs were computing the *uncorrected* difference and agreeing about it - a cross-program check on a convention proves nothing about the convention when both sides share the same omission, which is why the corrected check is constructed from the definition instead of mirrored from the other script. The corrected comparison, with ghost functions on both sides and the basis dimension read back per part, is [S30]. `evidence/ccsdt/20261001T052943Z_orca_crosscheck_three_systems.out` is the one to cite for it; it also carries the correction of an earlier claim in this directory, which is why the basis check is stated the way it is. The first version of that check read ORCA's `Number of basis functions` field against PySCF's orbital count and reported agreement at 18 for a water monomer in 6-31G\* - true, but not a criterion: for the same monomer in aug-cc-pVDZ the field prints 47 while ORCA's own SCF and coupled-cluster sections print `Basis Dimension Dim .... 41` and `Number of AO's ... 41`, which is PySCF's number. So the script now reads back the AO dimension per part and compares it with the PySCF nao for the same geometry and basis (24/24 equal), and its verdict refuses to print "agree" unless the energy test and the basis test hold at the same time. The 47 itself is recorded as unexplained rather than rationalised: 25 shells with maximum angular momentum 2 admits no s/p/d/sp bookkeeping that yields both 47 and 41. The frozen-core convention of each ORCA run is likewise read from its own output (`chemical core (4 el)` on a dimer, `(2 el)` on a monomer, `NO frozen core` on the all-electron rungs) rather than assumed from the input keyword. **Dated correction, 2026-10-03:** the column headed `dE_CP` in the four ladder archives named above is *not* a counterpoise value - the monomers were built in their own basis, so the partner's functions were absent. [S30] gives the corrected ladders, the row-by-row proof that only the monomer side moved between the two sets of archives, and the size of what the mismatch was worth (0.2518-2.9711 kcal/mol per complex). The row is kept because it is the record of what those runs computed, and because the correction is the point of §3.2's second paragraph |
| S30 | `nlcsplit/step_m_ccsdt.py`, `nlcsplit/tests/test_cc_convention.py`, `evidence/ccsdt/README.md`, `evidence/ccsdt/20261002T1230Z_cp_defect_diagnosis.out`, `evidence/ccsdt/snnu_cp_defect_diagnosis.py`, `evidence/ccsdt/20261003T0616Z_orca_ghost_probe.out`, `evidence/ccsdt/orca_ghost_probe.py`, `evidence/ccsdt/20261003T0620Z_orca_vs_pyscf_ghost_cp.out`, `evidence/ccsdt/orca_ghost_cc_probe.py`, `evidence/ccsdt/20261003T0605Z_stepm_dimers_ghostcp_local.out`, `evidence/ccsdt/20261003T0652Z_snnu_cp_rebuild_631.out`, `evidence/ccsdt/snnu_cp_rebuild_631.sh`, `evidence/ccsdt/20261003T0700Z_snnu_cp_rebuild_compare.out`, `evidence/ccsdt/cp_rebuild_compare.py`, `evidence/ccsdt/ladder_parse.py`, `evidence/ccsdt/ladder_parse_selftest.py`, `evidence/ccsdt/20261003T0653Z_ghost_monomer_scf_check.out`, `evidence/ccsdt/ghost_monomer_scf_check.py`, `evidence/ccsdt/MANIFEST.sha256` | the counterpoise correction itself, and the evidence chain that holds it up. `20261002T1230Z` is the 10-second diagnosis that found it (a water monomer at 18 basis functions against the complex's 36, -6.8559 against -4.8789). `20261003T0616Z` decides ORCA's ghost-atom spelling by the basis dimension rather than by the manual, and keeps two rejected spellings plus the dropped-partner case as negative controls, because without them "the colon form gives Dim=36" would not be evidence of anything. `20261003T0620Z` computes the corrected anchor in two programs and reports 0.0001 kcal/mol on the counterpoise difference and on the uncorrected one at both conventions, with the ghost construction carried into the correlation space (Dim 36 on every part) and the frozen-core field read back as `chemical core (2 el)` on a monomer whose second oxygen has basis functions but no charge. `20261003T0652Z` is the corrected ladder for all eight complexes at 6-31G*, Slurm job 51023 (COMPLETED, ExitCode 0:0, 42 min 30 s, 16 CPUs on cpu1), whose two pre-run guards compare the *complex's* RHF reference - the side the fix does not touch - against the archived values (4.31e-11 and 1.14e-11 Ha). `evidence/ccsdt/cp_rebuild_compare.py` then reads the old and new archives side by side and refuses to print a table unless every complex CCSD(T) energy is identical to 1e-7 Ha: 22 of 22 comparable rows agree to 0.0e+00, so the whole change in the `dE_CP` column is attributable to the monomer construction and not to the machine, the thread count or the geometry parse. The same script emits the eight deviations quoted in §3.2 and the two-grid-level table, reading both sides from archives rather than from this row. `20261003T0653Z` closes the remaining way a ghost monomer could be wrong without being noticed: every ghost and bare SCF converged, and every ghost energy lies *below* its bare counterpart, which is the variational direction a counterpoise construction must have - a check independent of the convergence flag itself. `evidence/ccsdt/ladder_parse.py` is the single parser both consumers use, and
`evidence/ccsdt/ladder_parse_selftest.py` is its eight-case self-test; four of those cases are fed deliberately broken rows, and the one that matters here is a positive interaction energy, which an earlier version of the parser dropped silently because its regex spelled the sign as `-?` |
| S31 | `evidence/ccsdt/20261003T1212Z_snnu_sandwich_avdz_ghostcp.out`, `evidence/ccsdt/20261004T0135Z_cp_rebuild_compare_derived7.out`, `evidence/l2cp/20261004T0120Z_snnu51025_dft_avdz_ASSERT.out`, `evidence/l2cp/20261003T1747Z_snnu51052-dft_cp_avdz_pi.out`, `evidence/l2cp/20261003T1747Z_snnu51052-sbatch.out`, `evidence/l2cp/20261004T0328Z_snnu51083-dft_cp_avdz_small.out`, `evidence/l2cp/20261004T0328Z_snnu51083-sbatch.out`, `evidence/l2cp/20261004T0903Z_wsl2121-small_crosscheck.out`, `evidence/l2cp/20261003T1721Z_snnu51050_dft_avdz_small_interleaved.out`, `evidence/l2cp/cp_version_runner.py`, `evidence/l2cp/20261003T0907Z_wsl2121-cp_levels.out`, `evidence/l2cp/20261003T0911Z_wsl2140-cp_levels.out`, `evidence/l2cp/20261003T0804Z_snnu51028-guard_FAIL.out`, `evidence/l2cp/cp_version_probe.py`, `evidence/l2cp/20261003T0928Z_cp_version_probe.out`, `evidence/l2cp/dtot_2121_aromatic.py`, `evidence/l2cp/20261003T1025Z_wsl2121-dtot_aromatic.out`, `evidence/ccsdt/20261003T0925Z_cp_rebuild_compare_2121.out`, `evidence/ccsdt/20261004T0110Z_cp_rebuild_compare_derived.out`, `evidence/l2cp/20261003T1025Z_wsl2121-dtot_aromatic.out`, `evidence/l2cp/dtot_2121_aromatic.py` | the counterpoise column of the functional side, and the fact that it was two columns. `20261003T0804Z` is the guard that found it: a cluster job that must reproduce a level-2 counterpoise value before spending time on aug-cc-pVDZ got -6.1526 where it was told to expect -6.1290 and stopped with rc=1, which is the whole point of a pre-spend guard. `evidence/l2cp/cp_version_runner.py` is then run twice on one machine - same file, same geometry, same basis, same OMP thread count, same numpy and python, only `PYTHONPATH` differentiating PySCF 2.12.1 from 2.14.0 - and its two outputs are `20261003T0907Z` and `20261003T0911Z`. The 2.14.0 run reproduces the 2026-09-28 batch (-6.129446 against the archived -6.129, -3.675086 against -3.6750, -0.465680 against -0.4660), so nothing in that batch was miscalculated: the paper had put two implementations in one column. `evidence/l2cp/cp_version_probe.py` reads both logs and refuses to print unless (i) every complex and bare-monomer grid is point-for-point identical between the versions, (ii) the production counterpoise and the script's own re-derivation of the ghost monomer agree to 1e-6, and (iii) all six (system, level) cells are present in both; its verdict is that the ghost atom grids are the only thing that differs, in six of six cells, and that the uncorrected interaction energies agree to 1e-6 kcal/mol. That last point was, at first, the only thing licensing 3.1's BSSE list, three of whose cells subtracted a 2.12.1 counterpoise value from a 2.14.0 uncorrected one. Borrowing that justification was not good enough, so the uncorrected side of the five aromatic cells is now measured in the same release (`evidence/l2cp/dtot_2121_aromatic.py` -> `evidence/l2cp/20261003T1025Z_wsl2121-dtot_aromatic.out`: -4.340866, -2.928830, -1.780045, -3.578184 and -3.185938 kcal/mol), which reproduces the older batch to the three decimals it prints and makes 3.1's list eight same-release numbers rather than six mixed ones. `20261003T0925Z` is the same comparison's output for the eight-row deviation table of 3.2: the table is now generated by `deviation_table()` rather than carried across by hand, the identity check has grown from 22 to 28 rows (worst complex-energy difference 2.0e-10 Ha across two days and two Slurm jobs), and the grid-level table has grown from five systems to eight. `20261003T1212Z` closes the last counterpoise anchor of the correlated side (the sandwich at aug-cc-pVDZ, both frozen-core conventions, Slurm job 51024 finished 12:12:57Z), which is what lets 3.2 quote a span and a ratio for that complex; `20261004T0135Z` is the regenerated derived table for seven systems. `20261004T0120Z` is a failure kept on purpose: the functional-side aug-cc-pVDZ job died on the counterpoise function's own dimension assert because that function built ghost monomers in the *module default* basis rather than the complex's - correct for every 6-31G* run in this paper, wrong the moment a caller passed another basis. The fix and its negative-control test are in `nlcsplit/step_h_s22.py` and `nlcsplit/tests/test_regression.py`. The re-submitted job 51052 is what closes the functional side's matched basis: its sbatch header records `3.10.19 pyscf 2.12.1` plus the SHA-256 of both the runner and the *fixed* module, it reproduces the two archived 6-31G\* guard values to 0.0000 before spending cluster time, and it prints the three π aug-cc-pVDZ counterpoise values used in 3.2. Its companion `20261003T1721Z` is the same rung's earlier attempt on the small dimers, kept because the bytes show two jobs writing one path: a `DFT_SET=pi` header over a `DONE DFT_SET=small` trailer, and guard rows whose closure field disagrees with the clean archive while every other printed field on that row is identical |
| S32 | `evidence/nlc_cp/nlc_bsse_measure.py`, `evidence/nlc_cp/20261006T0657Z_nlc_bsse_three_small_dimers.out`, `nlcsplit/step_h_s22.py`, `nlcsplit/logs/step_h.json`, `evidence/nlc_cp/MANIFEST.sha256` | the basis-set superposition error of dE_NLC itself, which §4.1 used to exempt by assertion instead of measuring it. The script evaluates the same nonlocal term twice on one frozen superposed density - monomers in their own basis, then monomers carrying the partner's functions with no charge (the ghost water monomer is printed at N=13832 grid points against 9192 for the bare one, which is what a ghost basis costs here) - and reports the difference at level 1, 6-31G\*, for water, ammonia and methane: -0.0074, -0.0031 and +0.0075 kcal/mol. Its denominator is not chosen at readout: the `span` column is read from the production sidecar `nlcsplit/logs/step_h.json`, the same four-scheme attribution span §2.3 publishes for that cell (0.0435, 0.0290, 0.0040 kcal/mol), so the ratios 0.17, 0.11 and 1.87 are two archived numbers divided, not a new estimate. Before any of it ran, the no-ghost side had to reproduce the archived dnlc values it claims to be the same quantity as, at a 0.001 kcal/mol gate: 8.660e-15, 6.443e-05 and 3.898e-04 kcal/mol. Three cells are the whole coverage of this row - the three aromatic complexes and both benzene dimers carry no measured dE_NLC superposition error, and this row names that gap instead of leaving the reader to find it |
| S33 | `evidence/common_grid/ownership_vs_quadrature.py`, `evidence/common_grid/20261006T085207Z_ownership_vs_quadrature_l1_small.out`, `evidence/common_grid/20261006T090714Z_ownership_vs_quadrature_l1_benzenex.out`, `evidence/common_grid/NOTE-clock-skew.md`, `nlcsplit/partition.py`, `nlcsplit/nlc.py`, `nlcsplit/tests/test_nlc_closure.py`, `evidence/common_grid/MANIFEST.sha256` | the measurement that separates the two things a "partition scheme" changes at once. One SCF, one grid and one set of weights are held fixed while only the ownership factors vary: the package's own multi-centre factor is evaluated on the common grid's coordinates, normalised point-by-point to sum to one over atoms, and handed to the decomposition function through its soft= path - so the quadrature cannot move and the reported spread is attribution alone. The quadrature side is then read separately, as the totals each scheme produces on its own grid with the same density matrix. Four guards are in the file: every point's soft weights must sum to 1 within 1e-8 or the run exits; the hard nearest-atom assignment on the common grid must reproduce the published census control value (water, -7.8950 kcal/mol, gate 0.005 - the archive prints a difference of 0.0000); the closure check is on throughout, so each block sum is compared against one monolithic evaluation over the same kept points rather than against itself; and the soft= path itself is pinned by nlcsplit/tests/test_nlc_closure.py, whose negative controls regroup the blocks so that one cross term is double-counted and then dropped, and require the guard to fire. The same runs print the discrete residual of the local term, beta times (sum W rho minus the electron number), which is the quantity the abstract's cancellation statement is about: 0.0000 to 0.0011 kcal/mol over six cells at grid level 1. Two things this archive is not. Its water cell reads a pure-attribution span of 0.0433 kcal/mol against the 0.0435 published for the same cell in Table 1, and the difference is the grid, not the density - one number is measured on the common grid with the weights held fixed, the other across the four schemes' own grids. And both filenames carry a host-supplied timestamp rather than the machine's own clock, because the Linux clock on the machine that produced them was three days behind when the first archive was named; `evidence/common_grid/NOTE-clock-skew.md` records which name was stamped by which clock and why the bytes were not renamed afterwards |
| S25 | `nlcsplit/fastpair.py`, `nlcsplit/step_j_scaling.py`, `evidence/scaling/step_j.json`, `evidence/scaling/20260929T1340Z_step_j_scaling.out`, `evidence/scaling/step_j_rerun_20260930.json`, `evidence/scaling/step_j_rerun_20260930.txt`, `evidence/fastpair_ab/fastpair_ab_compare.json`, `evidence/fastpair_ab/fastpair_ide_validation.json`, `nlcsplit/tests/test_fastpair.py`, `evidence/scaling/MANIFEST.sha256` | the wall-clock and certificate numbers in §3.6, recomputed from these sidecars rather than transcribed into the prose: 33 screened/exact pairs over two windows, 1.08-10.28x (archived, 18 pairs) and 1.37-13.29x (re-run, 15 pairs), none faster than exact; the minimum block-pair certificate 197.96 Ha against the -8.34e-4 Ha quantity it would decide on, with n_pairs_bound_below_value = 0 and dropped_pairs = []. Two windows are kept because the second was measured on a different day and the two must not be merged into one interval. Each row carries two different error quantities and conflating them changes the headline: cert_err_ha is the guarantee the traversal can actually use, abs_dE_kcal is the measured deviation from the exact sum. Restricted to tau = 1e-12, exactly 8 of the 11 rows have abs_dE_kcal <= 1e-6 kcal/mol and those span 84.4-95.4% of far-field point pairs evaluated; only 4 rows have a *certificate* that small, and those span 93.7-95.4%. The 84.4% figure is therefore the usable-accuracy statement, not a mistake, and the looser certificate is precisely the result being reported. The monotone accept rule and the box separation are pinned by nlcsplit/tests/test_fastpair.py, which fails if a leaf pair is accepted out of order |
| S27 | `evidence/ccsdt/20261002T0715Z_snnu_benzene_avdz.out`, `evidence/ccsdt/snnu_benzene_avdz.sh`, `evidence/ccsdt/20261002T043400Z_snnu_benzene_ladder.out`, `evidence/ccsdt/20261009T085405Z_cp_rebuild_compare_frozengap.out`, `evidence/ccsdt/MANIFEST.sha256` | the second basis for the three π complexes, i.e. the three spans quoted in §3.2, Slurm job 50946 (COMPLETED, ExitCode 0:0, 44 min 22 s, 16 CPUs on cpu1), same script and same call path as [S24] and [S26], with a first-stage guard that re-derives the archived water-dimer aug-cc-pVDZ value (-5.2478 against -5.248). Values are read from the archived detail blocks rather than transcribed, and which construction a value came from has to be said out loud now: the six numbers this job printed for the three π complexes - frozen-core -4.5172 / -3.7273 / -3.0093 and all-electron -4.7192 / -3.9240 / -3.2010 kcal/mol, in benzene-water / benzene-ammonia / benzene-methane order - are monomers built in their own basis, the construction [S30] retired, and against the uncorrected 6-31G* rows of [S26] they give the 0.864 / 1.454 / 1.951 this row used to carry. Under ghost functions the same six cells are -2.7107 / -1.8795 / -1.1200 and -2.7144 / -1.8824 / -1.1225, so the three spans that enter the §3.2 comparison are 0.7383 / 0.9913 / 1.2016 kcal/mol against the corrected 6-31G* rows, every one of them printed by `evidence/ccsdt/20261009T085405Z_cp_rebuild_compare_frozengap.out` rather than subtracted by hand. That run retells the frozen-core story too, and the retelling is a correction to this row: the gap between the frozen-core and all-electron counterpoise value of one complex at one basis was 0.0354-0.0427 kcal/mol at 6-31G* and 0.1917-0.2020 at aug-cc-pVDZ in the own-basis column, while the ghost column puts those same six gaps at 0.0026-0.0032 and 0.0025-0.0037. An earlier version of this row reported that basis dependence as a property of the frozen-core choice. It is not one - it is the correlated BSSE changing size with the basis, the same effect §3.2 measures on the deviation, and in the corrected column no basis trend is left to read. The runner script is a byte- and hash-verified copy of the remote producer. No CBS claim: two basis points, no extrapolation |
| S28 | `evidence/ccsdt/20261002T0630Z_snnu_benzene_dimer_ccsdt.out`, `evidence/ccsdt/snnu_benzene_dimer.sh`, `evidence/ccsdt/20261002T0905Z_snnu_benzene_dimer_dft_cp.out`, `evidence/ccsdt/snnu_dft_cp_dimer.py`, `evidence/ccsdt/MANIFEST.sha256` | the parallel-displaced benzene dimer (S22_11, 192 AO) as the seventh anchored complex: the correlated side and the functional side under one basis and one convention. Both archives named in this row, and the runner script beside them, call that geometry "sandwich"; the word predates the measurement now kept in `evidence/recompute/20261005T0340Z_benzene_dimer_label_measure.out` (interplanar angle 0.0 deg, in-plane slip 1.698 A, which is what parallel-displaced means), and the archived bytes stay as they are because their hashes are registered - the dated note recording the correction is `evidence/ccsdt/README.md`. CCSD(T) is Slurm job 50945 (COMPLETED, ExitCode 0:0, 11 min 48 s, 32 CPUs), the DFT counterpoise values are job 50969 (COMPLETED, ExitCode 0:0, 38 min 07 s, 16 CPUs), and both runs first re-derived an archived value before spending the rest of their wall-clock - 50945 reproduced the water-dimer anchor to 0.0001 and the benzene-methane one to 0.0000 kcal/mol, 50969 reproduced benzene-methane at level 2 to 0.0000. Frozen-core counterpoise as those two jobs printed it: CCSD(T) -1.4999, omegaB97X-V/6-31G* level 2 -1.9403 (deviation -0.440) and level 1 -0.7233 (deviation +0.777). Those two deviations are superseded rather than dropped: that CC row came from monomers solved in their own basis, and under the ghost-function construction of [S30] the same complex energy gives +1.4712, so the deviations become -3.4115 and -2.1945, which is what the table in section 3.2 carries. The same caveat applies to the rung-by-rung sentence after it: the corrected rebuild re-ran the CCSD(T) rung on this complex but did not print MP2 or CCSD for it, so those two rungs are on record only under the old monomer construction. The ladders also carry a result about correlation order that the deviation column cannot show: CCSD alone gives -0.6831 and the perturbative triples supply 0.817 of the -1.4999 total, while MP2 overbinds by a factor of two at -3.1059, so the two cheaper rungs err in opposite directions on the same system. Neither archive claims a CBS limit, a relaxed geometry, or that level 2 is grid-converged. This complex did get its second basis afterwards (`evidence/ccsdt/20261003T1212Z_snnu_sandwich_avdz_ghostcp.out`, named in [S31]), so its basis move and its ratio of 1.02 are quoted in section 3.2; what still has no correlated anchor of any kind is the third geometry, the one built by the benzene_sandwich() constructor of `nlcsplit/geomlib.py`, and Figure 4's lower panel stays at the six systems it was drawn with |
| S29 | `evidence/ccsdt/20261002T1030Z_snnu_benzene_dimer_B.out`, `evidence/ccsdt/snnu_benzene_B.sh`, `evidence/ccsdt/snnu_dft_cp_dimer_B.py`, `evidence/ccsdt/MANIFEST.sha256` | the eighth and last complex, the T-shaped benzene dimer (S22_20, 192 AO), which closes the counterpoise coverage of §3.2 at all eight systems - that archive's own header labels this geometry parallel-displaced, the same inverted pair of words the row above documents, and the measured interplanar angle of 90.0 deg is what makes it T-shaped. One Slurm job (50980, COMPLETED, ExitCode 0:0, 1 h 02 min 23 s, 16 CPUs) ran both sides: CCSD(T)/6-31G* frozen-core -2.5506 and all-electron -2.6300, and omegaB97X-V/6-31G* counterpoise -2.4297 at level 2 (deviation +0.121) against -2.6953 at level 1 (deviation -0.145). Two guards ran first and are quoted in the archive: the water-dimer anchor to 0.0001 kcal/mol and the sandwich's own CCSD(T) value to 0.0000, the latter being another cross-job reproduction of `evidence/ccsdt/20261002T0630Z_snnu_benzene_dimer_ccsdt.out`. The grid step on this complex is 0.266 kcal/mol and changes the sign of the deviation, which is why the grid paragraph counts three sign changes out of the five systems measured at both levels. No CBS limit, no relaxed geometry, and no claim that level 2 is grid-converged: the archive states all three as non-claims |
| S26 | `evidence/ccsdt/20261002T043400Z_snnu_benzene_ladder.out`, `evidence/ccsdt/snnu_benzene_runner.sh`, `evidence/ccsdt/20261002T0528Z_snnu_benzene_dft_cp.out`, `evidence/ccsdt/snnu_dft_cp_levels.py`, `evidence/ccsdt/20261002T0620Z_snnu_benzene_methane_l2.out`, `evidence/ccsdt/snnu_dft_cp_methane_l2.py`, `evidence/ccsdt/MANIFEST.sha256` | the benzene-complex ladder behind §3.2's third and fourth paragraphs, computed on a second cluster after the first one saturated. The CCSD(T) side is `nlcsplit/step_m_ccsdt.py` unchanged, run under Slurm on partition `cpu` (job 50937, COMPLETED, ExitCode 0, 4 min 08 s) through the same call path as the water/ammonia/methane ladder of [S24], which is what makes the two comparable rather than merely similar; the producer script is archived verbatim beside the output. Before any benzene wall-clock was spent, the runner re-derives the already-archived water-dimer value from the same code and refuses to proceed otherwise (`guard: \|-6.8559 - (-6.856)\| = 0.0001 <= 0.0015 -> PASS`), and the archive records the two ways that guard first failed in ways that both looked like success: a 0-byte uploaded script that the scheduler reported as COMPLETED with exit 0 in one second, and a guard that parsed a summary table the script does not print for a single system. The DFT side deliberately imports the counterpoise routine of `nlcsplit/step_h_s22.py` instead of running that module, because its output path is hardcoded to `nlcsplit/logs/step_h.json`, the carrier of the main table - three numbers are not worth overwriting a published archive. The level-2 grid claim rests on three archives, not two: the first DFT run (job 50938) was cancelled by a 30-minute limit and declares itself partial in its own header, and the missing benzene-methane row came from job 50943, whose archive also records that its level-1 line reproduces the earlier job byte for byte. The producer scripts were copied only after their sha256 matched the remote originals. None of the three archives claims a CBS limit (one basis, no extrapolation) or relaxed geometries (official S22 initial structures, unrelaxed), and the benzene dimer at 192 AO is in none of them |

Three absences are stated rather than hidden. `evidence/centos/...step_f_h2o2.out` predates the
water-dimer geometry fix (its inter-fragment minimum is 2.0258 A against 1.95 A in
`evidence/l2cp/`), so S8 cites it only for the component accounting, never as a
current-geometry result. S15's files were sitting in `scratch/`, which is gitignored - they
were promoted into `evidence/` on 2026-09-29 for exactly that reason. And one distinction has
to be kept: S6 and S13 come from the same CentOS batch timestamped 2026-09-28T16:58, which is
earlier than the geometry fix, while S12's primary artefact is a recompute run afterwards.
Within that earlier batch the initial S22 structure and the relaxed one are distinguishable
(the level-0 6-31G* value -0.5316 appears in S13's ladder, while the -0.5975 of the relaxed
structure does not), so S13's cross-grid spreads are read here as measured on the *initial*
S22 geometry, not on the relaxed one that carries the headline numbers. The level-1 column of
that same ladder agrees with the later recompute to four decimals for all three bases the two
runs share, so the grid-convergence conclusion does not turn on which geometry was used - but
that was checked after the fact. The full ladder has since been re-run on the geometry that
carries the headline numbers, and section 3.4 quotes that run
(`evidence/recompute/20260930T191014Z_stepg-official.out`); what remains true is the
weaker thing: the cross-grid spreads of S13 are still measured on the initial structure,
because that is the batch which contains all four grid levels.
