#!/usr/bin/env python3
"""Figure: the eight S22 dimers, ray-traced with PyMOL, composed as a 2x4 panel grid.

Why PyMOL and not GaussView: GaussView 6 has no command-line or batch image export (checked:
`gview.exe -h` returns silently, and its only export path is the File > Save Image dialog), so
every GaussView figure would have to be driven through the GUI -- the camera angle then depends on
hand-dragging, which is exactly the "the reader cannot tell what they are looking at" failure this
figure is meant to fix. PyMOL's ray tracer gives the same publication look (glossy spheres, shadows,
depth cueing) with the camera set from the coordinates.

The camera rule is the one from the matplotlib version, kept because it worked: of the three
principal axes, view along the one that puts the two fragment centroids farthest apart on screen.
A stacked complex seen face-on hides the second molecule inside the ring; seen edge-on it splits
into two recognisable halves.

Hydrogen bonds are drawn as dashed lines for donor-acceptor H...O/N contacts between 1.5 and
2.4 A, computed from the coordinates, not guessed.

Usage:
    python3 tools/render_systems_pymol.py --out figs/fig0_systems.png
"""
import argparse
import os
import subprocess
import sys
import tempfile

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

PANELS = [
    ("(a) (H$_2$O)$_2$",           "水二聚体"),
    ("(b) (NH$_3$)$_2$",           "氨二聚体"),
    ("(c) (CH$_4$)$_2$",           "甲烷二聚体"),
    ("(d) benzene$\\cdots$H$_2$O", "苯-水"),
    ("(e) benzene$\\cdots$NH$_3$", "苯-氨"),
    ("(f) benzene$\\cdots$CH$_4$", "苯-甲烷"),
    ("(g) benzene dimer A",        "苯二聚体(A)"),
    ("(h) benzene dimer B",        "苯二聚体(B)"),
]

RCOV = {"H": 0.31, "C": 0.76, "N": 0.71, "O": 0.66, "S": 1.05}
Z2S = {1: "H", 6: "C", 7: "N", 8: "O", 16: "S"}


def read_xyz(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    nat = int(lines[0].split()[0])
    syms, xyz = [], []
    for ln in lines[2:2 + nat]:
        t = ln.split()
        syms.append(Z2S[int(t[0])] if t[0].isdigit() else t[0].capitalize())
        xyz.append([float(v) for v in t[1:4]])
    if len(syms) != nat:
        raise SystemExit("%s: declared %d atoms, found %d" % (path, nat, len(syms)))
    return syms, np.asarray(xyz)


def fragments(syms, xyz):
    """Covalent-connectivity split into the two monomers (BFS over a distance graph)."""
    n = len(syms)
    adj = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if np.linalg.norm(xyz[i] - xyz[j]) < 1.25 * (RCOV[syms[i]] + RCOV[syms[j]]):
                adj[i].append(j)
                adj[j].append(i)
    seen, comps = set(), []
    for s in range(n):
        if s in seen:
            continue
        stack, comp = [s], set()
        while stack:
            x = stack.pop()
            if x in comp:
                continue
            comp.add(x)
            stack += [y for y in adj[x] if y not in comp]
        seen |= comp
        comps.append(sorted(comp))
    if len(comps) != 2:
        raise SystemExit("切出 %d 个片段，不是二聚体" % len(comps))
    return comps


def view_axis(syms, xyz, frags):
    """Return 'x', 'y' or 'z' in PyMOL's frame, chosen so the two monomers separate on screen."""
    p = xyz - xyz.mean(axis=0)
    best, best_k = -1e9, 0
    for k in range(3):
        # projecting onto the plane spanned by the other two axes => viewing along axis k
        keep = [a for a in range(3) if a != k]
        xy = p[:, keep]
        sep = np.linalg.norm(xy[frags[0]].mean(axis=0) - xy[frags[1]].mean(axis=0))
        span = np.linalg.norm(xy.max(axis=0) - xy.min(axis=0)) or 1.0
        if sep / span > best:
            best, best_k = sep / span, k
    return "xyz"[best_k], best


def hbonds(syms, xyz, frags):
    """Inter-fragment H...O/N contacts in the hydrogen-bond window, as (donor_heavy+1) ... H."""
    out = []
    for i in range(len(syms)):
        if syms[i] not in ("O", "N"):
            continue
        for j in range(i + 1, len(syms)):
            if syms[j] != "H":
                continue
            if (i in frags[0]) == (j in frags[0]):
                continue          # only between the two monomers
            d = float(np.linalg.norm(xyz[i] - xyz[j]))
            if 1.5 <= d <= 2.4:
                out.append((min(i, j), max(i, j)))
    return out


def build_pml(name, path, workdir):
    syms, xyz = read_xyz(path)
    frags = fragments(syms, xyz)
    axis, score = view_axis(syms, xyz, frags)
    hb = hbonds(syms, xyz, frags)
    lines = [
        "load %s, mol" % path,
        "hide everything",
        "show spheres, mol",
        "show sticks, mol",
        "set sphere_scale, 0.24",
        "set stick_radius, 0.10",
        "set valence, off",
        "color gray60, elem C",
        "color white, elem H",
        "color red, elem O",
        "color blue, elem N",
        "color yellow, elem S",
        "set ray_opaque_background, 1",
        "bg_color white",
        "set antialias, 2",
        "set ray_shadow, 1",
        "set specular, 0.30",
        "set shininess, 30",
        "set ambient, 0.30",
        "set direct, 0.45",
        "set orthoscopic, 1",
        "orient mol",
    ]
    # 视角：默认交给 orient（沿方差最小的主轴看，平面分子正面朝读者）。
    # 三格需要一次固定的小转：两个 benzene···X 叠层在 orient 下正好把环看成一条线，
    # 平行位移二聚体两环投影几乎重合——各转一个写死的角度，让环面与偏移看得见。
    TURN = {"苯-氨": "turn y, 90", "苯-甲烷": "turn y, 90", "苯二聚体(A)": "turn y, 28"}
    lines += [TURN.get(name, "turn x, -6")]
    for k, (a, b) in enumerate(hb):
        lines += ["distance hb%d, index %d, index %d" % (k, a, b),
                  "set dash_color, gray40, hb%d" % k,
                  "set dash_gap, 0.35, hb%d" % k,
                  "set dash_length, 0.30, hb%d" % k]
    png = os.path.join(workdir, name + ".png")
    lines += ["ray 1000, 760", "png %s, dpi=300" % png]
    pml = os.path.join(workdir, name + ".pml")
    open(pml, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return pml, png, axis, score, len(hb)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="scratch/lit/s22")
    ap.add_argument("--out", default="figs/fig0_systems.png")
    ap.add_argument("--pymol", default=os.path.expanduser("~/.local/bin/pymol"))
    args = ap.parse_args()

    sys.path.insert(0, os.getcwd())
    import nlcsplit.geomlib as geomlib

    work = tempfile.mkdtemp(prefix="sysfig_")
    pngs = []
    for label, name in PANELS:
        path = os.path.join(args.data_dir, geomlib.S22[name])
        if not os.path.exists(path):
            raise SystemExit(
                "%s 不存在。官方几何由 nlcsplit/tools/get_s22.sh 取回，先跑它或给 --data-dir。" % path)
        pml, png, axis, score, nhb = build_pml(name, path, work)
        r = subprocess.run([args.pymol, "-cq", pml], capture_output=True, text=True)
        if not os.path.exists(png):
            raise SystemExit("%s: PyMOL 没出图。stderr:\n%s" % (name, (r.stdout + r.stderr)[-800:]))
        print("  %-18s view-axis %s (sep/span %.2f)  H-bonds %d" % (name, axis, score, nhb))
        pngs.append(png)

    fig, axes = plt.subplots(2, 4, figsize=(7.2, 3.55))
    for ax, (label, _), png in zip(axes.ravel(), PANELS, pngs):
        im = mpimg.imread(png)
        ax.imshow(im)          # 不裁：上一版按 2% 裁边把 (e)(f) 的分子切掉了
        ax.set_xticks([])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.set_title(label, fontsize=8.2, pad=1.5)
    fig.subplots_adjust(left=0.005, right=0.995, top=0.94, bottom=0.01, wspace=0.03, hspace=0.10)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    fig.savefig(args.out, dpi=300)
    print("wrote %s (%d bytes)" % (args.out, os.path.getsize(args.out)))


if __name__ == "__main__":
    main()
