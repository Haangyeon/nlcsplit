#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Does ORCA 6.0.1's CCSD(T) module reproduce the counterpoise anchor with ghost atoms?

The colon syntax came from the installation itself (~/orca6/CompoundScripts/BSSE/
BSSECorrection.cmp, NOTE 4: "Ghost atom (':' after the symbol of the element)"), and a
first probe confirmed a partner written `O:` leaves the basis dimension at the complex's 36.
What is still open is whether the **correlation** module carries those functions through
rather than the SCF alone, and whether `FrozenCore` still means "one oxygen 1s" once a
second, charge-less oxygen sits in the geometry. Both are facts about this binary, and they
decide whether evidence/ccsdt/orca_crosscheck.py can become a real counterpoise cross-check
or has to be downgraded in the text.

The PySCF side runs through the same functions the ladder uses, so a mismatch is a
difference between programs and not between inputs. Bare monomers are computed as well,
because the archived -6.8559 is the uncorrected quantity: reproducing it in this execution
is what makes the new counterpoise number comparable to the record it replaces.
"""
import os
import re
import subprocess
import sys


def _find_root(start):
    """Find the repository by walking up to the package instead of a baked-in path.

    The working copy is in scratch/ and the archived producer copy lands in evidence/ccsdt/.
    """
    d = os.path.abspath(start)
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, "nlcsplit", "geomlib.py")):
            return d
        d = os.path.dirname(d)
    raise SystemExit("cannot find the repository root (nlcsplit/geomlib.py) from %s" % start)


ROOT = os.environ.get("REPO_ROOT") or _find_root(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from nlcsplit import geomlib, step_m_ccsdt          # noqa: E402

ORCA = os.path.expanduser("~/orca6/orca")
WORK = os.path.join(ROOT, "scratch", "orca_ghost_cc")
BASIS = "6-31G*"
KCAL = 627.509474


def orca_run(name, symbols, coords, extra=""):
    os.makedirs(WORK, exist_ok=True)
    inp = os.path.join(WORK, name + ".inp")
    lines = ["%-6s %14.8f %14.8f %14.8f" % (s, *c) for s, c in zip(symbols, coords)]
    open(inp, "w").write("! RHF CCSD(T) %s TightSCF %s\n%%maxcore 4000\n%%pal nprocs 4 end\n"
                         "* xyz 0 1\n%s\n*\n" % (BASIS, extra, "\n".join(lines)))
    out = inp + ".out"
    with open(out, "w") as fh:
        rc = subprocess.run([ORCA, os.path.basename(inp)], cwd=WORK,
                            stdout=fh, stderr=subprocess.STDOUT, check=False).returncode
    txt = open(out, errors="replace").read()
    grab = lambda pat: (re.findall(pat, txt) or [None])  # noqa: E731
    e = grab(r"FINAL SINGLE POINT ENERGY\s+(-?\d+\.\d+)")[0]
    dim = grab(r"Basis Dimension\s+Dim\s+\.*\s+(\d+)")[0]
    fz = grab(r"Frozen core treatment\s+\.\.\.\s+(\S[^\n]*?)\s*\n")[0]
    nc = grab(r"Number of correlated electrons\s+\.\.\.\s+(\d+)")[0]
    return dict(rc=rc, ok="ORCA TERMINATED NORMALLY" in txt,
                e=float(e) if e else None, dim=int(dim) if dim else None,
                fz=fz.strip() if fz else None, nc=int(nc) if nc else None,
                err=[l.strip() for l in txt.splitlines() if "ERROR" in l][:3], out=out)


def pyscf_rung(symbols, coords, frags, fz_d, fz_m, specs):
    d = step_m_ccsdt.correlated(step_m_ccsdt.build(symbols, coords, BASIS),
                                 fz_d)["CCSD(T)"][0]
    cp = [step_m_ccsdt.correlated(step_m_ccsdt.build(s, c, BASIS), fz_m[i])["CCSD(T)"][0]
          for i, (s, c) in enumerate(specs)]
    un = [step_m_ccsdt.correlated(
        step_m_ccsdt.build([symbols[j] for j in f], [coords[j] for j in f], BASIS),
        fz_m[i])["CCSD(T)"][0] for i, f in enumerate(frags)]
    return ((d - cp[0] - cp[1]) * KCAL, (d - un[0] - un[1]) * KCAL)


def main():
    atoms, frags = geomlib.s22_system("水二聚体", os.path.join(ROOT, "scratch/lit/s22"))
    symbols = [a[0] for a in atoms]
    coords = [a[1] for a in atoms]
    frag_syms = [[symbols[i] for i in f] for f in frags]
    specs = step_m_ccsdt.cp_frag_specs(symbols, coords, frags)

    print("== PySCF (the library the paper's anchor comes from) ==")
    ps = {}
    for rung, ae in (("frozen", False), ("all-el", True)):
        fz_d = step_m_ccsdt.freeze_plan([symbols], all_electron=ae)[0]
        fz_m = step_m_ccsdt.freeze_plan(frag_syms, all_electron=ae)
        ps[rung] = pyscf_rung(symbols, coords, frags, fz_d, fz_m, specs)
        print("  %-7s complex freezes %d orbital(s), fragments %s -> dE_CP %+.4f  "
              "dE_unc %+.4f  BSSE %+.4f"
              % (rung, fz_d, fz_m, ps[rung][0], ps[rung][1], ps[rung][0] - ps[rung][1]))
    print("  ghost monomer nao: %s (complex nao=%d)"
          % (str([step_m_ccsdt.build(s, c, BASIS).nao for s, c in specs]),
             step_m_ccsdt.build(symbols, coords, BASIS).nao))
    print()

    for rung, ae, extra in (("frozen", False, "FrozenCore"), ("all-el", True,
                                                              "NoFrozenCore")):
        got = {"dimer": orca_run("orca_dimer_%s" % rung, symbols, coords, extra)}
        for i, f in enumerate(frags):
            keep = set(f)
            got["ghost%d" % i] = orca_run("orca_ghost%d_%s" % (i, rung),
                                          [s + ("" if j in keep else ":")
                                           for j, s in enumerate(symbols)], coords, extra)
            got["bare%d" % i] = orca_run("orca_bare%d_%s" % (i, rung),
                                         [symbols[j] for j in f], [coords[j] for j in f],
                                         extra)
        print("== ORCA 6.0.1, %s ==" % extra)
        for k in ("dimer", "ghost0", "ghost1", "bare0", "bare1"):
            r = got[k]
            print("  %-7s rc=%-3d normal=%-5s Dim=%-4s E=%-16s core=%-24s correlated_e=%s"
                  % (k, r["rc"], r["ok"], r["dim"],
                     ("%.10f" % r["e"]) if r["e"] is not None else "NONE", r["fz"], r["nc"]))
            for ln in r["err"]:
                print("        %s" % ln[:130])
        if all(got[k]["e"] is not None and got[k]["ok"] for k in got):
            ocp = (got["dimer"]["e"] - got["ghost0"]["e"] - got["ghost1"]["e"]) * KCAL
            oun = (got["dimer"]["e"] - got["bare0"]["e"] - got["bare1"]["e"]) * KCAL
            print("  ORCA dE_CP = %+.4f   PySCF %+.4f   diff %+.4f kcal/mol"
                  % (ocp, ps[rung][0], ocp - ps[rung][0]))
            print("  ORCA dE_unc= %+.4f   PySCF %+.4f   diff %+.4f kcal/mol"
                  % (oun, ps[rung][1], oun - ps[rung][1]))
            print("  basis identity: complex Dim=%s vs PySCF nao=%d; ghost monomers %s,%s"
                  % (got["dimer"]["dim"],
                     step_m_ccsdt.build(symbols, coords, BASIS).nao,
                     got["ghost0"]["dim"], got["ghost1"]["dim"]))
        else:
            print("  no usable set of five energies -> ORCA gives no counterpoise number"
                  " under this convention.")
        print()


if __name__ == "__main__":
    main()
