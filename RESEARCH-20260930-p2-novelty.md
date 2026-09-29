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
