#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Negative controls for grid_level_convergence.py.  Each case must FAIL the way it claims to.

A convergence table whose judging path cannot be made to say "unstable" is not evidence -- it is a
formatter.  So every exit code the target script can emit is driven here on purpose, and each case
additionally requires a non-empty stdout (or stderr, for the crash case) containing a named marker:
an empty file left behind by a crash looks exactly like a control that behaved, which is how this
repository has been caught before.

Fixtures are built from a REAL archive's header block, so the format cannot drift away from what
the measurement script actually writes, but every number in the body is hand-chosen and exact, so
the expected verdict is known before the target runs and is never produced by the code under test.

Codes for THIS script (it never uses 1, which means "designed pass" elsewhere in the package):
    0 = every case behaved as declared
    3 = at least one case misbehaved
    2 = a fixture could not be built (the controls did not actually run)
    4 = uncaught exception
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "grid_level_convergence.py")
DONOR = os.path.join(HERE, "20261012T054743Z_hirshfeld_crossfamily_l1_水二聚体_after_unitfix.out")
OLD_DONOR = os.path.join(HERE, "20261009T193232Z_hirshfeld_crossfamily_l1_benzene_dimers.out")
PY = sys.executable

RE_SHA = re.compile(r"sha256 nlcsplit/partition\.py\s*=\s*([0-9a-f]{64})")

# Hand-chosen bodies: schemes -> E_AB, plus the spans they imply.  All values are exact to four
# decimals so the expected verdict is arithmetic anyone can redo on paper.
FAM0 = {"家族内 becke": -0.6000, "家族内 becke-becke-rad": -0.5900,
        "家族内 becke-treutler": -0.5950, "家族内 stratmann": -0.6000,
        "Voronoi(最近原子硬指派)": -0.5960, "Hirshfeld(自由原子库存化)": -0.5990}
SPANS0 = (0.0100, 0.0100)
FAM_IN = {"家族内 becke": -0.6000, "家族内 becke-becke-rad": -0.5870,
          "家族内 becke-treutler": -0.5950, "家族内 stratmann": -0.5990,
          "Voronoi(最近原子硬指派)": -0.5830, "Hirshfeld(自由原子库存化)": -0.5980}
SPANS_IN = (0.0130, 0.0170)
FAM_OUT = {"家族内 becke": -0.6000, "家族内 becke-becke-rad": -0.5100,
           "家族内 becke-treutler": -0.5800, "家族内 stratmann": -0.5990,
           "Voronoi(最近原子硬指派)": -0.5830, "Hirshfeld(自由原子库存化)": -0.5980}
SPANS_OUT = (0.0900, 0.0900)


def header(level, sha):
    """Real header lines of the donor archive, with level and partition hash substituted."""
    head = open(DONOR, encoding="utf-8").read().split("\n\n", 1)[0] + "\n"
    head = re.sub(r"^# level = \d+", "# level = %d" % level, head, flags=re.M)
    return RE_SHA.sub("sha256 nlcsplit/partition.py      = " + sha, head)


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return path


def make(dirpath, name, level, sha, body, spans, shift_span=None, header_only=False):
    fam, total = spans
    if shift_span:
        which, delta = shift_span
        if which == "fam":
            fam = round(fam + delta, 4)
        else:
            total = round(total + delta, 4)
    txt = header(level, sha)
    if header_only:
        txt += "\nVERDICT DONE -- truncated at startup, no system block ever printed\n"
        txt += "# exit=0 at 2026-10-21T00:00:00Z\n"
        return write(os.path.join(dirpath, name), txt)
    txt += "\n== 控制体系  level=%d  原子 6  公共网格 N=9999  片间min 1.95 Ang\n" % level
    for scheme, eab in body.items():
        txt += "   %-26s E_AB =  %8.4f  E_NL =   -7.8950\n" % (scheme, eab)
    txt += "   （对照，不计入判据）等权 1/natm E_AB =   -3.9475  E_NL =    -7.8950\n"
    txt += "   → 家族内跨度 = %.4f kcal/mol（四方案，同一网格同一权重）\n" % fam
    txt += "   → 含两个家族外构造的总跨度 = %.4f kcal/mol\n" % total
    txt += "   → 比值（含家族外 / 家族内） = 1.00（预登记）\n"
    txt += "   （用时 1.0 s）\n\n"
    txt += "VERDICT DONE\n# exit=0 at 2026-10-21T00:00:00Z\n"
    return write(os.path.join(dirpath, name), txt)


def with_rc(path, content="0\n"):
    write(path + ".rc", content)
    return path


def first_sha(path):
    return sorted(set(RE_SHA.findall(open(path, encoding="utf-8").read())))[0]


def run(args):
    p = subprocess.run([PY, TARGET] + args, capture_output=True)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def main():
    for must in (TARGET, DONOR, OLD_DONOR):
        if not os.path.exists(must):
            print("SETUP FAILURE: missing %s" % must)
            return 2
    sha_new, sha_old = first_sha(DONOR), first_sha(OLD_DONOR)
    tmp = tempfile.mkdtemp(prefix="glc_negctl_")
    cases = []
    try:
        def check(name, want_rc, want_marker, args, stream="out"):
            rc, out, err = run(args)
            body = out if stream == "out" else err
            marker_ok = bool(want_marker) and (want_marker in body)
            cases.append((name, want_rc, rc, marker_ok, len(body), rc == want_rc and marker_ok
                          and len(body) > 0, err))

        # C0 in-gate ladder -> 0, and it must actually say grid-stable
        d = os.path.join(tmp, "c0")
        os.makedirs(d)
        f0 = with_rc(make(d, "a_l0.out", 0, sha_new, FAM0, SPANS0))
        f1 = with_rc(make(d, "a_l1.out", 1, sha_new, FAM_IN, SPANS_IN))
        check("C0 in-gate ladder says grid-stable", 0, "grid-stable", ["--files", f0, f1])

        # C1 the same ladder, upper rung widened past the gate -> 3, not stable
        d = os.path.join(tmp, "c1")
        os.makedirs(d)
        g0 = with_rc(make(d, "a_l0.out", 0, sha_new, FAM0, SPANS0))
        g1 = with_rc(make(d, "a_l1.out", 1, sha_new, FAM_OUT, SPANS_OUT))
        check("C1 out-of-gate ladder says NOT grid-stable", 3, "NOT grid-stable",
              ["--files", g0, g1])

        # C2 a rung whose .rc sibling is absent must be excluded, never trusted
        f1_norc = write(f1[:-4] + "_norc.out", open(f1, encoding="utf-8").read())
        check("C2 rung without .rc is excluded, not silently trusted", 2, "EXCLUDED",
              ["--files", f0, f1_norc])

        # C3 .rc disagreeing with the archive's own exit line
        d = os.path.join(tmp, "c3")
        os.makedirs(d)
        h0 = with_rc(make(d, "a_l0.out", 0, sha_new, FAM0, SPANS0))
        h1 = with_rc(make(d, "a_l1.out", 1, sha_new, FAM_IN, SPANS_IN), "7\n")
        check("C3 disagreeing exit evidence is excluded", 2, "disagrees", ["--files", h0, h1])

        # C4 startup-truncated archive: the shape of the残件 that sat in this directory unnoticed
        d = os.path.join(tmp, "c4")
        os.makedirs(d)
        with_rc(make(d, "a_l1.out", 1, sha_new, FAM_IN, SPANS_IN, header_only=True))
        check("C4 truncated archive does not enter the table", 2, "UNPARSEABLE",
              [d, "--glob", "*.out"])

        # C5 a printed span two last digits off its own endpoints -> the tie-out must fail
        d = os.path.join(tmp, "c5")
        os.makedirs(d)
        with_rc(make(d, "a_l1.out", 1, sha_new, FAM_IN, SPANS_IN, shift_span=("fam", 0.0002)))
        check("C5 span inconsistent with its own columns is caught", 2, "tie-out FAIL",
              [d, "--glob", "*.out"])

        # C6 two rungs under DIFFERENT partition hashes must not be joined into a ladder
        d = os.path.join(tmp, "c6")
        os.makedirs(d)
        u0 = with_rc(make(d, "a_l0.out", 0, sha_old, FAM0, SPANS0))
        u1 = with_rc(make(d, "a_l1.out", 1, sha_new, FAM_IN, SPANS_IN))
        check("C6 cross-code pair is split, never joined", 2, "NO LADDER MEASURED",
              ["--files", u0, u1])

        # C7 an empty input set must not read as a pass
        check("C7 empty input set is a failure, not a pass", 2, "NOTHING ADMITTED",
              [tmp, "--glob", "definitely_no_such_pattern"])

        # C8 the crash hook: unwritable --write target gets the crash code, never the interpreter's 1
        rc, out, err = run(["--write", os.path.join(tmp, "no_such_dir", "x.out"),
                           tmp, "--glob", "definitely_no_such_pattern"])
        cases.append(("C8 crash exits with the crash code", 4, rc, "Traceback" in err, len(err),
                      rc == 4 and len(err) > 0, err))

        # C9 the real archive set. It must NOT pin a specific code: new rungs legitimately move the
        # verdict, and a control that fails because the SCIENCE changed is testing the date, not the
        # logic -- which is exactly what happened when the aromatic cells came in past the gate
        # (see the PROGRESS entry that introduced this file). What stays fixed is the internal
        # consistency between the two claims and the requirement that some ladder exists.
        rc_a, out_a, _ = run([HERE])
        rc_b, out_b, _ = run([HERE, "--ladders-only"])
        n_lad = re.search(r"ladders measured: (\d+)", out_b)
        nunstable = out_b.count("NOT grid-stable")
        nlad = int(n_lad.group(1)) if n_lad else -1
        consistent = ((rc_b == 3) == (nunstable >= 1)) and ((rc_b == 0) == (nunstable == 0))
        shape_ok = (rc_a in (0, 2, 3)) and (rc_b in (0, 3)) and nlad > 0 and (rc_b != 0 or rc_a in (0, 2))
        cases.append(("C9 real set: ladders exist and the two claims are self-consistent",
                      0, 0 if (consistent and shape_ok) else 3,
                      "real set", len(out_a) + len(out_b), consistent and shape_ok,
                      "rc_strict=%d rc_scoped=%d NOT-grid-stable-lines=%d ladders=%d"
                      % (rc_a, rc_b, nunstable, nlad)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("# negative controls for grid_level_convergence.py")
    print("# python %s  target sha256=%s" % (sys.version.split()[0],
          hashlib.sha256(open(TARGET, "rb").read()).hexdigest()[:16]))
    print("%-58s %6s %6s %8s %10s %s" % ("case", "want", "got", "marker", "bytes", "verdict"))
    bad = 0
    for name, want, got, marker_ok, nbytes, ok, _err in cases:
        bad += 0 if ok else 1
        print("%-58s %6d %6d %8s %10d %s"
              % (name, want, got, "yes" if marker_ok else "NO", nbytes, "PASS" if ok else "FAIL"))
    print("\n%d cases, %d behaved as declared, %d misbehaved" % (len(cases), len(cases) - bad, bad))
    if bad:
        for name, want, got, marker_ok, nbytes, ok, err in cases:
            if not ok:
                print("---- %s : want rc=%d got rc=%d marker_ok=%s bytes=%d"
                      % (name, want, got, marker_ok, nbytes))
                if err:
                    print(err[-1200:])
    print("VERDICT rc=%d" % (0 if bad == 0 else 3))
    return 0 if bad == 0 else 3


if __name__ == "__main__":
    def _die(t, v, tb):
        import traceback
        traceback.print_exception(t, v, tb, None, sys.stderr)
        try:
            sys.stdout.flush()
            sys.stderr.flush()
        finally:
            os._exit(4)
    sys.excepthook = _die
    sys.exit(main())
