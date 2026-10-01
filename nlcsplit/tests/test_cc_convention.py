"""Frozen-core convention guard for the coupled-cluster script (pure logic, no SCF).

Why this file exists rather than a comment. `step_m_ccsdt.py` reports the water-dimer
counterpoise interaction energy at two conventions - frozen oxygen 1s and all-electron.
The first version switched the convention on the dimer while leaving the monomers frozen,
which printed -23.16 kcal/mol for the water dimer. No exception was raised and no
assertion fired: both numbers on either side of that difference are individually
plausible energies, and only the difference is impossible. The failure was structural
(two different conventions feeding one subtraction), so the guard is structural too.

These tests do not recompute anything. They pin the invariant the counterpoise
difference needs - the frozen-orbital counts must sum from the fragments to the united
set, at every convention rung - and they re-create the broken pairing once, deliberately,
to show the invariant has teeth. A guard that cannot fail is not evidence.
"""

import pytest

from nlcsplit import geomlib
from nlcsplit.step_m_ccsdt import freeze_count, freeze_plan


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
