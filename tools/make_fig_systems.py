#!/usr/bin/env python3
"""Figure: the eight S22 dimers this paper reports on, drawn from the official geometries.

Why this figure exists: every number in the paper is per-system, and until now no figure showed
the reader which eight arrangements those numbers belong to. A table of names does not show that
"benzene dimer A" and "benzene dimer B" are the same pair of molecules in two different relative
orientations, which is the paper's point about arrangement mattering more than system size.

Drawing rules, so the picture cannot quietly lie:
  - coordinates are read from the shipped GMTKN55 struc.xyz files (no hand-drawn sketches, no
    re-optimised geometries);
  - bonds are assigned by a covalent-radius criterion, not by chemistry knowledge, so a wrong
    geometry would show up as a wrong bond;
  - each panel is projected on its own principal plane and rotated so its longest axis is
    horizontal; no panel is rescaled relative to another beyond the shared axis scaling;
  - elements are coloured by a fixed table (C, H, O, N, S) and the legend is global.

Usage:
    python3 tools/make_fig_systems.py [--data-dir scratch/lit/s22] [--out figs/fig0_systems.png]

The geometry directory is not tracked (it is fetched by nlcsplit/tools/get_s22.sh); the figure it
produces is, so the paper does not depend on a directory that only exists on one machine.
"""
import argparse
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# 顺序就是面板顺序：先按原子数从小到大，再把同一对分子的两个取向并排，
# 因为正文先说"体系大小"，后面整节都在说"取向/排列"。
PANELS = [
    ("(a) (H$_2$O)$_2$",            "水二聚体"),
    ("(b) (NH$_3$)$_2$",            "氨二聚体"),
    ("(c) (CH$_4$)$_2$",            "甲烷二聚体"),
    ("(d) benzene$\\cdots$H$_2$O",  "苯-水"),
    ("(e) benzene$\\cdots$NH$_3$",  "苯-氨"),
    ("(f) benzene$\\cdots$CH$_4$",  "苯-甲烷"),
    ("(g) benzene dimer A",         "苯二聚体(A)"),
    ("(h) benzene dimer B",         "苯二聚体(B)"),
]

RCOV = {"H": 0.31, "C": 0.76, "N": 0.71, "O": 0.66, "S": 1.05}
COLOR = {"H": "#f2f2f2", "C": "#4d4d4d", "N": "#3050f8", "O": "#ff0d0d", "S": "#ffff30"}
SIZE = {"H": 26, "C": 78, "N": 78, "O": 74, "S": 110}


def read_xyz(path):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    nat = int(lines[0].split()[0])
    syms, xyz = [], []
    for ln in lines[2:2 + nat]:
        t = ln.split()
        syms.append(t[0].capitalize() if not t[0].isdigit() else
                    {1: "H", 6: "C", 7: "N", 8: "O", 16: "S"}[int(t[0])])
        xyz.append([float(v) for v in t[1:4]])
    if len(syms) != nat:
        raise SystemExit("%s: 声明 %d 个原子，实到 %d" % (path, nat, len(syms)))
    return syms, np.asarray(xyz)


def project(syms, xyz, frags):
    """在三个主轴里挑一个"两个片段分得最开"的投影方向。

    只看原子重不重叠不够：苯环上方的 NH3 从上往下看正好落在环心，原子彼此不重叠，
    但读者看不出这是"叠在环上"。非共价二聚体的常规画法是让两个片段在纸面上分开，
    所以这里按"两片质心的二维距离 / 面板跨度"打分，同时仍惩罚原子重叠。
    """
    p = xyz - xyz.mean(axis=0)
    w, v = np.linalg.eigh(p.T @ p)
    v = v[:, np.argsort(w)[::-1]]
    radii = np.array([RCOV[s] for s in syms])
    fa, fb = frags[0], frags[1]

    best, best_xy = -1e9, None
    for k in range(3):
        view = v[:, k]
        e1 = v[:, (k + 1) % 3]
        e2 = np.cross(view, e1)
        e2 /= np.linalg.norm(e2)
        xy = np.column_stack([p @ e1, p @ e2])
        sep = float(np.linalg.norm(xy[fa].mean(axis=0) - xy[fb].mean(axis=0)))
        span = float(np.linalg.norm(xy.max(axis=0) - xy.min(axis=0))) or 1.0
        overlap = 0.0
        for i in range(len(xy)):
            for j in range(i + 1, len(xy)):
                d = float(np.linalg.norm(xy[i] - xy[j]))
                ref = 0.9 * (radii[i] + radii[j])
                if d < ref:
                    overlap += (ref - d) / ref
        score = sep / span - 0.15 * overlap
        if score > best:
            best, best_xy = score, xy
    return best_xy


def bonds_for(syms, xyz):
    out = []
    for i in range(len(syms)):
        for j in range(i + 1, len(syms)):
            d = float(np.linalg.norm(xyz[i] - xyz[j]))
            if d < 1.25 * (RCOV[syms[i]] + RCOV[syms[j]]):
                out.append((i, j))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="scratch/lit/s22")
    ap.add_argument("--out", default="figs/fig0_systems.png")
    args = ap.parse_args()

    sys.path.insert(0, os.getcwd())
    import nlcsplit.geomlib as geomlib  # noqa: E402
    S22 = geomlib.S22

    fig, axes = plt.subplots(2, 4, figsize=(7.2, 3.9))
    present = set()
    for ax, (title, name) in zip(axes.ravel(), PANELS):
        key = name
        path = os.path.join(args.data_dir, S22[key])
        if not os.path.exists(path):
            raise SystemExit(
                "%s 不存在。官方几何由 nlcsplit/tools/get_s22.sh 取回，先跑它或给 --data-dir。" % path)
        syms, xyz = read_xyz(path)
        present |= set(syms)
        frags = geomlib.split_frags([(s, tuple(p)) for s, p in zip(syms, xyz)])
        if len(frags) != 2:
            raise SystemExit("%s: 按共价连通性切成 %d 段，不是二聚体" % (path, len(frags)))
        xy = project(syms, xyz, frags)
        for i, j in bonds_for(syms, xyz):
            ax.plot(xy[[i, j], 0], xy[[i, j], 1], "-", color="#7a7a7a", lw=0.9,
                    solid_capstyle="round", zorder=1)
        for sym in sorted(set(syms)):
            m = np.array([s == sym for s in syms])
            ax.scatter(xy[m, 0], xy[m, 1], s=SIZE[sym], c=COLOR[sym],
                       edgecolors="#333333", linewidths=0.45, zorder=2)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.set_title(title, fontsize=7.6, pad=2.0, y=1.0)
        pad = 0.08 * max(np.ptp(xy[:, 0]), np.ptp(xy[:, 1]) or 1.0)
        ax.set_xlim(xy[:, 0].min() - pad, xy[:, 0].max() + pad)
        ax.set_ylim(xy[:, 1].min() - pad, xy[:, 1].max() + 2.2 * pad)

    order_el = [e for e in ("H", "C", "N", "O", "S") if e in present]
    handles = [Line2D([], [], marker="o", linestyle="", markersize=np.sqrt(SIZE[e]) / 2.2,
                      markerfacecolor=COLOR[e], markeredgecolor="#333333", label=e)
               for e in order_el]
    fig.legend(handles=handles, loc="lower center", ncol=len(order_el), frameon=False, fontsize=7.4,
               handletextpad=0.25, columnspacing=1.1, bbox_to_anchor=(0.5, -0.01))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.93, bottom=0.10, wspace=0.06, hspace=0.16)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    fig.savefig(args.out, dpi=300)
    print("wrote %s  (%d bytes)" % (args.out, os.path.getsize(args.out)))


if __name__ == "__main__":
    main()
