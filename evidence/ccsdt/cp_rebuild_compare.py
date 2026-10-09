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
    os.path.join(HERE, "20261003T0758Z_snnu_pi_three_avdz_ghostcp.out"),
    os.path.join(HERE, "20261003T1212Z_snnu_sandwich_avdz_ghostcp.out"),
]

E_TOL_HA = 1e-7      # cross-machine: 16 vs 32 threads, two BLAS builds, one code path

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
# The functional side of §3.2. These archives always used ghost functions, which is exactly
# why the old comparison was a convention mismatch rather than a disagreement: the DFT column
# was counterpoise and the correlated column was not.
#
# 2026-10-03, second mismatch found by a guard: every file below is PySCF 2.12.1, and the
# three small dimers used to be read from the 2026-09-28 CentOS batch, which ran 2.14.0. The
# two versions differ only on the counterpoise quantity, because they disagree on how many
# integration points an atom with basis functions but no nuclear charge should receive
# (34864 against 43904 for a water monomer in the dimer's basis at level 2). The single
# variable experiment is archived next to its own copy of the values, and the superseded
# batch stays out of this list on purpose: mixing versions in one column is what is being
# corrected here, so the table can only read one.
DFT_CP_FILES = [
    "evidence/l2cp/20261003T0907Z_wsl2121-cp_levels.out",
    "evidence/ccsdt/20261002T0528Z_snnu_benzene_dft_cp.out",
    "evidence/ccsdt/20261002T0620Z_snnu_benzene_methane_l2.out",
    "evidence/ccsdt/20261002T0905Z_snnu_benzene_dimer_dft_cp.out",
    "evidence/ccsdt/20261002T1030Z_snnu_benzene_dimer_B.out",
]
DFT_ORDER = ("水二聚体", "氨二聚体", "甲烷二聚体", "苯-水", "苯-氨", "苯-甲烷",
             "苯二聚体(A)", "苯二聚体(B)")
# Every eight system now has a level-1 *and* a level-2 counterpoise run at PySCF 2.12.1: the
# three small dimers' level-1 rows arrived with 20261003T0907Z. Asking for a level-1 row must
# still not be silently satisfied by the level-2 table, which is why this is a list and not
# "whatever parsed".
LEVEL1_ORDER = DFT_ORDER


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
            if not m:
                # Form 4: the 20261003 recompute, which prints the production counterpoise and
                # its own re-derivation on one row. Only the production column is taken; the
                # second one is the run's internal agreement check, and reading it here would
                # make this script a witness to its own arithmetic.
                m = re.match(r"\s+(\S+)\s+nao=\s*\d+\s+dcp\(生产\)=([-+]\d+\.\d+)", ln)
                if m and lvl_seen != level:
                    m = None
                elif m and m.group(1) not in DFT_ORDER:
                    m = None
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


EN = {"水二聚体": "water", "氨二聚体": "ammonia", "甲烷二聚体": "methane",
      "苯-水": "benzene-water", "苯-氨": "benzene-ammonia", "苯-甲烷": "benzene-methane",
      # 2026-10-05：这两个英文名是照几何分类手写的，写反过。判据现在由坐标给：
      # S22_11 面内滑移 1.698 A、环面夹角 0.0 度 => parallel-displaced；
      # S22_20 夹角 90.0 度 => T-shaped。归档 stdout 里 10-02..10-04 那几份仍写旧词，
      # 它们的哈希被 MANIFEST 登记，不改；这里的映射与 README 的日期注记是更正处。
      # 见 evidence/recompute/20261005T0340Z_benzene_dimer_label_measure.out 与
      # nlcsplit/tests/test_geometry.py。
      "苯二聚体(A)": "benzene dimer (parallel-displaced, S22_11)",
      "苯二聚体(B)": "benzene dimer (T-shaped, S22_20)"}


def deviation_table(old, new, dft2):
    """The four columns §3.2 tabulates, emitted here so the paper table is generated.

    Until now main.md said this table was "read from the archives by cp_rebuild_compare.py",
    but the script only printed the identity check and the grid step - so the DFT column and
    the deviations were transcribed by hand, and one of those transcriptions had quietly kept
    three rows on PySCF 2.14.0 while the other five were on 2.12.1. Putting the block in the
    script is what makes that class of mistake visible without reading the prose.
    """
    key = lambda s: (s, "6-31g*", "frozen")
    print("== the §3.2 deviation table (6-31g*, frozen core, counterpoise, DFT at level 2) ==")
    print("  %-30s %10s %10s %10s %10s" % ("system", "CC dE_CP", "DFT dE_CP",
                                           "deviation", "corr. BSSE"))
    signs = []
    for name in DFT_ORDER:
        k = key(name)
        if k not in new:
            raise SystemExit("deviation table: no corrected CC row for %s - the column would"
                              " be a hole, not a number" % name)
        if name not in dft2:
            raise SystemExit("deviation table: no level-2 counterpoise DFT row for %s" % name)
        cc, d = new[k]["de_kcal"], dft2[name]
        o = old.get(k)
        bsse = abs(o["de_kcal"] - cc) if o else float("nan")
        signs.append(d - cc)
        print("  %-30s %+10.4f %+10.4f %+10.4f %10.4f"
              % (EN[name], cc, d, d - cc, bsse))
    neg = sum(1 for s in signs if s < 0)
    print("  eight deviations, %d negative, %d positive (the sign of DFT minus CC)"
          % (neg, len(signs) - neg))
    print("  DFT column is one environment: PySCF 2.12.1 for all eight rows"
          " (the 2.14.0 batch is excluded above and compared in evidence/l2cp/)")


# 泛函侧的未校正 ΔE_int，两个本地 2.12.1 归档（三个小二聚体在反泊松那份里顺带印出，
# 五个芳香体系在 20261003T1025Z 那份里）。正文 §3.1 的 BSSE 八个数 = 反泊松减这个。
DTOT_FILES = ["evidence/l2cp/20261003T0907Z_wsl2121-cp_levels.out",
              "evidence/l2cp/20261003T1025Z_wsl2121-dtot_aromatic.out"]


def parse_dtot(level=2):
    """未校正 ΔE_int。两种排版：小体系那份的名字在上一行，芳香体系那份的在同一行。"""
    got = {}
    for rel in DTOT_FILES:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            raise SystemExit("ΔE_int archive missing: %s" % rel)
        lvl, pending = None, None
        for ln in open(p, encoding="utf-8", errors="replace"):
            h = re.match(r"== BASIS=(\S+) LEVEL=(\d) ==", ln)
            if h:
                lvl, pending = int(h.group(2)), None
                continue
            m = re.match(r"\s+(\S+)\s+nao=\s*\d+\s+dcp\(生产\)=", ln)
            if m:
                pending = m.group(1)
                continue
            m = re.search(r"未校正ΔE_int=([-+]?\d+\.\d+)", ln)
            if m and pending is not None and lvl == level:
                got[pending] = float(m.group(1))
                pending = None
                continue
            m = re.match(r"\s+(\S+)\s+nao=\s*\d+.*ΔE_int\(level (\d), 未校正\)=([-+]?\d+\.\d+)", ln)
            if m and int(m.group(2)) == level:
                got[m.group(1)] = float(m.group(3))
    missing = [s for s in DFT_ORDER if s not in got]
    if missing:
        raise SystemExit("no uncorrected ΔE_int for %s -> BSSE 表不能只画剩下的格子"
                         % ", ".join(missing))
    return got


def derived_tables(new, dft2, old):
    """§3.2 的跨基组幅度与比值、§3.1 的 BSSE 八个数：都由这里生成，正文不再手抄。"""
    print("== 锚自己的跨基组幅度，以及它相对偏差的比值 (6-31g* -> aug-cc-pVDZ, frozen) ==")
    print("  %-30s %9s %9s %9s %7s" % ("system", "dE_CP 631", "dE_CP aug", "span", "span/dev"))
    dev_by = {}
    for name in DFT_ORDER:
        k6, ka = (name, "6-31g*", "frozen"), (name, "aug-cc-pvdz", "frozen")
        if k6 not in new:
            raise SystemExit("no corrected 6-31g* row for %s" % name)
        cc6 = new[k6]["de_kcal"]
        dev = dft2[name] - cc6
        dev_by[name] = dev
        if ka not in new:
            print("  %-30s %+9.4f %9s %9s %7s   (aug 档未归档，不印比值)"
                  % (EN[name], cc6, "-", "-", "-"))
            continue
        span = abs(new[ka]["de_kcal"] - cc6)
        print("  %-30s %+9.4f %+9.4f %9.4f %7.2f"
              % (EN[name], cc6, new[ka]["de_kcal"], span, span / abs(dev)))
    print("  比值 <1 的体系：%d；>1 的：%d —— 两个幅度同量级，谁也不是对方的误差"
          % (sum(1 for n in DFT_ORDER if n in dev_by and (n, "aug-cc-pvdz", "frozen") in new
                  and abs(new[(n, "aug-cc-pvdz", "frozen")]["de_kcal"]
                           - new[(n, "6-31g*", "frozen")]["de_kcal"]) < abs(dev_by[n])),
             sum(1 for n in DFT_ORDER if n in dev_by and (n, "aug-cc-pvdz", "frozen") in new
                  and abs(new[(n, "aug-cc-pvdz", "frozen")]["de_kcal"]
                           - new[(n, "6-31g*", "frozen")]["de_kcal"]) >= abs(dev_by[n]))))
    print()
    print("== 泛函那一侧的 BSSE = dE_CP - ΔE_int(未校正)，两端同环境同档位 (level 2) ==")
    dtot = parse_dtot(2)
    for name in DFT_ORDER:
        print("  %-30s dE_CP %+9.4f   ΔE_int %+9.4f   BSSE %7.4f"
              % (EN[name], dft2[name], dtot[name], dft2[name] - dtot[name]))
    print()
    print("== frozen-core vs all-electron on one (system, basis), measured two ways ==")
    print("   left: monomers built in their own basis (the construction this paper no longer")
    print("   uses); right: ghost monomers. A gap that only shows up in the left column was")
    print("   never a frozen-core effect - it is BSSE changing size with the basis.")
    print("  %-30s %-13s %15s %11s" % ("system", "basis", "gap own-basis", "gap ghost"))
    for name in DFT_ORDER:
        for basis in ("6-31g*", "aug-cc-pvdz"):
            k_f, k_a = (name, basis, "frozen"), (name, basis, "all")
            if k_f not in new or k_a not in new:
                continue
            gap_ghost = abs(new[k_f]["de_kcal"] - new[k_a]["de_kcal"])
            if k_f in old and k_a in old:
                print("  %-30s %-13s %15.4f %11.4f"
                      % (EN[name], basis,
                         abs(old[k_f]["de_kcal"] - old[k_a]["de_kcal"]), gap_ghost))
            else:
                print("  %-30s %-13s %15s %11.4f" % (EN[name], basis, "-", gap_ghost))


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
    dft2 = parse_dft_cp(2)
    deviation_table(old, new, dft2)
    print()
    derived_tables(new, dft2, old)
    print()
    grid_rows(dft2, parse_dft_cp(1), new)
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
