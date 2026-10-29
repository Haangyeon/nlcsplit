#!/usr/bin/env python3
"""Figure: the eight S22 dimers, ray-traced with PyMOL, composed as a 2x4 panel grid.

Why PyMOL and not GaussView: GaussView 6 has no command-line or batch image export (checked:
`gview.exe -h` returns silently, and its only export path is the File > Save Image dialog), so
every GaussView figure would have to be driven through the GUI -- the camera angle then depends on
hand-dragging, which is exactly the "the reader cannot tell what they are looking at" failure this
figure is meant to fix. PyMOL's ray tracer gives a soft-lit ball-and-stick look with the camera set
from the coordinates.

The camera is built from the geometry: the ring normal fixes the pi-complex tilt, the
in-plane slip fixes the stacked-dimer axes, and the two ring normals fix the T-shape
view. Coordinates are rotated into that camera frame before rendering, so no PyMOL
`turn` guesswork is involved.

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


def _unit(v):
    v = np.asarray(v, dtype=float)
    n = float(np.linalg.norm(v))
    if n < 1e-12:
        raise ValueError("zero-length vector")
    return v / n


def _ring_normal(xyz, idx):
    p = xyz[idx] - xyz[idx].mean(axis=0)
    _, _, vt = np.linalg.svd(p)
    return _unit(vt[-1])


def _benzene_ring(frag, syms):
    carbons = [i for i in frag if syms[i] == "C"]
    return sorted(carbons) if len(carbons) == 6 else None


def camera_basis(name, syms, xyz, frags, theta_deg=65.0, alpha_deg=20.0):
    """Return (right, up, view) in the original frame; view points object -> camera.

    The axes are built from the geometry, not from trial rotations:
      pi complex   view 55 deg off the ring normal, with the small-molecule offset
                   vertical on screen, so the molecule reads as sitting above the ring;
      stack        slip horizontal and ring normal vertical, so the two rings sit
                   one above the other with the offset visible between them;
      T shape      side view 20 deg off the stem-ring normal: the stem ring is the
                   face-on hexagon and the top ring is a thin ellipse above it.
    """
    c0 = xyz[frags[0]].mean(axis=0)
    c1 = xyz[frags[1]].mean(axis=0)
    ring0 = _benzene_ring(frags[0], syms)
    ring1 = _benzene_ring(frags[1], syms)

    if ring0 and ring1:
        n0 = _ring_normal(xyz, ring0)
        n1 = _ring_normal(xyz, ring1)
        w = c1 - c0
        if abs(abs(float(n0 @ n1)) - 1.0) < 0.1:
            n = n0 if float(n0 @ w) > 0 else -n0
            slip = w - float(w @ n) * n
            if float(np.linalg.norm(slip)) < 0.2:
                p = xyz[ring0] - c0
                _, _, vt = np.linalg.svd(p)
                slip = vt[0]
            e = _unit(slip)
            phi = np.deg2rad(22.0)
            v = _unit(np.cos(phi) * _unit(np.cross(e, n)) + np.sin(phi) * n)
            u = _unit(n - float(n @ v) * v)
            r = _unit(np.cross(u, v))
            return r, u, v, "parallel-displaced: slip horizontal, rings stacked vertically"
        wu = _unit(w)
        top_is_1 = abs(float(n1 @ wu)) > abs(float(n0 @ wu))
        n_top = n1 if top_is_1 else n0
        n_stem = n0 if top_is_1 else n1
        if float(n_top @ w) < 0:
            n_top = -n_top
        # Side view: the stem ring is the face-on hexagon and the top ring is a
        # thin ellipse above it. Viewing along the top-ring normal (the old rule)
        # collapses the centroid separation along the view axis, which is why the
        # two rings overlapped on screen.
        beta = np.deg2rad(alpha_deg)
        v = _unit(np.cos(beta) * n_stem + np.sin(beta) * n_top)
        u = w - float(w @ v) * v
        if float(np.linalg.norm(u)) < 1e-6:
            u = n_top - float(n_top @ v) * v
        u = _unit(u)
        r = _unit(np.cross(u, v))
        return r, u, v, "T-shaped: stem ring face-on, top ring opened %g deg" % alpha_deg

    if ring0 or ring1:
        ring = ring0 if ring0 else ring1
        small = frags[1] if ring == ring0 else frags[0]
        n = _ring_normal(xyz, ring)
        w = xyz[small].mean(axis=0) - xyz[ring].mean(axis=0)
        if float(n @ w) < 0:
            n = -n
        inplane = w - float(w @ n) * n
        if float(np.linalg.norm(inplane)) < 0.15 * float(np.linalg.norm(w)):
            p = xyz[ring] - xyz[ring].mean(axis=0)
            _, _, vt = np.linalg.svd(p)
            inplane = vt[0]
        theta = np.deg2rad(theta_deg)
        # Screen-right must be a symmetry axis of the hexagon, otherwise the
        # ring reads as tilted even when its projected ellipse is level.  Pick
        # the in-plane ring axis nearest the small-molecule offset, then let
        # screen-right be the perpendicular axis (also a symmetry axis).
        ring_pts = xyz[ring]
        rc = ring_pts.mean(axis=0)
        cand = []
        for p in ring_pts:
            d = p - rc - float((p - rc) @ n) * n
            if float(np.linalg.norm(d)) > 1e-6:
                cand.append(_unit(d))
        for i in range(len(ring)):
            for j in range(i + 1, len(ring)):
                d = ring_pts[j] - ring_pts[i]
                if 1.2 < float(np.linalg.norm(d)) < 1.6:
                    m = 0.5 * (ring_pts[i] + ring_pts[j]) - rc
                    m = m - float(m @ n) * n
                    if float(np.linalg.norm(m)) > 1e-6:
                        cand.append(_unit(m))
        uniq = []
        for a in cand:
            if all(abs(float(a @ b)) < 0.999 for b in uniq):
                uniq.append(a)
        if float(np.linalg.norm(inplane)) > 1e-6:
            e_w = max(uniq, key=lambda a: abs(float(a @ inplane)))
            if float(e_w @ inplane) < 0:
                e_w = -e_w
        else:
            e_w = uniq[0]
        v = _unit(np.cos(theta) * n + np.sin(theta) * e_w)
        r = _unit(np.cross(n, e_w))
        u = _unit(np.cross(v, r))
        if float(u @ w) < 0:
            r, u = -r, -u
        return r, u, v, "pi complex: ring level on screen, small molecule above, tilt %g deg" % theta_deg

    # Small dimers: put the inter-fragment contact itself on screen-right.
    # The dashed H-bond is drawn O...H, so aligning to the centroid axis left
    # it visibly sloped; the contact vector makes it exactly horizontal.
    hb = hbonds(syms, xyz, frags)
    if hb:
        a, b = min(hb, key=lambda ij: float(np.linalg.norm(xyz[ij[1]] - xyz[ij[0]])))
        r = _unit(xyz[b] - xyz[a])
        note = "small dimer: H-bond horizontal"
    else:
        r = _unit(c1 - c0)
        note = "small dimer: contact axis horizontal"
    p = xyz - xyz.mean(axis=0)
    q = p - np.outer(p @ r, r)
    evals, evecs = np.linalg.eigh(q.T @ q)
    perp = [(float(np.linalg.norm(evecs[:, k] @ r)), k) for k in range(3)]
    perp = sorted([k for d, k in perp if d < 0.1])
    if len(perp) >= 2:
        k_small, k_large = perp[0], perp[-1]
        n_plane = evecs[:, k_small]
        side = evecs[:, k_large]
    else:
        n_plane = _unit(np.cross(r, [0.0, 0.0, 1.0]))
        side = _unit(np.cross(r, n_plane))
    beta = np.deg2rad(20.0)
    v = _unit(np.cos(beta) * n_plane + np.sin(beta) * side)
    u = _unit(np.cross(v, r))
    return r, u, v, note


def hbonds(syms, xyz, frags):
    """Inter-fragment acceptor (O/N) ... donor-H contacts, as (acceptor, H)."""
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


def pymol_settings():
    """Shared scene settings: GaussView/Avogadro-like ball-and-stick.

    Smooth soft sheen, no ray-traced black outline and no cast shadow.  The
    earlier matte+outline style read as a flat drawing; adding the outline back
    together with a strong highlight is what made the spheres look like plastic.
    """
    return [
        "hide everything",
        "show spheres, mol",
        "show sticks, mol",
        "set sphere_scale, 0.26",
        "set stick_radius, 0.10",
        "set valence, off",
        "color gray50, elem C",
        "color gray95, elem H",
        "color red, elem O",
        "color blue, elem N",
        "color yellow, elem S",
        "set ray_opaque_background, 1",
        "bg_color white",
        "set antialias, 2",
        "set ray_shadow, 0",
        "set specular, 0.22",
        "set shininess, 25",
        "set ambient, 0.36",
        "set direct, 0.58",
        "set orthoscopic, 1",
        "set depth_cue, 0",
        "set ray_trace_mode, 0",
        "set line_width, 0.4",
    ]


def build_pml(name, path, workdir):
    syms, xyz = read_xyz(path)
    frags = fragments(syms, xyz)
    hb = hbonds(syms, xyz, frags)
    r, u, v, note = camera_basis(name, syms, xyz, frags)
    center = xyz.mean(axis=0)
    xr = np.column_stack(((xyz - center) @ r, (xyz - center) @ u, (xyz - center) @ v))
    load_path = os.path.join(workdir, name + "_view.xyz")
    with open(load_path, "w", encoding="utf-8") as f:
        f.write("%d\n%s\n" % (len(syms), note))
        for s, p in zip(syms, xr):
            f.write("%-2s %12.6f %12.6f %12.6f\n" % (s, p[0], p[1], p[2]))
    camera = ["reset", "zoom mol, 0.90"]

    lines = ["load %s, mol" % load_path] + pymol_settings() + camera
    for k, (a, b) in enumerate(hb):
        # PyMOL's `index` is 1-based; passing the 0-based Python index drew the
        # dash between the wrong pair (for the water dimer, O...O instead of the
        # H...O contact).  The number label is left off: at panel size it sat on
        # top of the dashes and the caption already names the contact.
        lines += ["distance hb%d, index %d, index %d" % (k, a + 1, b + 1),
                  "label hb%d, \"\"" % k,
                  "set dash_color, gray40, hb%d" % k,
                  "set dash_gap, 0.24, hb%d" % k,
                  "set dash_length, 0.18, hb%d" % k]
    if hb:
        lines += ["hide labels"]
    png = os.path.join(workdir, name + ".png")
    lines += ["ray 1000, 760", "png %s, dpi=300" % png]
    pml = os.path.join(workdir, name + ".pml")
    open(pml, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return pml, png, note, 0.0, len(hb)


def _crop_white(path, pad=4):
    im = mpimg.imread(path)[..., :3]
    mask = np.any(im < 0.985, axis=2)
    ys, xs = np.where(mask)
    if len(xs) == 0:
        raise SystemExit("%s: 渲染图全白，无法构图" % path)
    y0, y1 = max(0, ys.min() - pad), min(im.shape[0], ys.max() + pad + 1)
    x0, x1 = max(0, xs.min() - pad), min(im.shape[1], xs.max() + pad + 1)
    return im[y0:y1, x0:x1]


def _panel_canvas(path, width=1000, height=760, fill=0.95):
    """Crop the render to its content and centre it with a fixed margin.

    The old composition pasted the full 1000x760 render, so any panel whose
    molecule reached the frame edge ended up touching its title. Cropping first
    makes the margin a property of the composition, not of the camera zoom.
    """
    from PIL import Image
    im = _crop_white(path)
    h, w = im.shape[:2]
    scale = min(width * fill / w, height * fill / h)
    nw, nh = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
    pil = Image.fromarray((np.clip(im, 0.0, 1.0) * 255).astype(np.uint8)).resize(
        (nw, nh), Image.LANCZOS)
    canvas = Image.new("RGB", (width, height), "white")
    canvas.paste(pil, ((width - nw) // 2, (height - nh) // 2))
    return np.asarray(canvas) / 255.0


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
        pml, png, note, score, nhb = build_pml(name, path, work)
        r = subprocess.run([args.pymol, "-cq", pml], capture_output=True, text=True)
        if not os.path.exists(png):
            raise SystemExit("%s: PyMOL 没出图。stderr:\n%s" % (name, (r.stdout + r.stderr)[-800:]))
        print("  %-18s %s  H-bonds %d" % (name, note, nhb))
        pngs.append(png)

    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["DejaVu Serif"],
        "mathtext.fontset": "cm",
    })
    fig, axes = plt.subplots(2, 4, figsize=(7.2, 3.95))
    for ax, (label, _), png in zip(axes.ravel(), PANELS, pngs):
        ax.imshow(_panel_canvas(png))
        ax.set_xticks([])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.set_title(label, fontsize=9.0, pad=4.0, fontfamily="serif",
                     fontweight="normal")
    fig.subplots_adjust(left=0.004, right=0.996, top=0.925, bottom=0.012,
                        wspace=0.045, hspace=0.24)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    fig.savefig(args.out, dpi=300)
    print("wrote %s (%d bytes)" % (args.out, os.path.getsize(args.out)))


if __name__ == "__main__":
    main()
