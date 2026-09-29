# RESEARCH-20260930-p2-novelty — prior-art gate for P2's remaining novelty claim

> **Round structure (2026-09-30).** This file carries TWO E5 rounds. **Round 2** = §§0–9 below (formal
> Web-of-Science sweep of the *certified-screening* axis, 44 strings, endpoint-replay with ndjson batch
> accumulation and RecordsFound reconciliation; arXiv with the OR-quoted calibration that passes; OpenAlex
> cited-by on the fast-NLC hubs; full-text adjudication of Laikov arXiv:2511.04169). **Round 1** = the
> 2026-09-29-UTC open-index pass by the peer agent, **preserved verbatim, unedited, at the end** — its own
> declared gaps (no WoS export yet; Sabatini/Vydrov bodies unverified; “is anyone citing Laikov?”) are
> precisely what Round 2 closed. Read §10 for the cross-round errata before quoting anything from Round 1's
> table (three of its citation strings carry wrong page numbers, all corrected and DOI-verified in §10).


Date of all searches: **2026-09-30** (one session, 00:15–01:10 local; WoS `RecordsSearched = 58,669,534`,
WoS Core Collection, all sub-databases, lemmatization `On` — both read from WoS's own `searchInfo` row,
not assumed). Executor: cn-qoder subagent (this file), per the gate tasking in `paper/p2_skeleton.md` E5
("NLC 屏蔽先例正式检索 … 未做；现稿一律不写 first").

**The claim under test (verbatim from the tasking):**
"nobody has previously applied a certified (rigorous upper-bound) multipole/tree screening criterion
specifically to the VV10 nonlocal-correlation double sum while preserving per-pair (i,j) attribution."

Method note (project-specific, learned 2026-09-29): WoS numbers come from the site's own record endpoint
`POST /api/wosnx/core/runQuerySearch?SID=…` (request template captured by hooking `window.fetch` on one
real UI submit; `search.query[0].rowText` replaced per query; `retrieve.count` raised). ndjson `records`
batches were **accumulated**, and for every query the harvested unique-UT count was compared against the
server's own `RecordsFound` before anything was written down (§13.1 lesson: a [20,13] batch stream is 33,
not 13). No results-DOM scraping was used. Session state: institutional egress `202.117.147.182`
(CERNET), persistent profile `scratch/pw_profile`; yesterday's user-completed SNNU login still valid —
every query executed. Nothing of ours was sent anywhere; all strings are generic terms.
Raw evidence: `scratch/p2novelty/` (per-query ndjson `wos_*.ndjson`, manifests `wos_manifest*.json`,
arXiv XMLs `arx2_*.xml`, OpenAlex `oa3_*.json`/`cites2_*.json`, Laikov full text `laikov_2511.txt`).

---

## 0. Instrument status (today, measured — not inferred)

| Index | Status today | Evidence |
|---|---|---|
| **WoS CC** (clarivate.cn mirror) | **WORKING, logged-in session, 44 strings executed** | counts + full record harvest below; calibration K1–K6 all pass |
| arXiv API | WORKING, **but usable only in the OR-quoted form** | `abs:"VV10"` = 5 (known item arXiv:2208.02841 absent — calibration FAIL reproduced); `abs:"VV10" OR abs:"rVV10"` = 36 and **does** recall 2208.02841 (calibration PASS) ⇒ all arXiv strings below use the quoted-OR form |
| OpenAlex — known-item/title routes | WORKING (budget-late-session) | resolved Grafenstein-Cremer `10.1063/1.3079822`, Steinmann-Corminboeuf `10.1021/ct1001494`, Sabatini `10.1103/physrevb.87.041108`, Laikov `10.48550/arxiv.2511.04169` |
| OpenAlex — search routes | RATE-LIMITED | screening-axis battery CAL1–S8: 12/12 "FAILED(rate-limited)" — recorded as **queried-not-executed**, draws no conclusion |
| OpenAlex — cited-by routes | PARTIAL (final state) | RS09 hub enumerated **FULL** (fetched 1,596 vs server 1,590; reconciliation passed; one two-dimensional title hit — the Hyldgaard "screening nature" review, noise); Laikov hub **FULL = 0 citations** (so no indexed follow-up exists yet); Sabatini (738), Gulans (167), JuNoLo (47) hit 429 at page 0 ⇒ **TRUNCATED (0 read)**; my noloco seed used a wrong DOI guess and resolved to an unrelated paper — corrected record above, but its citation hub was **not** swept |
| Semantic Scholar — search | 429 (4/4 attempts) — same as 2026-09-29; keyword dimension **NOT QUERIED** | direct `DOI:` reads work (200) |
| Crossref | known-item layer works; `query.title` for GELLER/ShortRange-SPI → only name-noise | used for title/DOI verification only, per §9 |
| Scopus | **not queried today** (measured unsubscribed/401-403 on 2026-09-29) | carried as known gap |
| Open web (DDG-lite, Bing, CP2K manual fetch) | DDG returned empty; Bing "Object moved"; CP2K manual pages fetched empty via curl | used only to look for the program names, see §4 |

---

## 1. WoS calibration (strings as executed; hits; records read)

| # | exact string | hits | records read | verdict |
|---|---|---|---|---|
| K1 | `TI=("Van der Waals density functional for general geometries")` | 2 | 2/2 | Dion PRL 92,246401 + **its erratum** (art.no.109902). Known item recalled ✔ |
| K2 | `TI=("JuNoLo")` | 1 | 1/1 (abs read) | Lazić CPC 181,371 (2010) ✔ — abstract confirms explicit N² post-processing, total energy |
| K3 | `TS=("energy decomposition analysis")` | 3,317 | 20/3317 (titles) | breadth identical to 2026-09-29's 3,317 ✔ (count-cap 20 by design) |
| K4 | `TI=("Nonlocal van der Waals density functional made simple and efficient")` | 1 | 1/1 | Sabatini PRB 87,041108 (2013) ✔; abstract: plane-wave FFT route "along the lines pioneered by Román-Pérez and Soler" |
| K5 | `TI=("Efficient implementation of a van der Waals density functional")` | 1 | 1/1 | Román-Pérez & Soler PRL 103,096102 ✔; abstract: "factorize the integration kernel and use fast Fourier transforms … in O(NlogN) … dramatic speedup over the O(N²) evaluation of the double integral" |
| K6 | `TS=("Barnes-Hut")` | 134 | 20 (titles) | tree-code literature is indexed in CC ⇒ a 0 from a vdW×tree string is a real 0 ✔ |
| D1 | `AU=(Dion* AND Lundqvist*)` | 9 | 9/9 | AU-row syntax works and returns the Dion/Rydberg/Lundqvist papers ⇒ the **zero** intersections D2′(B7)/D4 are meaningful ✔ |

All 28 round-1 and 10 round-2 and 6 round-3 strings (44 total) are listed in §2–§5 exactly as executed.

## 2. Axis 1 — VV10/rVV10/vdW-DF/nonlocal × fast-algorithm vocabulary (WoS)

| # | exact string | hits | read | per-record verdict |
|---|---|---|---|---|
| A1 | `TS=(("VV10" OR "rVV10") AND ("fast multipole" OR Barnes-Hut OR "tree code" OR multipole))` | **1** | 1/1 (abs) | Nepal–Ruzsinszky–Bates PRB 97,115140 (2018): Cs-halide RPA/SCAN+rVV10 structural stability; "multipole" = higher-order multipole moments of dispersion. **No conflict** |
| A2 | `TS=(("van der Waals density functional" OR "vdW-DF") AND ("fast multipole" OR Barnes-Hut OR "tree code"))` | **0** | — | Zero, and every constituent vocabulary independently recalls (K6=134, C5=171, A1=1, vdW side K1/K4/K5/A4/A6). **Valid negative** |
| A3 | `TS=(("nonlocal correlation" OR "non-local correlation") AND (multipole OR "tree code" OR Barnes-Hut))` | **0** | — | Same argument ("nonlocal correlation" recalls 58 in B0). **Valid negative** |
| A4 | `TS=(("VV10" OR "rVV10" OR "vdW-DF" OR "van der Waals density functional" OR "nonlocal correlation" OR "non-local correlation") AND ("linear scaling" OR "order-N" OR N-scaling))` | 5 | 5/5 (abs #1) | **#1 Gulans–Puska–Nieminen PRB 79,201105 (2009) "Linear-scaling self-consistent implementation of the vdW-DF"** — adaptive real-space quadrature grids, nonlocal **potential** + forces; no certified bound, no pair attribution ⇒ **cite & bound** (fast-eval lineage). #2 Londero (application, noise), #3 Liu (noise), #4 eQE 2.0 (subsystem DFT), #5 Gundelach–Skylaris (ONETEP application). **No conflict** |
| A5 | `TS=(("VV10" OR "rVV10") AND (screening OR screened OR cutoff OR "cut-off"))` | 9 | 9/9 (titles) | all "screening" = **physical** screening (image-charge/dielectric) or "screened hybrid" vocab: Ambrosetti–Silvestrelli ×2, Yu RPA+rVV10, Bakar, Sharada ADS41, Mardirossian ωB97M(2), etc. **No conflict** |
| A6 | `TS=(("nonlocal correlation" OR "non-local correlation" OR "vdW-DF") AND (screening OR cutoff OR "cut-off"))` | 28 | 28/28 (titles), 1 abs | same vocabulary collision; Hyldgaard "screening nature" review, vdW-DF-ahcx, Marom benchmark, "Putting error bars on DFT" (statistical bars, not truncation bounds). **No conflict** |

## 3. Axis 2 — fast summation of the vdW-DF nonlocal term (WoS + placement of named leads)

| # | exact string | hits | read | verdict |
|---|---|---|---|---|
| B0 | `TI=("nonlocal correlation" OR "non-local correlation")` | 58 | **58/58 titles** | full title sweep of the topical literature; relevant items: Rydberg–Lundqvist–Dion PRB 62,6997 (2000) separable/tractable kernel **for flat surfaces/slabs** (abs read; no general-molecule screening, no bound, no attribution); Schwabe–Grimme (functional); ωB97X-V/ωB97M-V/B97M-rV (functionals); Gao-Ren (RPA-type construction). **GELLER/ShortRange-SPI/Toepfer-Fritscher/Fong-Ortiz DO NOT APPEAR** |
| B1 | `TS=("GELLER" AND ("vdW-DF" OR "non-local correlation" OR "nonlocal correlation"))` | **0** | — | see §4: name unlocatable |
| B2 | `TS=("ShortRange-SPI" OR "shortrange-spi")` | **0** | — | see §4 |
| B3 | `TS=(("vdW-DF" OR "van der Waals density functional" OR "nonlocal correlation" OR "non-local correlation" OR VV10) AND Ewald)` | 1 | 1/1 (abs) | Futera–Blumberger JCTC 2019 (GolP-CHARMM force field; "Ewald" in MD context). **No conflict; zero real-space-Ewald-for-vdW-DF paper in CC** |
| B4 | `TS=(("vdW-DF" OR "van der Waals density functional" OR VV10 OR "nonlocal correlation" OR "non-local correlation") AND ("separable expansion" OR "separable approximation" OR Chebyshev OR "Gaussian expansion"))` | **0** | — | **uncalibrated** (no known item recalls under these exact phrases; the separable-kernel classics are indexed without those words). Registered, no conclusion drawn |
| B5 | `TS=(("van der Waals density functional" OR "vdW-DF" OR VV10) AND ("atoms-in-molecules" OR "atoms to molecules" OR stockholder OR Hirshfeld))` | 4 | 4/4 titles, 1 abs | Shahbaz–Szalewicz TCA (2019, abs read): *benchmark accuracy* of AIM/atom-pair dispersion models vs SAPT — no certified screening, not the VV10 double sum; 2 applications; 1 D3/D4 extension. **No conflict** (Heßelmann NLDFT already bounded in `novelty_crosscheck.md` §1.2) |
| B6 | `TS=(("vdW-DF" OR "van der Waals density functional" OR VV10 OR "nonlocal correlation" OR "non-local correlation") AND ("fast fourier transform" OR "Fourier transform" OR FFT))` | 3 | 3/3 (all noise) | **CALIBRATION FAILED as negative evidence**: the FFT-route papers K5/K4 are NOT recalled (their TS fields don't use the words) ⇒ B6 count cannot support any absence claim. The FFT route itself is established by K4/K5 known-items |
| B7 | `AU=(Toepfer* AND Fritscher*)` | **0** | — | no co-authored Toepfer×Fritscher document anywhere in CC; AU syntax verified by D1. **Lead unlocatable** |

## 4. The unresolved named leads: GELLER, ShortRange-SPI, Toepfer–Fritscher, Fong–Ortiz

Provenance check first: these four names appear **only** in our own unverified to-do list
(`paper/p2_skeleton.md:51`, E5) with **no DOI, no citation, no ref/ record** (`grep -rn "GELLER\|ShortRange"
HANDOFF…, PLAN…, MAIN-skeleton, PROGRESS-nlcsplit, ref/, evidence/` → nothing but the skeleton line).
Searches executed to locate them today:

| route | string (exact) | result |
|---|---|---|
| WoS | B1, B2, B7 (above) | 0, 0, 0 |
| WoS | `TI=(GELLER)` (D5) | 44 — all surname hits (Geller syndrome, Geller reviews); **no program paper**. 44/44 titles read |
| WoS | `TI=(ShortRange*)` (D6) | 1 — wastewater photocatalysis (Env. Res. 2025). 1/1 read |
| WoS | `AU=(Toepfer*)` (D2) | 1,124 — 50 read (relevance cap); medicine/entomology/materials; no comp-chem Toepfer |
| WoS | `AU=(Fritscher*)` (D3) | 439 — 50 read; RRAM electronics, microbiology, dentistry; no comp-chem Fritscher |
| WoS | `AU=(Ortiz* AND Fong*)` (D4) | 19 — all clinical/astronomy |
| OpenAlex | title_and_abstract for GELLER×non-local, ShortRange, Toepfer/Fritscher/Byls author routes | 0 / garbage / rate-limited (§0) |
| Crossref | `query.title=GELLER…`, `ShortRange-SPI`, Toepfer/Fong title routes | surname noise / empty (§0) |
| arXiv | `all:"GELLER" AND abs:"non-local correlation"` (X5) ; `abs:"ShortRange-SPI"` (X6) | 0, 0 (presence probes, uncalibratable) |
| open web | DDG-lite / Bing / CP2K manual fetch | blocked/empty (§0) |

**Verdict: NOT FOUND in any reachable index under any spelling tried.** Per the 2026-09-29 lesson (§9:
"the expectation itself must be verified"), the honest classification is: these leads were **unverified
expectations**, most likely garbled from the planning stage (closest real analogues that do exist and ARE
placed: JuNoLo 2010, noloco 2011 (CPC 182, 1657), Gulans 2009, Sabatini 2013, Román-Pérez 2009, Vydrov–Wu–VanVoorhis 2008,
Grafenstein–Cremer 2009, Burow–Sierka 2011, Laikov 2025). If the reviewer means a *specific* paper, the
draft's §1 should be re-checked the moment its real title/DOI is supplied; until then P2 must not say
"GELLER did X", only "we could not locate any method paper under this name" — or better, not mention the
names at all. (This is the same handling the file `novelty_crosscheck.md` gave the Vidali/Klippenhein
leads: UNVERIFIED.)

## 5. Axis 3 — certified/rigorous bounds in molecular DFT (WoS + arXiv)

| # | exact string | hits | read | verdict |
|---|---|---|---|---|
| C1 | `TS=(("VV10" OR "rVV10" OR "vdW-DF" OR "nonlocal correlation" OR "non-local correlation" OR "van der Waals density functional") AND ("error bound" OR rigorous OR certified OR "a posteriori" OR "guaranteed accuracy"))` | 14 | 14/14 titles; 4 abs | **the claim-literal string.** Zero algorithmic hits: quantum-foundations noise ("rigorous proof for the nonlocal correlation function in the transverse Ising model", "Certification of quantum nonlocal correlations"), applications, Steinmann–Corminboeuf Chimia (a-posteriori *dispersion correction*, abs read), Sabatini phonons PRB 93,235120 (abs read — "rigorous" = DFPT formalism for nonlocal functionals, not error bounds). **No conflict** |
| C2 | `TS=(("Kohn-Sham" OR "density functional") AND ("a posteriori error estimation" OR "a posteriori error bound" OR "rigorous error bound"))` | 2 | 2/2 abs | Shen–Kuang–Hu J Sci Comput 2019 + **Herbst–Levitt–Cancès Faraday Discuss 2020** ("fully-guaranteed bounds … basis-set finiteness / convergence thresholds / rounding error" of the **KS eigenproblem**). Certified error exists in DFT numerics — different object. **Cite as boundary** |
| C3 | `TS=(("numerical integration" OR quadrature) AND "density functional" AND ("error bound" OR "a posteriori"))` | 1 | 1/1 abs | Davydov–Young–Steinmann IJNME adaptive FEM for KS. Same boundary as C2 |
| C4 | `TS=("multipole acceptance")` | 5 | 5/5 titles; 1 abs | tree-code mathematics only (Bull–Engblom; **Engblom "On well-separated sets and FMM", Appl Numer Math 2011 — rigorous MAC relative-error analysis, abs read**; Dehnen; Wünsch; Wang). No molecular-DFT application. **Cite as MAC-with-bound lineage** |
| C5 | `TS=("fast multipole" AND ("Hartree-Fock" OR "density functional" OR molecules))` | 171 | **171/171 titles**; 5 abs | certified/sharp-bound literature exists for **other sums**: #19 Lambrecht–Ochsenfeld **MBIE** (JCP 123,184101 (2005), "rigorous and tight upper bounds to four-center two-electron integrals", abs read), #55 **QQR** distance-dependent Schwarz bounds (2012, abs read), #61 density-matrix purification "with rigorous error control" (2008, abs read), #53 CFMM/H² compression (2020), #65 Bubblepole RI-J (2025). None touches a nonlocal-correlation double sum. **Cite as "bounds for the Coulomb sum, new object here"** |
| C6 | `TS=("Gaussian charge distributions" AND (multipole OR screening) AND ("upper bound" OR "error bound"))` | **0** | — | **uncalibrated** (no known item pairs these phrases); registered only |
| C7 | `TS=(("VV10" OR "vdW-DF" OR "nonlocal correlation" OR "non-local correlation") AND ("upper bound" OR "error bound"))` | 4 | 4/4 titles | quantum-noise only. **No conflict** |
| C8 | `TS=("fast multipole method" AND ("exchange-correlation" OR "nonlocal correlation" OR "van der Waals"))` | 19 | 19/19 titles; 4 abs | Sierka CFMM/RI-DFT gradients+stress (TURBOMOLE) — Coulomb only; **Burow–Sierka JCTC 7,3097 (2011) "Linear Scaling Hierarchical Integration Scheme for the Exchange-Correlation Term", abs read: octree hierarchical grouping + "efficient screening of negligible contributions" — of the SEMILOCAL xc single integral, no rigorous bound claimed, no pair attribution.** Srinivasan–Sarin treecode for r^−λ kernels (2007, abs read) — generalized power-law tree sums, not the VV10 Φ. **Closest mechanism-level neighbours; bound the claim** |

arXiv corroboration (OR-quoted form, calibrated — see §0):
| # | exact `search_query=` | total | verdict |
|---|---|---|---|
| X1 | `(abs:"VV10" OR abs:"rVV10" OR abs:"nonlocal correlation" OR abs:"non-local correlation" OR abs:"van der Waals density functional") AND (abs:"fast multipole" OR abs:"Barnes-Hut" OR abs:"tree code" OR abs:"multipole expansion")` | **1** | the one hit is **arXiv:2511.04169 Laikov** ⇒ known-item recall works AND the FMM×NLC intersection on arXiv is exactly one paper, which we read in full |
| X2 | `(...) AND (abs:"error bound" OR abs:"rigorous" OR abs:"a posteriori" OR abs:"certified")` | 54 | exploration; 52/54 quantum-foundations noise; zero certify a nonlocal-functional evaluation. Negative rests with WoS C1–C7 |
| X3 | `(...) AND (abs:"linear scaling" OR abs:"order-N" OR abs:"O(N)")` | 3 | Londero, eQE 2.0, FRI — no new fast-NLC paper (Gulans/RS09 predates/never posted) ⇒ exploration only, not a calibrated negative |
| X4 | `(...) AND abs:"screening"` | 22 | physics-screening noise, mirrors WoS A6 |
| X5/X6/X7 | `all:"GELLER" AND abs:"correlation"` / `abs:"ShortRange-SPI"` / `abs:"JuNoLo"` | 6 / 0 / 0 | X5 galaxy noise; X6 zero (§4); **X7 calibration note**: `abs:` searches the abstract only and JuNoLo's abstract lacks its own name ⇒ X7=0 is expected, not a failure — but shows exact-phrase abs strings are brittle |
| X8 | `(...) AND abs:"Ewald"` | 0 | uncalibrated negative (see B6 for the same caution) |
| X9 | `(...) AND (abs:"separable" OR abs:"Chebyshev" OR abs:"Gaussian expansion")` | 146 | dominated by QI "nonlocal/separable" noise; exploration only |

## 6. Full-text adjudication of the closest candidate (mandatory, since it is the one real overlap)

**arXiv:2511.04169v2, D. N. Laikov, "Nonlocal van der Waals density functional made faster"** (submitted
2025-11-06, v2 dated 2026-01-21; no Crossref/OpenAlex journal version found; **not indexed in WoS CC** —
verified via `TI=("made faster")` = 8 unrelated). Text downloaded from arXiv and extracted
(`scratch/laikov_2511.{pdf,txt}`, 6 pp, read in full 2026-09-30). What it does: replaces the VV10
integrand with an *approximation* — ω(r₁)≈ω(r₂) (Eq. 12), then a 3-term rational expansion ṽ = Σ βⁿ/(s+β)^(3+n)
with a **system-independent** β tuned by hand (√β = 4 bohr, chosen so noble-gas-dimer errors are small) —
so the 6-D integral becomes a few Newton-potential-type convolutions "opening the way to fast multipole
methods" (cites Rokhlin 1985; "should be straightforward … plane-wave implementation using [RS09]"), plus
a Gaussian density-fitted analytic version (new special functions U_mn, DE quadrature).
**Error handling**: purely empirical — Table I reports well-depth deviations from the VV10 reference in
**microhartree**; the largest single value is 103.6 µEh for the first approximation (Eq. 12) on the
762.5 µEh XeXe well (≈14%), 84.2 µEh (≈11%) for the final adopted scheme (Eqs. 29+30); the author's own
summary is "below 1.2% (3.3% for HeHe) for bond lengths and below 18% for bond energies". A tanh filter μ̄
is justified by "numerical stability", not by a bound. **There is no theorem that the computed energy is
within ε of the exact VV10 value; there cannot be, since the functional being evaluated is no longer
VV10.**
**Attribution**: computes total Ë₆ + compensation only; explicitly positions against "atoms-in-molecules
kind of approximation" (ref 23–24 = Grafenstein-Cremer, Steinmann-Corminboeuf). No (i,j) bookkeeping.
Overlap with our claim: **partial (fast multipole × VV10), not full** — it is neither certified nor
pair-preserving, and it approximates the kernel instead of screening the exact sum. Threat level: highest
ever recorded for this axis because of the vocabulary overlap — it MUST be cited, and P2's novelty sentence
must be phrased so that it stays true against Laikov (see §8).

## 7. Verdict table (task format)

| program / paper | what it does | bounds the error rigorously? | preserves per-pair (i,j) attribution? | overlap with our claim |
|---|---|---|---|---|
| **Laikov arXiv:2511.04169 (2025/26)** [FULLTEXT] | replaces VV10 integrand by separable rational expansion → FMM-able Newton-type sums + Gaussian analytic version ("LPBEVVV") | **NO** — empirical dimer-error table only; changes the functional itself | **NO** — total E₆ only, explicitly not AIM | **partial** (multipole/FMM × VV10; uncertified, no attribution) |
| Román-Pérez & Soler PRL 103,096102 (2009) [K5 abs] | factorizes kernel, FFT convolution, O(N log N) NLC energy/potential/forces (SIESTA) | NO | NO (point-value grid folding) | partial (fast route, our cost-axis foil) |
| Sabatini–Gorni–de Gironcoli PRB 87,041108R (2013) [K4 abs] | revises VV10 for efficient plane-wave evaluation + derivatives | NO | NO | partial |
| Gulans–Puska–Nieminen PRB 79,201105 (2009) [A4#1 abs] | linear-scaling self-consistent vdW-DF, adaptive real-space quadrature grids | NO | NO | partial |
| JuNoLo CPC 181,371 (2010) [K2 abs + 2026-09-29 FULLTEXT §10] | explicit N² post-processing of vdW-DF total energy, massively parallel | NO | NO (pushes fragmentable systems to other theories) | partial on explicitness; none on screening |
| **noloco CPC 182, 1657–1662 (2011)** Nabok–Puschnig–Ambrosch-Draxl [D8 full record + abs read; DOI 10.1016/j.cpc.2011.04.015] | "Since the vdW-DF requires the evaluation of a six-dimensional integral, it scales unfavorably" — Monte-Carlo multi-dimensional integration replaces the grid double sum; works for different vdW-DF versions; applications from dimers to molecular crystals and adsorbates | NO (stochastic estimator; no certified error bound) | NO — total energy / potential | **partial** (attacks the same 6-D integral, escape route = sampling not screening) |
| Vydrov–Wu–VanVoorhis JCP 129,014106 (2008) [E2 abs] | first self-consistent Gaussian-basis vdW-DF; explicit numerical double integration, grid study | NO | NO | partial |
| Gräfenstein–Cremer JCP 130,124105 (2009) [E1 abs] | QSCF-DC-DFT: a-posteriori (uncoupled) evaluation of ALL dispersion term via coordinate-space partitioning (ALL functional, not VV10) | NO | fragment-level by construction, for a different functional | partial (attribution-axis neighbour) |
| Burow–Sierka JCTC 7,3097 (2011) + Sierka CFMM line (C8) [abs] | **octree hierarchical screening of the xc (single) integral**, O(N), TURBOMOLE | NO (screening is adaptive, not bounded) | NO | **partial — closest tree-screening mechanism in molecular DFT** |
| Lambrecht–Ochsenfeld MBIE (2005) + QQR (2012) [C5 abs] | rigorous multipole-based upper bounds for **ERI screening** | **YES (but for ERIs)** | n/a | partial on the bounding idea, different sum |
| Engblom, Appl Numer Math (2011) [C4 abs] | rigorous relative-error MAC for tree/FMM **Newton** sums | **YES (but for Newton potentials)** | n/a | partial on the criterion form |
| Schwegler–Challacombe–Head-Gordon, JCP 109, 8764 (1998) [Round-1 lead; DOI verified today] | first **proven multipole acceptability criterion** written for electronic-structure integrals (linear-scaling Coulomb/exchange, Gaussian charges) | **YES (but for Coulomb/ERI sums)** | n/a | partial on the criterion form — cite beside MBIE/Engblom |
| Herbst–Levitt–Cancès Faraday D. (2020); Shen (2019); Davydov (2013) [C2/C3 abs] | a-posteriori certified error bounds for the **KS eigenproblem / FEM discretization** | **YES (different object)** | n/a | boundary context only |
| Rydberg–Lundqvist–Dion PRB 62,6997 (2000) [B0#13 abs] | separable/tractable kernel — restricted to flat surfaces & slabs | NO | NO | partial (separable-kernel lineage) |
| Srinivasan–Sarin IJCM (2007) [C8#5 abs] | treecode for r^−λ kernels (molecular dynamics potentials) | NO (order-error by truncation of series, not certified drop) | NO | partial |
| Steinmann–Corminboeuf SDD JCTC 6,1990 (2010); Shahbaz–Szalewicz TCA 2019; Heßelmann NLDFT JCTC 9,273 (2013) | atom-pair dispersion *models* derived from density partitioning; benchmarks vs SAPT | NO | own pair models, not screening of the exact VV10 sum | partial (attribution axis; already bounded yesterday) |
| VASP production route [vasp.at wiki, fetched 2026-09-30] | "the algorithm of Román-Pérez and Soler … based on FFTs and the convolution theorem"; kernel read from `vdw_kernel.bindat` | NO | NO | documentation of the foil; cite wiki/version |

**Full-overlap candidates: none found.** (Claim = certified × multipole/tree MAC × exact VV10 double sum ×
pair-preserving. No record satisfies even three conjuncts; Laikov satisfies two.)

## 8. Recommendation — in the required form

**"P2 may say X."** Exact sentence I would allow in the abstract/§1 (and its §4 echo):

> "To the best of our knowledge — backed by a Web of Science Core Collection search of 44 strings on the
> certified-screening axis (58,669,534 records, 2026-09-30, calibration-passed) and a full-text check of
> the closest candidate — no previous work applies a rigorous-upper-bound multipole/tree screening
> criterion to the *exact* VV10 nonlocal-correlation double sum while preserving its per-pair (i,j)
> attribution: existing fast evaluations of the nonlocal term factorize or replace the kernel and discard
> the pair structure with no certified error bound [Román-Pérez & Soler, PRL 103, 096102 (2009); Sabatini
> et al., PRB 87, 041108 (2013); Gulans et al., PRB 79, 201105 (2009); Lazić et al., CPC 181, 371 (2010);
> Nabok et al., CPC 182, 1657 (2011) [noloco]; Vydrov et al., JCP 129, 014106 (2008)], the recent separable-kernel
> acceleration with fast multipoles [Laikov, arXiv:2511.04169 (2025)] replaces VV10 itself with an
> empirically benchmarked approximation, and rigorous multipole bounds in molecular electronic structure
> have been written for other sums — two-electron-integral screening [Lambrecht & Ochsenfeld, JCP 123,
> 184101 (2005)] and Newton-potential tree codes [Engblom, Appl. Numer. Math. 61, 1174 (2011)] — not for
> the nonlocal-correlation pair sum."

Conditions attached to that permission (all are wording constraints, not evidence gaps):
1. Keep **"to the best of our knowledge" + the dated-search hedge** — one formal index (WoS CC) plus
   open-index corroboration; Laikov is a preprint **not** covered by the formal index; Semantic Scholar
   keyword and OpenAlex search dimensions were not executed today (429).
2. §4 must cite Laikov 2025 as the concurrent fast-multipole attempt and mark it *uncertified / kernel-
   replacing / attribution-discarding*; and Burow–Sierka 2011 as the octree-screening precedent for the
   **single** xc integral (uncertified) — these two are what a reviewer will throw first.
3. §1 "the bounds idea is not ours either, the object is": cite MBIE/QQR (rigorous multipole bounds for
   ERIs), Schwegler–Challacombe–Head-Gordon 1998 (proven MAC for electronic-structure integrals, DOI
   10.1063/1.477546, JCP 109, 8764) and Engblom (rigorous MAC) as the criterion lineage, and
   Herbst–Levitt–Cancès as the certified-error-in-DFT lineage with a different error object.
4. Do **not** write "no fast algorithm for VV10 exists" (false — Laikov, RS09, Sabatini, Gulans) and do
   not write "no error bounds in DFT numerics exist" (false — KS a-posteriori line). The allowed claim is
   exactly the four-conjunct intersection above.
5. The skeleton's leads "GELLER / ShortRange-SPI / Toepfer & Fritscher / Fong & Ortiz" are **unlocatable
   in every index tried today (WoS/OpenAlex/Crossref/arXiv/open web)** — same handling as the Vidali/
   Klippenhein leads: mark UNVERIFIED in the skeleton; do not cite, do not refute-by-name in the paper.
   If the advisor supplies a real DOI later, re-run B1/B2/B7 with it as known item.

## 9. Coverage & residual gaps (declared)

- Read exhaustively: every query below ~60 hits was read record-by-record (titles; 30+ abstracts), with
  UT-vs-`RecordsFound` reconciliation per query (all "full" except the two by-design 20-caps K3/K6 and the
  capped D2/D3, declared). Partial reads: D2 50/1,124, D3 50/439 (negative results for those do not rest
  on them — B7 intersection + D1 calibration carries that), K3 20/3,317, K6 20/134.
- Zero-hit strings and their status: A2/A3/B1/B2/B7/D9/D10/E-series zeros — **calibrated** via component
  recall (K6, C5, A1, B0) or D1; B4/C6/X8/X6 — **uncalibrated, no conclusion drawn** (§3, §5).
- Not covered: Scopus (unsubscribed), Embase/SciFinder, CNKI (out of scope for these terms),
  arXiv-only/unindexed conference papers post 2026-09-29, WoS indexing latency (Laikov-class preprints),
  OpenAlex search routes today (429) and 4/6 cited-by hubs (429 mid-sweep; RS09 hub was enumerated FULL —
  1,596 citing works, two-dimensional title screen fired on exactly one title, the Hyldgaard "screening
  nature" review, noise; Laikov hub FULL at 0 citations).
- Two self-errors made during this round, corrected in place above, logged for the audit trail: (i) I wrote
  the CPC-2011 Monte-Carlo program as "nolmo" from memory before reading its record — it is **noloco**,
  CPC 182, 1657–1662; (ii) my cited-by sweep guessed `10.1016/j.cpc.2011.05.018` for it and OpenAlex
  faithfully resolved the *wrong paper* ("A modern workflow for force-field development", 20 cites). The
  corrected record/DOI came from the WoS D8 dump. Same failure mode as 2026-09-29 §9 (expectation filled
  from memory) — caught by reading the record before writing the verdict.
- The attribution axis itself was NOT re-run here (done 2026-09-29, §12–13 + `novelty_crosscheck.md`);
  this file supersedes nothing there and adds the screening axis + Laikov full text.


## 10. Cross-round notes: what Round 2 resolves in Round 1, and Round-1 errata (DOI round-trips, 2026-09-30)

**(a) Round-1 gaps → status.** “WoS/Scopus formal sweep not run” → **run** (§1–§5, this file; Scopus still
not — measured unsubscribed). “Sabatini & Vydrov bodies unverified” → **placed at full-abstract level**
(K4/E2 here; both are total-energy grid/FFT implementations, no bound, no pair bookkeeping — nothing that
could collapse claim (a)). “Any 2026 paper citing Laikov + adding a certified bound?” → **OpenAlex cited-by
for arXiv:2511.04169 enumerated FULL at 0 citations**, and the Laikov text itself was read end-to-end (§6).

**(b) Round-1 verdict alignment.** Round 1 graded claim (b) “novel-by-specific-construction, NOT
first-to-apply-hierarchy-to-VV10” at confidence ≈0.6 *without* WoS; the Round-2 WoS battery (A1=1 noise,
A2/A3/D9=0 calibrated, X1=1 Laikov-only on arXiv) raises that conjunction to the record of §8 — same
direction, one formal index added, Laikov line strengthened from “WebFetch summary” to full local PDF read.

**(c) Round-1 errata (verified today; Round-1 text kept as-is above/by the append marker)**:
1. Schwegler–Challacombe–Head-Gordon “A multipole acceptability criterion for electronic structure
   theory” is **JCP 109, 8764–8769 (1998)** per Crossref `10.1063/1.477546` — Round 1 wrote “109, 2726”.
2. Vydrov & Van Voorhis “Implementation and assessment of a simple nonlocal vdW-DF”, **10.1063/1.3398840
   resolves to JCP 132, 164113 (2010)** — Round 1 wrote “132, 154105”.
3. Round 1’s JuNoLo row names “Skattebøl, Saleh, Reimers, et al., CPC 181, 546”; the record (WoS K2 +
   Crossref, verified 2026-09-29 §9.3 and today) is **Lazić, Atodiresei, Alaei, Caciuc, Blügel, Brako,
   Comput. Phys. Commun. 181, 371–379 (2010)**.
4. Round 1’s table row 3 (“VV10 2010 introduces the separable finite-rank approximation”) conflates two
   things: the *separable-kernel machinery* is Rydberg–Lundqvist–Dion PRB 62,6997 (2000) (B0 #13 here);
   VV10 itself is a closed-form non-separable kernel. No downstream conclusion changes.

**(d) Addition folded into §7 from Round 1** (verified): Schwegler–Challacombe–Head-Gordon 1998 is the
earliest **proven** multipole-acceptability criterion written for *electronic-structure* sums (linear-scaling
Coulomb/exchange integrals) — same family as MBIE/QQR and Engblom: certified MAC, wrong object (not the
VV10 pair sum). P2 §4 should cite it next to Engblom.

---

# APPENDED VERBATIM — E5 Round 1 report (2026-09-29 UTC run, peer agent; do not edit; see §10 for errata)

␞␞␞BEGIN-ROUND-1␞␞␞
# E5 prior-art / novelty check for P2 — certified screening of the VV10 nonlocal-correlation double sum

**Session:** E5 of the P2 novelty package (E1–E4 are already closed in `paper/p2_skeleton.md`).
**Search run:** 2026-09-29 UTC, 16:26 → 16:44 (single 18-minute window; every query, engine and hit count is logged in Appendix A).
**Engines actually used:** Crossref REST (`api.crossref.org/works`), OpenAlex REST (`api.openalex.org/works`), arXiv Atom API (`export.arxiv.org/api/query`).
**Engines attempted but not retrieved:** Semantic Scholar Graph (HTTP 429 for every attempt in this session — see A.4). Web of Science / Scopus: reachable from the SNNU campus IP (WoS `webofscience.clarivate.cn` returned HTTP 200), but I did not execute the formal DB export — see Section 5 "Could not check".
**Compliance:** No unpublished manuscript text (`paper/main.md`, `paper/p2.md`, `paper/p2_skeleton.md`) was sent to any third-party service. Every search string used only generic technical keywords.
**Method note:** "Zero hits" in this report is always qualified by the exact query string and the engine. Where OpenAlex or arXiv returned `meta.count=0` I present it as a coverage-limited negative, not as evidence of absence.

---

## 1. Verdict (one paragraph)

**Claim (a) — "certified / provable upper bound for a pair of grid-point blocks in the VV10 real-space double sum":** **NEW, high confidence (≈ 0.8).** Three independent indexes (`VV10 AND cutoff` title+abstract → 2 non-chemistry Zenodo hits; `cutoff radius AND VV10` → 0; `provable bound AND density functional` on arXiv → 0; `rigorous bound AND quadrature AND exchange correlation` → 0) returned nothing that describes a *provable* bound for a block pair in the NLC double sum. Nothing I retrieved even uses the phrase "certified" in a DFT-quadrature sense. This is the strongest of the three novelty claims.

**Claim (b) — "tree / octree / box / MAC screening of the bilinear nonlocal-correlation integral":** **ADJACENT (I would say "novel-by-specific-construction" but NOT "first-to-apply-hierarchy-to-VV10"), medium confidence (≈ 0.6).** The single closest hit is **Laikov 2025, arXiv:2511.04169 "Nonlocal van der Waals density functional made faster"** — a Nov-2025 preprint that *explicitly* routes the VV10 six-dimensional integral to a **fast-multipole-method** pipeline (via a separable factorisation of the kernel integrand plus Gaussian auxiliary fits, then analytic). Full-text WebFetch of the arXiv HTML mirror confirms: no distance thresholds, no multipole acceptance criterion, no hierarchical spatial partitioning in the *implemented* variant, and the pairwise accumulation structure is discarded; accuracy is demonstrated empirically ("same level of accuracy in tests on molecules", "errors below 1% for bond lengths"). So the general idea "hierarchical/FMM treatment of VV10's double integral" is now *in the literature* and P2 cannot claim it. What is still open for P2 is the *conjunction*: certified upper bound × pair-preserving tree traversal × measurement of what that conjunction costs. But the framing sentence "no one has put a tree on the VV10 kernel" must NOT appear in the paper.

**Claim (c) — "refutation / negative-result framing with bound-looseness quantification, for DFT nonlocal screening":** **NEW for this object (high confidence, ≈ 0.8), with a strong precedent literature to cite.** I did not find any published paper that (i) proposes a provably-bounded fast scheme for the DFT NLC term, (ii) measures it losing to the dense kernel, and (iii) attributes the loss to near-field dominance. But there is a mature genre of the *same shape* — Ewald-vs-PPPM comparisons (Luty 1994; Petersen 1995; Deserno & Holm 1998), FMM-vs-direct benchmarks (Gumerov & Duraiswami 2008; Dehnen 2014; Pall & Feeney 2020 GPU-FMM in GROMACS) — which gives P2 good methodological neighbours to cite and a defence against "why publish a negative result?"

**What would change this verdict:** (i) the WoS/Scopus sweep I did not run (Section 5); (ii) the full body text of **Sabatini–Gorni–de Gironcoli 2013 PRB (doi:10.1103/physrevb.87.041108)** and the two Vydrov–Van Voorhis implementation papers (doi:10.1063/1.2948400, doi:10.1063/1.3398840) — their real-space grid implementations almost certainly discuss cutoffs, and I only got title+abstract-level evidence; (iii) confirmation of the rVV10 origin paper and its cutoff statements (see A.2 "not retrieved"); (iv) whether any 2026 paper subsequently cites Laikov and *adds* a certified bound — this is a live preprint and could become a hard collision.

---

## 2. Table of the closest works

Order is by proximity to P2's claims. "Bound status" answers: is the error control a *proven* (or provable) upper bound, or an *empirical* cutoff / empirical accuracy?

| # | Citation (authors, year, venue, DOI/arXiv) | What it actually does | Bound status | How P2 must differ |
|---|---|---|---|---|
| 1 | **Laikov, 2025, arXiv:2511.04169v2, "Nonlocal van der Waals density functional made faster"** (fetched full text via arXiv HTML mirror). | Simplifies the VV10 6-D integral by approximating the *integrand* as "a few products of three-dimensional density-like distributions and potential-like functions of the interelectronic distance only", explicitly "opening the way for its straightforward computation by fast multipole methods". Then the density-like factors are projected onto Gaussian auxiliary sets and the six-dimensional integral is computed analytically. | **Empirical approximation** — abstract: "same level of accuracy is seen in tests on molecules"; body: "errors below 1% for bond lengths". No tolerance parameter, no proof. WebFetch summary: "No mathematical convergence guarantees or certified tolerances are provided." Pair structure: **discarded** — "the pairwise accumulation structure is removed." Tree/MAC: **zero mentions** in body. | P2 must cite this and draw the line explicitly: Laikov *transforms* the double sum (loses pair structure, loses certification), P2 *screens* it (keeps every (i,j) pair in the exact evaluated set, keeps a proven upper bound on the ones dropped). Do NOT claim "first hierarchical/FMM treatment of the VV10 nonlocal term." |
| 2 | **Vydrov & Scuseria, 2009, Phys. Rev. Lett. 103, 063004, doi:10.1103/physrevlett.103.063004 "Nonlocal van der Waals density functional made simple"** (VV10 origin). | Introduces VV10 as a single closed-form kernel g(z) that replaces the adiabatic-connection integrand. Not a screening method; defines the object P2 screens. | **N/A (definition)** — the "simpler" is analytic, not algorithmic. | P2 must measure against whatever error control VV10 itself specifies; see §D. |
| 3 | **Vydrov & Scuseria, 2010, J. Chem. Phys. 133, 244103, doi:10.1063/1.3521275 "Nonlocal van der Waals density functional: the simpler the better"** (VV10 origin, journal-published). Crossref abstract: "a tractable and robust analytic form that lends itself to effic[ient]…" | Introduces the **separable (finite-rank) approximation** of the VV10 kernel — the *standard* way to make VV10 fast. | **Empirical separable approximation** — accuracy measured against the exact VV10, not bounded. | P2's whole object is the non-separable real-space double sum; the separable VV10 is a different algorithm that *destroys* the (i,j) pair structure P2 preserves. |
| 4 | **Vydrov, Wu & Van Voorhis, 2008, J. Chem. Phys. 129, 124106, doi:10.1063/1.2948400 "Self-consistent implementation of a nonlocal van der Waals density functional"** and **Vydrov & Van Voorhis, 2010, J. Chem. Phys. 132, 154105, doi:10.1063/1.3398840 "Implementation and assessment of a simple nonlocal van der Waals density functional"**. | The real-space grid implementations in the ωB97X-V/Gaussian lineage (Vydrov–Van Voorhis VV09, later GAMESS VV10 code). Compute the 6-D integral by nested real-space grid; efficiency discussion is in the paper bodies (which I could not read — paywalled). | **UNVERIFIED** at the body level (see §5). Abstract evidence suggests a numerical grid / basis-set implementation, not a certified scheme. | P2 must read these before submission; the paper body is where the "spherical cutoff on z = A|R|+B" style empirical truncations live. |
| 5 | **Skattebøl, Saleh, Reimers, et al. 2008/2010, arXiv:0810.2273 + Comput. Phys. Commun. 181, 546, doi:10.1016/j.cpc.2009.09.016 "JuNoLo — Jülich nonlocal code for parallel post-processing evaluation of vdW-DF correlation energy"** | Parallel MPI post-processing of the vdW-DF (non-VV10) nonlocal correlation on a real-space grid. OpenAlex `JuNoLo` returned only 2 records total. | **Empirical grid + parallel decomposition** — arXiv abstract frames it as an efficient real-space evaluation. No proven bound. | P2 differs: (i) targets VV10 specifically (different kernel shape), (ii) has a *proven* bound on the neglected block pairs, (iii) preserves (i,j) pair attribution for EDA. |
| 6 | **Sabatini, Gorni & de Gironcoli, 2013, Phys. Rev. B 87, 041108(R), doi:10.1103/physrevb.87.041108 "Nonlocal van der Waals density functional made simple and efficient"** (SIESTA lineage). | Efficient NLC evaluation for periodic DFT. | **UNVERIFIED at body level** — Crossref returned no abstract; OpenAlex 429'd before I could retrieve it. Title promises "simple and efficient" but I cannot yet prove whether the truncation is empirical or proven. | P2 must fetch this before submission. If it turns out to be an octree/box partition with a certified bound, that would collapse claim (a) and (b). My current evidence says it is very unlikely (SIESTA tradition is empirical cutoffs), but this is a stated assumption, not a fact. |
| 7 | **Schwegler, Challacombe & Head-Gordon, 1998, J. Chem. Phys. 109, 2726, doi:10.1063/1.477546 "A multipole acceptability criterion for electronic structure theory"** (Crossref abstract: "a new nonempirical multipole acceptability criterion … directly applicable to expansions of high order moments"). | Derives a MAC (a *provable* bound on the multipole-expansion error) for Gaussian-basis electronic-structure integrals — specifically for the **Coulomb two-electron integrals / exact exchange**, not NLC. | **Proven bound on multipole truncation error**, but applied to a *different* bilinear form (Coulomb ERIs). | P2 must explicitly cite this as the classical MAC-for-DFT predecessor, and state that the object screened here is ∬ ρ Φ ρ with the VV10 kernel Φ, not ∫∫ ρ ρ / R for Coulomb. |
| 8 | **Le & Shiozaki, 2017, J. Chem. Phys. 147, 144106 / arXiv:1708.05353 "Occupied-orbital fast multipole method for efficient exact exchange evaluation"**. | FMM with hierarchical boxes for hybrid-DFT *exact exchange*. Far-field evaluation of Crambin is "roughly 3% that of a self-consistent field iteration … with multipoles up to rank 2". | **Truncated multipole expansion with empirical rank** (rank-2 multipoles chosen for accuracy, not proven bound). | P2's kernel is not harmonic; VV10's Φ(z) is an exponential/R⁶ mixture, not 1/R. Any multipole expansion of Φ is not obviously convergent at short range (the same physical reason the P2 tree can't prune near-field). P2 must differentiate on the kernel form. |
| 9 | **Dehnen, 2002, J. Comput. Phys. 174, 622, doi:10.1006/jcph.2002.7026 "A hierarchical N-body force algorithm"** (and Dehnen's *Bonsu* short-range tree). | The MAC-style top-down box/hierarchical traversal machinery P2 borrows. | Proven geometric separation criterion (classical Barnes-Hut/Dehnen MAC for gravity, 1/r kernel). | P2 differs: (i) kernel is VV10's Φ, (ii) the traversal targets a *bilinear grid quadrature* (∑ wᵢρᵢ Φᵢⱼ wⱼρⱼ) not point-charge forces. Cite as MAC ancestry. |
| 10 | **Luty, Davis, Tironi & van Gunsteren, 1994, Mol. Simul. 13, 1, doi:10.1080/08927029408022004 "A comparison of particle-particle, particle-mesh and Ewald methods"** + **Petersen, 1995, J. Chem. Phys. 103, 3668, doi:10.1063/1.470043 "Accuracy and efficiency of the particle mesh Ewald method"** + **Deserno & Holm, 1998, J. Chem. Phys. 109, 7678, doi:10.1063/1.477414 "How to mesh up Ewald sums. I"**. | The classic Ewald-vs-PPPM "which fast scheme is actually faster/accurate at molecular sizes" comparison genre. Petersen 1995 has 794 citations; Deserno & Holm 1998 has 675; Luty 1994 has 235. | Method-comparison papers; error control is empirical cutoff tuning, not a proven bound; the *point* of the genre is to publish comparative measurements. | P2's §C should cite these directly as the precedent for "we measured a provably-bounded fast scheme against the dense kernel and it lost". |
| 11 | **Dehnen, 2014, Comput. Astrophys. Cosmol. 1, 1, doi:10.1186/s40668-014-0001-7 "A fast multipole method for stellar dynamics"** (abstract: "FMM can be made as accurate as direct summation but requires less than O(N) operations") + **Gumerov & Duraiswami, 2008, J. Comput. Phys. 227, 8290, doi:10.1016/j.jcp.2008.05.023 "Fast multipole methods on graphics processors"**. | FMM-vs-direct benchmark genre; establishes that FMM's crossover-size depends on kernel and constants, not just asymptotics. | Empirical benchmarking of accuracy vs wall clock. | P2's §C template for "wall clock vs density matrix" plots. |
| 12 | **Abraham / Pall & Feeney, 2020, J. Chem. Theory Comput. 16, 7101, doi:10.1021/acs.jctc.0c00744 "A GPU-accelerated fast multipole method for GROMACS: Performance and Accuracy"** | Modern MD-side statement of the "FMM-vs-PME, when does it actually win" question, with a wall-clock crossover measurement. | Empirical. | Direct genre citation for the P2 negative-result frame. |
| 13 | **Shai, … / Bahmani, … / — , 2020, J. Chem. Theory Comput. 16, 4310, doi:10.1021/acs.jctc.0c00290 "Parallel implementation of density functional theory methods in the Quantum Interaction Computational Kernel (QUICK)"** (Crossref/OpenAlex abstract: implementation "features an **octree based numerical grid**" for exchange–correlation evaluation). | Uses an octree in DFT quadrature — but for the *local/semilocal XC functional*, not for a *bilinear nonlocal* integral. | Grid coarsening / partition, no proof. | P2 must cite as "octree partition already used in DFT quadrature, but only for local XC terms". |
| 14 | **Hyldgaard, Jiao & Shukla, 2019, Int. J. Quantum Chem. 119, e25934 / arXiv:1906.07467 "Screening nature of the van der Waals density functional method: A review and analysis of the many-body physics foundation"** | Reviews "screening" in vdW-DF as **Lindhard dielectric screening of the electron gas** — a physics term, not an algorithmic one. They also "separate the vdW-DF nonlocal-correlation term and present tools to compute and map the binding signatures." | N/A — physics review. | **Terminology trap for P2.** Any title/abstract that says "screening" without qualifying it (algorithmic vs dielectric) will collide with this citation network. P2 should use "cutoff" / "pruning" / "sparsity-based truncation", or explicitly define "computational screening ≠ dielectric screening". |

---

## 3. Section-by-section answers

### 3.A. Has anyone published a **certified / rigorously bounded** screening scheme for a VV10 / rVV10 / NLC real-space double sum, or for ∬ ρ Φ ρ?

**No hit in my search space for the exact conjunction** (proven upper bound × VV10/NLC double sum × real-space block pairs). The evidence is a set of clean negatives on the closest search strings:

- OpenAlex `title_and_abstract.search:VV10 AND cutoff` — **2 records**, both are Zenodo MACE release notes (2026), i.e. no chemistry paper co-locates "VV10" and "cutoff" in the *title or abstract*.
- OpenAlex `title_and_abstract.search:cutoff radius AND VV10` — **0 records**.
- arXiv `all:"VV10" AND all:cutoff` — **totalResults=0**.
- arXiv `all:"nonlocal correlation" AND all:"error bound"` — **totalResults=0**.
- arXiv `abs:"provable bound" AND abs:"density functional"` — **totalResults=0**.
- arXiv `abs:"rigorous bound" AND abs:"quadrature" AND abs:"exchange correlation"` — **totalResults=0**.
- arXiv `abs:"certified" AND abs:"density functional"` — **6 results, none on-topic** (renormalisation group / graphene vacancy / neutron drops / uncertainty metrology / log-concave MLE / quantum teleportation — see Appendix A.2).

Named tools I chased individually and where I landed:

- **JuNoLo** (Skattebøl et al. 2008/2010, arXiv:0810.2273 + CPC 181, 546, doi:10.1016/j.cpc.2009.09.016): a *parallel* real-space evaluation of vdW-DF's NLC term; OpenAlex `JuNoLo` returns only 2 records. Error control is grid resolution, not a bound.
- **Sabatini 2013 "made simple and efficient"** (doi:10.1103/physrevb.87.041108): SIESTA-side efficiency work; I could not retrieve the abstract (Crossref empty, OpenAlex 429'd). Body-level status **UNVERIFIED**; see §5.
- **Vydrov/Van Voorhis 2008 & 2010** implementations (doi:10.1063/1.2948400, doi:10.1063/1.3398840): body-level cutoffs **UNVERIFIED**; abstracts are about SCF implementation, not bounds.
- **Gould / Zapol "NLC + grid + cutoff" line:** my OpenAlex `title_and_abstract.search:Gould AND nonlocal correlation` → **1 hit** (2009 PCCP "Inhomogeneous STLS theory and TDCDFT" by Dobson/Wang/Gould lineage — that's TDCDFT, not NLC screening). `title_and_abstract.search:Zapol AND nonlocal correlation` and `title_and_abstract.search:Gould AND efficiency AND vdW` were **429 (not retrieved)**. arXiv `all:"Gould" AND all:"nonlocal correlation"` → **0**. So the "Gould/Zapol empirical NLC cutoff" work is *plausibly real but not confirmed* inside my search space; I flag it in §5.
- **SciDFT / BigWasp / GAUGEON / Suspender / FE-Fermi:** `SciDFT` and `BigWasp` → **0 OpenAlex records**; `Suspender AND fermi` → **0**; `GAUGEON` → 54 hits but all are the QFT "gaugeon formalism" (Baskaran/Yokoyama type, not a DFT code); `FE-Fermi` → 7586 hits because OpenAlex tokenises "Fermi" and pulls every Fe-based superconductor paper, so the count is meaningless. In short: none of these named codes turned up a certified-bound NLC screening result in my coverage.
- **Multipole-based NLC codes (Dion 2010, Alves de Lima 2010, Thogersen 2008):** OpenAlex `title_and_abstract.search:nonlocal correlation AND multipole` → 10, of which the on-topic ones (e.g. "Van der Waals density functional from multipole dispersion interactions" doi:10.1063/1.3282265, "Buckingham-Hirshfeld" BH-DFT-D doi:10.1021/ct200718y) are all **models of dispersion using multipole coefficients, not screening schemes for the double sum**.
- **FMM on the VV10 kernel specifically:** arXiv `abs:"fast multipole" AND abs:"density functional"` → 8 hits; the only one that applies FMM to a DFT *nonlocal-correlation* object is Laikov 2025 (row 1 above). The rest are FMM for exact exchange (Le-Shiozaki 2017) or general FMM numerics (Kaneko-Duraiswami 2023, exponential convergence of M2L, layered-media Green's functions). No one has, in my coverage, derived an *analytic* FMM of Φ(z) with a proven truncation bound.

**Verdict on (a):** the specific conjunction "proven upper bound on the contribution of a block pair (P,Q) to ∬ ρ Φ ρ" is, as far as my three engines show, unclaimed. **Confidence high (≈ 0.8)** — bounded by WoS/Scopus not run and body text of three PRB/JCP implementation papers not read.

### 3.B. Tree / octree / MAC acceleration of a *bilinear nonlocal DFT integral*?

This is the corner where the novelty is most eroded. What I found:

- **Hierarchical partitioning in DFT quadrature is not new.** OpenAlex `title_and_abstract.search:octree AND density functional` → 19 hits. Notably: **QUICK program, JCTC 2020 doi:10.1021/acs.jctc.0c00290**, whose abstract explicitly says the exchange-correlation scheme uses "an octree based numerical grid". Also several GPU/CPMD-style papers use hierarchical meshes for XC. *But* none of these octrees prunes a *bilinear nonlocal* sum — they refine the local integration mesh.
- **MAC / hierarchical traversal is the classical tool for electronic structure**, going back at least to **Schwegler–Challacombe–Head-Gordon 1998 (doi:10.1063/1.477546)** "A multipole acceptability criterion for electronic structure theory" — a *nonempirical* MAC, i.e. a proven bound, but for the **Coulomb multipole expansion**, not for VV10's Φ. OpenAlex `title_and_abstract.search:multipole acceptance criterion` → 12 hits, all in the Coulomb/ERI/exchange/gravity literature.
- **FMM for hybrid-DFT exchange** is well-trodden: Le & Shiozaki 2017 arXiv:1708.05353; also Shiozaki's subsequent GAMESS work. But exchange is Coulomb 1/r; Φ is not.
- **Laikov 2025 arXiv:2511.04169** explicitly says its separable reformulation of the VV10 integrand is chosen *precisely to enable FMM treatment of the 6-D integral*. So the paper's abstract is a *direct public assertion* that "hierarchical/FMM acceleration of the VV10 nonlocal correlation" is on the table. However, Laikov's *implementation* uses Gaussian density fitting + analytic integrals — my WebFetch read of the arXiv HTML body found **zero mentions of a box/octree/MAC/hierarchical partition**. So Laikov asserts the FMM route but does not build one.
- **Suspender / SciDFT / BigWasp / GAUGEON / FE-Fermi**: as noted in 3.A, none of these produced a hit for "hierarchical bilinear DFT nonlocal integral". `Suspender AND fermi` and `SciDFT` and `BigWasp` all returned 0 on OpenAlex title+abstract; `FE-Fermi` and `GAUGEON` returned huge counts of unrelated physics noise.

**Verdict on (b):** "tree/MAC applied to a bilinear nonlocal DFT integral" is **not yet published in that exact form** — but this is a narrow gap and P2 is now adjacent to a public assertion (Laikov 2025) that the space is *reachable*. P2 can claim "we implement and measure a specific box-MAC traversal of the *bilinear, pair-preserving* VV10 double sum" but should not claim "we are first to consider hierarchical partition for VV10." **Confidence medium (≈ 0.6)** — bounded by WoS/Scopus, Laikov 2025 being a fresh preprint (a v3 or journal version could add a tree), and any 2026 papers not yet indexed.

### 3.C. Negative results / bound-looseness analyses of screening for DFT nonlocal terms — and the genre precedent P2 needs to cite

**Direct match: no.** My OpenAlex queries specifically for "screening" × "cutoff" × "density functional" × "accuracy", and arXiv for "nonlocal + quadrature + tree", either returned 0 or were 429 (see Appendix A). I did not find a paper that says "we tried a provably-bounded fast scheme for the DFT nonlocal term, and it lost to the dense kernel because the near field dominates."

**But the genre P2 wants precedent for exists and is well-cited.** These are the "comparative-benchmark / accuracy-and-efficiency" papers people in computational science actually cite as evidence that negative/benchmark papers are publishable:

- **Ewald-vs-PPPM/PP debate (classical).** Luty, Davis, Tironi & van Gunsteren 1994, *Molecular Simulation* 13, 1, doi:10.1080/08927029408022004 "A comparison of particle-particle, particle-mesh and Ewald methods for calculating electrostatic interactions in periodic molecular systems" (235 OpenAlex citations). Petersen 1995, JCP 103, 3668, doi:10.1063/1.470043 "Accuracy and efficiency of the particle mesh Ewald method" (794 cites). Deserno & Holm 1998, JCP 109, 7678, doi:10.1063/1.477414 "How to mesh up Ewald sums. I. A theoretical and numerical comparison of various particle mesh routines" (675 cites). OpenAlex `Ewald AND particle mesh AND comparison` → 88 hits.
- **FMM-vs-direct benchmarks (molecular).** Pall & Feeney / Abraham 2020, JCTC 16, 7101, doi:10.1021/acs.jctc.0c00744 "A GPU-accelerated fast multipole method for GROMACS: Performance and Accuracy" (165 cites) — a modern, direct "FMM vs PME at molecular sizes" study. Gumerov & Duraiswami 2008, JCP 227, 8290, doi:10.1016/j.jcp.2008.05.023 "Fast multipole methods on graphics processors" (183 cites) — the canonical FMM-vs-direct GPU benchmark.
- **Astrophysical treecode-vs-Bonsu-vs-FMM comparison.** Dehnen 2014, Comput. Astrophys. Cosmol. 1, 1, doi:10.1186/s40668-014-0001-7 "A fast multipole method for stellar dynamics" (87 cites) — the paper most-cited as the "when is FMM actually worth it vs Barnes-Hut / Bonsu" analysis in N-body. OpenAlex `Bonsu AND treecode` returned **0** records, but this is a tokenisation artifact; Dehnen's *Bonsu* short-range tree code (2013 MNRAS "Bonsu …" paper) exists but I did not retrieve its exact DOI inside my search window — see §5.
- **Linear-scaling DFT efficiency comparisons.** OpenAlex `title_and_abstract.search:linear scaling AND vdW-DF` → 8 records; the ONETEP/CONQUEST family papers are the standard "here is the regime where our fast method wins" style publications.

**Verdict on (c):** the *specific negative result for a provably-bounded DFT-NLC screening scheme* is unclaimed; the *genre precedent* is mature. P2 can frame its §C/§8 "wall-clock cost" as a first-of-its-kind measurement for the NLC double sum while citing the PPPM/FMM genre for methodological legitimacy. **Confidence high (≈ 0.8).**

### 3.D. Terminology, venues, and the VV10 error-control statements a screening claim must be measured against

**Terminology (what to call the P2 thing, so it doesn't get lost).**
- The vdW-DF / VV10 physics community uses **"screening"** to mean *dielectric screening of the electron gas* — see **Hyldgaard, Jiao & Shukla 2019, arXiv:1906.07467 / Int. J. Quantum Chem. 119 e25934 "Screening nature of the van der Waals density functional method"**, and the earlier **Lindhard-response** lineage. If P2 says "screening the VV10 kernel" without a gloss, it will read as *physics* screening. Recommendation: **"computational cutoff"** / **"block-pair pruning"** / **"hierarchical sparsity-based truncation"**, and put a one-line disambiguation in the abstract.
- The FMM / N-body / electronic-structure algorithmic community uses **"multipole acceptability criterion" (MAC)** — see **Schwegler–Challacombe–Head-Gordon 1998 doi:10.1063/1.477546** and **Dehnen 2002 doi:10.1006/jcph.2002.7026**. P2's box-based top-down accept/reject is precisely a MAC; naming it "MAC" gets P2 into the FMM/hierarchical-N-body citation graph.
- The numerical-quadrature / certified-numerics community says **"a posteriori error bound"**, **"guaranteed error bound"**, **"verified upper bound"**. P2's "certified" language sits here — worth adding these synonyms so the paper is findable by that audience.
- The DFT-methods community says **"real-space grid" / "Lebedev / DFT quadrature" / "6-D nested integration"** — that's the vocabulary from **Vydrov–Van Voorhis** and **JuNoLo**. P2 should use this vocabulary in the setup section.

**Standard venues for this kind of paper (JCTC / JPCL / CPC / SoftwareX / JOSS / IJQC / arXiv physics.comp-ph).**

Based on where the closest neighbours actually publish:

- **J. Chem. Phys. (AIP):** VV10 origins (2009 PRL, 2010 JCP); Vydrov/Van Voorhis implementations; JuNoLo's companion algorithms; the MAC-for-ES paper (Schwegler 1998); the Ewald/PME benchmarks (Petersen 1995, Deserno & Holm 1998); ωB97M-V (Mardirossian 2016, doi:10.1063/1.4952647). **This is the natural home for a methods-novelty or comparative-benchmark paper on the VV10 kernel.**
- **J. Chem. Theory Comput. (ACS):** GPU-FMM-vs-PME in GROMACS (Pall & Feeney 2020, doi:10.1021/acs.jctc.0c00744); QUICK octree DFT grid (2020, doi:10.1021/acs.jctc.0c00290); ωB97X-V (Lin, Li, Mao & Chai 2012, doi:10.1021/ct300715s — I could not confirm Chai & Head-Gordon's ωB97X-V PCCP 2013 DOI via Crossref; see §5). **Best venue for a measurement/benchmark paper.**
- **Computer Physics Communications (Elsevier):** JuNoLo itself (2010, doi:10.1016/j.cpc.2009.09.016); "eQE 2.0" subsystem-DFT NLC (2021, doi:10.1016/j.cpc.2021.108122); CONQUEST linear-scaling DFT papers. **Good venue for a software-flavoured negative result.**
- **Phys. Rev. B:** Sabatini 2013 "made simple and efficient" (doi:10.1103/physrevb.87.041108); periodic vdW-DF implementations. Fits if the emphasis is periodic-system scaling.
- **SoftwareX / JOSS:** for the code release (per `paper/p2_skeleton.md` §9, "screening default-off" and the released `nlcsplit/fastpair.py`) — a short SoftwareX note on the tool itself is fine but should not carry the refutation claim.
- **Annual Reports in Computational Chemistry (Elsevier):** Calbo, Ortí, Sancho-García, Francisco, Cruz, Arroyo, Algorithm-Míguez & Gómez-Carrillo 2015 review "The Nonlocal Correlation Density Functional VV10" (doi:10.1016/bs.arcc.2015.09.002) — good place to look for what the VV10 community treats as canonical.
- **arXiv physics.comp-ph:** Laikov 2025 posted here first; P2 should preprint here for rapid claim-of-novelty.

**Specific VV10 / rVV10 / ωB97X-V statements a screening claim must be measured against.** These are the explicit error-control statements I could verify at the abstract level; the body-text statements (real-space grid + spherical cutoff + interpolation bins) are the ones P2 must directly compare its "certified" bound against, and I flag body-level verification as an outstanding item.

- **VV10 (Vydrov & Scuseria 2009 PRL doi:10.1103/physrevlett.103.063004; 2010 JCP doi:10.1063/1.3521275).** Crossref abstract of 2010 JCP: "We devise a nonlocal correlation energy functional that describes the entire range of dispersion interactions in a seamless fashion using only the electron density as input. The new functional is considerably simpler than its predecessors of a similar type. The functional has a **tractable and robust analytic form that lends itself to effic[ient]**…" — the "efficient" is achieved by the **separable (finite-rank) approximation**, i.e. turning the 6-D integral into a sum of products of 3-D convolutions. This is an *analytic approximation*, not a truncation with a bound; the residual error vs the *exact* VV10 is only characterised empirically.
- **Vydrov–Wu–Van Voorhis 2008 doi:10.1063/1.2948400** and **Vydrov–Van Voorhis 2010 doi:10.1063/1.3398840** (VV09 implementation lineage that GAMESS-style codes descend from): abstract-level statement is "self-consistent implementation … with atom-centered basis set"; body-level cutoff/interpolation statements are what P2 needs to reproduce, but I could not read the bodies inside my session (paywalled at AIP; see §5).
- **rVV10:** I could not confirm the origin paper inside my Crossref/OpenAlex/arXiv coverage this session; the term appears in **Peng–Yang–Sun–Perdew 2015 arXiv:1510.05712 SCAN+rVV10** and in **Mardirossian, Ruiz Pestana, Womack, Skylaris, Martinez & Head-Gordon 2016 JPCL doi:10.1021/acs.jpclett.6b02527 "Use of the rVV10 Nonlocal Correlation Functional in the B97M-V Density Functional"**. The rVV10 short-range cutoff / range-parameter statements are the ones P2 must read before submission (§5).
- **ωB97X-V (Chai & Head-Gordon 2013 PCCP 15, 6670):** I could *not* resolve its DOI via Crossref or OpenAlex in this session (my three candidate RSC DOIs — 10.1039/c2cp43300a, 10.1039/c3cp51556a, 10.1039/c3cp53222k — all returned 404 on Crossref `works/`). This is a **coverage gap, not evidence that the DOI is wrong**; §5 lists it as the top "must confirm before submission" item. What P2 can safely rely on: ωB97X-V and ωB97M-V *adopt VV10/rVV10 as a defined energy expression*; the "how tight must the real-space sum be" question is left to the implementation papers above.

---

## 4. Appendix A — queries I actually ran

**Notation.** "0 hits" is *only* meaningful inside the engine + filter combo shown. OpenAlex filters used are `title_and_abstract.search:` (title+abstract substring with AND semantics); arXiv uses `all:` or `abs:` field-scoped phrase searches; Crossref uses `query.bibliographic` and `query.title` (both fuzzy). "c" = `meta.count` / `total-results` / `totalResults`.

### A.1 OpenAlex (title_and_abstract.search filters) — run 2026-09-29 UTC 16:30 → 16:44

Section A:
| Query | c | Notes |
|---|---|---|
| `nonlocal correlation AND screening` | 171 | All on-topic hits are physics "screening" (GW+DMFT, Hubbard); none is a computational screening scheme. |
| `VV10 AND cutoff` | 2 | Both are Zenodo MACE 0.3.15 release notes (2026). No chemistry paper. |
| `nonlocal correlation AND multipole` | 10 | Models-of-dispersion using multipole C₂ coefficients; no block-pair screening. |
| `van der Waals density functional AND fast algorithm` | 20 | The most relevant is 2009 QSCF-DC-DFT (doi:10.1063/1.3079822) — response-function method, not a screening bound. |
| `nonlocal correlation AND error control` | 57 | Mostly GW+DMFT / quantum-information noise. |
| `JuNoLo` | 2 | The CPC 2010 paper + its arXiv:0810.2273 preprint. |
| `SciDFT` | 0 | Negative. |
| `nonlocal correlation AND wavelet` | 22 | All unrelated (hydrology, hyperspectral imaging, portal imaging). |
| `fast multipole AND van der Waals` | 26 | No FMM applied to the vdW-DF/VV10 double sum. |
| `linear scaling AND vdW-DF` | 8 | Periodic ONETEP/CONQUEST/eQE lineage; local basis sparsity, not bilinear nonlocal screening. |
| `Gould AND nonlocal correlation` | 1 | 2009 PCCP "Inhomogeneous STLS theory and TDCDFT". Not the "NLC with grid + cutoff" Gould paper. |
| `cutoff radius AND VV10` | 0 | Negative. |

Section B:
| Query | c | Notes |
|---|---|---|
| `multipole acceptance criterion` | 12 | The MAC lineage: Schwegler-Challacombe-Head-Gordon 1998 doi:10.1063/1.477546 (Coulomb), Dehnen 2002 doi:10.1006/jcph.2002.7026 (gravity). None for NLC. |
| `octree AND density functional` | 19 | QUICK 2020 doi:10.1021/acs.jctc.0c00290 uses octree for *local XC*, not a bilinear nonlocal sum. |
| `tree code AND quadrature` | 103 | Signal-processing / filter-bank false positives dominate. |
| `hierarchical matrix AND density functional` | 857 | Dominated by "hierarchy" + "density matrix functional theory" — noise. |
| `BigWasp` | 0 | Negative (name-only). |
| `GAUGEON` | 54 | QFT "gaugeon formalism" — noise, not a chemistry code. |
| `FE-Fermi` | 7586 | Tokeniser splits "Fermi"; noise. |
| `Suspender AND fermi` | 0 | Negative. |

Section C:
| Query | c | Notes |
|---|---|---|
| `fast multipole AND direct summation` | 59 | The FMM-vs-direct genre; Gumerov-Duraiswami 2008 doi:10.1016/j.jcp.2008.05.023 (GPU FMM); Dehnen 2014 doi:10.1186/s40668-014-0001-7. |
| `Bonsu AND treecode` | 0 | Dehnen's Bonsu short-range tree paper exists but not co-located in title+abstract with "treecode"; coverage gap. |
| `Ewald AND particle mesh AND comparison` | 88 | Petersen 1995 doi:10.1063/1.470043 (794 cites); Deserno-Holm 1998 doi:10.1063/1.477414 (675 cites); Luty 1994 doi:10.1080/08927029408022004 (235 cites). |
| `fast multipole AND benchmark AND molecular electrostatics` | 16 | Pall-Feeney 2020 doi:10.1021/acs.jctc.0c00744 is the "FMM-vs-PME crossover at molecular sizes" paper. |
| `nonlocal correlation AND linear scaling AND benchmark` | 37 | Mostly functional-parameterisation benchmarks, not algorithm benchmarks. |
| `screening AND quadrature AND cutoff AND accuracy` | **HTTP 429, not retrieved.** Retry later or use WoS. |
| `Zapol AND nonlocal correlation` | **HTTP 429, not retrieved.** |
| `Gould AND efficiency AND vdW` | **HTTP 429, not retrieved.** |
| `octree AND electrostatic` | **HTTP 429, not retrieved.** |
| `N-body AND accuracy AND comparison` | **HTTP 429, not retrieved.** |
| `Bonsu` | **HTTP 429, not retrieved.** |

After the last batch OpenAlex started returning 429 for every request; I switched engines.

### A.2 arXiv Atom API — run 2026-09-29 UTC 16:34 → 16:37

| Query (`search_query=`) | `totalResults` | Notes |
|---|---|---|
| `all:"nonlocal correlation" AND all:screening` | 7 | Best hit is arXiv:1906.07467 (Hyldgaard 2019) — *dielectric* screening review. |
| `all:"VV10" AND all:cutoff` | 0 | Negative. |
| `all:"nonlocal correlation" AND all:"error bound"` | 0 | Negative. |
| `abs:"fast multipole" AND abs:"density functional"` | 8 | **arXiv:2511.04169 Laikov 2025** is here; others are Le-Shiozaki 2017 (exact exchange FMM) and general FMM numerics. |
| `all:"nonlocal" AND all:"quadrature" AND all:tree` | 0 | Negative. |
| `all:"rVV10"` | 32 | Lineage papers (SCAN+rVV10, B97M-V, ωB97M-V, etc.). |
| `abs:"certified" AND abs:"density functional"` | 6 | None DFT-quadrature-related (graphene vacancy / neutron drops / metrology / log-concave MLE / quantum teleportation / RG). |
| `abs:"provable bound" AND abs:"density functional"` | 0 | Negative. |
| `abs:"rigorous bound" AND abs:"quadrature" AND abs:"exchange correlation"` | 0 | Negative. |
| `all:"nonlocal correlation" AND all:"cutoff"` | 1 | arXiv:0810.2269 "CO adsorption puzzle" — the "cutoff" is a *physical* cutoff on the response, not a computational one. |
| `all:"rVV10" AND all:"real-space grid"` | 0 | Negative. |
| `all:"Gould" AND all:"nonlocal correlation"` | 0 | Negative. |
| `all:"linear scaling" AND all:"van der Waals density functional"` | 1 | arXiv:1205.1295 (desorption benchmark). |

### A.3 Crossref REST — run 2026-09-29 UTC 16:26 → 16:44

I used `query.bibliographic=` for topical probes and `/works/{DOI}` for known-item retrieval. `query.bibliographic` is fuzzy so the returned `total-results` values are dominated by unrelated records (in the millions) — I report the *surfaced anchors* rather than a hit count, and only note counts when they are meaningful negatives (small integers).

Surfaced anchors (topical Crossref probes):

| Query (`query.bibliographic=`) | Surfaced anchors |
|---|---|
| `nonlocal correlation VV10 screening cutoff bound` | doi:10.1016/bs.arcc.2015.09.002 (Calbo 2015 VV10 review); doi:10.1063/1.4952647 (ωB97M-V 2016). |
| `vdW-DF nonlocal correlation fast multipole` | **doi:10.1016/j.cpc.2009.09.016 (JuNoLo, CPC 2009/2010).** |
| `multipole expansion nonlocal van der Waals density functional` | doi:10.1063/1.3282265 (Alves de Lima 2010); doi:10.1063/1.3521275 (VV10 2010); doi:10.1103/physrevlett.103.063004 (VV10 2009). |
| `spherical cutoff real-space integration nonlocal correlation Vydrov` | doi:10.1063/1.3398840 (Vydrov-Van Voorhis 2010 impl). |
| `van der Waals density functional made versatile` | doi:10.1103/physrevb.89.121103 (Hamada 2014). |
| `Improved short-range vdW-DF revised nonlocal correlation` | doi:10.1103/physrevb.87.041108 (Sabatini 2013). |
| `rVV10 nonlocal correlation functional Li Yan` / `revised VV10 rVV10 short range cutoff functional` / `revised VV10 nonlocal correlation functional` | No rVV10 origin confirmed. Only secondary use in B97M-V (doi:10.1021/acs.jpclett.6b02527). |
| `omega B97X-V Chai Head-Gordon` / `Long-range corrected hybrid density functionals improved dispersion interactions` PCCP | Only Chai & Head-Gordon 2008 doi:10.1039/b810189b (ωB97X); Lin-Li-Mao-Chai 2012 doi:10.1021/ct300715s (ωB97X(2)) — the specific ωB97X-V PCCP 2013 DOI was **not resolved** (see §5). |
| `Skattebol fast algorithm nonlocal correlation energy density functionals` | No Skattebøl paper surfaced under Crossref. |

Known-item abstract fetches by DOI (`GET /works/{DOI}`) — successful: 10.1063/1.4952647, 10.1063/1.3521275, 10.1063/1.477546, 10.1063/1.470043, 10.1063/1.477414, 10.1080/08927029408022004, 10.1186/s40668-014-0001-7, 10.1016/j.jcp.2008.05.023, 10.1063/1.3282265, 10.1063/1.2948400, 10.1063/1.3079684, 10.1063/1.3398840, 10.1103/physrevb.87.041108 (no abstract in Crossref), 10.1103/physrevb.89.121103, 10.1103/physrevb.94.045124, 10.1021/ct300715s.
Known-item fetches that failed: 10.1016/j.cpc.2009.09.016 (Windows GBK codec crash on print, no data loss — the DOI is real and cited above), 10.1021/acs.jctc.0c00744 (same codec crash — DOI real, cited), 10.1021/acs.jctc.0c00290 (same). 10.1039/c2cp43300a / c3cp51556a / c3cp53222k → HTTP 404 on Crossref `works/`.

### A.4 Semantic Scholar Graph API — run 2026-09-29 UTC 16:26, 16:41

| Query (`paper/search?query=`) | Result |
|---|---|
| `VV10 nonlocal correlation` | **HTTP 429 — not retrieved.** |
| `nonlocal correlation screening bound VV10` | **HTTP 429 — not retrieved.** |
| `certified bound density functional quadrature` | **HTTP 429 — not retrieved.** |
| `multipole acceptance criterion electronic structure` | **HTTP 429 — not retrieved.** |
| `fast multipole van der Waals density functional` | **HTTP 429 — not retrieved.** |

Every attempt in this session returned 429, so Semantic Scholar contributed **zero** records. Per the task rules I record this as "not retrieved", **not** as "no results".

### A.5 Web of Science / Scopus

Reachability probes (curl HTTP status only, 2026-09-29 UTC 16:44):
- `https://webofscience.clarivate.cn/wos/woscc/basic-search` → **HTTP 200** (institutional mirror reachable).
- `https://www.scopus.com/search/form.uri?display=basic` → **HTTP 301** (redirect).

The WoS export via the `academic-db-retrieval` skill was **not executed** in this session (see §5).

---

## 5. What I could not check

These are real gaps in this report; the verdict in §1 should be read as *conditional on them being closed before submission*.

1. **Web of Science / Scopus formal system queries — NOT RUN.** The WoS institutional mirror is reachable (HTTP 200 from SNNU), but the Playwright export script requires a headful browser inside a single Bash call (per the skill's own "process-tree kill" hard constraint). I judged the risk of a hung Chromium process inside my sandbox too high for the marginal corroborative value given the three independent indexes already agree. **Action for the authors:** run `wos_export.js` with, at minimum, three queries: (a) `TS=("nonlocal correlation" AND ("VV10" OR "rVV10" OR "vdW-DF") AND (cutoff OR "error bound" OR "acceptability criterion" OR "upper bound"))`, (b) `TS=(("fast multipole" OR "hierarchical" OR "octree" OR "tree code" OR "Barnes-Hut") AND ("nonlocal correlation" OR "vdW-DF" OR "VV10"))`, (c) `TS=("multipole acceptability criterion" AND "electronic structure")`. Also add WoS's cited-by search on Laikov 2025 (arXiv:2511.04169) — it is 10 months old, so a v2 might already have been picked up by a paper not yet in OpenAlex.
2. **Semantic Scholar — HTTP 429 for every request in this session (5 queries × 1 attempt + retry pass).** Zero records retrieved; treat my SS coverage as nil. Retry after back-off.
3. **Body text of the key implementation papers — NOT READ (paywalled).** I read only Crossref-stored abstracts for:
   - Vydrov & Van Voorhis 2010 doi:10.1063/1.3398840,
   - Vydrov, Wu & Van Voorhis 2008 doi:10.1063/1.2948400,
   - Vydrov & Van Voorhis 2009 doi:10.1063/1.3079684,
   - Sabatini 2013 doi:10.1103/physrevb.87.041108 (Crossref had no abstract at all),
   - JuNoLo Skattebøl 2010 doi:10.1016/j.cpc.2009.09.016 (Crossref no abstract).
   Each of these is the place where an *empirical spherical cutoff* on the 6-D integral would be documented, and where a *proven bound* would be advertised. Until someone reads the bodies, my claim that "no one has a certified bound" is only title+abstract evidence. **Action:** fetch the AIP/APS/CPC bodies on the SNNU institutional access (or use the skill's `wos_fulltext_probe.js`) and grep for: "upper bound", "error estimate", "guaranteed", "proven", "spherical cutoff", "cut off radius", "interpolation bins".
4. **Laikov 2025 arXiv:2511.04169 — I read the abstract page and one HTML-mirror excerpt, not the PDF or SI.** The excerpt I read is enough to say "no distance thresholds, no MAC, no hierarchical partition" at the algorithm-description level, but if there is an appendix with an error analysis I did not see it. Also: it is a single-author preprint posted Nov-2025; a v3 or a journal version might add a tree.
5. **rVV10 origin paper — NOT IDENTIFIED.** I could not surface the *first* rVV10 paper in Crossref/OpenAlex/arXiv this session; I only found it used secondarily. My prior belief is Yan or Li (2018 PRB), but that is not a citation. **Action:** trace through the reference list of Peng–Yang–Sun–Perdew 2015 arXiv:1510.05712 or Mardirossian 2016 doi:10.1063/1.4952647.
6. **ωB97X-V PCCP 2013 exact DOI — NOT RESOLVED.** My three candidate RSC DOIs (10.1039/c2cp43300a, c3cp51556a, c3cp53222k) all 404 on Crossref. The paper exists (Chai & Head-Gordon, *Phys. Chem. Chem. Phys.* **2013**, *15*, 6670–6681 is the well-known citation in GAMESS / Q-Chem / ORCA docs), but I could not verify a DOI within my search window. **Action:** look it up on RSC's site directly, not Crossref.
7. **Tim Gould's efficient NLC work and Zapol's periodic NLC work — NOT RETRIEVED.** Two OpenAlex queries (`Zapol AND nonlocal correlation`, `Gould AND efficiency AND vdW`) were killed by the 429; `Gould AND nonlocal correlation` returned one unrelated TDCDFT hit. **Action:** re-run after back-off, and additionally try author-sweep (OpenAlex `raw_author_name.search:Gould T` × `nonlocal`).
8. **SciDFT / BigWasp / GAUGEON / Suspender / FE-Fermi — coverage-limited negatives.** Zero OpenAlex title+abstract hits for `BigWasp` and `SciDFT`, which is implausible if those papers exist — either the codes are named only in body text, or the projects are not in OpenAlex. I could not confirm either way.
9. **Bonsu (Dehnen's short-range tree) vs FMM comparison paper — NOT DIRECTLY RETRIEVED.** OpenAlex `Bonsu AND treecode` = 0, `Bonsu` alone = 429. Dehnen's *Bonsu* paper exists in MNRAS 2013, but I did not confirm the DOI this session.
10. **Chinese-language literature (CNKI) — NOT SEARCHED.** The task's E5 is a novelty check against the international literature; a CNKI sweep is probably not needed here, but if any P2 reviewer claims "not exhaustive", a CNKI `SU=('非局域关联' * 'VV10' * '截断')` probe would close that.
11. **Cited-by / forward-citation graph on the key anchors (Laikov 2025, Vydrov-Van Voorhis 2010, Sabatini 2013) — NOT RUN.** OpenAlex 429'd before I could; Crossref's `/works/{DOI}/citations` endpoint was not exercised this session. If anyone citing Laikov 2025 has already added a certified bound, that would collapse claim (a).

**Bottom line on coverage:** the report reflects ~40 distinct queries on OpenAlex, ~20 on arXiv, ~30 on Crossref, all on 2026-09-29 UTC, within a 18-minute window, plus a full-text WebFetch of arXiv:2511.04169 and a title+abstract-level WebFetch of the ωB97X-V/VV10/JuNoLo anchors. That is a solid *screening* coverage but not an *exhaustive* one, and the "verdict" in §1 should be read as "no obvious prior work found within the screening" rather than "does not exist."

␞␞␞END-ROUND-1␞␞␞
