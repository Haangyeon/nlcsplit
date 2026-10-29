#!/usr/bin/env python3
"""Ionic control: F- ... H2O at wB97X-V/aug-cc-pVDZ.

Geometry: fw_opt.xyz in this directory, optimized at the same level with ORCA 6.
Fragments are F- (atom 0) and H2O (atoms 1-3).  The complex carries charge -1;
the water monomer is neutral, the F- monomer carries charge -1.  Counterpoise
monomers use ghost functions of the partner and the same charge.
"""
import json
import os
import sys
import time

os.environ.setdefault("NCBAS", "aug-cc-pvdz")
os.environ.setdefault("NCPC", "1")

import numpy as np
from pyscf import gto

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, ROOT)

from nlcsplit import geomlib, partition, nlc  # noqa: E402
from nlcsplit.step_f_dispersion import terms, KCAL  # noqa: E402

BASIS = "aug-cc-pvdz"
SCHEMES = ["becke", "becke-becke-rad", "becke-treutler", "stratmann"]
XYZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fw_opt.xyz")


def build(atoms, charge):
    return gto.M(atom=[(s, c) for s, c in atoms], basis=BASIS, charge=charge,
                 spin=0, verbose=0, unit="Angstrom")


def frag_atoms(atoms, keep, ghost):
    return ([(atoms[i][0], atoms[i][1]) for i in keep]
            + [("ghost-" + atoms[i][0], atoms[i][1]) for i in ghost])


def frag_terms(atoms, keep, ghost, charge, level, tag):
    mol = gto.M(atom=frag_atoms(atoms, keep, ghost), basis=BASIS, charge=charge,
                spin=0, verbose=0, unit="Angstrom")
    return terms(mol, level, tag)


def pair_terms(mol, frags, mf, level):
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


def metrics(atoms):
    def d(i, j):
        return float(np.linalg.norm(np.asarray(atoms[i][1]) - np.asarray(atoms[j][1])))

    def angle(i, j, k):
        a = np.asarray(atoms[i][1]) - np.asarray(atoms[j][1])
        b = np.asarray(atoms[k][1]) - np.asarray(atoms[j][1])
        return float(np.degrees(np.arccos(np.clip(a @ b / np.linalg.norm(a) / np.linalg.norm(b), -1, 1))))

    return {"F-O_A": d(0, 1), "F-H_A": d(0, 2), "O-H_A": [d(1, 2), d(1, 3)],
            "H-O-H_deg": angle(2, 1, 3)}


def run(level, atoms):
    t0 = time.time()
    frags = [[0], [1, 2, 3]]
    mol = build(atoms, charge=-1)
    d = terms(mol, level, f"F-...H2O complex level {level}")
    own = {}
    for k, (keep, ch) in enumerate((([0], -1), ([1, 2, 3], 0))):
        ghost = [i for i in range(4) if i not in keep]
        s = frag_terms(atoms, keep, [], ch, level, f"fragment {k} level {level}")
        own[k] = s
    dcp_terms = []
    for keep, ch in (([0], -1), ([1, 2, 3], 0)):
        ghost = [i for i in range(4) if i not in keep]
        s = frag_terms(atoms, keep, ghost, ch, level, f"ghost fragment level {level}")
        dcp_terms.append(s["e_tot"])
    dcp = (d["e_tot"] - sum(dcp_terms)) * KCAL
    pint = pair_terms(mol, frags, d["mf"], level)
    row = {"level": level, "basis": BASIS, "natm": 4,
           "frags": frags, "charge": -1,
           "dtot": (d["e_tot"] - sum(s["e_tot"] for s in own.values())) * KCAL,
           "dxc": (d["e_xc"] - sum(s["e_xc"] for s in own.values())) * KCAL,
           "dnlc": (d["e_nlc"] - sum(s["e_nlc"] for s in own.values())) * KCAL,
           "dcp": dcp, "pint": pint,
           "span": max(pint.values()) - min(pint.values()),
           "ratio_pfrz_dnlc": pint["becke"] / ((d["e_nlc"] - sum(s["e_nlc"] for s in own.values())) * KCAL),
           "seconds": round(time.time() - t0, 1)}
    print("level %d: Dtot %+.4f Dxc %+.4f DNLC %+.4f CP %+.4f P_becke %+.4f span %.4f ratio %.3f %.0fs"
          % (level, row["dtot"], row["dxc"], row["dnlc"], dcp, row["pint"]["becke"],
             row["span"], row["ratio_pfrz_dnlc"], row["seconds"]), flush=True)
    print("  P_frz: " + ", ".join("%s %+.4f" % (s, pint[s]) for s in SCHEMES), flush=True)
    return row


if __name__ == "__main__":
    atoms = geomlib.read_xyz(XYZ)
    assert len(atoms) == 4 and [s for s, _ in atoms] == ["F", "O", "H", "H"]
    print("geometry:", json.dumps(metrics(atoms), indent=1, ensure_ascii=False), flush=True)
    rows = [run(level, atoms) for level in (1, 2)]
    out = {"system": "F-...H2O", "geometry_source": os.path.relpath(XYZ, ROOT),
           "geometry_method": "wB97X-V/aug-cc-pVDZ Opt TightSCF TightOpt, ORCA 6",
           "basis": BASIS, "schemes": SCHEMES, "metrics": metrics(atoms),
           "rows": rows, "host": os.uname().nodename,
           "pyscf_version": __import__("pyscf").__version__}
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fw_nlc.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, allow_nan=False)
    print("wrote fw_nlc.json", flush=True)
