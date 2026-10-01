# evidence/ccsdt — the coupled-cluster anchor for the water-dimer binding energy

Three water-dimer runs of the same five-basis ladder, all counterpoise-corrected, all on the
official S22 entry-2 geometry (`scratch/lit/s22/S22_02.xyz`, O...O = 2.9104 A, the initial
unrelaxed complex geometry). Producer: `nlcsplit/step_m_ccsdt.py`. Cited by
`paper/main.md` §3.2 as **[S24]**, and summarised in `MAIN-skeleton.md` table 3b.

| file | what it is | cite this one |
|---|---|---|
| `20260930T224400Z_stepm_ladder_after_refactor.out` | the run made by the script **as it now ships** | yes - this is the object [S24] names |
| `20260930T212300Z_stepm_ladder.out` | the earlier run, which is where the first numbers came from | only as the predecessor, for the comparison below |
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
