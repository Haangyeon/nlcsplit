#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One parser for the archived `nlcsplit/step_m_ccsdt.py` ladders.

Why a shared module and not a regex in each consumer. Two scripts need these numbers -
`orca_crosscheck.py` (which compares them against ORCA) and `cp_rebuild_compare.py` (which
proves that a re-run changed the monomer construction and nothing else). Written twice, the
two copies drift, and the drift shows up as one script passing a row the other rejects. This
repository has already had a check go green because its parser accepted only one of two
spellings of the same header ("frozen(O 1s)" before the refactor, "frozen(cores)" after).

What is read per rung is deliberately more than the interaction energy: `E_dimer` and the
printed basis dimensions are what let a comparison say "the complex side is byte-for-byte the
same run, so the only thing that moved is the monomer construction". A difference in dE with
no such statement is just a new number.
"""
import os
import re

SYSTEM_RE = re.compile(r"== Step M · (\S+) CCSD\(T\) ")
BASIS_RE = re.compile(r"### basis = (\S+)")
Nao_RE = re.compile(r"复合物 nao=(\d+) nbas=(\d+) nelec=(\d+)；单体 nao=(\d+)/(\d+)")
FREEZE_RE = re.compile(r"每片段冻核 \[(\d+), (\d+)\]，合计 (\d+)")
RUNG_RE = re.compile(r"\s*--- (\S+)")
# Capture the fields as far as non-space runs go and convert them, rather than spelling a sign
# into the pattern: a version of this regex written as `-?\d+\.\d+` silently dropped every
# POSITIVE interaction energy, and "the row is absent" is indistinguishable from "the row was
# never run" unless the parser cannot skip a line it was handed.
# The first field has to look like a number, because archive prose is indented the same way as
# the table and one such line exists ("    CCSD(T) 冻核 -2.5506，全电子 -2.6300"). Requiring all
# three up front would have to reject that line by shape alone and then a genuinely broken row
# could hide in the same way, so only the first field gates on looks; the other two are
# converted or the row raises.
CC_RE = re.compile(r"^\s{4}CCSD\(T\)\s+([-+]?\d+\.\d+)\s+(\S+)\s+(\S+)")


def parse_ladder(paths):
    """{(system, basis, rung): row} from one or more archived ladders.

    `rung` is "frozen" or "all". Each row is a dict with e_dimer, sum_mono, de_kcal, source
    (the file it came from), nao_complex, nao_mono (tuple) and freeze (tuple). Two ways this
    parser could lie are closed off: a file that yields no rows raises, and a CCSD(T) line
    seen before its system/basis/rung header raises, because a row skipped for want of
    context is indistinguishable from a row that was never run.
    """
    rows = {}
    for p in paths if isinstance(paths, (list, tuple)) else [paths]:
        if not os.path.exists(p):
            raise SystemExit("ladder archive missing: %s" % p)
        name = basis = rung = None
        nao = freeze = None
        n_lines = 0
        skipped = []
        for ln in open(p, errors="replace"):
            m = SYSTEM_RE.search(ln)
            if m:
                name, basis, rung = m.group(1), None, None
                continue
            m = BASIS_RE.search(ln)
            if m:
                basis, rung, nao, freeze = m.group(1), None, None, None
                continue
            m = Nao_RE.search(ln)
            if m and name and basis:
                nao = (int(m.group(1)), (int(m.group(4)), int(m.group(5))))
                continue
            m = FREEZE_RE.search(ln)
            if m:
                freeze = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
                continue
            m = RUNG_RE.match(ln)
            if m and (m.group(1).startswith("frozen") or m.group(1).startswith("all")):
                rung = "frozen" if m.group(1).startswith("frozen") else "all"
                continue
            m = CC_RE.match(ln.rstrip("\n"))
            if m:
                try:
                    vals = [float(m.group(i)) for i in (1, 2, 3)]
                except ValueError:
                    raise SystemExit("CCSD(T) row does not carry three numbers: %r in %s"
                                     % (ln.strip(), os.path.basename(p)))
                if not (name and basis and rung):
                    # Archives in this directory quote a condensed echo of the ladder before
                    # the detailed blocks, and the echo has no "### basis"/"--- rung" headers.
                    # Those rows cannot be keyed, so they are skipped - but skipping is only
                    # safe if each one is re-presented with a header somewhere in the same
                    # file, which is checked below rather than assumed.
                    skipped.append((name, vals[0], vals[2], ln.strip()))
                    continue
                row = dict(
                    e_dimer=vals[0], sum_mono=vals[1],
                    de_kcal=vals[2], source=os.path.basename(p),
                    nao_complex=nao[0] if nao else None,
                    nao_mono=nao[1] if nao else None, freeze=freeze)
                key = (name, basis, rung)
                # Several archives in this directory re-run the same row on purpose (that is
                # how cross-job determinism was evidenced). If the two copies ever disagree,
                # "last file wins" would be a silent choice between two numbers, so the
                # disagreement is raised instead.
                if key in rows:
                    prev = rows[key]
                    if abs(prev["de_kcal"] - row["de_kcal"]) > 1e-4 or \
                       abs(prev["e_dimer"] - row["e_dimer"]) > 1e-8:
                        raise SystemExit(
                            "duplicate row %s/%s/%s disagrees between %s (%.10f, %+.4f) and"
                            " %s (%.10f, %+.4f) - which one is the reference is a decision,"
                            " not a parsing detail"
                            % (key[0], key[1], key[2], prev["source"], prev["e_dimer"],
                               prev["de_kcal"], row["source"], row["e_dimer"],
                               row["de_kcal"]))
                rows[key] = row
                n_lines += 1
        if n_lines == 0:
            raise SystemExit("no CCSD(T) rows parsed from %s - the parser, not the archive,"
                             " is the thing to check" % p)
        # The echo rows are skipped above. That is only harmless if the numbers still reach a
        # keyed row somewhere in this file, so each skipped row is matched against the keyed
        # set - on (system, complex energy, interaction energy), not on the system name alone,
        # because "some row for this system exists" would also be true when the echo carries a
        # row the detailed block lost.
        unclaimed = [s for s in skipped
                     if not any(k[0] == s[0] and abs(r["e_dimer"] - s[1]) < 1e-9
                                and abs(r["de_kcal"] - s[2]) < 1e-4 for k, r in rows.items())]
        if unclaimed:
            raise SystemExit("%d CCSD(T) row(s) in %s were seen without a header and have no"
                             " headered twin - this is where a row would silently disappear:"
                             " %s" % (len(unclaimed), os.path.basename(p),
                                      "; ".join("%s: %s" % (u[0], u[3]) for u in unclaimed[:3])))
    return rows
