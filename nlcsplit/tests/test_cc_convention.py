"""Frozen-core convention guard for the coupled-cluster script (pure logic, no SCF).

Why this file exists rather than a comment. `step_m_ccsdt.py` reports the water-dimer
counterpoise interaction energy at two conventions - frozen oxygen 1s and all-electron.
The first version switched the convention on the dimer while leaving the monomers frozen,
which printed -23.16 kcal/mol for the water dimer. No exception was raised and no
assertion fired: both numbers on either side of that difference are individually
plausible energies, and only the difference is impossible. The failure was structural
(two different conventions feeding one subtraction), so the guard is structural too.

The pure-logic tests below do not recompute anything. They pin the invariant the
counterpoise difference needs - the frozen-orbital counts must sum from the fragments to
the united set, at every convention rung, and the monomers must be evaluated in the
complex's basis - and they re-create each broken pairing once, deliberately, to show the
invariant has teeth. A guard that cannot fail is not evidence. The one `slow` test does
recompute, on the water dimer, because the basis invariant has a numeric consequence
(-4.8789 against -6.8559) and that is the price of proving the two constructions are
different quantities rather than different spellings of one.
"""

import pytest

from nlcsplit import geomlib
from nlcsplit.step_m_ccsdt import (build, correlated, cp_frag_specs, freeze_count,
                                   freeze_plan)


@pytest.fixture(scope="module")
def dimer_split():
    atoms, frags = geomlib.h2o_dimer(), geomlib.FRAGS["(H2O)2"]
    symbols = [a[0] for a in atoms]
    return symbols, [[symbols[i] for i in f] for f in frags]


def test_core_count_is_per_element_and_zero_for_hydrogen():
    assert freeze_count(["O"]) == 1
    assert freeze_count(["H", "H"]) == 0
    assert freeze_count(["O", "H", "H"]) == 1
    # the three-system ladder also runs ammonia and methane, so N and C must count exactly
    # like O; an element silently missing from the table would freeze nothing and quietly
    # change every number in that row
    assert freeze_count(["N"]) == 1
    assert freeze_count(["C"]) == 1
    assert freeze_count(["N", "H", "H", "H"]) == 1
    assert freeze_count(["C", "H", "H", "H", "H"]) == 1


def test_frozen_plan_sums_from_fragments_to_the_united_set(dimer_split):
    symbols, frag_syms = dimer_split
    whole = freeze_plan([symbols])[0]
    parts = freeze_plan(frag_syms)
    assert sum(parts) == whole, (
        "counterpoise difference mixes conventions: fragments freeze %s, "
        "the complex freezes %d" % (parts, whole))
    assert parts == [1, 1] and whole == 2       # one O per water, two in the dimer


def test_all_electron_plan_freezes_nothing_anywhere(dimer_split):
    symbols, frag_syms = dimer_split
    assert freeze_plan([symbols], all_electron=True)[0] == 0
    assert freeze_plan(frag_syms, all_electron=True) == [0, 0]
    # the invariant still has to hold in that rung, which is the property the bug broke
    assert sum(freeze_plan(frag_syms, all_electron=True)) == \
        freeze_plan([symbols], all_electron=True)[0]


def test_the_broken_pairing_does_violate_the_invariant(dimer_split):
    """Falsification for the guard above: the old code path must be detectable.

    `mono_fz = coreO if fz else [0, 0]` combined a united-set count of 0 (all-electron
    dimer) with fragment counts of [1, 1] (still frozen). Asserting that this mismatch
    is caught is what stops the passing test above from being decoration.
    """
    symbols, frag_syms = dimer_split
    united_ae = freeze_plan([symbols], all_electron=True)[0]
    fragments_still_frozen = freeze_plan(frag_syms, all_electron=False)
    assert sum(fragments_still_frozen) != united_ae
    # and the difference is not a rounding matter: it is a whole shell on each side
    assert sum(fragments_still_frozen) - united_ae == 2


# ---- the other convention the same subtraction needs: the counterpoise basis --------
# Added 2026-10-02. This file guarded frozen-core pairing and said nothing about whether
# the monomers carry the partner's basis functions, and that hole was worth more than the
# one it covered: the water dimer's CCSD(T) column read -6.8559 because each monomer was
# computed in its own basis, while with the partner present as ghosts the same run gives
# -4.8789. 1.98 kcal/mol, i.e. enough to turn "the functional is too shallow" into
# "too deep" - and it survived every cross-program check, because the other program was
# being fed the same uncorrected construction.


def _h2o_dimer_atoms():
    atoms = geomlib.h2o_dimer()
    return [a[0] for a in atoms], [a[1] for a in atoms], geomlib.FRAGS["(H2O)2"]


def test_cp_frag_specs_put_the_partner_in_as_ghost_functions():
    symbols, coords, frags = _h2o_dimer_atoms()
    specs = cp_frag_specs(symbols, coords, frags)
    assert len(specs) == len(frags)
    for (syms, crds), f in zip(specs, frags):
        assert len(syms) == len(symbols) == len(crds)
        real = [s for s in syms if not s.startswith("ghost-")]
        ghosts = [s for s in syms if s.startswith("ghost-")]
        assert real == [symbols[i] for i in f]
        assert len(ghosts) == len(symbols) - len(f)
        assert crds == coords                      # same geometry, nothing shifted


def test_the_ghostless_construction_is_a_different_thing():
    """Falsification: the shape that shipped is detectable by the test above."""
    symbols, coords, frags = _h2o_dimer_atoms()
    old = [[symbols[i] for i in f] for f in frags]
    new = [syms for syms, _ in cp_frag_specs(symbols, coords, frags)]
    assert [len(x) for x in old] == [3, 3]                 # half the atoms, half the basis
    assert all(len(x) == len(symbols) for x in new)        # 6 entries, 3 of them ghosts


@pytest.mark.slow
def test_water_dimer_ccsdt_counterpoise_and_its_bsse():
    """The real path, one number each, and the basis dimension that distinguishes them.

    On the **official S22 geometry**, not the constructed one: the archived -6.8559 and the
    -4.8789 it is compared against are both S22_02 numbers, and the two geometries differ by
    enough to make the assertion meaningless. Tolerances are set by the four decimals the
    archives print, not by taste.
    """
    import os
    pytest.importorskip("pyscf")
    d = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                     "scratch", "lit", "s22")
    if not os.path.isdir(d):
        pytest.skip("S22 官方几何未取回（跑 nlcsplit/tools/get_s22.sh）")
    atoms, frags = geomlib.s22_system("水二聚体", d)
    symbols = [a[0] for a in atoms]
    coords = [a[1] for a in atoms]
    basis = "6-31g*"
    dim = build(symbols, coords, basis)
    mono = [build(s, c, basis) for s, c in cp_frag_specs(symbols, coords, frags)]
    bare = [build([symbols[i] for i in f], [coords[i] for i in f], basis) for f in frags]
    for m in mono:
        assert m.nao_nr() == dim.nao_nr()
        assert m.nelectron < dim.nelectron
    for m in bare:                       # pin the buggy shape so it cannot come back quietly
        assert m.nao_nr() != dim.nao_nr()
    frag_syms = [[symbols[i] for i in f] for f in frags]
    ed = correlated(dim, freeze_plan([symbols])[0])
    em = [correlated(m, c) for m, c in zip(mono, freeze_plan(frag_syms))]
    eb = [correlated(m, freeze_plan([s])[0]) for m, s in zip(bare, frag_syms)]
    K = 627.509474
    cp = (ed["CCSD(T)"][0] - sum(x["CCSD(T)"][0] for x in em)) * K
    un = (ed["CCSD(T)"][0] - sum(x["CCSD(T)"][0] for x in eb)) * K
    assert cp == pytest.approx(-4.8789, abs=2e-3)
    assert un == pytest.approx(-6.8559, abs=2e-3)
    assert abs(cp - un) > 1.0            # the BSSE is ~2 kcal/mol, not a rounding matter
