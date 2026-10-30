#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ORCA 6.0.1 cross-check of the CCSD(T) **counterpoise** anchor (third program, not our library).

Why this exists
---------------
`evidence/ccsdt/` reported the water-dimer counterpoise interaction energy at CCSD(T) from one
program (PySCF's own cc/mp modules) and the paper compares it against our functional numbers.
That is the same shape of argument that failed once already in this repository: the nonlocal
term was checked against a second implementation living inside the same library, and a reviewer
of that claim asked what a third program would say. So this script asks it: same geometries,
same basis, same convention, but ORCA.

What changed on 2026-10-03, and why the first version of this file did not check what it said
---------------------------------------------------------------------------------------------
The first version built the monomers from the fragment's **own** atoms, exactly like
`nlcsplit/step_m_ccsdt.py` did, so the quantity it printed as `dE_CP` was the uncorrected
interaction energy. It agreed with PySCF to 0.0002 kcal/mol - and both sides were wrong the
same way, which is the reason a cross-program check on a convention has to be constructed from
the definition rather than mirrored from the other script. A Boys-Bernardi monomer is computed
in the complex's basis, so the partner's atoms enter as basis functions carrying no nuclear
charge.

ORCA spells that with a colon after the element symbol. This is taken from the installation
itself - `~/orca6/CompoundScripts/BSSE/BSSECorrection.cmp`, NOTE 4: "Ghost atom (':' after the
symbol of the element)" - and confirmed by measurement in `20261003T0616Z_orca_ghost_probe.out`:
a water monomer whose partner is written `O:`/`H:` reports `Basis Dimension Dim .... 36`, the
complex's dimension, and its frozen-core field reads `chemical core (2 el)`, i.e. one oxygen
1s, so the correlation module carries the ghost functions and still freezes the same shell.
Both the corrected and the uncorrected construction are run here, because the paper's §3.2
compares both, and because reproducing the old uncorrected number in the same execution is
what makes the new counterpoise number comparable to the record it replaces.

The PySCF reference is parsed out of the archived ladders rather than transcribed into this
file; a number typed in here would be a second copy to go stale.

Run (WSL, repository root, ORCA at ~/orca6):
    PYTHONPATH=. python3 -u evidence/ccsdt/orca_crosscheck.py
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (ROOT, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from nlcsplit import geomlib                                    # noqa: E402
from nlcsplit import step_m_ccsdt                               # noqa: E402
from ladder_parse import parse_ladder                           # noqa: E402

KCAL = 627.509474
ORCA = os.path.expanduser(os.environ.get("ORCA_BIN", "~/orca6/orca"))
WORK = os.path.join(ROOT, "scratch", "orca_ccsdt")
S22DIR = os.environ.get("S22DIR", "scratch/lit/s22")
NPROC = int(os.environ.get("ORCA_NPROC", "4"))
MAXCORE = int(os.environ.get("ORCA_MAXCORE", "4000"))

# Archives holding the PySCF side. The corrected (counterpoise) numbers and the superseded
# (uncorrected) ones live in different files, and the two must not be confused, so each list
# is labelled with the quantity it is read for.
PYSCF_CP_ARCHIVES = [
    os.path.join(HERE, "20261003T0605Z_stepm_dimers_ghostcp_local.out"),
]
PYSCF_UNC_ARCHIVES = [
    os.path.join(HERE, "20260930T235900Z_stepm_three_systems_631g.out"),
    os.path.join(HERE, "20261001T000400Z_stepm_three_systems_avdz.out"),
]
PLAN = [("水二聚体", "6-31g*"), ("水二聚体", "aug-cc-pvdz"),
        ("氨二聚体", "6-31g*"), ("甲烷二聚体", "6-31g*")]

# Per-part comparison of ORCA's printed AO dimension against PySCF's nao, filled by main().
AOCHK = []


def atom_lines(symbols, coords, keep, ghost):
    """Fragment `keep` as real atoms; the rest as ghosts (`:`) when ghost, dropped when not.

    keep=None means nobody is ghosted and nothing is dropped - the complex itself.
    """
    lines = []
    for i, (s, c) in enumerate(zip(symbols, coords)):
        if keep is None or i in keep:
            tok = s
        elif ghost:
            tok = s + ":"
        else:
            continue
        lines.append("%-6s %14.8f %14.8f %14.8f" % (tok, *c))
    return lines


def orca_input(path, lines, basis, frozen_core):
    """One single point. The frozen-core choice is passed explicitly, never left to default."""
    ncore = "FrozenCore" if frozen_core else "NoFrozenCore"
    open(path, "w").write(
        "! RHF CCSD(T) %s TightSCF %s\n%%maxcore %d\n%%pal nprocs %d end\n* xyz 0 1\n%s\n*\n"
        % (basis, ncore, MAXCORE, NPROC, "\n".join(lines)))


def run_orca(inp):
    base = inp[:-4]
    out = base + ".out"
    with open(out, "w") as fh:
        subprocess.run([ORCA, os.path.basename(inp)], cwd=os.path.dirname(inp) or ".",
                       stdout=fh, stderr=subprocess.STDOUT, check=False)
    txt = open(out, errors="replace").read()
    e = re.findall(r"FINAL SINGLE POINT ENERGY\s+(-?\d+\.\d+)", txt)
    conv = "ORCA TERMINATED NORMALLY" in txt
    # ORCA words it as "Frozen core treatment ... chemical core (2 el)" - 2 *electrons*, i.e.
    # one orbital per oxygen. Parsing this rather than trusting the input keyword is the point,
    # and with a ghost atom in the geometry it is also the only way to see that the charge-less
    # partner contributes no core of its own.
    fz = re.findall(r"Frozen core treatment\s+\.\.\.\s+chemical core \((\d+) el\)", txt)
    ae = re.findall(r"Frozen core treatment\s+\.\.\.\s+NO frozen core", txt)
    nc = re.findall(r"Number of correlated electrons\s+\.\.\.\s+(\d+)", txt)
    nb = re.findall(r"Number of basis functions\s+\.\.\.\s+(\d+)", txt)
    # Which field to compare with PySCF's nao is itself a thing that had to be found out.
    # ORCA's "Number of basis functions" is NOT it: for a water monomer in aug-cc-pVDZ that
    # field prints 47 while ORCA's own SCF section reports "Basis Dimension Dim .... 41" and
    # its CC section "Number of AO's ... 41", and 41 is PySCF's number. So the header field is
    # kept only to show the discrepancy, and the AO dimension is the identity check.
    dim = re.findall(r"Basis Dimension\s+Dim\s+\.*\s+(\d+)", txt)
    return (float(e[-1]) if e else None), conv, (int(fz[0]) if fz else (0 if ae else None)), \
        (int(nc[0]) if nc else None), (int(nb[0]) if nb else None), \
        (int(dim[0]) if dim else None), out


def pyscf_ao(atoms, basis):
    """PySCF's AO count for the same geometry and basis. Building the Mole costs no SCF."""
    return step_m_ccsdt.build([a[0] for a in atoms], [a[1] for a in atoms], basis).nao


def main():
    os.makedirs(WORK, exist_ok=True)
    cp_ref = {k: r["de_kcal"] for k, r in parse_ladder(PYSCF_CP_ARCHIVES).items()}
    unc_ref = {k: r["de_kcal"] for k, r in parse_ladder(PYSCF_UNC_ARCHIVES).items()}
    print("== ORCA cross-check of the CCSD(T) counterpoise anchor ==")
    print("  ORCA: %s   nprocs=%d maxcore=%d MB   workdir=%s" % (ORCA, NPROC, MAXCORE, WORK))
    print("  PySCF counterpoise reference parsed from: %s (%d rows)"
          % (", ".join(os.path.basename(p) for p in PYSCF_CP_ARCHIVES), len(cp_ref)))
    print("  PySCF uncorrected reference parsed from: %s (%d rows)"
          % (", ".join(os.path.basename(p) for p in PYSCF_UNC_ARCHIVES), len(unc_ref)))
    if not os.path.exists(ORCA):
        print("  FAIL: no ORCA at %s" % ORCA)
        sys.exit(1)

    rows = []
    AOCHK[:] = []
    for name, basis in PLAN:
        atoms, frags = geomlib.s22_system(name, S22DIR)
        symbols = [a[0] for a in atoms]
        coords = [a[1] for a in atoms]
        for frozen_core in (True, False):
            rung = "frozen" if frozen_core else "all"
            tag = "%s_%s_%s" % (name, basis.replace("*", "star").replace("/", "_"),
                                "fc" if frozen_core else "ae")
            parts = [("complex", atom_lines(symbols, coords, None, False),
                      pyscf_ao(atoms, basis))]
            for i, f in enumerate(frags):
                parts.append(("ghost%d" % i,
                              atom_lines(symbols, coords, set(f), True),
                              step_m_ccsdt.build(*step_m_ccsdt.cp_frag_specs(
                                  symbols, coords, frags)[i], basis).nao))
                parts.append(("bare%d" % i,
                              atom_lines(symbols, coords, set(f), False),
                              pyscf_ao([atoms[j] for j in f], basis)))
            got = {}
            for label, lines, ao_ps in parts:
                inp = os.path.join(WORK, "%s_%s.inp" % (tag, label))
                orca_input(inp, lines, basis, frozen_core)
                e, conv, nfz_el, ncorr, nbas, ao_orca, out = run_orca(inp)
                got[label] = (e, conv, nfz_el)
                AOCHK.append((tag, label, ao_orca, ao_ps, nbas))
                print("  %-46s %-8s E=%s  ok=%s  frozen_core_electrons=%s  correlated=%s"
                      % (os.path.basename(out), label,
                         ("%.10f" % e) if e is not None else "NONE", conv, nfz_el, ncorr))
                print("      basis identity: AO dimension ORCA=%s vs PySCF nao=%s -> %s"
                      "   (ORCA's own header field says %s)"
                      % (ao_orca, ao_ps,
                         "same space" if ao_orca == ao_ps else "*** DIFFERENT SPACE ***", nbas))
            if any(v[0] is None or not v[1] for v in got.values()):
                print("  FAIL: a part is missing or unconverged for %s" % tag)
                continue
            dcp = (got["complex"][0] - got["ghost0"][0] - got["ghost1"][0]) * KCAL
            dunc = (got["complex"][0] - got["bare0"][0] - got["bare1"][0]) * KCAL
            rcp = cp_ref.get((name, basis, rung))
            runc = unc_ref.get((name, basis, rung))
            print("  --- %s / %s  %s" % (name, basis, rung))
            print("      dE_CP   ORCA %+.4f   PySCF %s   diff %s"
                  % (dcp, ("%+.4f" % rcp) if rcp is not None else "NO REFERENCE",
                     ("%+.4f" % (dcp - rcp)) if rcp is not None else "n/a"))
            print("      dE_unc  ORCA %+.4f   PySCF %s   diff %s   (BSSE %+.4f)"
                  % (dunc, ("%+.4f" % runc) if runc is not None else "NO REFERENCE",
                     ("%+.4f" % (dunc - runc)) if runc is not None else "n/a", dcp - dunc))
            rows.append((name, basis, rung, dcp, rcp, dunc, runc))
        print()

    print("== summary ==")
    print("  %-10s %-14s %-8s %10s %10s %10s %10s %10s %10s"
          % ("system", "basis", "conv", "ORCA_CP", "PySCF_CP", "d_CP",
             "ORCA_unc", "PySCF_unc", "d_unc"))
    worst_cp = worst_unc = 0.0
    missing = []
    for name, basis, rung, dcp, rcp, dunc, runc in rows:
        for tag, ref, got in (("CP", rcp, dcp), ("unc", runc, dunc)):
            if ref is None:
                missing.append((name, basis, rung, tag))
                continue
            d = abs(got - ref)
            if tag == "CP":
                worst_cp = max(worst_cp, d)
            else:
                worst_unc = max(worst_unc, d)
        print("  %-10s %-14s %-8s %+10.4f %10s %+10s %+10.4f %10s %+10s"
              % (name, basis, rung, dcp, ("%+.4f" % rcp) if rcp is not None else "n/a",
                 ("%+.4f" % (dcp - rcp)) if rcp is not None else "n/a", dunc,
                 ("%+.4f" % runc) if runc is not None else "n/a",
                 ("%+.4f" % (dunc - runc)) if runc is not None else "n/a"))
    # The bar is the author's standard, not a convenient one: three decimal places in
    # kcal/mol is what two programs using the same basis are expected to reach on an
    # interaction energy. An earlier version of this script used 0.02, which would have
    # passed a real convention mismatch (6d vs 5d shells are worth 0.01-0.1 kcal/mol).
    print("  worst |ORCA - PySCF| : counterpoise %.4f   uncorrected %.4f kcal/mol"
          "   (bar: 0.001)" % (worst_cp, worst_unc))
    bad = [a for a in AOCHK if a[2] != a[3]]
    print("  basis identity: %d/%d parts have ORCA's printed AO dimension equal to the PySCF"
          " nao for the same geometry and basis" % (len(AOCHK) - len(bad), len(AOCHK)))
    for tag, label, ao_orca, ao_ps, nbas in bad:
        print("    MISMATCH %-28s %-8s ORCA=%s PySCF=%s (header field %s)"
              % (tag, label, ao_orca, ao_ps, nbas))
    # 5 parts (complex, 2 ghost monomers, 2 bare monomers) x 2 rungs per (system, basis).
    # The comment said "two rungs" while the expression omitted the factor, so the guard could
    # never pass: it printed NOT ESTABLISHED over a measurement that was inside the bar. A
    # check that cannot succeed is as useless as one that cannot fail; this one at least failed
    # safe, and the execution that exposed it is archived with that verdict line intact.
    expected = 2 * 5 * len(PLAN)
    same_basis = not bad and len(AOCHK) == expected
    ok = (worst_cp < 0.001 and worst_unc < 0.001 and same_basis and not missing
          and len(rows) == 2 * len(PLAN))
    print("  rows compared: %d/%d rungs;  rows with no PySCF reference: %d"
          % (len(rows), 2 * len(PLAN), len(missing)))
    print("  VERDICT: %s" % ("two programs agree to three decimals on BOTH the counterpoise"
                             " and the uncorrected difference, in the same AO space" if ok else
                             "NOT ESTABLISHED - worst CP diff %.4f, worst uncorrected diff"
                             " %.4f, basis identity on %d/%d parts, %d rows without a"
                             " reference, %d/%d rungs compared; agreement between two"
                             " different basis sets is not agreement"
                             % (worst_cp, worst_unc, len(AOCHK) - len(bad), len(AOCHK),
                                len(missing), len(rows), 2 * len(PLAN))))


if __name__ == "__main__":
    main()
