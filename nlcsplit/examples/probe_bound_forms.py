"""Per-block-pair diagnostic for the certified bound in fastpair.block_bound.

Why: test_L1 failed on its own anti-vacuity guard - no pair was ever dropped. One number
("sum of bounds / |double sum| = 2.5e6") does not say *which* pairs are loose or why, and
"tighten the bound" is not actionable without that. This prints, for every atom-block pair,
the exact block sum, the certified bound, their ratio, and the geometry the bound used.

Read-only. Nothing here is a result; it is a measuring pass over existing code.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np                                        # noqa: E402
from pyscf import dft, gto                                # noqa: E402

from nlcsplit import fastpair, geomlib, nlc, partition    # noqa: E402

HA2K = 627.50947400
BASIS = "6-31g*"


def _mol(builder):
    return gto.M(atom=builder(), basis=BASIS, verbose=0, unit="Angstrom")


def report(tag, mol, level):
    mf = dft.RKS(mol)
    mf.xc = "wb97x_v"
    mf.grids.level = level
    mf.kernel()
    d = fastpair.screened_decomposition(mol, mf, level=level, scheme="becke", screen=None)
    bs = d["blocks"]
    print(f"\n=== {tag}  level={level}  n_grid={d['n_grid']}  kept_points={d['n_kept_points']}")
    print(f"    E_pair = {d['E_pair']*HA2K:+.6f} kcal/mol   n_total={d['n_total']}")
    print(f"{'pair':>7} {'gap_A':>7} {'exact_kcal':>12} {'bound_kcal':>12} {'b/e':>10}"
          f" {'massP':>7} {'massQ':>7} {'w0P':>7} {'kP':>7}")
    tot_e = 0.0
    tot_b = 0.0
    rows = []
    for (a, q), v in sorted(d["pairs"].items()):
        mult = 1.0 if a == q else 2.0
        P, Q = bs[a], bs[q]
        gap = fastpair._gap(P, Q) * 0.529177210903   # bohr -> angstrom
        bnd = fastpair.block_bound(P, Q) * mult * HA2K
        ex = abs(v) * mult * HA2K
        tot_e += ex
        tot_b += bnd
        rows.append((bnd / ex if ex > 0 else float("inf"), a, q, gap, ex, bnd,
                     P.mass, Q.mass, P.w0min, P.kmin))
    for r in sorted(rows, reverse=True):
        ratio, a, q, gap, ex, bnd, mp, mq, w0p, kp = r
        print(f"{a:>3}-{q:<3} {gap:>7.2f} {ex:>12.4e} {bnd:>12.4e} {ratio:>10.1e}"
              f" {mp:>7.3f} {mq:>7.3f} {w0p:>7.3f} {kp:>7.3f}")
    print(f"    sum(exact per-pair magnitudes) = {tot_e:.6f} kcal/mol")
    print(f"    sum(bound)                     = {tot_b:.6f} kcal/mol")
    print(f"    ratio                          = {tot_b/tot_e:.3e}")
    # What the bound says each single pair must cost, vs the tolerance P1 needs.
    eps_target = 1e-8 * HA2K
    droppable = sum(1 for r in rows if r[5] <= eps_target)
    print(f"    pairs whose bound is already <= 1e-8 Ha ({eps_target:.3e} kcal/mol): "
          f"{droppable}/{len(rows)}")
    # and the distance at which an H-H-like pair would reach that bound
    print("    gap needed for the *smallest-mass* pair's bound to reach 1e-8 Ha:")
    small = min(rows, key=lambda r: r[6] * r[7])
    _, a, q, gap, ex, bnd, mp, mq, w0p, kp = small
    P, Q = bs[a], bs[q]
    for D in (5, 10, 20, 40, 80, 160):
        bb = 0.75 * mp * mq / ((w0p * D * D + kp) * (Q.w0min * D * D + Q.kmin)
                               * ((w0p * D * D + kp) + (Q.w0min * D * D + Q.kmin)))
        print(f"      D={D:>4} bohr ({D*0.529:>5.1f} A): bound={bb:.3e} Ha")


if __name__ == "__main__":
    report("h2o_dimer", _mol(geomlib.h2o_dimer), 1)
    report("benzene_sandwich", _mol(geomlib.benzene_sandwich), 0)
