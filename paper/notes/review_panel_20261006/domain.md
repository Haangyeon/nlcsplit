# Domain Review (Peer Reviewer 2) — DFT / noncovalent interactions
`paper/main.md`, 2026-10-06.

## (a) Contribution, four lines

1. Keeps the (i,j) index of the VV10 double sum on a real-space grid, grouped into fragment blocks at fixed ωB97X-V density.
2. Reports the spread of E_AB over four Becke-family partitions of eight S22 dimers as a per-system "attribution uncertainty" (0.004–0.247 kcal/mol).
3. Argues ΔE_NLC is not "the dispersion": 16%→97% of ΔE_xc, more than all of it for methane dimer.
4. Adds a partition-free two-Gaussian referee and a negative screening result.

## (b) Prior art

**Fair.** Heßelmann, JCTC 9, 273 (2013): his abstract does say "partitioning of the correlation-energy density into atom-atom contributions", and §1 reports this accurately — omitting only that the scheme is Heßelmann's own, not VV10. JuNoLo is treated honestly, anti-fragment stance included.

**Understated.** Dasgupta, Palos, Pan, Paesani, JCTC 20, 49–67 (2024) already holds that dispersion models "rely on error compensation among the different components of the interaction energy" — this paper's second claim, in one sentence.

**Missing (CONFIRMED — record seen this session).**
- Horn, Mao, Head-Gordon, JCP 144 (2016) [10.1063/1.4942921]: electrostatics, Pauli repulsion and dispersion defined inside DFT. Refutes §4.1's premise.
- IQA/QTAIM atom-pair resolution of a KS-DFT XC energy: Molecules 25, 4028 (2020); JCTC 19 (2023) [10.1021/acs.jctc.3c00143]; Tognetti & Joubert (2024). Threatens "no precedent".
- Partition-DFT: PRA 82 (2010); JCTC 5, 827 (2009) (Elliott, Burke, Cohen, Wasserman) — §3.5's soft-vs-hard. Hirshfeld-I promolecule stockholder, unused: Comput. Theor. Chem. 975, 2 (2011).
- vdW-DF sub-quadratic routes: PRL 103, 096102 (2009); PRB 79 (2009); JCP 136 (2012). These also destroy the pair index — the cost argument §3.6 should make.
- NLC-term contributions in solids and layers: PRB 83, 195131 (2011); PRM 3 (2019). None fragment-resolved: the claim survives, the survey looks thin.
- Atom/fragment-resolved dispersion: PRB 111, 054103 (2025).
- Treutler & Ahlrichs, JCP 102, 346 (1995): §2.3's "Becke–Treutler" names a non-existent paper, cites nothing.

**SUSPECTED (leads, not citations):** rVV10 original (§4.5, uncited); pair-potential reformulations of vdW-DF; an official S22 hydrogen-bonded/dispersion/mixed categorisation (§3.4 sorts by "interaction type").

## (c) Findings

**Critical 1 — the four "partitions" move the total, not only its split (§3.4).** "the sum of the blocks reproduces the total to machine precision" (Abstract). Their additivity census gives level-0 E_NL of −56.6202/−56.6574/−56.7887/−56.8369 kcal/mol for one benzene sandwich geometry: 0.22 kcal/mol of spread in a supposedly partition-independent quantity, at identical point counts. Radii adjustment moves the coordinates, so the span mixes ownership with quadrature, and that mixing is unmeasured at level 1.

**Critical 2 — "cancels identically" is a continuum identity (§3.5, §6).** "the term's local part is beta times the electron number and cancels identically in any superposition difference" (Abstract). β = 3.0415 kcal/mol per electron amplifies the grid's error in ∫ρ by that factor, and the same census reads ∫ρ = 84.057/84 and 84.061/84 at level 0 — ~0.2 kcal/mol uncancelled, more than four of eight spans. §3.5 argues this for populations, never for the grid; §3.3 reads level-0 ratios 1.017/1.025/0.915 as relaxation physics.

**Critical 3 — wrong denominator, near-tautological headline (§3.2, §4.1).** ΔE_xc^rest is semilocal exchange, semilocal correlation and the HF fraction: charge-overlap and repulsion, not a dispersion pool; ΔE_xc excludes classical electrostatics (their ΔE_int − ΔE_xc = −4.1 kcal/mol for water). 16% for a hydrogen bond and 97% for a stacked aromatic is what EDA has long said. The methane row (−0.517 vs −0.232, remainder +0.285) is what a frozen superposition difference must give where electrostatics are weak: **genuine, not a bug, not an ωB97X-V pathology** (ORCA: −0.5160) — but unsurprising, and sold as a discovery.

**Critical 4 — band contaminated below, understated above (§3.4 vs §4.3/§6).** Abstract: "0.8-18.2%"; §6: "the owner/Becke cross term sits 6.2-35.9% of the exact cross term there" — their own referee doubles the advertised maximum. Methane's 0.141 kcal/mol "excess" is certified against the 4.5e-5 reproducibility of the *uncorrected* energy, yet 0.089 cross-release and 0.219 grid moves of that same cell are conceded.

**Major 5 — E_AB conflates frozen cross term and response (§3.3).** Numerator on the SCF density, denominator frozen, so a ratio near 1 cannot separate them. w0 and κ are functionals of the *total* density, so a retained point's kernel parameters already carry the partner: E_AB is no pairwise-additive A–B term, which is why §3.6's certificate could not bind.

**Major 6 — "four published real-space partitions" is one family (§2.3).** Two switches inside `gen_grid.get_partition`, plus an excluded control; no Voronoi, zero-flux basins or promolecule stockholder. Within-family parameter sensitivity.

**Major 7 — cost overstated (§3.6).** Against "the index is not free", `evidence/scaling/step_j.json` gives exact pair sums of 4.5 s (level 1, water) and 9.6 s (9 atoms) against SCF of 50 s and 119 s: under 10% of wall time.

**Major 8 — basis choice undercuts the error bar (§3.4).** Table 1 uses 6-31G*, no diffuse functions, for an integrand living in the density tail, while §3.4 measures ~0.18 kcal/mol of basis drift: four times the span called "the error bar this method has to carry".

**Minor — terminology.** "Correlation" in the functional label is not electron correlation in the SAPT/MP2 sense, and ΔE_xc^rest is where electrostatics and repulsion actually sit; §1/§3.2/§3.3 use "dispersion" loosely. "BSSE" is right for ΔE_int, then declared irrelevant to ΔE_NLC (§4.1) untested. `dasgupta2023` dated 2023 against a 2024 issue; rVV10 named, uncited.

## (d) Requirements before acceptance

1. Four ownership assignments on one common grid, levels 1–2, plus the scheme-spread of the *total* E_NL. Hours coding, 2–3 core-days.
2. Tabulate discrete Δ(β∫ρ) per system and level; drop or recompute §3.3's level-0 ratios. Hours.
3. Split ΔE_xc^rest into semilocal E_x, semilocal E_c, HF E_x; compare ΔE_NLC to counterpoise MP2 interfragment correlation. 1 day coding, hours per dimer.
4. Add two non-stockholder partitions (Voronoi/zero-flux; Hirshfeld-I) or rename the quantity "within-family parameter sensitivity"; reconcile 18.2% with §6's 35.9%. 2–4 days.
5. Extend to S66's hydrogen-bonded and stacking subsets, or two nucleobase pairs: 10²–10³ core-hours on their own timings. Cost is no objection.
6. Re-run Table 1 in aug-cc-pVDZ. 1–2 days.
7. Related-work rewrite engaging IQA, partition-DFT, Hirshfeld-I, KS-DFT dispersion definitions, vdW-DF linear scaling. Writing, 2–3 days.

## (e) Recommendation

Major revision; nearer reject-and-resubmit if 1–4 are refused. Confidence 4/5. §4.2's ORCA anchor and §4.3's partition-free referee are the best-verified parts and the asset to promote. The narrow novelty claim probably stands; the framing does not: one functional, one basis, one grid level, one partition family, and an error bar its own authors' referee exceeds.

*Blindness: read `main.md`, `references.bib`, greps of `p2.md`/`software.md`, `nlcsplit/*.py`, `evidence/**`. No PROGRESS-*, nothing under `paper/notes/` (listing only), no audit/rebuttal/review-named file.*
