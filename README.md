# nlcsplit

Fragment and pair resolution of the VV10 nonlocal-correlation energy.

Functionals that pair a range-separated hybrid with a VV10 nonlocal term - ωB97X-V and
ωB97M-V above all - are routine for non-covalent interactions. The term itself,

$$
E_{\mathrm{NL}} = \frac{1}{2}\iint \rho(\mathbf r)\,\rho(\mathbf r')\,\Phi(\mathbf r,\mathbf r')\,d^3r\,d^3r'
$$

is a two-centre object, but production codes evaluate it by collapsing the pair sum into
per-point values, which discards the pair index. `nlcsplit` evaluates the double sum
explicitly on the host program's integration grid and attributes every grid point to atoms and
fragments through a real-space partition, so the nonlocal contribution separates into
intra-fragment and inter-fragment blocks that add back to the total:

$$
E_{\mathrm{NLC}} = \sum_A E^{\mathrm{intra}}_A + \sum_{A<B} E^{\mathrm{inter}}_{AB}.
$$

Pure Python and NumPy on top of [PySCF](https://pyscf.org). Apache-2.0. No GAMESS source is
included, linked or required.

## Install

```bash
pip install .                                   # needs numpy and pyscf>=2.12
python -m pytest -q -m "not slow"               # the non-slow subset (58 today)
python -m pytest -q                             # everything (79 today), incl. SCF-based tests
```

Those two counts are not typed here from memory: `evidence/release_qa/test_count_census.py`
re-collects the suite and archives its printout, with per-module rows that must sum to the
total (`evidence/release_qa/20261009T105424Z_test_count_census.out`: 79 collected, 58 non-slow
plus 21 slow). The published wheel carries 59 of those 79 - 39 members, eight test modules
(`evidence/release_qa/20261009T113844Z_shipping_wheel_census.out`, which names the wheel it counted:
`7bdcb6f6...`). Twenty stay out: they are the
tests of `nlcsplit/fastpair_ide.py`, a peer's frozen reference implementation that is deliberately
not distributed, and that reason is named in the export tool's `INTERNAL_ONLY_MODULES` so the gap
is a stated exclusion rather than a silence. Installed out of tree, the wheel's own suite is
56 passed and 3 skipped in 404.44 s, exit 0
(`evidence/release_qa/20261009T113900Z_wheel_out_of_tree.out`, whose header carries that same
`7bdcb6f6...` hash, and whose exit code is kept in a file of its own beside it); the three skips
want the official S22 geometries, which are not in the wheel. Those two archives name one build,
`7bdcb6f6...`, and it is deliberately not promised as the wheel that will carry this sentence:
pyproject.toml sets readme = "README.md", so the bytes of this file go into the wheel's METADATA and
any hash written here necessarily describes a build made from an earlier draft of it. What is stable
is content, and that is checked rather than claimed - `evidence/release_qa/20261009T120455Z_wheel_member_diff.out`
compares the measured build against the build produced by the next run of the export: both have 39 members, 37 of
their per-member digests agree, all 34 Python modules under nlcsplit/ (tests included) are
byte-identical, and the two that differ are METADATA and the RECORD that lists METADATA's own digest.
Until today the shipped test list had also dropped
`nlcsplit/tests/test_nlc_closure.py` - the closure guard and the two regroupings that must make
it fail - and the export gate said so in terms ("pip install . would install it, the wheel has no
reason not to"), so it ships now and its five tests are among the 56.

## Quickstart

```python
from pyscf import gto
from nlcsplit import partition, nlc, geomlib

mol = gto.M(atom=geomlib.h2o_dimer(), basis="6-31g*", unit="Angstrom", verbose=0)
mf, *_  = partition.scf_grid(mol, xc="wb97x_v", level=1, basis="6-31g*")
b, C      = mf._numint.nlc_coeff("wb97x_v")[0][0]
coords, weights, owner = partition.atom_partition(mol, level=1, scheme="becke")
ao        = mf._numint.eval_ao(mol, coords, deriv=1)
rho       = mf._numint.eval_rho(mol, ao, mf.make_rdm1(), xctype="GGA")
sigma     = rho[1]**2 + rho[2]**2 + rho[3]**2

res = nlc.fragment_decomposition(coords, weights, rho[0], sigma,
                                 geomlib.FRAGS["(H2O)2"], b=b, C=C, owner=owner)
```

Output (ωB97X-V/6-31G\*, water dimer, grid level 1, kcal/mol) - the same numbers
`nlcsplit/examples/quickstart.py` prints, re-run verbatim from the source tree and archived
as `evidence/release_qa/20261003T1901Z_quickstart_readme_example.out`:

```
inter[(0,1)] = -0.5237      intra = -3.5457  -3.7437
E_nl = -7.8130    E_loc = 60.8303    E_total = 53.0172
```

$E_{\mathrm{loc}} = \beta\int\rho$, with $\beta=(1/32)(3/b^2)^{3/4}$, is exactly one-body,
since $\int\rho$ is the electron number, so it cancels identically from any superposition
difference. An inter-fragment
decomposition therefore needs no convention for splitting a local energy density; it is a
property of the pair sum alone. The absolute local term of one fragment is nonetheless
β·N_A, and its spread across partition schemes is 3.0415 kcal/mol per electron - reported
as a limitation, not hidden.

## Conventions

The kernel fields are read from PySCF rather than hard-coded:

$$
w_0=\sqrt{C\,\sigma^2/\rho^4+\tfrac{4\pi}{3}\rho},\qquad
\kappa=b\,\tfrac{3\pi}{2}\left(\tfrac{\rho}{9\pi}\right)^{1/6},\qquad
g = w_0(\mathbf r_i)R^2+\kappa(\mathbf r_i),\qquad
\Phi=-\frac{3}{2\,g\,g'\,(g+g')}
$$

* **Same-centre pairing** (both factors at the same grid point) is the convention that
  reproduces the native kernel. The cross-paired variant is kept as a definition-sensitivity
  control; it shifts monomer energies by 0.1379 (water), 0.4182 (argon) and 0.1346 (methane)
  kcal/mol at level 1 and 0.9057 for benzene at level 0, and it is not a harmless re-indexing.
* **Half blocks.** `pair_energy(A,B)` returns the half block
  $\tfrac{1}{2}\sum_{i\in A}\sum_{j\in B}$; `inter[(A,B)]` is reported as twice that, which
  is what makes the additivity identity above hold.
* **Density floor.** Points below ρ = 1e-12 are dropped from the pair sum. Sweeping the floor
  from 1e-8 to 1e-16 moves the inter-fragment term by at most 2.1e-11 Ha at level 1 and
  4.2e-11 Ha at level 2, while discarding 10.7-22.6% of the points and at most 2.3e-6
  electrons - an implementation detail, not a tunable parameter.
* **Soft attribution** must be fed the partitioned weights, not the raw `base_w` returned by
  `partition_factors`; the latter is not a spatial measure. `nlcsplit/tests/test_partition_factors.py`
  pins both this and the two internal assertions.

## What checks it

| Referee | Result |
|---|---|
| Against PySCF's own native VV10 kernel, one grid and one density | 1.0e-08 and 1.5e-08 Ha |
| Block additivity, five partitions and two repeated schemes (water dimer, level 1) | 1.73e-18 to 6.94e-18 Ha |
| Against a second program - ORCA 6.0.1 `NL Energy, E(C,NL)`, same quantity, geometry and basis, eight S22 systems | 0.067-0.952%, max 0.0416 kcal/mol |
| Attribution choice (four partitions, eight systems) | 0.0040-0.2470 kcal/mol, no ordering by interaction type or size |

Every number above is regenerated by a named script and its archived standard output lives
under `evidence/` with a SHA-256 manifest; the provenance appendix that maps each table to
the script and artefact producing it ships as `docs/tables_and_provenance.md` (built from
`MAIN-skeleton.md`).

## What it is not

* **Not the dispersion energy.** The share of ΔE_xc carried by the nonlocal term is
  system- and geometry-dependent (16% for the water dimer at the official S22 geometry; 97%
  and 52% for two geometries of the benzene dimer). Where the two parts carry opposite signs
  the ratio is meaningless, and the package refuses to state a share in that case
  (`|ΔE_NLC/ΔE_xc| > 2` reports the two absolute terms instead). It performs no SAPT/EDA-style
  decomposition and does not separate electrostatics from exchange repulsion.
* Not a geometry optimizer (gradients appear only as internal validation), and not rVV10:
  only the σ form of w0 is implemented.

## Layout

```
nlcsplit/nlc.py           VV10 fields, pair_energy, fragment_decomposition
nlcsplit/partition.py     four attribution schemes, partition_matrix, partition_factors
nlcsplit/geomlib.py       geometry of record, covalent fragment splitting, S22 loader
nlcsplit/step_*.py        one script per table; stdout archived UTC-stamped
nlcsplit/tests/           kernel, regression, geometry and partition-factor suites
```

## Cite and license

`CITATION.cff` carries the citation metadata. Released under Apache-2.0; see `LICENSE`.
