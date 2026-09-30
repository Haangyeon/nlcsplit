#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Heteronuclear extension of the attribution referee — a sidecar, not a replacement.

WHY
---
`README.md` section 10 declared the referee homonuclear-only, and gave a reason: the
package side is evaluated on a PySCF grid whose Becke radii come from the *atom types*
in `mk_mol`, and both centres were `He`.  Making the two Gaussians unequal therefore
forces a choice of element - a choice of the very partition convention under test -
before the offset means anything.

That argument has a hole, and this script is where it gets closed.  Two of the three
things being compared do NOT depend on the element choice:

  * the exact reference (3-D tensor GL, 5-D cylindrical reduction, importance-sampled
    Monte-Carlo) needs no nuclei at all - it is a six-dimensional integral of an
    analytic density pair;
  * the density-factor soft partition is defined from the density alone.

Only the owner/Becke assignment does, and only through the radii table.  So instead of
avoiding the element choice this script measures it: the principled mapping is
**Z = the electron number of that Gaussian** (n=2 -> He, 4 -> Be, 6 -> C), and every
heteronuclear configuration is additionally run with one deliberately different label
pair at the SAME density, so the reader can see how much of the offset is the radii
table and how much is the attribution rule.

WHAT IS REUSED AND WHAT IS SKIPPED
----------------------------------
Same `referee_lib`, same orders, same truncation, same production-grid call as `run.py`.
The referee's own *disjoint half-box* node set is NOT used: its construction assumes two
congruent boxes and is therefore a homonuclear device.

Nothing in `results.json`, `table.md` or `mc_tight.json` is touched.  Output is
`outputs/hetero.json` plus stdout.

THE FALSIFICATION THAT MAKES THIS WORTH TRUSTING
------------------------------------------------
Row 0 is homonuclear and must reproduce the archived (alpha=1.0, sep=4.0) reference
value and package cross term.  If it drifts, this script is a divergent copy and every
heteronuclear row in it is worthless.  The verdict is printed and stored.

Run (repository root):
    PYTHONPATH=. python3 -u evidence/attribution_referee/hetero.py
"""

import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (ROOT, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from pyscf import gto                                        # noqa: E402
from pyscf.dft import numint                                # noqa: E402
from nlcsplit import nlc, partition                          # noqa: E402
import referee_lib as rl                                     # noqa: E402

KCAL = 627.509474
OUT = os.path.join(HERE, "outputs")
N5D, N3D, F_TRUNC, PKG_LEVEL = 48, 20, 5.0, 3
MC_M = int(os.environ.get("HETERO_MC", "1000000"))
Z_BY_N = {2.0: "He", 4.0: "Be", 6.0: "C"}

# (alpha_A, alpha_B, n_A, n_B, sep, label pairs).  Row 0 is the homonuclear control and
# its FIRST pair must be the archived one ("He/He") or the falsification is meaningless:
# run.py always labelled both centres He whatever the electron number, whereas the
# principled Z=n mapping here would say Be for a 4-electron Gaussian.  Reporting both is
# deliberate - it measures the radii table's effect on a density that is not even
# heteronuclear.
CONFIGS = [
    (1.0, 1.0, 4.0, 4.0, 4.0, ["He/He", "Be/Be"]),
    (1.0, 2.0, 2.0, 4.0, 4.0, ["He/Be", "He/Ne"]),
    (1.0, 0.5, 2.0, 6.0, 6.0, ["He/C", "He/Be"]),
    (2.0, 0.5, 4.0, 6.0, 2.5, ["Be/C", "He/C"]),
]


def mk_mol(sep, symA, symB):
    return gto.M(atom="%s 0 0 %.6f; %s 0 0 %.6f" % (symA, -0.5 * sep, symB, 0.5 * sep),
                 basis="sto-3g", verbose=0, unit="B")


def df_soft(ra, rb):
    tot = ra + rb
    with np.errstate(divide="ignore", invalid="ignore"):
        fa = np.where(tot > 0.0, ra / np.where(tot > 0.0, tot, 1.0), 0.5)
    return np.vstack([fa, 1.0 - fa])


def one(aa, ab, na, nb, sep, pairs, B, C):
    t0 = time.time()
    gp = rl.GaussPair(sep=sep, alpha_a=aa, alpha_b=ab, n_a=na, n_b=nb)
    ntot = na + nb
    r = dict(alpha_a=aa, alpha_b=ab, n_a=na, n_b=nb, sep=sep,
             hetero=bool(aa != ab or na != nb))

    # ---- exact reference: three routes that share nothing but the density --
    ex = {}
    for tag in ("AA", "BB", "AB", "BA", "TOT"):
        ex[tag], d = rl.integral_cyl5d(gp, B, C, N5D, int(1.5 * N5D), F_TRUNC, which=tag)
        ex["nf_" + tag] = d["nonfinite"]
    ex["CLOSED"] = 0.5 * (ex["AA"] + ex["BB"]) + ex["AB"]
    r.update(I_AA=ex["AA"], I_BB=ex["BB"], I_AB=ex["AB"], I_BA=ex["BA"],
             E_nl_exact_sum=ex["CLOSED"], E_nl_exact_undecomposed=ex["TOT"],
             closure=abs(ex["CLOSED"] - ex["TOT"]),
             sym_ab_ba=abs(ex["BA"] - ex["AB"]), sym_aa_bb=abs(ex["BB"] - ex["AA"]),
             nonfinite_AB=ex["nf_AB"])

    b3, _ = rl.integral_box3d(gp, B, C, N3D, F_TRUNC, which="AB")
    r["I_AB_3d"] = b3
    r["d_3d_vs_5d"] = b3 - ex["AB"]
    mcp, mcs = rl.mc_integral(gp, B, C, "AB", m=MC_M)
    r["I_AB_mc"], r["I_AB_mc_se"] = mcp, mcs
    r["mc_vs_5d"] = mcp - ex["AB"]
    r["bar_ha"] = max(2.0 * mcs, abs(mcp - ex["AB"]), abs(b3 - ex["AB"]))

    beta = (1.0 / 32.0) * (3.0 / (B * B)) ** 0.75
    r["E_loc_exact"] = beta * ntot

    # ---- package machinery on the production grid, once per label choice ---
    for pair in pairs:
        symA, symB = pair.split("/")
        mol = mk_mol(sep, symA, symB)
        X, W, owner = partition.atom_partition(mol, level=PKG_LEVEL, scheme="becke")
        rhoP, sigP, raP, rbP = gp.state(X)
        integ = float(np.sum(W * rhoP))
        if abs(integ - ntot) > 0.05 * ntot:
            raise AssertionError("grid integrates %s to %.6f, expected %.1f"
                                 % (pair, integ, ntot))
        prod = nlc.fragment_decomposition(X, W, rhoP, sigP, [[0], [1]], b=B, C=C,
                                          rho_floor=nlc.RHO_FLOOR, owner=owner)
        dfp = nlc.fragment_decomposition(X, W, rhoP, sigP, [[0], [1]], b=B, C=C,
                                         rho_floor=nlc.RHO_FLOOR, soft=df_soft(raP, rbP))
        w0, kap, keep = nlc.vv10_fields(rhoP, sigP, B, C)
        add = float(prod["E_nl"] - nlc.pair_energy(X, W * rhoP, w0, kap,
                                                   np.where(keep)[0], np.where(keep)[0]))
        k = "grid_%s" % pair.replace("/", "_")
        r[k] = dict(
            labels=pair, n=int(len(X)), integrated=integ, n_dropped=int(prod["n_dropped"]),
            inter=prod["inter"][(0, 1)], df_inter=dfp["inter"][(0, 1)],
            d_headline=prod["inter"][(0, 1)] - ex["AB"],
            d_grid_only=dfp["inter"][(0, 1)] - ex["AB"],
            d_partition=prod["inter"][(0, 1)] - dfp["inter"][(0, 1)],
            rel_to_cross=(prod["inter"][(0, 1)] - ex["AB"]) / abs(ex["AB"]),
            additivity=add)
    r["runtime_s"] = time.time() - t0
    return r


def main():
    B, C = numint.NumInt().nlc_coeff("wb97x_v")[0][0]
    print("== heteronuclear attribution referee (sidecar; results.json untouched) ==")
    print("  b=%.10f C=%.10f  (read from PySCF, never hard-coded)" % (B, C))
    print("  N5D=%d N3D=%d F_TRUNC=%.1f PKG_LEVEL=%d MC m=%d"
          % (N5D, N3D, F_TRUNC, PKG_LEVEL, MC_M))
    print("  element mapping: Z = electrons in that Gaussian -> %s" % Z_BY_N)
    rows = [one(*cfg, B=B, C=C) for cfg in CONFIGS]

    for r in rows:
        tag = "CONTROL(homonuclear)" if not r["hetero"] else "heteronuclear"
        print("\n--- %s  alpha=(%.2f,%.2f) n=(%.1f,%.1f) sep=%.2f  [%.0fs]"
              % (tag, r["alpha_a"], r["alpha_b"], r["n_a"], r["n_b"], r["sep"],
                 r["runtime_s"]))
        print("    I_AB(5-D) = %+.12e   I_BA = %+.12e   |I_BA - I_AB| = %.3e"
              % (r["I_AB"], r["I_BA"], r["sym_ab_ba"]))
        print("    I_AA      = %+.12e   I_BB = %+.12e   |I_BB - I_AA| = %.3e%s"
              % (r["I_AA"], r["I_BB"], r["sym_aa_bb"],
                 "" if r["hetero"] else "   <- must be 0 here"))
        print("    closure |0.5(I_AA+I_BB)+I_AB - undecomposed| = %.3e   nonfinite=%s"
              % (r["closure"], r["nonfinite_AB"]))
        print("    bar = max(2se, |MC-5D|, |3D-5D|) = %.3e Ha   (MC se %.3e, "
              "3D-5D %.3e, MC-5D %.3e)"
              % (r["bar_ha"], r["I_AB_mc_se"], r["d_3d_vs_5d"], r["mc_vs_5d"]))
        for key, v in r.items():
            if not key.startswith("grid_"):
                continue
            res = "RESOLVED" if abs(v["d_headline"]) > r["bar_ha"] else "below bar"
            print("    labels %-6s N=%d dropped=%d  inter=%+.12e" % (v["labels"], v["n"],
                  v["n_dropped"], v["inter"]))
            print("        d_headline %+.4e (%+.2f%% of I_AB) -> %s | d_grid_only %+.4e"
                  " | d_partition %+.4e | additivity %.2e"
                  % (v["d_headline"], 100 * v["rel_to_cross"], res, v["d_grid_only"],
                     v["d_partition"], v["additivity"]))
        sys.stdout.flush()

    ctrl = rows[0]
    arch = json.load(open(os.path.join(OUT, "results.json")))
    hit = [x for x in arch["rows"]
           if abs(x["alpha"] - 1.0) < 1e-12 and abs(x["sep"] - 4.0) < 1e-12]
    if not hit:
        print("\nFAIL: no (alpha=1.0, sep=4.0) row in results.json to control against")
        sys.exit(1)
    a = hit[0]
    if "grid_He_He" not in ctrl:
        print("\nFAIL: control row did not run the archived He/He labelling")
        sys.exit(1)
    dI = ctrl["I_AB"] - a["I_AB"]
    dG = ctrl["grid_He_He"]["inter"] - a["grid_inter"]
    print("\n== control vs the archived homonuclear run (this is the falsification) ==")
    print("  I_AB       : %+.12e  vs  %+.12e   diff %.3e" % (ctrl["I_AB"], a["I_AB"], dI))
    print("  grid inter : %+.12e  vs  %+.12e   diff %.3e  [grid_He_He]"
          % (ctrl["grid_He_He"]["inter"], a["grid_inter"], dG))
    ok = max(abs(dI), abs(dG)) < 1e-12
    print("  verdict    : %s" % ("PASS - not a divergent copy" if ok else
                                 "FAIL - heteronuclear rows are unusable"))

    with open(os.path.join(OUT, "hetero.json"), "w") as fh:
        json.dump(dict(n5d=N5D, n3d=N3D, f_trunc=F_TRUNC, pkg_level=PKG_LEVEL, mc_m=MC_M,
                       b=float(B), C=float(C), z_by_n={str(k): v for k, v in Z_BY_N.items()},
                       control_diff_I_AB=dI, control_diff_grid_inter=dG,
                       control_verdict="PASS" if ok else "FAIL", rows=rows), fh, indent=1)
    print("wrote outputs/hetero.json (%d rows)" % len(rows))
    if not ok:
        sys.exit(2)


if __name__ == "__main__":
    main()
