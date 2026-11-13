#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Which token spelling of a ghost atom does THIS ORCA 6.0.1 binary accept, and what does each
one actually build?

Why a probe rather than the manual. `evidence/ccsdt/orca_crosscheck.py` needs counterpoise
monomers: the partner's atoms must stay in the geometry as basis functions carrying no nuclear
charge. The installation ships the answer - ~/orca6/CompoundScripts/BSSE/BSSECorrection.cmp,
NOTE 4, "Ghost atom (':' after the symbol of the element)" - but a documented spelling is still
a claim about a binary until that binary accepts it, and there are three ways for it to be
wrong in a way that looks like success: the parser could reject the line (loud), silently drop
the partner (quiet, and it would print a *plausible* monomer energy), or keep the functions only
in the SCF and not the correlation space (invisible at this level, which is why the CCSD(T)
comparison in 20261003T0558Z is the one that closes the question).

The discriminating quantity is therefore the basis dimension ORCA prints, not the energy:
a real ghost construction must land on the complex's 36, a dropped partner lands on 18.
The rejected spellings are kept in the same run as negative controls - a probe that only shows
the working form cannot show that the test distinguishes anything.

RHF-only, seconds. Run (WSL, repository root):
    python3 -u scratch/orca_ghost_probe.py
"""
import os
import re
import subprocess
import sys


def _find_root(start):
    """Locate the repository by walking up to the package, not by a path baked in here.

    The archived copy of this probe lives in evidence/ccsdt/ and the working copy in scratch/,
    so a literal /mnt/e/... line would be true in one of the two and silently wrong in the other.
    """
    d = os.path.abspath(start)
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, "nlcsplit", "geomlib.py")):
            return d
        d = os.path.dirname(d)
    raise SystemExit("cannot find the repository root (nlcsplit/geomlib.py) from %s" % start)


ROOT = os.environ.get("REPO_ROOT") or _find_root(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from nlcsplit import geomlib            # noqa: E402
from nlcsplit import step_m_ccsdt       # noqa: E402

ORCA = os.path.expanduser("~/orca6/orca")
WORK = os.path.join(ROOT, "scratch", "orca_ghost_probe")
BASIS = "6-31G*"

# (label, keep-fragment-index or None for the complex, spelling, drop-the-rest, extra keywords)
CASES = [
    ("colon_ghost",            0, ":",      False, ""),
    ("bare_monomer_dropped",   0, "",       True,  ""),
    ("complex_all_real",    None, "",       False, ""),
    ("word_Ghost_prefix",      0, "Ghost ", False, ""),
    ("word_Ghost_nospace",     0, "Ghost",  False, ""),
    ("colon_ghost_frozen",     0, ":",      False, "FrozenCore"),
]


def build(name, symbols, coords, keep, spelling, drop, extra):
    lines = []
    for i, (s, c) in enumerate(zip(symbols, coords)):
        real = keep is None or i in keep
        if real:
            tok = s
        elif spelling == ":":
            tok = s + ":"
        elif spelling:
            tok = spelling + s
        else:
            if not drop:
                tok = s          # complex with no ghosts: every atom real
            else:
                continue
        lines.append("%-8s %14.8f %14.8f %14.8f" % (tok, *c))
    path = os.path.join(WORK, name + ".inp")
    open(path, "w").write(
        "! RHF %s TightSCF %s\n%%maxcore 1000\n%%pal nprocs 2 end\n* xyz 0 1\n%s\n*\n"
        % (BASIS, extra, "\n".join(lines)))
    return path


def read_out(out):
    txt = open(out, errors="replace").read()
    dim = re.findall(r"Basis Dimension\s+Dim\s+\.*\s+(\d+)", txt)
    e = re.findall(r"FINAL SINGLE POINT ENERGY\s+(-?\d+\.\d+)", txt)
    complaint = [l.strip() for l in txt.splitlines() if "expected in COORDS" in l]
    return (int(dim[0]) if dim else None, float(e[-1]) if e else None,
            "ORCA TERMINATED NORMALLY" in txt, complaint[:1])


def main():
    os.makedirs(WORK, exist_ok=True)
    atoms, frags = geomlib.s22_system("水二聚体", os.path.join(ROOT, "scratch/lit/s22"))
    symbols = [a[0] for a in atoms]
    coords = [a[1] for a in atoms]
    ps_complex = step_m_ccsdt.build(symbols, coords, BASIS).nao
    ps_bare = step_m_ccsdt.build([symbols[i] for i in frags[0]],
                                 [coords[i] for i in frags[0]], BASIS).nao
    print("== ORCA 6.0.1 ghost-atom token spelling, decided by running it ==")
    print("  basis %s   PySCF nao: complex=%d  bare monomer=%d" % (BASIS, ps_complex, ps_bare))
    print("  the acceptance test is the basis dimension, because a construction that silently")
    print("  drops the partner still prints a plausible energy at the bare dimension.")
    print()
    for name, keep, spelling, drop, extra in CASES:
        inp = build(name, symbols, coords, set(frags[keep]) if keep is not None else None,
                    spelling, drop, extra)
        with open(inp + ".out", "w") as fh:
            rc = subprocess.run([ORCA, os.path.basename(inp)], cwd=WORK, stdout=fh,
                                stderr=subprocess.STDOUT, check=False).returncode
        dim, e, ok, complaint = read_out(inp + ".out")
        if name == "complex_all_real":
            # Nothing is ghosted here; it is the reference dimension and the archived complex
            # energy, so it also shows the probe's geometry path agrees with the record.
            verdict = "reference: the complex itself, no ghosts"
        elif name == "bare_monomer_dropped":
            verdict = ("partner dropped on purpose (dim == bare); this is what the broken"
                       " construction looked like from the inside - a plausible energy"
                       " reported at the wrong dimension")
        elif dim == ps_complex:
            verdict = "ghost functions ARE in the space (dim == complex)"
        elif dim == ps_bare:
            verdict = "partner silently dropped (dim == bare) -> NOT a counterpoise part"
        elif dim is None:
            verdict = "rejected by the parser"
        else:
            verdict = "unexpected dimension %s" % dim
        print("  %-22s rc=%-3d normal=%-5s Dim=%-5s E=%-14s %s"
              % (name, rc, ok, dim, ("%.8f" % e) if e is not None else "-", verdict))
        for ln in complaint:
            print("        parser said: %s" % ln[:140])
    print()
    print("  Three negative controls are in this run on purpose: the two rejected spellings")
    print("  show the parser is not silently inventing a construction from anything, and the")
    print("  dropped-partner case shows what the WRONG construction returns (dim 18, an energy")
    print("  that looks fine). Without them, dim==36 for the colon form would not be evidence.")


if __name__ == "__main__":
    main()
