# Methodology Review — seat 1 (adversarial, method only)

`E:\Project\GAMESS\paper\main.md` (1313 lines) against the repo root.

## (a) Method in five lines

1. E_NL evaluated as an explicit O(N²) double sum over retained grid points, keeping the (i,j) index rather than folding it into point values.
2. Each point gets one owner atom under four PySCF partitions (Becke, Becke+radius-adjust, Becke–Treutler, Stratmann) plus a nearest-atom control; sums group into E_AA, E_AB.
3. Blocks sum to the total by construction; the "attribution uncertainty" is the min–max spread of E_AB over those schemes.
4. ΔE_NLC compared to ΔE_xc and counterpoise energies; CCSD(T) and ORCA anchor externally.
5. Guards: a two-Gaussian partition-free referee; a measured screening study on cost.

## (b) Spot-checked numbers (paths under `evidence/`)

| # | § | Claim | Artefact, quoted line | Verdict |
|---|---|---|---|---|
|1|2.1|cross-pairing offsets +0.1379/0.4182/0.1346 (l1), +0.9057 (l0)|`recompute/20261001T083716Z_step_e_pairing_control.out:36,43,50,57` "与参照核差=+0.1379 … +0.9057"|Matches; tags `[S1, S5]` name no carrier (S1 = WoS record, S5 = the .py); this archive is never cited|
|2|2.2|13 rows/3 systems, 0.000e+00-5.551e-17 Ha, max = S22_11 becke-treutler|`recompute/20261005T0410Z_additivity_census.out:27-28` "残差最小 = 0.000e+00 … 最大 = 5.551e-17 Ha"|PASS|
|3|2.5|18336 vs 20248 = "the partitioned level-1 grid … official S22 geometry"; 19936 dismissed as constructed-geometry|census `:6-7` "official S22_02 … 公共网格 18336 点 … / becke N= 19936"; `recompute/20260930T191014Z_stepg-official.out:1` "几何: 官方 S22 几何 … 19936"|**FAIL**|
|4|3.4|methane span 0.8% relative|`centos/…step_h_l1.out:39` "甲烷二聚体 … 跨度 0.004 ( 0.9%)"|**FAIL**|
|5|3.5|populations 10.1559…10.0478 e; 0.108 e = 0.329 kcal/mol; β = 3.0415|`population/20260929T131530Z_stepk_pop-official.out:11` "ΔN_A = 1.081e-01 e ⇒ β·ΔN_A = 0.3288"|PASS|
|6|3.6|197.96 Ha vs -8.34e-4 Ha = 2.4e5; 0 pairs bound-below-value, empty drop list|`fastpair_ab/fastpair_ab_compare.json:75-79` "min_atomblock_root_bound_ha": 197.95986835848444 … "dropped_pairs": []|PASS; caveats: the `ide` variant's bound (`:876` "197.96 vs 221.32"), constructed water dimer; text says neither|
|7|4.2|eight ORCA rows; res/span 1.301; 4.1-111×|`orca_widen/cross_program_table.txt:12,17` "跨度/残差 的区间 = 4.1 到 111.1 倍"|PASS|
|8|4.3, §6|U = 1.060e-05; 5/12 vs U, 12/12 vs 1.819e-06; resolved 0.013-0.079 = 2.5-9.7% of cross term; §6 says 2.5-5.2%|`attribution_referee/outputs/summary.md:7,31-32`, `table.md:51` "-9.67"|§4.3 PASS; §6 **FAIL** (`hetero.json:52` control 6.4%)|
|9|3.2, S27|deviations -1.2737…-3.4115, BSSE 1.9770…0.2518 (`:91-98,115-122`); S27's "0.864 / 1.454 / 1.951 … enter the §3.2 comparison" vs `:107-109` 0.7383/0.9913/1.2016|`ccsdt/20261005T0414Z_cp_rebuild_compare_labels_fixed.out`|Table PASS; S27 **FAIL**, cites superseded -4.5172/-3.7273/-3.0093|

**Four FAILed outright** (#3, #4, #8-§6, #9-S27) and #1's tag resolves to no carrier. The abstract's 5.7e-06 checks out at `…step_h_l1.out:11`.

## (c) Findings by severity

**Critical 1 — the grid under every E_AB is misidentified (§2.5).** 18336 and 20248 are SCF/`Grids` counts (`partition.py:177-187`, printed by `step_f_dispersion.terms`); the decomposition runs on `atom_partition` — 19936 points at level 1, official geometry, 2.12.1. The ground given for rejecting 19936 is contradicted by two tracked archives, and `evidence/l2cp/20261003T0907Z_wsl2121-cp_levels.out:15-17` labels the pair the other way ("18336 … 分区后 … 20248 … 未分区").

**Critical 2 — the additivity check in the producing path cannot fail (§2.2).** `step_h_s22.py:60-61` asserts `abs(res["E_nl"] - sum(res["intra"].values()) - sum(res["inter"].values())) < 1e-10` while `nlc.py:138` defines `out["E_nl"]` as that expression; ditto `tests/test_regression.py:69`, `step_d_floor.py:212`. Only `additivity_census.py` compares blocks against an independently grouped monolithic sum — real, but sensitive to nothing beyond index-set coverage and the factor 2. Kernel, floor, owner and density errors are common-mode and cancel, so "we record the additivity residual rather than trusting it" is a self-comparison.

**Critical 3 — the level-dependence of the span is measured and omitted (§3.4, §6).** `centos/20260928T193520Z_centos-step_h_benz_l0.out:10,16` prints 苯二聚体(A) "方案跨度 0.072" and (B) "0.310" at level 0 against 0.032 and 0.219 at level 1: the uncertainty moves 2.2-fold with the grid and 0.310 sits outside the published 0.004–0.247 band, while §6 claims the dominant uncertainty is "the attribution scheme, not the numerics".

**Major 4 — §3.2 contradicts §2.5 on release.** §3.2: 2.12.1 "is the version every other DFT number in the paper — Table 1, the figures, the sidecar — was produced in". `nlcsplit/logs/step_h.json` tags seven of eight rows `2.14.0`.

**Major 5 — a convergence claim the body disowns.** §6: the span is confined "to within 0.001 kcal/mol between grid levels 1 and 2"; §3.2: "that number is a statement about storage precision, not a measurement". The Table 1 caption still reads "levels 1 and 2 agree to the last digit".

**Major 6 — statistical status of the headline quantity (§3.4).** Min–max over n = 4 deterministic schemes, no std, no centroid, denominator one of the members: Becke is argmax|P| in all eight systems with four published values, minimising every percentage. The four collapse to about two — Becke and Stratmann agree to ≤0.006 kcal/mol, the radii-adjusted pair sits 0.02–0.22 away. Sampled is one design decision (`radi.*_atomic_radii_adjust` on/off), not four conventions.

**Major 7 — the category-error objection is never staged (§4.1, §4.5).** §4.1's "is not" list covers EDA and dispersion only; "observable", "undefined", "arbitrary" appear nowhere. §4.3 holds the material for an answer, but its reference splits ρ as ρ_X + ρ_Y — also a partition — so it shows two conventions differ, not that either is true.

**Minor 8.** (a) §4.3 cites "the documented-wrong pairing of section 3.5"; it is §2.1. (b) §2.1 pairs 430,768 points with 428,920 kept; 430,768 is the other script's grid, ours is 430,760. (c) §4.3's MC "agrees … within its own standard error everywhere, worst |z| = 2.23"; 2.23 s.e. is not within one. (d) The abstract's "On a fixed density … 5.7e-06" quotes the complex's self-consistent row; the fixed-density level-1 figure is 6.4e-06. (e) No table gives grid point counts; mixed sig figs (−0.5935/−0.593) have no rule.

## (d) Questions for the authors

1. Which grid carries each published E_AB — `atom_partition` (19936) or `mf.grids` (18336)? Give level → (npts, rmax, angular order).
2. Report the scheme span at levels 0, 1, 2 per system, and how 0.004–0.247 moves.
3. Justify the min–max/Becke denominator, or give mean ± std.
4. Which quantities are guarded by a check capable of failing, on which geometry and release?
5. §4.3's I_AB differs from E_AB only by splitting ρ, not ownership: in what sense is that partition-free? Why is 19936 dismissed as the constructed geometry's count when two archives print it under 官方 S22 几何?
6. Which PySCF release is the record for Table 1, and which configurations give §6's "2.5-5.2% homonuclear"?

## (e) Reproducibility by an outsider

Not yet, though close: every checked value sits in a tracked, hash-manifested artefact, one script per table. Four blockers. Geometries are uncommitted — `geomlib.s22_system()` reads gitignored `scratch/lit/s22/`, so −0.601 rather than −0.524 needs a re-download. The environment is pinned only in prose (2.12.1 vs 2.14.0 moves the counterpoise energy 0.089 kcal/mol); `pyproject.toml` fixes no release. "Grid level" is nowhere specified numerically, so level 1 cannot be matched elsewhere. Provenance is lossy where it counts: three `step_h.json` rows hold 3-decimal spans, S27 cites superseded values, two archives label 18336/20248 oppositely, and a tag often resolves to a script, not the stdout that printed the number.
