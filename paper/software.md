# nlcsplit — fragment and pair resolution of the VV10 nonlocal-correlation energy

*Draft for a software venue (SoftwareX / JOSS shape). Numerical claims carry a
`[S#]` tag into `paper/main.md` and `MAIN-skeleton.md`; scripts named here are in
the repository and their archived stdout under `nlcsplit/logs/` is the source.*

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
uncertainty that the attribution choice contributes (0.004-0.310 kcal/mol
absolute, 0.8-18.2% relative, unchanged across five basis sets and across grid
levels, with no ordering by interaction type), which is the error bar any future
use of such numbers must carry [S12]. And it produces evidence about the quantity
itself: ΔE_NLC ranges from 16% to 223% of ΔE_xc across one benchmark set, and
100% versus 54% for two geometries of the same benzene dimer, so the VV10 term
cannot be reported as "the dispersion energy" without qualification [S2].

## 5. Availability and quality assurance

Apache-2.0; no GAMESS source is included, linked or required. Every table in the
companion text maps to one `step_*.py`, and archived stdout is kept under a
UTC-stamped filename. The test suite has 40 tests, including a naive triple-loop
versus BLAS comparison of the kernel, per-scheme additivity checks, and geometry
guards that assert bond lengths and angles at construction time.

Release hygiene is checked end to end rather than assumed: the package is pip
installed into a separate directory and its tests are then run from outside the
source tree with `pytest --pyargs nlcsplit`. That procedure found two real defects
- script-style modules named `test_*.py` inside the package, which pytest collects
and executes at import, and a `slow` marker registered only in repository
configuration - plus one non-obvious build hazard: pip builds local directories in
place, and the setuptools `build_py` step does not prune deleted modules from
`build/lib`, so a module moved out of the package can still be shipped from the
stale build tree unless that tree is removed first (`CONTRIBUTING.md`).

Continuous integration runs the suite on a PySCF version matrix in two stages: a
fast pass with `-m "not slow"`, then the full pass. The split is documented as a
hazard rather than a convenience - the fast pass excludes the two tests that
compare against the native kernel, so CI must not be read as satisfied by the
first stage alone.

Independent verification is currently limited to a second implementation of the
same kernel inside the same library. An earlier version of this documentation
claimed agreement with ORCA 6.0.1 to 6e-4 kcal/mol; re-reading the archived ORCA
output showed it prints no separately reported nonlocal term, and the cited figure
could not be reconstructed from any file in the project, so the claim is withdrawn
here as well as in the companion text. A second-program check (an ORCA run that
prints the VV10 term, Psi4, or libxc `xc_nlc_vxc` through its own bindings) is the
first item outstanding.

## 6. Limitations

Quadratic cost in retained grid points, with no sub-quadratic approximation.
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
