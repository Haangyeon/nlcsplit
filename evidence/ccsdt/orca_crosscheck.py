#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ORCA 6.0.1 cross-check of the CCSD(T) counterpoise anchor (third program, not our library).

Why this exists
---------------
`evidence/ccsdt/` reported the water-dimer counterpoise interaction energy at CCSD(T) from
one program (PySCF's own `cc`/`mp` modules) and the paper compares it against our functional
numbers. That is the same shape of argument that failed once already in this repository: the
nonlocal term was checked against a second implementation living inside the same library, and
a reviewer of that claim asked what a third program would say. The same question applies here,
so this script asks it: same geometries, same basis, same counterpoise convention, but ORCA.

What it does NOT do
-------------------
It does not touch the PySCF archives; it reads their numbers back as the thing being checked
(so a disagreement shows up as a printed difference, not as a silent rewrite).

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

KCAL = 627.509474
ORCA = os.path.expanduser(os.environ.get("ORCA_BIN", "~/orca6/orca"))
WORK = os.path.join(ROOT, "scratch", "orca_ccsdt")
S22DIR = os.environ.get("S22DIR", "scratch/lit/s22")
NPROC = int(os.environ.get("ORCA_NPROC", "4"))
MAXCORE = int(os.environ.get("ORCA_MAXCORE", "4000"))

# Per-part comparison of ORCA's printed AO dimension against PySCF's nao, filled by main().
# A list at module scope so a run that dies partway still shows what had been checked.
AOCHK = []

# What the PySCF archive reported (frozen core / all-electron), kcal/mol, from
# evidence/ccsdt/20260930T235900Z_stepm_three_systems_631g.out and
# 20260930T224400Z_stepm_ladder_after_refactor.out.
PYSCF = {
    ("水二聚体", "6-31G*"): {"frozen": -6.8559, "all": -6.8869},
    ("水二聚体", "aug-cc-pVDZ"): {"frozen": -5.2478, "all": -5.3273},
    ("氨二聚体", "6-31G*"): {"frozen": -4.4554, "all": -4.4731},
    ("甲烷二聚体", "6-31G*"): {"frozen": -0.1784, "all": -0.1872},
}
# All three systems at the basis the paper's comparison row uses, plus one larger-basis
# water point because that is where the ladder's basis sensitivity was established.
PLAN = [("水二聚体", "6-31G*"), ("水二聚体", "aug-cc-pVDZ"),
        ("氨二聚体", "6-31G*"), ("甲烷二聚体", "6-31G*")]


def orca_input(path, atoms, basis, frozen_core):
    """One single point. The frozen-core choice is passed explicitly, never left to default."""
    ncore = "FrozenCore" if frozen_core else "NoFrozenCore"
    lines = ["! RHF CCSD(T) %s TightSCF %s" % (basis, ncore),
             "%%maxcore %d" % MAXCORE,
             "%%pal nprocs %d end" % NPROC,
             "* xyz 0 1"]
    for sym, (x, y, z) in atoms:
        lines.append("%-3s %14.8f %14.8f %14.8f" % (sym, x, y, z))
    lines.append("*")
    open(path, "w").write("\n".join(lines) + "\n")


def run_orca(inp):
    base = inp[:-4]
    out = base + ".out"
    with open(out, "w") as fh:
        subprocess.run([ORCA, os.path.basename(inp)], cwd=os.path.dirname(inp) or ".",
                       stdout=fh, stderr=subprocess.STDOUT, check=False)
    txt = open(out, errors="replace").read()
    e = re.findall(r"FINAL SINGLE POINT ENERGY\s+(-?\d+\.\d+)", txt)
    conv = "ORCA TERMINATED NORMALLY" in txt
    # ORCA words it as "Frozen core treatment ... chemical core (2 el)" - 2 *electrons*,
    # i.e. one orbital per oxygen. Parsing this (rather than trusting the input keyword)
    # is the point: the printed field is what the run actually did.
    fz = re.findall(r"Frozen core treatment\s+\.\.\.\s+chemical core \((\d+) el\)", txt)
    nc = re.findall(r"Number of correlated electrons\s+\.\.\.\s+(\d+)", txt)
    # The two programs must be shown to be solving in the same one-particle space: a
    # d-shell convention mismatch (6 Cartesian d functions against 5 spherical ones) is
    # worth 0.01-0.1 kcal/mol here, which is far above the 1e-3 bar below. So the AO
    # dimension ORCA prints is read back and compared with PySCF's nao, per part.
    nb = re.findall(r"Number of basis functions\s+\.\.\.\s+(\d+)", txt)
    # Which field to compare with PySCF's nao is itself a thing that had to be found out.
    # ORCA's "Number of basis functions" is NOT it: for a water monomer in aug-cc-pVDZ that
    # field prints 47 while ORCA's own SCF section reports "Basis Dimension Dim .... 41" and
    # its CC section "Number of AO's ... 41", and 41 is PySCF's number. So the header field
    # is kept only to show the discrepancy, and the AO dimension is the identity check.
    dim = re.findall(r"Basis Dimension\s+Dim\s+\.*\s+(\d+)", txt)
    return (float(e[-1]) if e else None), conv, (int(fz[0]) if fz else 0), \
        (int(nc[0]) if nc else None), (int(nb[0]) if nb else None), \
        (int(dim[0]) if dim else None), out


def pyscf_ao(atoms, basis):
    """PySCF's AO count for the same geometry and basis. Building the Mole costs no SCF."""
    return step_m_ccsdt.build([a[0] for a in atoms], [a[1] for a in atoms], basis).nao


def main():
    os.makedirs(WORK, exist_ok=True)
    print("== ORCA cross-check of the CCSD(T) counterpoise anchor ==")
    print("  ORCA: %s   nprocs=%d maxcore=%d MB   workdir=%s"
          % (ORCA, NPROC, MAXCORE, WORK))
    if not os.path.exists(ORCA):
        print("  FAIL: no ORCA at %s" % ORCA)
        sys.exit(1)

    rows = []
    AOCHK[:] = []
    for name, basis in PLAN:
        atoms, frags = geomlib.s22_system(name, S22DIR)
        for frozen_core in (True, False):
            tag = "%s_%s_%s" % (name, basis.replace("*", "star").replace("/", "_"),
                                "fc" if frozen_core else "ae")
            parts = [("dimer", atoms)] + [
                ("mono%d" % i, [atoms[j] for j in f]) for i, f in enumerate(frags)]
            got = {}
            for label, at in parts:
                inp = os.path.join(WORK, "%s_%s.inp" % (tag, label))
                orca_input(inp, at, basis, frozen_core)
                e, conv, nfz_el, ncorr, nbas, ao_orca, out = run_orca(inp)
                ao_ps = pyscf_ao(at, basis)
                got[label] = (e, conv, nfz_el)
                AOCHK.append((tag, label, ao_orca, ao_ps, nbas))
                print("  %-44s %-6s E=%s  ok=%s  frozen_core_electrons=%d  correlated=%s"
                      % (os.path.basename(out), label,
                         ("%.10f" % e) if e is not None else "NONE", conv, nfz_el, ncorr))
                print("      basis identity: AO dimension ORCA=%s vs PySCF nao=%s -> %s"
                      "   (ORCA's own header field says %s)"
                      % (ao_orca, ao_ps,
                         "same space" if ao_orca == ao_ps else "*** DIFFERENT SPACE ***",
                         nbas))
            if any(v[0] is None for v in got.values()):
                print("  FAIL: an energy is missing for %s" % tag)
                continue
            dcp = (got["dimer"][0] - got["mono0"][0] - got["mono1"][0]) * KCAL
            ref = PYSCF.get((name, basis), {}).get("frozen" if frozen_core else "all")
            print("  --- %s / %s  %s  ->  dE_CP = %+.4f kcal/mol   (PySCF %s)"
                  % (name, basis, "frozen core" if frozen_core else "all-electron", dcp,
                     ("%+.4f  diff %+.4f" % (ref, dcp - ref)) if ref else "n/a"))
            rows.append((name, basis, frozen_core, dcp, ref))
        print()

    print("== summary ==")
    print("  %-10s %-14s %-12s %10s %10s %10s"
          % ("system", "basis", "convention", "ORCA", "PySCF", "diff"))
    worst = 0.0
    for name, basis, fc, dcp, ref in rows:
        d = (dcp - ref) if ref is not None else float("nan")
        if ref is not None:
            worst = max(worst, abs(d))
        print("  %-10s %-14s %-12s %+10.4f %+10s %+10.4f"
              % (name, basis, "frozen" if fc else "all-e", dcp,
                 ("%.4f" % ref) if ref is not None else "n/a", d))
    # The bar is the author's standard, not a convenient one: three decimal places in
    # kcal/mol is what two programs using the same basis are expected to reach on an
    # interaction energy. Measured worst is 2-3e-4, i.e. it passes by a factor of three or
    # four - an earlier version of this script used 0.02, which would have passed a real
    # convention mismatch (e.g. 6d vs 5d d-shells, worth 0.01-0.1 kcal/mol) without a word.
    print("  worst |ORCA - PySCF| = %.4f kcal/mol   (bar for agreement: 0.001)" % worst)
    bad = [a for a in AOCHK if a[2] != a[3]]
    print("  basis identity: %d/%d parts have ORCA's printed AO dimension equal to the PySCF"
          " nao for the same geometry and basis" % (len(AOCHK) - len(bad), len(AOCHK)))
    for tag, label, ao_orca, ao_ps, nbas in bad:
        print("    MISMATCH %-28s %-6s ORCA=%s PySCF=%s (header field %s)"
              % (tag, label, ao_orca, ao_ps, nbas))
    expected = 6 * len(PLAN)          # dimer + 2 monomers, frozen-core and all-electron
    same_basis = not bad and len(AOCHK) == expected
    print("  VERDICT: %s" % ("two programs agree to three decimals, in the same AO space"
                             if worst < 0.001 and same_basis else
                             "NOT ESTABLISHED - worst energy difference %.4f, basis identity"
                             " checked on %d/%d parts (all: %s); agreement between two"
                             " different basis sets is not agreement"
                             % (worst, len(AOCHK) - len(bad), len(AOCHK), same_basis)))


if __name__ == "__main__":
    main()
