#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every ghost monomer behind the counterpoise anchor, checked at the SCF level.

Why this is a separate file rather than two lines inside `nlcsplit/step_m_ccsdt.py`. The
ladder asserts the two structural properties that the counterpoise difference needs - the
monomer must have the complex's basis dimension and fewer electrons - and it reports the
convergence of the COMPLEX's RHF and CCSD. It does not report convergence for the ghost
monomers, and an unconverged ghost-monomer SCF would show up only as a wrong interaction
energy, which is the class of failure that already cost this directory a correction.

Adding the print to the shipped module now would mean the code that produces the aug batch
is not the code that produced the 6-31g* batch, for a diagnostics-only reason. So the check
lives here, in evidence, and runs the same functions the ladder runs.

Run from the repository root:
    PYTHONPATH=. python3 -u evidence/ccsdt/ghost_monomer_scf_check.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (ROOT, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from nlcsplit import geomlib, step_m_ccsdt                 # noqa: E402

KCAL = 627.509474
SYSTEMS = ("水二聚体", "氨二聚体", "甲烷二聚体", "苯-水", "苯-氨", "苯-甲烷",
           "苯二聚体(A)", "苯二聚体(B)")
BASES = [b.strip() for b in os.environ.get("BASES", "6-31g*").split(",") if b.strip()]
S22DIR = os.environ.get("S22DIR", os.path.join(ROOT, "scratch", "lit", "s22"))


def main():
    os.environ.setdefault("OMP_NUM_THREADS", "8")
    bad = []
    print("== ghost-monomer SCF check for the counterpoise anchor ==")
    print("  s22 dir=%s   bases=%s   rho threshold: an unconverged SCF is reported by PySCF's"
          " own converged flag, which is what this reads" % (S22DIR, BASES))
    print()
    print("  %-12s %-12s %-8s %6s %9s %14s %14s %10s"
          % ("system", "basis", "part", "nao", "converged", "E(RHF)", "bare E(RHF)",
             "dHa(ghost-bare)"))
    for name in SYSTEMS:
        atoms, frags = geomlib.s22_system(name, S22DIR)
        symbols = [a[0] for a in atoms]
        coords = [a[1] for a in atoms]
        for basis in BASES:
            dim = step_m_ccsdt.build(symbols, coords, basis)
            mf_c = dim.RHF()
            mf_c.kernel()
            print("  %-12s %-12s %-8s %6d %9s %14.10f %14s %10s"
                  % (name, basis, "complex", dim.nao, mf_c.converged, mf_c.e_tot, "-", "-"))
            if not mf_c.converged:
                bad.append((name, basis, "complex", "not converged"))
            for i, (s, c) in enumerate(step_m_ccsdt.cp_frag_specs(symbols, coords, frags)):
                gm = step_m_ccsdt.build(s, c, basis)
                assert gm.nao_nr() == dim.nao_nr(), "ghost nao != complex nao"
                assert gm.nelectron < dim.nelectron, "ghost electron count did not drop"
                m1 = gm.RHF()
                m1.kernel()
                bare = step_m_ccsdt.build([symbols[j] for j in frags[i]],
                                          [coords[j] for j in frags[i]], basis)
                m2 = bare.RHF()
                m2.kernel()
                # A ghost construction can only lower the energy: same nuclei, more functions.
                # If it does not, the SCF found a different state and the counterpoise number
                # is meaningless - so the sign of this difference is a check, not a curiosity.
                dd = m1.e_tot - m2.e_tot
                print("  %-12s %-12s %-8s %6d %9s %14.10f %14.10f %+10.6f"
                      % (name, basis, "ghost%d" % i, gm.nao, m1.converged, m1.e_tot,
                         m2.e_tot, dd))
                for tag, ok in (("ghost scf", m1.converged), ("bare scf", m2.converged)):
                    if not ok:
                        bad.append((name, basis, "ghost%d" % i, tag + " not converged"))
                if dd > 1e-8:
                    bad.append((name, basis, "ghost%d" % i,
                                "ghost RHF ABOVE bare by %.3e Ha - variational direction"
                                " violated, so the two calculations are not in the same"
                                " state" % dd))
    print()
    if bad:
        print("  VERDICT: %d problem(s):" % len(bad))
        for b in bad:
            print("     %s / %s / %s : %s" % b)
        sys.exit(1)
    print("  VERDICT: every complex and every ghost/bare monomer pair converged, and every"
          " ghost energy lies BELOW its bare counterpart (the variational direction a"
          " counterpoise construction must have). Basis dimensions checked by assertion.")


if __name__ == "__main__":
    main()
