# Devil's Advocate Review — "Fragment-Resolved Nonlocal Correlation: Pair Attribution of the VV10 Term"

## Calibration Status
`NOT_CALIBRATED`

## The One Claim to Pull Out
§4.1: `text: §4.1 "it is evaluated at fixed (non-self-consistent) superposed density, so basis-set flexisation does not enter"` — twin at §3.3, `text: §3.3 "the superposition difference d_sup computed from the unrelaxed monomer densities"`. The producer path is `step_f_dispersion.terms()` → `partition.scf_grid()` → `mf.kernel()`, run separately on the complex and on each monomer built by `step_h_s22.geomlib_sub()` from that fragment's own atoms in `BASIS` with **no ghost functions**. Table 1's headline column is therefore a relaxed, ghost-free superposition difference — the identical defect the paper finds, quantifies and repairs in its own coupled-cluster ladder (§3.2). Pull it and the shares, the 0.92–1.08 band, §4.1's CP exemption and the grid-convergence argument all go.

## Strongest Counter-Argument
The paper sells two things that cancel. It sells an error bar — the attribution span, "the error bar this method has to carry" (§3.4), "the dominant uncertainty" (§6). It then sells its chemistry: the inter-fragment block is 0.92–1.08 of ΔE_NLC (§3.3). Propagating the paper's own spans into `p_over_ds` (`step_h_l2cp.json`) gives water 1.01±0.07, ammonia 0.96±0.04, methane 0.92±0.006, benzene···water 1.08±0.20, benzene···ammonia 1.05±0.17, benzene···methane 1.03±0.15. Five of six are indistinguishable from 1.00; the "ratio can exceed unity, so relaxation is a signed correction" reading is 0.4σ. A ratio of 1 means the N² pair sum returns, on five of six systems, what the folded kernel gives free to ~1e-8 Ha (§4.5). The only resolved departure, methane, sits on the one complex the paper's own CCSD(T) anchor calls unbound (+0.0734). The band is also not a spread of rival partitions: `partition.py:SCHEMES` is one Becke mutual-share formula plus three radius tables and `stratmann`; in every fully resolved row the endpoints are plain Becke versus one radius-adjusted variant, Stratmann 0.0012–0.0021 from Becke (4–5% of span). Hirshfeld/QTAIM/Voronoi/Mulliken appear only inside the paper's own search string. And the 16→97% share is predicted by arithmetic the paper declines: ΔE_xc^rest (−3.115 water, −0.119 parallel-displaced benzene) *is* the electrostatics/repulsion/induction carrier, so dispersion-dominated geometries must score high.

## Attack-Vector Verdict (STRONG vs WEAK/ANSWERED)
| Vector | Dim. | Judgement | Anchor | Why |
|---|---|---|---|---|
| Quantity is convention-dependent, so no "uncertainty" | 1,3 | STRONG | code: `nlcsplit/partition.py` L17-22 | one family, one knob; Becke used as reference in every table while §1 disclaims choosing one |
| ΔE_NLC construction mis-described | 1,4 | STRONG | code: `step_h_s22.py` L107-115, L138-143 | prose claims frozen/non-SCF/BSSE-immune |
| Own error bar voids §3.3 | 2,8 | STRONG | dataset: `step_h_l2cp.json` | dev/σ 0.14–0.41 in 5 of 6 |
| Share varies is definitional | 1,4 | STRONG | table: §3.2 rest column | rest carries electrostatics by their own definition |
| External dispersion check inverted | 2,6 | STRONG | table: `MAIN-skeleton.md` table 4 | 20% tolerance at §3.3, 1–8% resolution at §3.4 |
| "Attribution not numerics" | 7 | STRONG (narrow) | dataset: `20260930T191014Z_stepg-official.out` | basis range 0.0401 vs span 0.0423, one system |
| Trivially additive / honesty sentence | 2 | WEAK/ANSWERED | `text: §1 "grouping the summation indices is trivially additive"` | disclaimed at §1; §6's first sentence re-sells it |
| Generality beyond ωB97X-V | 5 | WEAK/ANSWERED | `text: §4.5 "regularised rVV10 form have not been tested"` | no such claim present; but see M6 |
| Circularity (PySCF referees PySCF) | 3 | WEAK/ANSWERED | §2.5, §4.2, §4.3 | named and closed for the value; only attribution lacks a real-density referee |
| 52–97% is a small-denominator accident | 4 | WEAK/ANSWERED | table: §3.2 | denominators −4.486/−4.555 are not residuals; methane guarded by the >2 rule |

## Issue List
#### CRITICAL
| # | Dim. | Issue | Evidence Anchor | Conf. | Field-Norm Boundary | Evidence-Crossing Rationale |
|---|---|---|---|---|---|---|
| C1 | 1,4 | Table 1's ΔE_NLC and §3.3's denominator come from monomer SCFs in the monomers' own basis, ghost-free; §4.1 states the opposite and uses it to exempt the quantity from CP. The paper measures this construction's error elsewhere at 0.285–1.663 kcal/mol — ≥ every non-aromatic \|ΔE_NLC\| | text: §4.1 "which is precisely why it converges a grid level earlier than dE_int does" | 5 | Boys–Bernardi CP is the convention for supramolecular ΔE at finite basis; applied to ΔE_int in §3.2 | the same construction exempted for the headline quantity, by assertion, unmeasured |
| C2 | 2,8 | §3.3's headline is unresolvable under the paper's own span: 5 of 6 ratios consistent with 1.00, so pair resolution buys nothing over the free folded kernel there | dataset: `nlcsplit/logs/step_h_l2cp.json` `p_over_ds`,`span` | 5 | a method claim must exceed the error bar its method defines | band width equals the claimed departure from unity |

#### MAJOR
| # | Dim. | Issue | Evidence Anchor | Conf. | Field-Norm Boundary | Evidence-Crossing Rationale |
|---|---|---|---|---|---|---|
| M1 | 3,5 | "Four published partitions" is one family with swapped radii; three of four within 5% of the first, endpoints always one knob. A lower bound sold as *the* uncertainty (§4.5, §6) | code: `nlcsplit/partition.py` SCHEMES | 5 | a convention uncertainty must span conventions in use — the paper's own §1 string lists Hirshfeld, Mulliken, atoms-in-molecules | sampled subfamily is a strict subset |
| M2 | 1,6 | "Not the dispersion" argued only from ΔE_NLC/ΔE_xc; no computed E_disp on these systems at matched basis/geometry | absence: §3.2–§4.1 checked for a dispersion reference — expected E_disp on ≥3 complexes at ωB97X-V/6-31G*; checked Tables 1–2 | 4 | mis-identifying a component needs a non-DFT component reference | only external number cited is used to support §3.3, its opposite |
| M3 | 2,6 | §3.3 calls −4.367 "the same kind of quantity" as published dispersion −3.34…−3.80; skeleton puts the gap at 18–21%, while the uncorrected ΔE_int (−3.580) — declared non-comparable — falls inside that range | table: `MAIN-skeleton.md` table 4 | 4 | comparability needs one stated tolerance | loose tolerance at §3.3, tight at §3.4 |
| M4 | 7 | "Attribution, not numerics" rests on one system/geometry/level: P_frz across four non-minimal bases ranges 0.0401 vs mean span 0.0423; the "near CBS" verdict uses a 0.05 criterion set above the span it protects | dataset: `evidence/recompute/20260930T191014Z_stepg-official.out` | 5 | basis convergence must be shown before ranking error sources | the two are equal to 5% |
| M5 | 5,8 | One functional, one kernel, rVV10/ωB97M-V untested, 8/22 S22, no charged or intramolecular case; §1 concedes atom-pair attribution of a nonlocal term to Heßelmann 2013 | text: §1 "attributing a nonlocal correlation term to atoms is not ours and is not claimed here" | 5 | — | leaves only the port plus the sensitivity accounting |
| M6 | 4 | §3.3's numerator (`atom_partition`) and denominator (`scf_grid`) sit on different grids; §3.1 measures that shift at −0.0282 kcal/mol (water, level 0) — a quarter of the interpreted departure from unity | code: `step_h_s22.py` pair_terms vs terms | 4 | ratio terms must share a discretisation | shift same order as the effect |

#### MINOR
| # | Dim. | Issue | Anchor | Conf. |
|---|---|---|---|---|
| m1 | 4 | §3.3 says the level-1 benzene ratio has "a different denominator"; the producer prints `P_frz[becke]/dnlc` for every row, same denominator as the six kept | code: `step_h_s22.py` P/Δsup print | 4 |
| m2 | 3 | Table 1 publishes uncorrected ΔE_int for all eight (water −7.816, BSSE 1.663) after §3.2 establishes it is not a publishable value | table: §3.2 col. 3 | 4 |
| m3 | 8 | ~40% of Results benchmarks ωB97X-V binding on a CCSD(T) ladder the section itself calls "unsupportable"; it referees neither ΔE_NLC nor attribution | text: §3.2 "remains unsupportable" | 4 |

## Salvage Statement
On ωB97X-V/6-31G* at official S22 geometries the VV10 double sum resolves into named inter-fragment pair blocks whose value depends on the partition rule and on how the monomers were solved by amounts comparable to the block's own departure from ΔE_NLC — so any fragment-resolved nonlocal energy must state partition, basis and monomer construction, and cannot be made cheaper by distance-only screening (33/33 timed pairs slower; tightest certificate loose by 2.4e5).

## Bottom Line
Not publishable at **JCTC** as written: the interpretive claims (ii)–(iv) rest on a quantity the manuscript mis-describes (C1), and its marquee result is voided by its own error bar (C2); the venue will read the 8-system/1-functional scope (M5) as a validation note, not a method. At **JCC** it is major-revise today. §3.6's measured negative screening result and §4.3's falsification design are already JCC-publishable on their own. For me to be wrong: (1) recompute all eight ΔE_NLC with ghost functions and show the shift <0.01 kcal/mol; (2) propagate the span into `p_over_ds` and keep §3.3 — or delete it; (3) add two non-Becke families and show 0.8–18.2% survives; (4) compute one SAPT(DFT)/ALMO E_disp on these geometries and show the share is not the trivial consequence of the rest carrying the electrostatics.

## Ignored Alternative Explanations
1. The 16→97% share follows definitionally from electrostatics sitting in ΔE_xc^rest — not a discovery.
2. The band is an artefact of which points one code generates, not of ownership; §4.3 is exact only because two separated Gaussians make ownership unambiguous — the regime real dimers abandon.

## Missing Stakeholder Perspectives
- EDA/SAPT practitioners who would read per-pair numbers as interpretable.
- PySCF/ORCA implementers asked to maintain pair-resolved output.

## Unexamined Premise
That a grid point's ownership is a meaningful carrier of "belongs to a fragment". §3.5's β·N_A identity (0.329 kcal/mol, larger than every headline span) prices it on the one use case that needs the decomposition — absolute fragment energies.

## Observations
- The candour is real and self-defeating: most of §3.2 dismantles claims the paper no longer makes, which reads as a prior on the survivors.
- §2.5/§4.2/§4.3 self-refereeing is unusually thorough and should survive any transfer.
