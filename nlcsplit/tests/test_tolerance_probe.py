"""Measure the residual that `test_regression.py:46` allows at 0.10 kcal/mol.

This is a probe, not a tightening: the assertion here is deliberately the same loose bound
the existing test uses, so this file cannot turn the suite red by itself. The point is to
get the distribution on record - across grid levels and across systems - so the choice of a
real tolerance is made from measured spread instead of from what someone happened to get
away with when the test was written.

Context for why 0.10 is suspected loose: the cross-program anchor against ORCA 6.0.1 puts
the agreement on the *reported* quantity at 4e-4 kcal/mol (water dimer), and the two
internal implementations of the double sum agree to <=3e-5 kcal/mol at level 1. A guard
that is 3 orders of magnitude looser than both cannot fail for any reason a reviewer would
care about, and it will not catch a real regression either.
"""
import pytest

from nlcsplit import geomlib, nlc, partition

KCAL = 627.509474
BASIS = "6-31g*"
LEVELS = (0, 1, 2)


@pytest.fixture(scope="module")
def dimer():
    gto = pytest.importorskip("pyscf.gto")
    return gto.M(atom=geomlib.h2o_dimer(), basis=BASIS, verbose=0, unit="Angstrom")


def _residual(mol, level):
    """(ours - native) in kcal/mol, alongside both totals so the sign is checkable."""
    from pyscf.dft import numint
    mf, X, W, rho, sig = partition.scf_grid(mol, xc="wb97x_v", level=level, basis=BASIS)
    b, C = mf._numint.nlc_coeff("wb97x_v")[0][0]
    res = nlc.fragment_decomposition(X, W, rho, sig, geomlib.FRAGS["(H2O)2"],
                                     b=b, C=C,
                                     owner=partition.nearest_partition(mol, X))
    _, e_ref, _ = numint.nr_nlc_vxc(mf._numint, mol, mf.grids, "wb97x_v", mf.make_rdm1())
    return (res["E_total"] - e_ref) * KCAL, res["E_total"] * KCAL, e_ref * KCAL


@pytest.mark.slow
def test_L8_residual_distribution(dimer):
    print(f"\n{'lvl':>3} {'ours(kcal)':>14} {'native(kcal)':>14} {'diff(kcal)':>12} "
          f"{'rel':>10}")
    rows = []
    for level in LEVELS:
        d, ours, ref = _residual(dimer, level)
        rows.append((level, d))
        print(f"{level:>3} {ours:>14.6f} {ref:>14.6f} {d:>+12.3e} "
              f"{abs(d) / abs(ours):>10.2e}")
    spread = max(abs(d) for _, d in rows)
    print(f"    max |diff| over levels {LEVELS} = {spread:.3e} kcal/mol")
    print(f"    existing guard at test_regression.py:46 = 1.0e-01 kcal/mol"
          f"  -> measured residual is {0.10 / spread:.1f}x smaller than allowed")
    # Deliberately the same bound the shipped test uses, so this probe cannot fail a build.
    assert spread < 0.10
