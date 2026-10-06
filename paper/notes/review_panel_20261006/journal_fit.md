# Journal-Fit Review Card — `paper/main.md` (VV10 pair attribution)

Seat: Journal-Fit Reviewer — scope, framing, audience fit, novelty-signalling, over/under-claiming.
Reviewed: 19,156 words (body 14,246; appendix 4,569); also cited code/archives, `software.md`, `p2.md`, `MAIN-skeleton.md` table 4b, `figs/`.
Blindness respected: no `paper/notes/` file (except this output), no `PROGRESS-*`, no audit/rebuttal/review-named file read.

## 1. What the paper claims

The VV10 double sum is evaluated explicitly with the (i,j) pair index retained, which production codes are said to discard; grid points are assigned to fragments by four real-space partitions, splitting E_NLC into intra- and inter-fragment blocks that sum back to the total. Two claims follow on eight S22 complexes at ωB97X-V/6-31G*: the VV10 share of the exchange-correlation change spans 16%–97% (methane dimer: it exceeds the whole change, the semi-local remainder being repulsive), so ΔE_NLC must not be relabelled "the dispersion"; and the attribution is non-unique (0.004–0.247 kcal/mol, 0.8–18.2% relative, no ordering by interaction type or basis), so a per-system error bar is required. Verification: PySCF-kernel agreement to 5.7e-6 kcal/mol, ORCA 6.0.1 under 1% of the term on all eight systems (§4.2), a two-Gaussian partition-free referee, and a negative cost result. I could state this cleanly; the draft cannot: its contribution sentence is buried mid-introduction — "Two things are not trivial, and they are the content of this paper" (L92–93) — and neither title nor abstract reproduces it.

## 2. Journal fit

**(a) JCC — right venue; Major-Revision level after surgery.** JCC takes implementation papers whose advance is a usable quantity plus validation, and this has them: shipped package, cross-program anchor under 1% on all eight systems, measured cost (§3.6), Apache-2.0, 74 tests. Realistic odds decide it: JCC accepts an uncertainty-audit contribution that JCTC sorts as incremental, and as written its reviewers will spend their reports on §3.2's self-correction narrative instead of Table 1.

**(b) JCTC — wrong first move; probable rejection without review.** Two of its own sentences do the editor's work: "attributing a nonlocal correlation term to atoms is not ours and is not claimed here" (§1, L136) concedes priority, and "This is not an energy decomposition analysis" (§4.1, L877) disclaims the citing community. JCTC requires a conceptual advance of broad interest. The JCTC-shaped asset here is the screening-certificate result (§3.6, `p2.md` §4–5) — a different paper.

Logistics: JCC is Wiley, not Elsevier; both are SCIE-listed, so the SCI constraint holds either way.

## 3. Highest gain-per-work change

Rebalance §3.2: of its 4,730 words, 3,960 (L422–718) are the CCSD(T)/counterpoise/release-grid anchor narrative and 770 carry the headline claim. Move L422–718 — the eight-row deviation table, "How this section was wrong before…" (L483), "A fourth nuisance parameter, found by a guard that refused to pass" (L657) — to SI as "Reference anchor and nuisance parameters", keeping a 150-word summary plus the table. Editing only: every number is tagged [S24], [S26]–[S31] with hashed archives, and appendix rows S24/S30/S31 retell the same story, so this is de-duplication; body falls to ~10,300 words. §3.6 should take the unreferenced `figs/fig3_screening_cost.png`.

## 4. Desk-reject triggers, by likelihood

1. Length/proportion: a 4,569-word appendix deliberately "left inside the manuscript" (L1228).
2. Debugging-log framing: 12 "correction", 8 "earlier version", 2 "superseded" in the body (L210–11).
3. Self-declared title overclaim (L128–29).
4. Unresolved front matter: ORCID "still to be supplied" (L9); COI and funding left as instructions (L1231–35).
5. Data availability: Table 1's complement cited to `MAIN-skeleton.md` table 4b (L373), provenance to `paper/tex_audit.md` (L18) — internal files, not SI objects.
6. Novelty claim resting on one index (L42 vs §4.4 L1060).
7. Figure order: Figure 2 captioned at L777, after Figures 3 and 4 (L684, L705).

## 5. Severity-ranked findings

**Critical**
- C1 — "production implementations fold that sum into per-point values before returning them, which destroys the pair index" (Abstract, L26–28) against "We have not audited the equivalent paths inside libxc, ORCA, Psi4 or Gaussian" (§1, L61). Audited: PySCF only. Scope the abstract or audit ORCA.
- C2 — "it is narrower than the title suggests" (§1, L128–129), with the Heßelmann concession at L136: the manuscript says its own title overclaims. Retitle to the measured result or promote the delta sentence (L147–150) to the abstract.

**Major**
- M1 — §3.2 disproportion: 84% of the section named for the headline claim is verification forensics, which makes the central result look under-evidenced by construction; the framing fails, not the core.
- M2 — "this is not an energy decomposition analysis" (§1, L180; §4.1, L877) repeated while all four closest-prior comparisons (L129–145) are EDA work; "does not" ×21, "rather than" ×63. State what an ALMO-EDA or SAPT user should do differently.
- M3 — "We found no published implementation that resolves this term into fragment pairs" (Abstract, L42) rests on one index; §4.4 concedes Embase and SciFinder "were not searched at all" (L1060).
- M4 — "unsafe even within one benchmark set" (§6, L1145) rests on seven ratios drawn from 8 of S22's 22 complexes; the subset is never justified.
- M5 — §2.5 Verification (710 words) is largely PySCF 2.12.1-vs-2.14.0 grid-count auditing (L315), not method.

**Minor**
- m1 — Raw LaTeX in prose: "(Fig.~\ref{fig:2})" (L785).
- m2 — Editing residue: "the constructed the benzene_sandwich() constructor" (L586, L1291).
- m3 — Symbol drift: `dE_NLC` ×9 vs ΔE_NLC ×9; "omegaB97X-V" ×11 vs ωB97X-V ×3.
- m4 — Abstract density: 267 words carry implementation, cancellation, two anchors, the dispersion claim, the error bar and the no-precedent statement; the screening bound belongs in the body.
