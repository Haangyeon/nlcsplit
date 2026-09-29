"""Which bound form is loose, and how far the tree gets you: a measuring pass.

Why: `test_L1` failed on its own anti-vacuity guard - no pair was ever dropped. One number
("sum of bounds / |double sum| = 2.5e6") does not say *which* pairs are loose or why, and
"tighten the bound" is not actionable without that. This prints, per atom pair, the exact
block sum, both certified bounds (atom ball vs axis-aligned box), the geometry each used,
and then what the MAC recursion actually accepted at a given tau.

Read-only. Nothing here is a result; it is a measuring pass over existing code.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np                                        # noqa: E402
from pyscf import dft                                     # noqa: E402
from pyscf import gto                                     # noqa: E402

from nlcsplit import fastpair, geomlib, partition          # noqa: E402

HA2K = 627.50947400
BOHR2A = 0.529177210903
BASIS = "6-31g*"


def _mol(builder):
    return gto.M(atom=builder(), basis=BASIS, verbose=0, unit="Angstrom")


def report(tag, mol, level, taus=(1e-8, 1e-6, 1e-4)):
    mf = partition.scf_grid(mol, xc="wb97x_v", level=level, basis=BASIS)[0]
    t0 = time.perf_counter()
    exact = fastpair.screened_decomposition(mol, mf, level=level, scheme="becke")
    t_exact = time.perf_counter() - t0
    t0 = time.perf_counter()
    d = fastpair.screened_decomposition(mol, mf, level=level, scheme="becke",
                                        screen=None, bound="tree")
    t_tree_setup = time.perf_counter() - t0
    bs = d["blocks"]
    print(f"\n=== {tag}  level={level}  n_grid={d['n_grid']}"
          f"  kept_points={d['n_kept_points']}")
    print(f"    E_pair = {exact['E_pair']*HA2K:+.6f} kcal/mol"
          f"   atoms={d['n_atoms']}  leaves={d['n_leaves']}"
          f"   leafpairs={d['n_leafpairs_total']}")
    print(f"    原子块精确路径耗时 {t_exact:.2f} s；建树 {t_tree_setup:.2f} s")

    print(f"{'pair':>7} {'gapA':>6} {'boxA':>6} {'exact':>11} {'ball_bnd':>11}"
          f" {'box_bnd':>11} {'ball/ex':>9} {'box/ex':>9} {'nleafP':>7} {'nleafQ':>7}")
    tot_e = tot_ball = tot_box = 0.0
    rows = []
    for (a, q), v in sorted(exact["pairs"].items()):
        mult = 1.0 if a == q else 2.0
        P, Q = bs[a], bs[q]
        ex = abs(v) * mult * HA2K
        if a == q:
            continue
        ball = fastpair.ball_bound(P, Q, mult) * HA2K
        box = fastpair.node_bound(P.tree, Q.tree, mult) * HA2K
        tot_e += ex
        tot_ball += ball
        tot_box += box
        rows.append((ball / max(ex, 1e-300), a, q,
                     fastpair.ball_sep(P, Q) * BOHR2A,
                     fastpair.box_sep(P.tree, Q.tree) * BOHR2A, ex, ball, box,
                     len(fastpair.leaves(P.tree)), len(fastpair.leaves(Q.tree))))
    for r in sorted(rows, reverse=True):
        ratio, a, q, gball, gbox, ex, ball, box, nl, nq = r
        print(f"{a:>3}-{q:<3} {gball:>6.2f} {gbox:>6.2f} {ex:>11.3e} {ball:>11.3e}"
              f" {box:>11.3e} {ratio:>9.1e} {box/max(ex,1e-300):>9.1e}"
              f" {nl:>7d} {nq:>7d}")
    print(f"    sum(exact) = {tot_e:.4f}   sum(ball bound) = {tot_ball:.3e}"
          f"   sum(box bound) = {tot_box:.3e} kcal/mol")
    print(f"    ball/exact = {tot_ball/tot_e:.2e}   box/exact = {tot_box/tot_e:.2e}"
          f"   box is {tot_ball/tot_box:.1e}x tighter")
    print(f"    pairs whose *root* box bound is already <= 1e-8 Ha: "
          f"{sum(1 for r in rows if r[7] <= 1e-8*HA2K)}/{len(rows)}")

    for tau in taus:
        t0 = time.perf_counter()
        s = fastpair.screened_decomposition(mol, mf, level=level, screen=tau)
        el = time.perf_counter() - t0
        print(f"    tau={tau:g} Ha: accepted {s['n_accepted']:7d}  visited"
              f" {s['n_visited']:7d}  leafpairs {s['n_leafpairs_evaluated']:7d}"
              f"/{s['n_leafpairs_total']}  work_frac={s['work_frac']:7.3%}"
              f"  pointpairs kept {s['pointpairs_evaluated']:12d}"
              f"/{s['pointpairs_far'] + s['pointpairs_self']:12d}"
              f"  flop_frac={s['total_frac']:7.3%}"
              f"  cert={s['cert_err']:.3e} Ha  |dE|={abs(s['E_nl']-exact['E_nl']):.3e} Ha"
              f"  {el:6.1f} s  vs 原子块 {t_exact:.1f} s")
        assert s["cert_err"] + 1e-16 >= abs(s["E_nl"] - exact["E_nl"]), "界不成立"


if __name__ == "__main__":
    TAUS = (1e-12, 1e-10, 1e-8, 1e-6, 1e-4)
    report("h2o_dimer", _mol(geomlib.h2o_dimer), 1, taus=TAUS)
    report("benzene_sandwich", _mol(geomlib.benzene_sandwich), 0, taus=TAUS)
