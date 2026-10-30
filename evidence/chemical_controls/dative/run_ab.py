#!/usr/bin/env python3
"""Evaluate one chemically motivated dative complex (H3N-BH3) with the existing pipeline.

Geometry: ab_opt.xyz in this directory, optimized at wB97X-V/6-31G* with ORCA 6.
The four real-space partition schemes and the counterpoise definition are inherited
from nlcsplit.step_h_s22; no new attribution code is introduced here.

This is a feasibility/evidence run, not a manuscript edit.  It reports:
  - geometry invariants (B-N, N-H, B-H, H-N-H, H-B-H)
  - Delta E_int, Delta E_xc, Delta E_NLC, counterpoise interaction energy
  - P_frz for becke / becke-becke-rad / becke-treutler / stratmann
  - four-scheme span at grid levels 1 and 2
"""
import json
import os
import sys
import time

# The S22 driver reads these at import time; keep the new run on the same basis/grid.
os.environ.setdefault("NCBAS", "6-31g*")
os.environ.setdefault("NCLV", "1")
os.environ.setdefault("NCPC", "1")

import numpy as np
from pyscf import dft, gto

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, ROOT)

from nlcsplit import geomlib, partition, nlc  # noqa: E402
from nlcsplit.step_f_dispersion import terms, KCAL  # noqa: E402
from nlcsplit.step_h_s22 import (  # noqa: E402
    BASIS, NUMKEYS, SCHEMES, counterpoise, geomlib_sub,
)

XYZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ab_opt.xyz")


def metrics(atoms):
    def d(i, j):
        return float(np.linalg.norm(np.asarray(atoms[i][1]) - np.asarray(atoms[j][1])))

    def angle(i, j, k):
        a = np.asarray(atoms[i][1]) - np.asarray(atoms[j][1])
        b = np.asarray(atoms[k][1]) - np.asarray(atoms[j][1])
        c = float(a @ b / np.linalg.norm(a) / np.linalg.norm(b))
        return float(np.degrees(np.arccos(np.clip(c, -1.0, 1.0))))

    # Atom order follows ab_opt.xyz: N,H,H,H,B,H,H,H.
    return {
        "B-N_A": d(0, 4),
        "N-H_A": [d(0, i) for i in (1, 2, 3)],
        "B-H_A": [d(4, i) for i in (5, 6, 7)],
        "H-N-H_deg": [angle(i, 0, j) for i, j in ((1, 2), (1, 3), (2, 3))],
        "H-B-H_deg": [angle(i, 4, j) for i, j in ((5, 6), (5, 7), (6, 7))],
    }


def pair_terms_level(mol, frags, mf, level):
    """Same four-scheme core as step_h_s22.pair_terms, with level passed explicitly.

    The production helper reads its module-level LEVEL (set from NCLV at import).
    Calling it from a second grid level would silently reuse the first level's
    partition points.  This local copy makes the grid level an argument.
    """
    ni = mf._numint
    b, C = ni.nlc_coeff(mf.xc)[0][0]
    dm = mf.make_rdm1()
    out = {}
    for scheme in SCHEMES:
        X, W, owner = partition.atom_partition(mol, level=level, scheme=scheme)
        rho = ni.eval_rho(mol, ni.eval_ao(mol, X, deriv=1), dm, xctype="GGA")
        sig = rho[1] ** 2 + rho[2] ** 2 + rho[3] ** 2
        res = nlc.fragment_decomposition(X, W, rho[0], sig, frags,
                                         b=b, C=C, owner=owner)
        out[scheme] = res["inter"][(0, 1)] * KCAL
    return out


def run(level, atoms, frags):
    t0 = time.time()
    mol = gto.M(atom=[(s, c) for s, c in atoms], basis=BASIS, verbose=0, unit="Angstrom")
    d = terms(mol, level, f"H3N-BH3 complex level {level}")
    mono = {k: 0.0 for k in NUMKEYS}
    for f in frags:
        s = terms(geomlib_sub(mol, f), level, f"H3N-BH3 fragment level {level}")
        for k in NUMKEYS:
            mono[k] += s[k]
    pint = pair_terms_level(mol, frags, d["mf"], level)
    dcp = counterpoise(mol, frags, level)
    row = {
        "level": level,
        "basis": BASIS,
        "natm": mol.natm,
        "frags": frags,
        "dtot": (d["e_tot"] - mono["e_tot"]) * KCAL,
        "dxc": (d["e_xc"] - mono["e_xc"]) * KCAL,
        "dnlc": (d["e_nlc"] - mono["e_nlc"]) * KCAL,
        "dcp": dcp,
        "pint": pint,
        "span": max(pint.values()) - min(pint.values()),
        "ratio_pfrz_dnlc": None,
        "seconds": round(time.time() - t0, 1),
    }
    # ratio = P_frz[becke] / Delta E_NLC, both in kcal/mol (the S22 table's P/Delta_sup)
    row["ratio_pfrz_dnlc"] = row["pint"]["becke"] / row["dnlc"] if row["dnlc"] else None
    print("level %d: Dtot %+.4f  Dxc %+.4f  DNLC %+.4f  CP %+.4f  "
          "P_becke %+.4f  span %.4f  ratio %.3f  %.0fs"
          % (level, row["dtot"], row["dxc"], row["dnlc"], dcp,
             row["pint"]["becke"], row["span"], row["ratio_pfrz_dnlc"], row["seconds"]),
          flush=True)
    print("  P_frz: " + ", ".join("%s %+.4f" % (s, pint[s]) for s in SCHEMES), flush=True)
    return row


if __name__ == "__main__":
    atoms = geomlib.read_xyz(XYZ)
    frags = geomlib.split_frags(atoms)
    assert len(frags) == 2, f"expected two fragments, got {frags}"
    assert sorted(i for f in frags for i in f) == list(range(len(atoms)))
    print("geometry:", json.dumps(metrics(atoms), indent=1, ensure_ascii=False), flush=True)
    print("fragments:", frags, "basis:", BASIS, flush=True)
    rows = [run(level, atoms, frags) for level in (1, 2)]
    out = {
        "system": "H3N-BH3",
        "geometry_source": os.path.relpath(XYZ, ROOT),
        "geometry_method": "wB97X-V/6-31G* Opt TightSCF TightOpt, ORCA 6",
        "basis": BASIS,
        "schemes": SCHEMES,
        "metrics": metrics(atoms),
        "rows": rows,
        "host": os.uname().nodename,
        "pyscf_version": __import__("pyscf").__version__,
    }
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ab_nlc.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, allow_nan=False)
    print("wrote ab_nlc.json", flush=True)
