# LaTeX build and `[S#]` provenance audit --- software

Written by `tools/md2tex.js`. Regenerate with `node tools/md2tex.js software`; do not edit here.

- source `paper/software.md`: 55993 chars, 650 lines
- output `paper/software.tex`: title from the level-1 heading, 8 sections
- characters with no mapping: 0 (a nonzero count stops the script)
- YAML front matter excluded from the typeset text: 32 lines (metadata; it is not body prose, so it is not in the PDF)
- tags cited in the body: 13
- figures pulled in: 0 -> tracked
- inline backticked paths in the body text: 56 scanned -> tracked
- appendix rows never cited in the body: none
- artefact checks that failed: 0
- bib entries cited: 7 of 25; **not cited anywhere in the body: altun2018dlpno, becke1988, calbo2015vv10review, dion2004, goerigk2017gmtkn55, hamada2011c60au, hesselmann2013nldft, hujo2011hbond, hyldgaard2014interp, jurecka2006s22, kruse2019dna, lehtola2018libxc, sinha2015fdevdw, stratmann1996, takatani2010s22, treutler1995, vydrov2009vv10, vydrov2010simple**

| tag | artefact | check |
|---|---|---|
| S1 | `RESEARCH-20260929-lit.md` | tracked; also §1, §6, §9 of the same file |
| S2 | `evidence/recompute/20260929T010500Z_step1_geomfix.out`<br>`evidence/recompute/MANIFEST.sha256`<br>`nlcsplit/logs/step_h.json`<br>`nlcsplit/logs/step_h_l2cp.json`<br>`MAIN-skeleton.md` | tracked |
| S3 | `nlcsplit/step_f_dispersion.py` | tracked |
| S5 | `nlcsplit/step_e_kernel.py`<br>`evidence/recompute/20261001T083716Z_step_e_pairing_control.out`<br>`evidence/recompute/MANIFEST.sha256` | tracked; also §2. of the same file |
| S7 | `nlcsplit/step_d_floor.py`<br>`evidence/recompute/20260928T150222Z_step_d_floor.out` | tracked |
| S9 | `nlcsplit/step_i_gridrepr.py`<br>`evidence/recompute/20260929T_step_i_gridrepr.out` | tracked; also §1, §2 of the same file |
| S10 | `evidence/l2cp/20260928T213839Z_centos-step_h_l2cp.out`<br>`evidence/l2cp/20260929T051912Z_centos-l2_benzmeth_cp.out` | tracked |
| S12 | `evidence/recompute/20260929T003144Z_stepg-recompute.out` | tracked |
| S17 | `nlcsplit/tests/test_partition_factors.py` | tracked |
| S18 | `evidence/orca_run/`<br>`evidence/orca_control/`<br>`evidence/orca_widen/`<br>`evidence/orca_widen/cross_program_table.txt`<br>`evidence/orca_run/MANIFEST.sha256`<br>`evidence/orca_control/MANIFEST.sha256`<br>`evidence/orca_widen/MANIFEST.sha256` | tracked |
| S19 | `evidence/release_qa/` | tracked |
| S20 | `evidence/bound_forms/`<br>`evidence/fastpair_ab/`<br>`evidence/scaling/`<br>`evidence/coretail/`<br>`paper/p2.md` | tracked; also §6 of the same file |
| S21 | `evidence/attribution_referee/run.py`<br>`evidence/attribution_referee/referee_lib.py`<br>`evidence/attribution_referee/summarize.py`<br>`evidence/attribution_referee/README.md`<br>`evidence/attribution_referee/outputs/summary.md`<br>`evidence/attribution_referee/outputs/results.json`<br>`evidence/attribution_referee/outputs/results_run1_20261001.json`<br>`evidence/attribution_referee/outputs/table_run1_20261001.md`<br>`evidence/attribution_referee/MANIFEST.sha256`<br>`evidence/attribution_referee/run.py`<br>`evidence/attribution_referee/summarize.py` | tracked |
