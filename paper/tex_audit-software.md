# LaTeX build and `[S#]` provenance audit --- software

Written by `tools/md2tex.js`. Regenerate with `node tools/md2tex.js software`; do not edit here.

- source `paper/software.md`: 32370 chars, 376 lines
- output `paper/software.tex`: title from the level-1 heading, 8 sections
- characters with no mapping: 0 (a nonzero count stops the script)
- YAML front matter excluded from the typeset text: 32 lines (metadata; it is not body prose, so it is not in the PDF)
- tags cited in the body: 13
- figures pulled in: 1 -> tracked
- tables emitted: 2; with a numbered caption: 2 -> all numbered
- inline backticked paths in the body text: 20 scanned -> tracked
- appendix rows never cited in the body: none
- artefact checks that failed: 0
- bib entries cited: 20 of 92; **not cited anywhere in the body: adamo1999pbe0, altun2018dlpno, ambrosetti2014, andres2019ninequestions, becke1993b3lyp, becke2005disp, bultinck2007, burns2017bfdb, calbo2015vv10review, caldeweyher2017d3, caldeweyher2019d4, chai2008wb97x, chai2008wb97xd, chien2006sg0, cohen2012challenges, dion2004, dunning1989, francisco2006, gill1993, goerigk2011benchmark, goerigk2017gmtkn55, grimme2006jcc, grimme2010d3, grimme2011damping, grimme2011wires, halkier1998, hamada2011c60au, hesselmann2013nldft, hobza1999, hohenstein2010df, hujo2011hbond, hujo2011performance, hunter2007matplotlib, hyldgaard2014interp, jeziorski1994, kendall1992, klimes2012perspective, knizia2013, kruse2019dna, lebedev1976, lee1988lyp, lehtola2018libxc, lehtola2022illbehaved, mardirossian2017review, marshall2011, martinpendas2004, mentel2014cp, mitoraj2009, neese2012orca, neese2018orca, perdew1996pbe, rezac2011s66, rezac2016bench, riley2011, sinha2015fdevdw, smith2020psi4, steinmann2011ddsc, szalewicz2012, takatani2010s22, tao2003tpss, tkatchenko2009, tkatchenko2012mbd, vanduijneveldt1994cp, virtanen2020scipy, vydrov2009vv10, weigend2005def2, wheeler2014, wilkinson2016fair, xantheas1996, zhang1998revpbe, zhao2008m06, ziegler1977**

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
