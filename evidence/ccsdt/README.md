# evidence/ccsdt — the coupled-cluster anchor for the water-dimer binding energy

Three water-dimer runs of the same five-basis ladder, all counterpoise-corrected, all on the
official S22 entry-2 geometry (`scratch/lit/s22/S22_02.xyz`, O...O = 2.9104 A, the initial
unrelaxed complex geometry). Producer: `nlcsplit/step_m_ccsdt.py`. Cited by
`paper/main.md` §3.2 as **[S24]**, and summarised in `MAIN-skeleton.md` table 3b.

| file | what it is | cite this one |
|---|---|---|
| `20260930T224400Z_stepm_ladder_after_refactor.out` | the run made by the script **as it now ships** | yes - this is the object [S24] names |
| `20260930T212300Z_stepm_ladder.out` | the earlier run, which is where the first numbers came from | only as the predecessor, for the comparison below |
| `20261001T052943Z_orca_crosscheck_three_systems.out` | ORCA 6.0.1 recomputing the same counterpoise energies on **three systems**, with the AO dimension checked per part | yes - this is the object the third-program claim names |
| `20261001T044833Z_orca_crosscheck.out` | the same check on water only, two executions | as the predecessor: its stdout stands, its header carries a claim that was wrong, and the file opens with a dated correction |
| `20260930T235900Z_stepm_three_systems_631g.out` | water + ammonia + methane at 6-31g\* | yes, for the three-system statement |
| `20261001T000400Z_stepm_three_systems_avdz.out` | the same three in aug-cc-pVDZ | yes - and this is the run that kills the 6-31g\* methane reading |

**The two water runs agree, and that is a check, not a restatement.** Stripping every
wall-clock column and comparing line by line: 60 content lines each, five differing, and all
five are the one print statement whose wording changed in the refactor. No energy and no
interaction energy differs. The refactor replaced "switch the dimer's frozen count, leave the
monomers hard-coded" with a single `freeze_plan()` call feeding both sides of the counterpoise
difference, which is what `nlcsplit/tests/test_cc_convention.py` now pins - including one test
that rebuilds the broken pairing and asserts it violates the invariant, so the guard has teeth.
The generalisation to multiple systems is checked the same way: the water column of the
three-system 6-31g* run reproduces -7.149 / -6.682 / -6.856 / -6.887 exactly.

Read the numbers as ladders, not as single reference values:

| system | basis | MP2 | CCSD | CCSD(T) frozen | CCSD(T) all-electron | our wB97X-V CP |
|---|---|---|---|---|---|---|
| water | 6-31g\* | -7.149 | -6.682 | **-6.856** | -6.887 | -6.129 |
| water | cc-pVDZ | -7.394 | -6.871 | -7.085 | -7.116 | |
| water | aug-cc-pVDZ | -5.210 | -4.966 | **-5.248** | -5.327 | |
| water | cc-pVTZ | -6.111 | -5.646 | -5.932 | -6.140 | |
| water | aug-cc-pVTZ | -5.161 | -4.942 | **-5.203** | -5.699 | |
| ammonia | 6-31g\* | -4.620 | -4.293 | **-4.455** | -4.473 | -3.675 |
| ammonia | aug-cc-pVDZ | -3.373 | -3.070 | **-3.331** | -3.372 | |
| methane | 6-31g\* | -0.149 | -0.129 | **-0.178** | -0.187 | -0.466 |
| methane | aug-cc-pVDZ | -0.918 | -0.821 | **-0.947** | -0.981 | |

kcal/mol. The functional values are ωB97X-V/6-31g\* level-2 at the same geometries
(`evidence/l2cp/20260928T213839Z_centos-step_h_l2cp.out:6`).

**Do not read a sign off the 6-31g\* block.** On that basis alone the functional looks
shallower than correlation for water (0.73) and ammonia (0.78) and deeper for methane (0.29),
i.e. a sign that changes with the system. The aug-cc-pVDZ run moves methane by a factor of
five and inverts that comparison, because a dispersion-bound dimer needs diffuse functions
that 6-31g\* does not have. The paper states the surviving version: at fixed basis the
deviation is 0.3-0.8 kcal/mol with no single sign, while the correlated reference itself moves
0.18→0.95 (methane), 4.46→3.33 (ammonia) and 6.86→5.25 (water) on the basis alone - two
effects of the same size, which is why §3.2 judges the functional nowhere.

Two things this directory does not claim. It is not a CBS extrapolation: no two-point formula
is applied, because with these rungs no error bound could be attached to it, and the
aug-cc-pVQZ rung that would matter was not run here. And the all-electron column is not a
second reference - it is the measurement of what the frozen-core choice is worth in each
basis, which at 6-31g\* is 0.031 kcal/mol and at cc-pVTZ is 0.21.

## Third-program check: ORCA 6.0.1 recomputes the same counterpoise energies

Everything above was produced by one program (PySCF's own `cc`/`mp` modules). That is the
same shape of argument that this repository already had to repair once for the nonlocal term,
where "checked against a second implementation" turned out to mean a second implementation
inside the same library. `orca_crosscheck.py` asks the analogous question here: same
geometries, same basis, same counterpoise convention, ORCA instead of PySCF.

The first two executions covered the water dimer only; that table is repeated here because
these are the rows the correction below is about:

    basis          convention     ORCA       PySCF      diff
    6-31G*         frozen        -6.8560    -6.8559    -0.0001
    6-31G*         all-electron  -6.8870    -6.8869    -0.0001
    aug-cc-pVDZ    frozen        -5.2480    -5.2478    -0.0002
    aug-cc-pVDZ    all-electron  -5.3275    -5.3273    -0.0002

kcal/mol, worst |difference| **2e-04**, duplicated in a second execution at 3e-04 - three
decimal places, which is the agreement two programs using the same basis are expected to
reach on an interaction energy. Read as "at the level of the noise these runs have", not as a
calibrated two-program error bar: the two executions move one row by ~1e-4 kcal/mol, which is
ORCA's own run-to-run repeatability here. The absolute CCSD(T) energies are tighter still: the
dimer agrees to 1.0-1.2e-07 Ha and the monomer sums to 2.8-4.6e-07 Ha across all four rungs.

Three details that keep this from being a coincidence - one of which we got wrong first.

**The basis has to be proven identical, and the field originally used to prove it does not.**
An earlier version of this README claimed both programs "report 18 basis functions for a
water monomer in 6-31G\*, so the d shells carry the same convention". Widening the plan to
ammonia and methane showed that ORCA's `Number of basis functions` is not an identity
criterion: the same water monomer in aug-cc-pVDZ prints 47 in that field, while ORCA's own
SCF section prints `Basis Dimension Dim .... 41` and its coupled-cluster section
`Number of AO's ... 41` - and 41 is PySCF's nao. The 18/18 agreement in 6-31G\* was a
coincidence of that field in that basis. The check now reads the AO dimension for every part
of every run, and `20261001T052943Z_orca_crosscheck_three_systems.out` reports 24/24 same
space. The 47 could not be accounted for from ORCA's own output (25 shells, maximum angular
momentum 2 - no s/p/d/sp bookkeeping reproduces 47 and 41 together), so the archive records
that the field disagrees with the AO count and stops there instead of inventing a reason.

**The verdict needs both halves at once.** The bar is 0.001 kcal/mol - three decimals, which
is what two programs sharing a basis are expected to reach on an interaction energy, and not
the 0.02 this script was first written with; the measured 0.0002 clears the tight bar by a
factor of five, while the loose one would have passed a real 6d/5d mismatch (worth
0.01-0.1 kcal/mol) without a word. The script also refuses to print "agree" unless the energy
test and the 24/24 basis test hold together, because 2e-4 between two different basis sets
would not be agreement.

**The frozen-core convention is read back, not assumed**, from each run's own
`Frozen core treatment ... chemical core (4 el)` on the dimer and `(2 el)` on a monomer, and
`NO frozen core` on the all-electron rungs.

On three systems the worst difference is still 0.0002 kcal/mol: water -0.0001 and -0.0001
(6-31G\*, frozen then all-electron), -0.0002 and -0.0002 (aug-cc-pVDZ), ammonia +0.0001 and
-0.0000, methane +0.0001 and +0.0000. Between two executions of identical configuration all
24 absolute energies reproduce, largest difference 1.09e-08 Ha = 6.8e-06 kcal/mol - so the
1e-4 scatter visible in the earlier pair lives in the interaction energy, where three
independently noisy energies are combined, not in the CCSD(T) evaluations themselves.

ORCA reports what it actually did rather than what was asked, and the script reads that back
instead of trusting the input keyword. The two forms in these logs are
`Frozen core treatment ... chemical core (4 el)` on the dimer and `... chemical core (2 el)`
on each monomer for the frozen rungs - 4 = two oxygens, 2 = one - and
`Frozen core treatment ... NO frozen core` for the all-electron ones, where the parser records
zero and the run is compared against PySCF's all-electron column.
