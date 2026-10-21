#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Grid-convergence table for the cross-scheme attribution spread (read-only).

Why this exists
---------------
External review (2026-10-20, referee MCP) named one cheap move that would change the tier
assessment: establish whether the partition-scheme spread survives *adequate grid convergence*.
The raw material is scattered over `evidence/common_grid/*hirshfeld_crossfamily*.out`, but nobody
had put the rungs next to each other -- so the answer was being asserted from two hand-read numbers
instead of recomputed.

Two confounds this script is built to refuse
-------------------------------------------
(1) TWO `nlcsplit/partition.py` VERSIONS ARE ARCHIVED HERE. Read the header line
    "# sha256 nlcsplit/partition.py" in each file: the runs of 2026-10-09/10 carry one hash, the
    "after_unitfix" runs from 2026-10-12 on (and the 2026-10-21 level-0/level-2 runs) carry another.
    The same level-1 water grid was measured under both, and diffing those two files shows the
    family-internal span agrees while the all-six span does not. A ladder that crosses the hash
    boundary is not a grid ladder -- the rung difference is confounded with a code difference. So
    every step here is grouped by (partition hash, system), and a single-rung group is reported as
    NOT MEASURED instead of being filled in from the other version.
(2) SAME-LEVEL REPEATS ARE NOT RUNGS. Two files can measure the same system at the same level;
    that is a repeatability check. Only strictly increasing levels feed the convergence gate.

What counts as an admissible archive
------------------------------------
    FINAL  = the `.out` carries its own `# exit=` line, a sibling `.rc` exists, and the two agree
             and read as the script's success code.  A half-written file, or one whose exit line
             disagrees with its `.rc`, is EXCLUDED and listed -- this repository has already had a
             truncated startup artifact sit in a directory full of good ones.
    SUPERSEDED = listed in the table below by exact basename, with the reason printed. Nothing is
             dropped silently; every file the glob saw is accounted for in the output.

Judgement, fixed before the level-2 datum landed
------------------------------------------------
* Primary quantity = family-internal span: the four deterministic becke-family schemes only. The
  all-six span contains the Hirshfeld column, whose thread dependence is documented in this
  repository (`nlcsplit/partition.py` builds free atoms with UHF and no spherical averaging) and
  none of these archives record a thread count -- so the all-six span is printed as indicative and
  the repeatability line for it, never as the convergence criterion.
* Tolerance = GATE below, set to the same value the runner's own census guardrail uses in these
  archives (see the "护栏" line of any level-1 file). An absolute energy, borrowed from an
  independent on-file gate, not a function of the knob being tested. No percentage-of-itself
  criterion: a tiny denominator lets a ratio jump bands after the fact.
* Spans are recomputed from the printed `E_AB` columns and tied out against the printed spans,
  allowing one unit in the last place of the four-decimal print, so a parse that grabs the wrong
  rows cannot pass.

Exit codes -- the code itself is a claim, so they are printed on every run
-------------------------------------------------------------------------
    0 = every admissible ladder has >= 2 distinct levels and all adjacent deltas within the gate
    3 = measurement succeeded and at least one adjacent delta EXCEEDS the gate (a real finding)
    2 = cannot measure: an admissible system has < 2 distinct levels, a file will not parse, or an
        archive's exit evidence is inconsistent.  With --ladders-only the single-rung groups are
        still printed as a coverage statement but no longer set this code; the two invocations are
        two different claims -- the full set, and only the systems that have a same-code ladder
    4 = uncaught exception (never 1, because elsewhere in this package exit 1 means "designed pass")

Nothing is written except the file named by --write. The archives are opened read-only.
"""
import argparse
import fnmatch
import hashlib
import os
import re
import sys


def _die_on_crash(t, v, tb):
    import traceback
    traceback.print_exception(t, v, tb, None, sys.stderr)
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    finally:
        os._exit(4)


sys.excepthook = _die_on_crash

# The system names in these archives are Chinese; a cp936 console kills the process on the write
# direction, so the archive text must land before any decorative print can fail.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RE_LEVEL = re.compile(r"^# level = (\d+)\b")
RE_PSHA = re.compile(r"^# sha256 nlcsplit/partition\.py\s*=\s*([0-9a-f]{64})")
RE_HEAD = re.compile(r"^# git HEAD\s+(\S+)")
RE_BLOCK = re.compile(r"^== (\S.*?)\s+level=(\d+)\s+原子\s+(\d+)\s+公共网格\s+N=(\d+)")
RE_ROW = re.compile(r"^\s+(家族内 \S+|Voronoi\S*|Hirshfeld\S*|（对照，不计入判据）等权 \S+)"
                    r"\s+E_AB =\s*(-?\d+\.\d+)\s+E_NL =\s*(-?\d+\.\d+)")
RE_SPAN_FAM = re.compile(r"家族内跨度 =\s*(-?\d+\.\d+)")
RE_SPAN_ALL = re.compile(r"总跨度 =\s*(-?\d+\.\d+)")
RE_TIME = re.compile(r"用时 ([\d.]+) s")

GATE = 0.005     # kcal/mol; same value as the census guardrail printed in these archives
PRINTED_DP = 4   # the archives print four decimals
MAX_ULP = 1      # tie-out in whole units of the last printed digit; see the ulp note below
SUCCESS_RC = 0

# The grid level that the certificate archives in this directory declare in their own headers,
# established by census of those headers rather than by me.  A rung below it is not what the
# convergence question is about, so a top pair containing one is reported as NOT MEASURED.
PUBLISHED_LEVEL = 1

# Why one unit of the last printed digit is the right tie-out, and why it is not a free parameter.
# Each span in an archive is printed from full-precision internals, while this script recomputes it
# from two independently rounded endpoints; the two can differ by at most one last digit. The
# archives do show exactly that -- the four benzene-family cells in
# 20261010T061455Z_hirshfeld_crossfamily_l1_benzex.out and
# 20261009T193232Z_hirshfeld_crossfamily_l1_benzene_dimers.out print a span whose last digit
# disagrees with the difference of their own printed endpoints, and the identical offsets reappear
# in the "_after_unitfix" copies of the same cells, so they are arithmetic, not a code change. This
# is the same convention the certificates already use: see the tie-out block of
# 20261015T113349Z_s22_full_band_columns.out, which reports its maximum deviation and how many
# items exceeded tolerance. Comparing in integer last-digits instead of floats keeps the bound
# float-safe.

# Archives kept on disk for provenance but not admissible as ladder rungs, with the reason.
SUPERSEDED = {
    "20261009T152500Z_hirshfeld_crossfamily_l1_small.out":
        "run before the grid-coordinate fix; its out-of-family columns are the wrong-unit values "
        "that the '_after_position_fix' file replaced",
}


def parse_file(path):
    """Return (meta, [records]) for one crossfamily archive; raises on an unparseable file."""
    with open(path, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    meta = {
        "path": path, "name": os.path.basename(path),
        "bytes": len(raw),
        "sha256_16": hashlib.sha256(raw).hexdigest()[:16],
        "partition": None, "level_hdr": None, "head": None,
        "exit_marker": None, "rc_file": None,
    }
    for ln in lines:
        m = RE_PSHA.match(ln)
        if m:
            meta["partition"] = m.group(1)
        m = RE_LEVEL.match(ln)
        if m:
            meta["level_hdr"] = int(m.group(1))
        m = RE_HEAD.match(ln)
        if m:
            meta["head"] = m.group(1)[:8]
        if ln.startswith("# exit="):
            meta["exit_marker"] = ln.split("# exit=", 1)[1].split()[0]
    rc_path = path + ".rc"
    if os.path.exists(rc_path):
        with open(rc_path, "rb") as fh:
            meta["rc_file"] = fh.read().decode("ascii", "replace").strip()
    recs, cur = [], None
    for ln in lines:
        m = RE_BLOCK.match(ln)
        if m:
            cur = {"system": m.group(1), "level": int(m.group(2)), "natoms": int(m.group(3)),
                   "npts": int(m.group(4)), "rows": {}, "span_fam": None, "span_all": None,
                   "secs": None}
            recs.append(cur)
            continue
        if cur is None:
            continue
        m = RE_ROW.match(ln)
        if m:
            cur["rows"][m.group(1)] = (float(m.group(2)), float(m.group(3)))
            continue
        m = RE_SPAN_FAM.search(ln)
        if m:
            cur["span_fam"] = float(m.group(1))
            continue
        m = RE_SPAN_ALL.search(ln)
        if m:
            cur["span_all"] = float(m.group(1))
            continue
        m = RE_TIME.search(ln)
        if m:
            cur["secs"] = float(m.group(1))
    return meta, recs


def spans(rows):
    """Family span and all-six span recomputed from the E_AB column; None if the set is short."""
    fam = [v for k, (v, _) in rows.items() if k.startswith("家族内 ")]
    oof = [v for k, (v, _) in rows.items() if k.startswith(("Voronoi", "Hirshfeld"))]
    if len(fam) != 4 or len(oof) != 2:
        return None, None, len(fam), len(oof)
    return (max(fam) - min(fam), max(fam + oof) - min(fam + oof), len(fam), len(oof))


def admissibility(meta):
    """(ok, reason): an archive is usable only with self-reported exit evidence that agrees."""
    em, rc = meta["exit_marker"], meta["rc_file"]
    if meta["name"] in SUPERSEDED:
        return False, "SUPERSEDED: " + SUPERSEDED[meta["name"]]
    if em is None and rc is None:
        return False, "no `# exit=` line and no `.rc` sibling (still running, or never finished)"
    if em is None:
        return False, "`.rc` present but the `.out` lacks its own `# exit=` line"
    if rc is None:
        return False, "`# exit=` line present but no `.rc` sibling"
    if em != rc:
        return False, "exit evidence disagrees: `.rc`=%s vs in-file `# exit=`=%s" % (rc, em)
    if em != str(SUCCESS_RC):
        return False, "archive self-reports rc=%s, not the success code %s" % (em, SUCCESS_RC)
    return True, "FINAL"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default="evidence/common_grid")
    ap.add_argument("--glob", default="*hirshfeld_crossfamily*.out")
    ap.add_argument("--files", nargs="*", default=[], help="explicit list, overrides --glob")
    ap.add_argument("--only-code", default=None, help="restrict to one partition sha256 prefix")
    ap.add_argument("--force-include-all", action="store_true",
                    help="ignore the FINAL/SUPERSEDED screen (negative controls only)")
    ap.add_argument("--ladders-only", action="store_true",
                    help="do not let a single-rung group force the 'cannot measure' code; use this "
                         "for the scoped claim over systems that DO have a same-code ladder, and "
                         "run without it for the full-set coverage verdict")
    ap.add_argument("--write", default=None, help="write this exact stdout to a file (only side effect)")
    args = ap.parse_args(argv)
    if args.write:
        sys.stdout = open(args.write, "w", encoding="utf-8", newline="\n")

    print("# grid-convergence of the cross-scheme attribution spread -- READ-ONLY, recomputed")
    print("# python %s  cwd %s" % (sys.version.split()[0], os.getcwd()))
    print("# gate on |delta(family span)| between adjacent distinct levels = %.3f kcal/mol (GATE);"
          " tie-out allows one unit in the last place of the printed value" % GATE)

    if args.files:
        paths = list(args.files)
    else:
        paths = [os.path.join(args.root, f) for f in sorted(os.listdir(args.root))
                 if fnmatch.fnmatch(f, args.glob) and not f.endswith(".rc")]

    groups, problems, badfiles, excluded, ulps = {}, [], [], [], []
    n_seen = 0
    for p in paths:
        n_seen += 1
        try:
            meta, recs = parse_file(p)
        except Exception as exc:
            badfiles.append((os.path.basename(p), repr(exc)))
            continue
        if not recs:
            badfiles.append((meta["name"], "no '== system' blocks parsed"))
            continue
        if meta["partition"] is None:
            badfiles.append((meta["name"], "header carries no nlcsplit/partition.py sha256"))
            continue
        ok, why = admissibility(meta)
        print("\n# file %s  bytes=%d  sha256=%s  partition=%s..  head=%s  rc-file=%s  exit-line=%s  -> %s"
              % (meta["name"], meta["bytes"], meta["sha256_16"], meta["partition"][:8],
                 meta["head"], meta["rc_file"], meta["exit_marker"], why))
        if not ok and not args.force_include_all:
            excluded.append((meta["name"], why))
            continue
        for r in recs:
            fs, a, nf, no = spans(r["rows"])
            if fs is None:
                problems.append("short scheme set in %s / %s (family=%d out-of-family=%d)"
                                % (meta["name"], r["system"], nf, no))
                continue
            for lbl, mine, theirs, printed in (("fam", fs, r["span_fam"], "家族内跨度"),
                                               ("all", a, r["span_all"], "总跨度")):
                if theirs is None:
                    problems.append("no printed %s (%s) line to tie out in %s / %s"
                                    % (lbl, printed, meta["name"], r["system"]))
                    continue
                scale = 10 ** PRINTED_DP
                dev = abs(int(round(mine * scale)) - int(round(theirs * scale)))
                ulps.append((dev, meta["name"], r["system"], r["level"], lbl, mine, theirs))
                if dev > MAX_ULP:
                    problems.append("tie-out FAIL %s / %s level %d %s: recomputed %.6f vs printed "
                                    "%.4f, off by %d last digits"
                                    % (meta["name"], r["system"], r["level"], lbl, mine, theirs, dev))
            key = (meta["partition"][:8], r["system"])
            groups.setdefault(key, []).append(
                {"level": r["level"], "npts": r["npts"], "fam": fs, "all": a,
                 "e_nl": list(r["rows"].values())[0][1], "secs": r["secs"], "file": meta["name"]})

    for p, why in badfiles:
        print("  UNPARSEABLE  %s : %s" % (p, why))

    print("\n== accounting: glob saw %d archives; %d admitted as FINAL; %d excluded; %d unparseable"
          % (n_seen, n_seen - len(excluded) - len(badfiles), len(excluded), len(badfiles)))
    for name, why in excluded:
        print("   EXCLUDED %s : %s" % (name, why))

    if ulps:
        worst = max(u[0] for u in ulps)
        over = [u for u in ulps if u[0] > MAX_ULP]
        print("== tie-out of recomputed spans against the spans printed in the same file: %d "
              "comparisons, max deviation %d last digit(s) of the printed value, %d over tolerance %d"
              % (len(ulps), worst, len(over), MAX_ULP))
        for dev, name, system, level, lbl, mine, theirs in sorted(ulps, key=lambda u: -u[0])[:5]:
            print("   dev=%d  %-58s %-12s level %d  %s  recomputed %.6f  printed %.4f"
                  % (dev, name, system, level, lbl, mine, theirs))
    else:
        print("== tie-out: no comparisons were made, which means nothing was admitted")

    print("\n== ladders grouped by (partition sha256 prefix, system) ==")
    print("%-10s %-16s %5s %8s %10s %10s %7s %10s  %s"
          % ("code", "system", "lvl", "Npts", "fam span", "all-six", "ratio", "E_NL", "file"))
    rc = 0
    incomplete = []
    adequate = {}
    for (code, system) in sorted(groups, key=lambda k: (k[1], k[0])):
        if args.only_code and not code.startswith(args.only_code):
            continue
        rows = sorted(groups[(code, system)], key=lambda d: (d["level"], d["file"]))
        for d in rows:
            print("%-10s %-16s %5d %8d %10.4f %10.4f %7.2f %10.4f  %s"
                  % (code, system, d["level"], d["npts"], d["fam"], d["all"],
                     (d["all"] / d["fam"]) if d["fam"] > 0 else float("nan"), d["e_nl"], d["file"]))
        # same-level repeats: repeatability, not convergence
        by_lvl = {}
        for d in rows:
            by_lvl.setdefault(d["level"], []).append(d)
        for lvl, dups in sorted(by_lvl.items()):
            if len(dups) < 2:
                continue
            wf = max(x["fam"] for x in dups) - min(x["fam"] for x in dups)
            wa = max(x["all"] for x in dups) - min(x["all"] for x in dups)
            print("  ~ repeat at level %d, %s / code %s: %d files, fam-span spread %.4f, "
                  "all-six spread %.4f  (repeatability line, NOT a convergence rung)"
                  % (lvl, system, code, len(dups), wf, wa))
        rungs = sorted({d["level"] for d in rows})
        if len(rungs) < 2:
            print("  -> %s under code %s: only level %s => grid convergence NOT MEASURED"
                  % (system, code, rungs[0]))
            incomplete.append((system, code))
            continue
        worst = 0.0
        for lo_lvl, hi_lvl in zip(rungs, rungs[1:]):
            lo = [d for d in by_lvl[lo_lvl]][0]
            hi = [d for d in by_lvl[hi_lvl]][0]
            dfam = hi["fam"] - lo["fam"]
            worst = max(worst, abs(dfam))
            print("  -> rung level %d to %d, %s / code %s: fam span %.4f -> %.4f (delta %+.4f, "
                  "|delta| %.4f %s gate); all-six delta %+.4f; E_NL delta %+.4f"
                  % (lo_lvl, hi_lvl, system, code, lo["fam"], hi["fam"], dfam, abs(dfam),
                     "<=" if abs(dfam) <= GATE else ">", hi["all"] - lo["all"], hi["e_nl"] - lo["e_nl"]))
        if worst > GATE:
            print("  => %s / code %s: NOT grid-stable over the whole ladder (worst adjacent "
                  "|delta| %.4f), under the pre-registered gate." % (system, code, worst))
            rc = 3
        else:
            print("  => %s / code %s: grid-stable over levels %s (worst adjacent |delta fam span| %.4f)."
                  % (system, code, rungs, worst))
        # SECONDARY CLAIM, declared here as post-hoc.  The registered verdict above is unchanged and
        # still sets the exit code.  It collapsed every rung into one number, so a cell that is
        # converged BETWEEN THE RUNGS AT OR ABOVE THE PUBLISHED LEVEL read as a flat failure whenever
        # the coarse rung also entered the ladder -- and "is the span stable at adequate convergence?"
        # is a different question from "is it stable all the way down to the coarsest grid?".  Same
        # quantity, same gate, restricted to the top two rungs AND only when both of them are at or
        # above PUBLISHED_LEVEL: a pair that includes a disqualified coarse rung cannot answer the
        # question, so it is reported as NOT MEASURED instead of being counted.
        if len(rungs) >= 2 and rungs[-2] >= PUBLISHED_LEVEL:
            lo = by_lvl[rungs[-2]][0]
            hi = by_lvl[rungs[-1]][0]
            d = abs(hi["fam"] - lo["fam"])
            adequate[system] = d
            print("  -- SECONDARY (post-hoc split, same gate, rungs %d<->%d both >= level %d): "
                  "%s / code %s |delta fam span| %.4f -> %s"
                  % (rungs[-2], rungs[-1], PUBLISHED_LEVEL, system, code, d,
                     "stable" if d <= GATE else "NOT stable"))
        elif len(rungs) >= 2:
            print("  -- SECONDARY: NOT MEASURED for %s / code %s -- its top pair is %d<->%d and the "
                  "lower one is below level %d, so the pair contains a rung the convergence question "
                  "is not about" % (system, code, rungs[-2], rungs[-1], PUBLISHED_LEVEL))

    if problems:
        print("\n!! measurement-integrity problems (these are not scientific findings):")
        for w in problems:
            print("   - " + w)
        rc = 2
    if badfiles:
        rc = 2
    if incomplete:
        print("\n!! ladders that are single-rung, so convergence is NOT MEASURED for them:")
        for system, code in incomplete:
            print("   - %s under partition.py %s.." % (system, code))
        print("   (a coverage statement, not a verdict of stability)")
        if rc == 0 and not args.ladders_only:
            rc = 2

    n_ladders = sum(1 for k in groups if len({d["level"] for d in groups[k]}) >= 2)
    if not groups:
        print("\n!! NOTHING ADMITTED: no archive survived the exit-evidence/superseded screen, so "
              "the judging path below never ran. A green code here would be vacuous.")
        rc = 2
    elif n_ladders == 0:
        print("\n!! NO LADDER MEASURED: archives were admitted but not one (code, system) group has "
              "two distinct levels, so 'all ladders stable' would be vacuously true.")
        rc = 2

    n_adm = len(adequate)
    n_adm_stable = sum(1 for v in adequate.values() if v <= GATE)
    if n_adm:
        print("\n== SECONDARY claim only (top-two-rung pair with both rungs at or above "
              "PUBLISHED_LEVEL, same gate, split added after the coarse steps were seen): "
              "%d of %d ladders stable" % (n_adm_stable, n_adm))
        for system, d in sorted(adequate.items()):
            print("   %-16s |delta| %.4f  %s" % (system, d, "stable" if d <= GATE else "NOT stable"))
        print("   NOT MEASURED for %d further ladder(s): their top pair reaches below "
              "PUBLISHED_LEVEL, so no second adequate rung exists for them yet."
              % (n_ladders - n_adm))
        print("   This does NOT change the exit code above, and is not the registered primary claim.")

    print("\nladders measured: %d; single-rung groups: %d"
          % (n_ladders, len(incomplete)))
    print("VERDICT rc=%d -- 0 every admissible ladder stable; 3 a delta exceeds the gate; "
          "2 something could not be measured%s"
          % (rc, "" if not args.ladders_only else " (ladders-only scope: single-rung groups "
             "reported as coverage, not as a failure to measure)"))
    print("# no cross-system sum appears above; per-system quantities stay per-system.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
