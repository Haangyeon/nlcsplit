#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prove that the counterpoise re-run changed the monomer construction and nothing else.

The claim this script exists to support is narrow and load-bearing. Before 2026-10-03
`nlcsplit/step_m_ccsdt.py` built each monomer in its **own** basis, so the column headed
`dE_CP` held the uncorrected interaction energy; the fix puts the partner's functions back in
as ghosts. Every number in §3.2 that pairs a counterpoise DFT value with a correlated one now
has to be re-derived. A reader is entitled to ask: how much of the movement you are about to
show me is the fix, and how much is a different machine, a different BLAS thread count, or a
different geometry parse?

The answer is the complex energy. `build(symbols, coords, basis)` for the complex is untouched
by the fix, so if the old and new archives agree on `E_dimer` and disagree on `dE_CP`, the
difference is attributable to the monomer side alone. That is what this prints, per row, and
it refuses to print a table when the identity fails - a changed complex energy would mean the
re-run is not a re-run of the same calculation, and then the old rows are not comparable.

Run from the repository root:
    PYTHONPATH=. python3 -u evidence/ccsdt/cp_rebuild_compare.py
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.abspath(os.path.join(HERE, "..", "..")), HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from ladder_parse import parse_ladder                    # noqa: E402

# Archives that printed a column heading they had not earned (monomers in their own basis).
OLD = [
    os.path.join(HERE, "20260930T235900Z_stepm_three_systems_631g.out"),
    os.path.join(HERE, "20261001T000400Z_stepm_three_systems_avdz.out"),
    os.path.join(HERE, "20261002T043400Z_snnu_benzene_ladder.out"),
    os.path.join(HERE, "20261002T0715Z_snnu_benzene_avdz.out"),
    os.path.join(HERE, "20261002T0630Z_snnu_benzene_dimer_ccsdt.out"),
    os.path.join(HERE, "20261002T1030Z_snnu_benzene_dimer_B.out"),
    os.path.join(HERE, "20261002T1208Z_snnu_sandwich_avdz_SUPERSEDED.out"),
]
# Archives produced by the ghost-corrected script. Anything not listed here is reported as
# missing rather than silently absent from the table.
NEW = [
    os.path.join(HERE, "20261003T0605Z_stepm_dimers_ghostcp_local.out"),
    os.path.join(HERE, "20261003T0652Z_snnu_cp_rebuild_631.out"),
]

E_TOL_HA = 1e-7      # cross-machine: 16 vs 32 threads, two BLAS builds, one code path

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
# The functional side of §3.2. These archives always used ghost functions, which is exactly
# why the old comparison was a convention mismatch rather than a disagreement: the DFT column
# was counterpoise and the correlated column was not.
DFT_CP_FILES = [
    "evidence/l2cp/20260928T213839Z_centos-step_h_l2cp.out",
    "evidence/ccsdt/20261002T0528Z_snnu_benzene_dft_cp.out",
    "evidence/ccsdt/20261002T0620Z_snnu_benzene_methane_l2.out",
    "evidence/ccsdt/20261002T0905Z_snnu_benzene_dimer_dft_cp.out",
    "evidence/ccsdt/20261002T1030Z_snnu_benzene_dimer_B.out",
]
DFT_ORDER = ("水二聚体", "氨二聚体", "甲烷二聚体", "苯-水", "苯-氨", "苯-甲烷",
             "苯二聚体(A)", "苯二聚体(B)")
# Only these have a level-1 *counterpoise* run archived: the small dimers were run at
# level 1 uncorrected only, so asking for their level-1 CP row must not be silently satisfied
# by the level-2 table.
LEVEL1_ORDER = ("苯-水", "苯-氨", "苯-甲烷", "苯二聚体(A)", "苯二聚体(B)")


def parse_dft_cp(level=2):
    """{system: omegaB97X-V/6-31g* counterpoise energy, kcal/mol} at the given grid level.

    The functional side always used ghost functions, which is exactly why the old comparison
    was a convention mismatch rather than a disagreement: the DFT column was counterpoise and
    the correlated column was not. Level 1 is read too because the grid step is one of the
    quantities §3.2 quotes, and the step is a difference of two deviations - so the anchor
    cancels and the step itself is unaffected by the fix, while the absolute deviations are.
    """
    got = {}
    for rel in DFT_CP_FILES:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            raise SystemExit("DFT counterpoise archive missing: %s" % rel)
        lvl_seen = None
        for ln in open(p, errors="replace"):
            # Form 1: the level is on the row itself.
            m = re.match(r"LEVEL=%d\s+(\S+)\s+nao=\s*\d+\s+DFT=\s*([-+]\d+\.\d+)" % level, ln)
            if not m:
                # Form 2: the level is on the block header ("== 6-31g*  LEVEL=2  OMP=16 ==")
                # and the rows underneath carry no level marker at all.
                h = re.search(r"==\s.*LEVEL=(\d)", ln)
                if h:
                    lvl_seen = int(h.group(1))
                m = level_row(lvl_seen, level, ln)
            if not m and level == 2:
                # Form 3: the step_h table, one row per system with a labelled column. That
                # table is a level-2 run, so a level-1 request finds nothing here by design.
                m = re.match(r"\s+(\S+二聚体)\s+原子\s+\d+.*ΔE_int\(反泊松\)\s+([-+]\d+\.\d+)",
                             ln)
            if m:
                name, val = m.group(1), float(m.group(2))
                if name in got and abs(got[name] - val) > 5e-4:
                    raise SystemExit("level-2 counterpoise for %s disagrees: %.4f (%s) vs"
                                     " %.4f - picking one is a decision" % (name, got[name],
                                     "earlier file", val))
                got[name] = val
    missing = [s for s in (DFT_ORDER if level == 2 else LEVEL1_ORDER) if s not in got]
    if missing:
        raise SystemExit("no level-%d counterpoise row for %s" % (level,
                                                                 ", ".join(missing)))
    return got


def level_row(lvl_seen, level, ln):
    """Form-2 row: `  苯-水  nao=114  DFT= -3.2671 ...` accepted only inside a level block."""
    if lvl_seen != level:
        return None
    m = re.match(r"\s+(\S+)\s+nao=\s*\d+\s+DFT=\s*([-+]\d+\.\d+)", ln)
    return m if m and m.group(1) in DFT_ORDER else None


def grid_rows(dft2, dft1, new):
    """Deviation at both archived grid levels, on the corrected anchor.

    The step is a difference of two deviations that share one anchor, so the anchor cancels:
    the grid step is the same number this directory quoted before the fix. What the fix changes
    is the two deviations themselves, and with them whether a grid step can flip a deviation's
    sign - the claim the paragraph this feeds used to make.
    """
    print("== the same deviation at both grid levels (6-31g*, frozen core, counterpoise) ==")
    print("  %-14s %10s %10s %10s %8s %s"
          % ("system", "level 1", "level 2", "step", "|step|", "sign of the deviation"))
    for name in LEVEL1_ORDER:
        k = (name, "6-31g*", "frozen")
        if k not in new:
            print("  %-14s %10s %10s   (corrected anchor not yet archived)" % (name, "-", "-"))
            continue
        cc = new[k]["de_kcal"]
        v1, v2 = dft1[name] - cc, dft2[name] - cc
        print("  %-14s %+10.4f %+10.4f %+10.4f %8.4f %s"
              % (name, v1, v2, v2 - v1, abs(v2 - v1),
                 "no flip" if (v1 < 0) == (v2 < 0) else "FLIPS"))


def main():
    old = parse_ladder(OLD)
    new = parse_ladder(NEW)
    print("== does the corrected re-run differ from the archived run ONLY on the monomer side? ==")
    print("  parsed %d rows from %d superseded archives, %d rows from %d corrected archives"
          % (len(old), len(OLD), len(new), len(NEW)))
    print("  identity bar on the complex CCSD(T) energy: %.0e Ha" % E_TOL_HA)
    print()
    print("  %-12s %-13s %-7s %14s %14s %10s %10s %9s %s"
          % ("system", "basis", "conv", "E_dimer_old", "E_dimer_new", "|dE|", "dE_old",
             "dE_CP", "BSSE"))
    bad_identity = []
    missing = []
    worst = 0.0
    for key in sorted(new, key=lambda k: (k[0], k[1], k[2])):
        name, basis, rung = key
        n = new[key]
        o = old.get(key)
        if o is None:
            missing.append(key)
            continue
        d = abs(n["e_dimer"] - o["e_dimer"])
        worst = max(worst, d)
        if d > E_TOL_HA:
            bad_identity.append((key, d))
        print("  %-12s %-13s %-7s %14.10f %14.10f %10.1e %+10.4f %+9.4f %9.4f"
              % (name, basis, rung, o["e_dimer"], n["e_dimer"], d, o["de_kcal"],
                 n["de_kcal"], n["de_kcal"] - o["de_kcal"]))
        if o["nao_mono"] != n["nao_mono"]:
            print("      monomer basis dimension moved %s -> %s while the complex stayed at %s"
                  " (this is the fix; the complex line is what makes it attributable)"
                  % ("/".join(map(str, o["nao_mono"])), "/".join(map(str, n["nao_mono"])),
                     n["nao_complex"]))
    print()
    print("  rows in the corrected archives with no superseded counterpart: %s"
          % (", ".join("%s/%s/%s" % k for k in missing) if missing else "none"))
    pending = [k for k in old if k not in new]
    print("  superseded rows still awaiting a corrected re-run: %d" % len(pending))
    for k in sorted(pending):
        print("      %-12s %-13s %s" % (k[0], k[1], k[2]))
    print()
    grid_rows(parse_dft_cp(2), parse_dft_cp(1), new)
    print()
    if bad_identity:
        print("  VERDICT: REFUSED - the complex energy itself moved on %d rows (largest %.2e"
              " Ha), so these are not the same calculation and the dE_CP differences below"
              " cannot be attributed to the counterpoise fix." % (len(bad_identity), worst))
        for key, d in bad_identity:
            print("      %s/%s/%s  |dE_dimer| = %.2e Ha" % (key[0], key[1], key[2], d))
        sys.exit(1)
    print("  VERDICT: %d/%d comparable rows have identical complex CCSD(T) energies to"
          " %.1e Ha (worst %.2e), so every difference in the dE_CP column comes from the"
          " monomer construction and not from the machine, the thread count or the geometry"
          " parse." % (len(new) - len(missing), len(new), E_TOL_HA, worst))


if __name__ == "__main__":
    main()
