# LaTeX build and `[S#]` provenance audit

Written by `tools/md2tex.js`. Regenerate with `node tools/md2tex.js`; do not edit here.

- source `paper/main.md`: 99896 chars, 1127 lines
- output `paper/main.tex`: title from the level-1 heading, 9 sections
- characters with no mapping: 0 (a nonzero count stops the script)
- YAML front matter excluded from the typeset text: none (this document has no front matter)
- tags cited in the body: 29
- figures pulled in: 4 -> tracked
- inline backticked paths in the body text: 22 scanned -> tracked
- appendix rows never cited in the body: none
- artefact checks that failed: 0
- bib entries cited: 24 of 24

| tag | artefact | check |
|---|---|---|
| S1 | `RESEARCH-20260929-lit.md` | tracked; also §1, §6 of the same file |
| S2 | `MAIN-skeleton.md`<br>`nlcsplit/logs/step_h.json` | tracked |
| S3 | `nlcsplit/step_f_dispersion.py` | tracked |
| S4 | `MAIN-skeleton.md` | tracked |
| S5 | `nlcsplit/step_e_kernel.py` | tracked |
| S6 | `evidence/centos/20260928T165857Z_centos-step_c.out` | tracked |
| S7 | `nlcsplit/step_d_floor.py`<br>`evidence/recompute/20260928T150222Z_step_d_floor.out`<br>`nlcsplit/tests/test_kernel.py` | tracked; also §3 of the same file |
| S8 | `nlcsplit/logs/step_h.json`<br>`nlcsplit/logs/step_h_l2cp.json`<br>`evidence/l2cp/20260929T051912Z_centos-l2_benzmeth_cp.out`<br>`evidence/l2cp/20260929T051849Z_l2_benzmeth-wsl.out`<br>`evidence/centos/20260928T165857Z_centos-step_f_h2o2.out`<br>`evidence/recompute/20260929T010500Z_step1_geomfix.out` | tracked |
| S9 | `nlcsplit/step_i_gridrepr.py`<br>`evidence/recompute/20260929T_step_i_gridrepr.out` | tracked |
| S10 | `evidence/l2cp/20260928T213839Z_centos-step_h_l2cp.out`<br>`evidence/l2cp/20260929T051912Z_centos-l2_benzmeth_cp.out`<br>`nlcsplit/logs/step_h_l2cp.json` | tracked |
| S11 | `RESEARCH-20260929-lit.md` | tracked; also §6.2 of the same file |
| S12 | `evidence/recompute/20260930T191014Z_stepg-official.out`<br>`evidence/recompute/20260929T003144Z_stepg-recompute.out`<br>`nlcsplit/step_g_basis.py`<br>`evidence/centos/20260928T165857Z_centos-step2.out` | tracked |
| S13 | `evidence/centos/20260928T165857Z_centos-step2.out` | tracked |
| S14 | `RESEARCH-20260929-lit.md` | tracked; also §10 of the same file |
| S15 | `evidence/retrieval_calibration/oa_stab.js`<br>`evidence/retrieval_calibration/openalex_stability.json`<br>`evidence/retrieval_calibration/xref_calib2.js`<br>`evidence/retrieval_calibration/xref_r3.js` | tracked |
| S16 | `RESEARCH-20260929-lit.md` | tracked; also §8.1 of the same file |
| S17 | `RESEARCH-20260929-lit.md` | tracked; also §13 of the same file |
| S18 | `nlcsplit/logs/orca_anchor.json`<br>`evidence/orca_run/h2o_dimer.out`<br>`evidence/orca_run/h2o_mono0.out`<br>`evidence/orca_run/h2o_mono1.out`<br>`evidence/orca_run/benz_dimer.out`<br>`evidence/orca_run/benz_mono0.out`<br>`evidence/orca_run/benz_mono1.out`<br>`evidence/orca_run/MANIFEST.sha256`<br>`evidence/orca_control/h2o_wb97x.out`<br>`evidence/orca_control/h2o_wb97xv.out`<br>`evidence/orca_control/MANIFEST.sha256`<br>`evidence/orca_widen/orca_widen.json`<br>`evidence/orca_widen/RECHECK_convergence.txt`<br>`evidence/orca_widen/generator_rescan_convergence.py`<br>`evidence/orca_widen/generator_merge_run.py`<br>`evidence/orca_widen/generator_cross_program_table.py`<br>`evidence/orca_widen/cross_program_table.txt`<br>`evidence/orca_widen/MANIFEST.sha256`<br>`nlcsplit/logs/orca_anchor.json`<br>`evidence/orca_widen/`<br>`evidence/orca_widen/MANIFEST.sha256` | tracked |
| S19 | `evidence/centos/20260928T165857Z_centos-step_c.out` | tracked |
| S20 | `nlcsplit/step_k_population.py`<br>`evidence/population/20260929T131530Z_stepk_pop-official.out`<br>`evidence/population/20260929T131055Z_stepk_pop-constructed.out` | tracked |
| S21 | `evidence/agentb_sweep/20260928T071951Z_agentb-sweep_631gstar.txt`<br>`evidence/agentb_sweep/20260929T151414Z_step_l_sweep_compare_levels0-9.out`<br>`evidence/agentb_sweep/20260929T151414Z_step_l_sweep_compare_levels0-9.json`<br>`nlcsplit/step_l_sweep_compare.py` | tracked |
| S22 | `evidence/attribution_referee/run.py`<br>`evidence/attribution_referee/referee_lib.py`<br>`evidence/attribution_referee/summarize.py`<br>`evidence/attribution_referee/probe_quadrature.py`<br>`evidence/attribution_referee/README.md`<br>`evidence/attribution_referee/outputs/results.json`<br>`evidence/attribution_referee/outputs/table.md`<br>`evidence/attribution_referee/outputs/summary.md`<br>`evidence/attribution_referee/outputs/validation.md`<br>`evidence/attribution_referee/outputs/convergence.md`<br>`evidence/attribution_referee/outputs/headline.md`<br>`evidence/attribution_referee/outputs/run_log.txt`<br>`evidence/attribution_referee/outputs/results_run1_20261001.json`<br>`evidence/attribution_referee/outputs/table_run1_20261001.md`<br>`evidence/attribution_referee/outputs/rerun_verify_20261001.log`<br>`evidence/attribution_referee/MANIFEST.sha256`<br>`evidence/attribution_referee/hetero.py`<br>`evidence/attribution_referee/outputs/hetero.json`<br>`evidence/attribution_referee/outputs/hetero_run_20261001.log` | tracked |
| S23 | `evidence/population/20260930T200927Z_stepk_soft-vs-hard-official.out`<br>`evidence/population/20260930T201142Z_stepk_soft-vs-hard-constructed.out`<br>`nlcsplit/step_k_population.py`<br>`evidence/population/MANIFEST.sha256` | tracked |
| S24 | `nlcsplit/step_m_ccsdt.py`<br>`evidence/ccsdt/20260930T224400Z_stepm_ladder_after_refactor.out`<br>`evidence/ccsdt/20260930T235900Z_stepm_three_systems_631g.out`<br>`evidence/ccsdt/20261001T000400Z_stepm_three_systems_avdz.out`<br>`evidence/ccsdt/20260930T212300Z_stepm_ladder.out`<br>`evidence/ccsdt/20261001T044833Z_orca_crosscheck.out`<br>`evidence/ccsdt/20261001T052943Z_orca_crosscheck_three_systems.out`<br>`evidence/ccsdt/orca_crosscheck.py`<br>`evidence/ccsdt/README.md`<br>`evidence/ccsdt/MANIFEST.sha256`<br>`nlcsplit/tests/test_cc_convention.py`<br>`nlcsplit/tests/test_cc_convention.py`<br>`evidence/ccsdt/orca_crosscheck.py`<br>`evidence/ccsdt/20261001T052943Z_orca_crosscheck_three_systems.out` | tracked |
| S25 | `nlcsplit/fastpair.py`<br>`nlcsplit/step_j_scaling.py`<br>`evidence/scaling/step_j.json`<br>`evidence/scaling/20260929T1340Z_step_j_scaling.out`<br>`evidence/scaling/step_j_rerun_20260930.json`<br>`evidence/scaling/step_j_rerun_20260930.txt`<br>`evidence/fastpair_ab/fastpair_ab_compare.json`<br>`evidence/fastpair_ab/fastpair_ide_validation.json`<br>`nlcsplit/tests/test_fastpair.py`<br>`evidence/scaling/MANIFEST.sha256` | tracked; also §3.6 of the same file |
| S26 | `evidence/ccsdt/20261002T043400Z_snnu_benzene_ladder.out`<br>`evidence/ccsdt/snnu_benzene_runner.sh`<br>`evidence/ccsdt/20261002T0528Z_snnu_benzene_dft_cp.out`<br>`evidence/ccsdt/snnu_dft_cp_levels.py`<br>`evidence/ccsdt/20261002T0620Z_snnu_benzene_methane_l2.out`<br>`evidence/ccsdt/snnu_dft_cp_methane_l2.py`<br>`evidence/ccsdt/MANIFEST.sha256`<br>`nlcsplit/step_m_ccsdt.py`<br>`nlcsplit/step_h_s22.py`<br>`nlcsplit/logs/step_h.json` | tracked; also §3.2 of the same file |
| S27 | `evidence/ccsdt/20261002T0715Z_snnu_benzene_avdz.out`<br>`evidence/ccsdt/snnu_benzene_avdz.sh`<br>`evidence/ccsdt/20261002T043400Z_snnu_benzene_ladder.out`<br>`evidence/ccsdt/MANIFEST.sha256` | tracked; also §3.2 of the same file |
| S28 | `evidence/ccsdt/20261002T0630Z_snnu_benzene_dimer_ccsdt.out`<br>`evidence/ccsdt/snnu_benzene_dimer.sh`<br>`evidence/ccsdt/20261002T0905Z_snnu_benzene_dimer_dft_cp.out`<br>`evidence/ccsdt/snnu_dft_cp_dimer.py`<br>`evidence/ccsdt/MANIFEST.sha256` | tracked |
| S29 | `evidence/ccsdt/20261002T1030Z_snnu_benzene_dimer_B.out`<br>`evidence/ccsdt/snnu_benzene_B.sh`<br>`evidence/ccsdt/snnu_dft_cp_dimer_B.py`<br>`evidence/ccsdt/MANIFEST.sha256`<br>`evidence/ccsdt/20261002T0630Z_snnu_benzene_dimer_ccsdt.out` | tracked; also §3.2 of the same file |
