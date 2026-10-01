# evidence/ccsdt — the coupled-cluster anchor for the water-dimer binding energy

Two runs of the same five-basis ladder, both counterpoise-corrected, both on the official
S22 entry-2 geometry (`scratch/lit/s22/S22_02.xyz`, O...O = 2.9104 A, the initial
unrelaxed complex geometry). Producer: `nlcsplit/step_m_ccsdt.py`. Cited by
`paper/main.md` §3.2 as **[S24]**, and summarised in `MAIN-skeleton.md` table 3b.

| file | what it is | cite this one |
|---|---|---|
| `20260930T224400Z_stepm_ladder_after_refactor.out` | the run made by the script **as it now ships** | yes - this is the object [S24] names |
| `20260930T212300Z_stepm_ladder.out` | the earlier run, which is where the first numbers came from | only as the predecessor, for the comparison below |

**The two agree, and that is a check, not a restatement.** Stripping every wall-clock column
and comparing line by line: 60 content lines each, five differing, and all five are the one
print statement whose wording changed in the refactor. No energy and no interaction energy
differs. The refactor replaced "switch the dimer's frozen count, leave the monomers hard-coded"
with a single `freeze_plan()` call feeding both sides of the counterpoise difference, which is
what `nlcsplit/tests/test_cc_convention.py` now pins - including one test that rebuilds the
broken pairing and asserts it violates the invariant, so the guard has teeth.

Read the numbers as a ladder, not as a single reference value:

| basis | MP2 | CCSD | CCSD(T) frozen O 1s | CCSD(T) all-electron |
|---|---|---|---|---|
| 6-31g\* | -7.149 | -6.682 | **-6.856** | -6.887 |
| cc-pVDZ | -7.394 | -6.871 | -7.085 | -7.116 |
| aug-cc-pVDZ | -5.210 | -4.966 | -5.248 | -5.327 |
| cc-pVTZ | -6.111 | -5.646 | -5.932 | -6.140 |
| aug-cc-pVTZ | -5.161 | -4.942 | **-5.203** | -5.699 |

kcal/mol. ωB97X-V/6-31g\* level-2 at the same geometry and convention is -6.129
(`evidence/l2cp/20260928T213839Z_centos-step_h_l2cp.out:6`). So at fixed basis the
functional is 0.73 kcal/mol *shallower* than CCSD(T); against the near-limit correlated
value it is 0.93 *deeper*. The correlated ladder itself moves 1.9 kcal/mol across five
bases, which is larger than the quantity anyone would be judging - the reason §3.2
declines to render a verdict of the form "the functional overbinds".

Two things this directory does not claim. It is not a CBS extrapolation: no two-point
formula is applied, because with these rungs no error bound could be attached to it, and
the aug-cc-pVQZ rung that would matter was not run here. And the all-electron column is
not a second reference - it is the measurement of what the frozen-core choice is worth in
each basis, which at 6-31g\* is 0.031 kcal/mol and at cc-pVTZ is 0.21.
