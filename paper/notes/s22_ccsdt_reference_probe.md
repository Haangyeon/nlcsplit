# S22 water-dimer CCSD(T) reference-value probe (literature metadata, read-only)

Run: this session (workspace dated 2026-10). Tools used: WebSearch + WebFetch of
Crossref REST (`api.crossref.org`), OpenAlex (`api.openalex.org`), Semantic Scholar
(graph API, metadata only), Europe PMC, arXiv, and publisher pages. No cloud-AI
service. No file under `evidence/` touched; no git operations. This file is the only
artifact created.

## Purpose / discipline note
Earlier drafts carried (i) an untraceable sentence "the literature CCSD(T) dispersion is
-1.4 kcal/mol" and (ii) a fabricated bibliography entry "Jurecka PCCP 5, 1811 (2003)".
Both were retracted. This probe obtains the S22 reference value first-hand from primary
sources, and states an evidence level for every number. Where a value could not be read
from an accessible full text it is reported as **NOT VERIFIED**, not reconstructed.

## Evidence-level legend
- **METADATA-ONLY** — citation (authors/journal/vol/pages/year/DOI) verified via
  Crossref/OpenAlex; the numeric table value was NOT reachable in any full text I could open.
- **FULLTEXT (open)** — number read from a genuinely open-access full text.
- **TABLE-QUOTE** — a table row quoted (extracted) verbatim from an open full text.
- **SECONDARY** — value seen only in a paper that itself cites the original.

## Table: candidate reference values for the water-dimer interaction energy

| # | Citation (verified form) | DOI (resolvable) | Convention / what it is | Numeric value + unit | Evidence level | URL actually read |
|---|---|---|---|---|---|---|
| 1 | Jurečka P., Šponer J., Černý J., Hobza P., *Phys. Chem. Chem. Phys.* **8**, 1985–1993 (2006) — the original S22 | `10.1039/b600027d` | Scope (per verified title/abstract): **total** MP2 and CCSD(T)/CBS **interaction energies** (no dispersion-only component listed at this level). CP status / geometry / exact CBS rungs **not read** (table not accessible). | Water-dimer value **NOT VERIFIED** | **METADATA-ONLY** | https://api.crossref.org/works/10.1039/b600027d ; https://api.openalex.org/works/doi:10.1039/b600027d (is_oa=false) |
| 2 | Takatani T., Hohenstein E. G., Malagoli M., Marshall M. S., Sherrill C. D., *J. Chem. Phys.* **132**, 144104 (2010), "Basis set consistent revision of the S22 test set…" | `10.1063/1.3378024` | Revision of #1 with a basis-set-consistent CBS extrapolation. Would restate both the original and revised water-dimer values — **not read**. | **NOT VERIFIED** | **METADATA-ONLY** | Crossref/OpenAlex; AIP PDF + OSTI `purl/1564692` both unreachable (403 / scanned image, no text layer) |
| 3 | Goerigk L., Hansen A., Bauer C., Ehrlich S., Najibi A., Grimme S., *Phys. Chem. Chem. Phys.* **19**, 32184–32215 (2017) — GMTKN55 | `10.1039/c7cp04913g` | GMTKN55 reuses S22 (H-bonded subset) as reference values. Exact restated number + any convention change **not read**. | **NOT VERIFIED** | **METADATA-ONLY** | https://api.crossref.org/works?query.bibliographic=Goerlich… (returned `10.1039/c7cp04913g`); SI 404/403 |
| 4 | Klopper W., van Duijneveldt-van de Rijdt J. G. C. M., van Duijneveldt F. B., *Phys. Chem. Chem. Phys.* **2**, 2227–2234 (2000) — "equilibrium geometry and dissociation energy of the water dimer" | `10.1039/a910312k` | **Different lineage from S22**: equilibrium-geometry *De* of the isolated water dimer (monomer-relaxed/equilibrium convention), not an S22 complex-geometry CCSD(T)/CBS entry. Primary full text not opened. | **NOT VERIFIED** (primary); `−4.95` seen only via #5 | **METADATA-ONLY** (+SECONDARY via #5) | https://api.crossref.org/works/10.1039/a910312k |
| 5 | "Local energy decomposition analysis of hydrogen-bonded dimers…", *Beilstein J. Org. Chem.* (2018), DOI as printed on page: `10.3762/bjoc.14.79` | `10.3762/bjoc.14.79` | **This paper's OWN** CBS/BSSE-corrected supermolecular interaction energy (Table 1), referenced to Klopper (#4); plus this paper's **own** DLPNO-CCSD(T)/LED **dispersion** component. Geometry O···H ≈ 1.943 Å, RI-MP2-based, BSSE-corrected. **NOT the S22 number.** | ΔE ≈ **−4.95 kcal/mol**; LED **dispersion ≈ −1.24 kcal/mol** | **FULLTEXT (open) / TABLE-QUOTE** | https://www.beilstein-journals.org/bjoc/articles/14/79 |
| 6 | "Molecular orbital analysis of the hydrogen bonded water dimer", *Sci. Rep.* **6**, 22099 (2016), PMC4764947 | `10.1038/srep22099` | Table 1: SAPT decomposition Eint = −4.76, with "−4.95(a)"; footnote (a) = **"calculated at CCSD(T)/aug-cc-pVQZ level"** — i.e. **this paper's own** supermolecular value (single-aug-QZ, not their CBS). **NOT the S22 number.** | CCSD(T)/aug-cc-pVQZ ≈ **−4.95 kcal/mol** | **FULLTEXT (open) / TABLE-QUOTE** | https://pmc.ncbi.nlm.nih.gov/articles/PMC4764947/ |

## What I searched and could not read (so the absence is bounded, not proof)
Paywalled/blocked full texts that certainly contain the S22/Takatani/GMTKN55 water-dimer
rows but returned 403 or image-only PDFs: RSC `pubs.rsc.org/.../b600027d` and the GMTKN55
SI (404), AIP `pubs.aip.org/.../144104_1_online.pdf` (403), the OSTI DOE copy of the
Takatani paper (valid but a scanned image, no extractable text layer), MDPI, Nature article
pages (303 redirect loop), CORE (403). Open reproductions checked that did **not** tabulate
the S22 water-dimer value: arXiv 2412.16405v2 ("systematic discrepancies…" — only cites S22
as ref [63], gives no (H2O)2 total); PMC3206731; PMC9875315 ("An Imbalance in the Force");
PMC9979596; J. Phys. Chem. A 2026 `10.1021/acs.jpca.6c00689` (PMC13112346). A "0 hits"
result is weak evidence of absence, so the S22 number is flagged NOT VERIFIED, not absent.

## On the retracted items
- The canonical S22 benchmark is PCCP **8**, 1985–1993 **(2006)**, DOI `10.1039/b600027d`
  (verified). A Crossref search for a Jurečka paper at PCCP **5**, 1811 **(2003)** returned
  **no match**, which is consistent with that earlier bibliography entry being erroneous;
  it is not the S22 source under any reading.
- The original S22 (per its verified title/abstract) reports **total** MP2/CCSD(T)/CBS
  interaction energies. A **CCSD(T) "dispersion" component** is *not* one of the quantities
  verifiable for S22 here — dispersion-only terms of this type come from SAPT or from LED
  decompositions (e.g. #5's −1.24 kcal/mol). So a "literature CCSD(T) dispersion = −1.4
  kcal/mol" sentence cannot be sourced to S22 at all.

## What can and cannot be stated in our paper (plain language)
- **Cannot** write any specific number as "the S22 CCSD(T)/CBS water-dimer reference value" —
  that figure was not readable from an accessible primary full text this session; quoting it
  would repeat the earlier failure mode. Obtain it by opening the Jurečka 2006 PDF (or the
  Takatani 2010 / GMTKN55 tables) directly.
- **Can** cite, fully verified: Jurečka et al., *PCCP* **8**, 1985–1993 (2006),
  DOI `10.1039/b600027d`, as the S22 source.
- **Can** cite the S22 revision: Takatani et al., *J. Chem. Phys.* **132**, 144104 (2010),
  DOI `10.1063/1.3378024`, noting it re-derives the values on a basis-set-consistent basis.
- **Can** note (from open full texts #5/#6) that independent supermolecular CCSD(T) water-dimer
  interaction energies cluster near **−4.95 kcal/mol**, but must label that as *their own*
  computations (Klopper-referenced / aug-cc-pVQZ), **not** as the S22 published figure.
- **Can** state, safely, that S22 reports total interaction energies, so any per-component
  "CCSD(T) dispersion" number must be sourced to SAPT/LED, never to S22.

## Main-agent re-verification, same day (why this section exists)

The paper needed one number from row #5, so I fetched that page myself rather than
trusting the row. What I got back, verbatim from the section "Geometries and dissociation
energies: comparison with experiment":

> "The dE_e value of the water dimer calculated previously at the CCSD(T)/CBS level
> (-5.01 kcal/mol [68]) agrees"

So the open text carries **two** water-dimer numbers and they are not the same quantity:
**-5.01** is the *previously published* equilibrium-geometry CCSD(T)/CBS dissociation
energy, attributed by that paper to its own reference [68] (the Klopper lineage, row #4),
and **-4.95** is the Table-1 value this probe recorded as that paper's own
CBS/BSSE-corrected supermolecular number. I read the first one; I did not independently
open Table 1, so -4.95 keeps its evidence level as this probe's reading and -5.01 is
FIRST-HAND for me.

What `paper/main.md` section 3.2 therefore states, and no more: our own
CCSD(T)/aug-cc-pVTZ counterpoise value at the official S22 initial geometry is -5.203
kcal/mol (`evidence/ccsdt/`), and it is externally consistent with -5.01 kcal/mol quoted
from an open-access full text (DOI `10.3762/bjoc.14.79`) which itself attributes that
number to a primary source we have not opened. Difference 0.19 kcal/mol, with the basis
rung (TZ+diffuse, not CBS) and the geometry convention (initial vs equilibrium) both
pointing the same way, which is why the sentence is "consistent with" and not "agrees to".

The "cannot write the S22 figure" bullet stands unchanged: no number is quoted as
"the S22 CCSD(T)/CBS reference value" anywhere in the paper.
