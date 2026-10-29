"""Draw the JCTC TOC/abstract graphic for the pair-attribution manuscript.

The graphic is illustrative, not a data figure: the measured values live in the
paper and its provenance appendix.  Output is exactly 3.25 x 1.75 in at 600 dpi.
"""
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch


ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "figs" / "toc_graphic_attribution.png"

BLUE = "#2b6cb0"
ORANGE = "#c05621"
PURPLE = "#6b46c1"
GREY = "#718096"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 7,
    "axes.linewidth": 0.6,
})


def blob(ax, xy, width, height, color, label):
    ax.add_patch(Ellipse(xy, width, height, facecolor=color, alpha=0.16,
                         edgecolor=color, linewidth=0.8))
    ax.text(xy[0], xy[1] + height / 2 + 0.045, label, ha="center", va="bottom",
            fontsize=7.5, fontweight="bold", color=color)


def points(ax, xy, width, height, color, n=7):
    cx, cy = xy
    offsets = [(-0.115, -0.045), (-0.060, 0.035), (0.000, -0.060),
               (0.055, 0.050), (0.110, -0.020), (-0.020, 0.105),
               (0.070, 0.105)]
    return [(cx + dx * width / 0.30, cy + dy * height / 0.22)
            for dx, dy in offsets[:n]]


fig = plt.figure(figsize=(3.25, 1.75), facecolor="white")
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

# Left: the folded kernel has already summed over j, so no pair can be addressed.
blob(ax, (0.19, 0.58), 0.30, 0.40, GREY, "folded kernel")
for x, y in points(ax, (0.19, 0.58), 0.30, 0.40, GREY):
    ax.add_patch(Circle((x, y), 0.014, facecolor=GREY, edgecolor="white", lw=0.4))
ax.text(0.19, 0.20, "per-point values\npair index lost", ha="center", va="center",
        fontsize=7, color="0.25", linespacing=1.25)

ax.add_patch(FancyArrowPatch((0.37, 0.60), (0.48, 0.60), arrowstyle="-|>",
                             mutation_scale=10, lw=1.0, color="0.35"))
ax.text(0.425, 0.68, "this work", ha="center", va="bottom", fontsize=6.5,
        color="0.35", style="italic")

# Right: the explicit (i, j) sum keeps the pair index; cross-fragment pairs are E_AB.
blob(ax, (0.66, 0.58), 0.22, 0.40, BLUE, "A")
blob(ax, (0.86, 0.58), 0.22, 0.40, ORANGE, "B")
left_pts = points(ax, (0.66, 0.58), 0.22, 0.40, BLUE, n=5)
right_pts = points(ax, (0.86, 0.58), 0.22, 0.40, ORANGE, n=5)
# Intra-fragment pairs are E_AA / E_BB; only the purple lines cross the cut.
for i, j in [(0, 1), (2, 4)]:
    ax.plot([left_pts[i][0], left_pts[j][0]], [left_pts[i][1], left_pts[j][1]],
            color=BLUE, lw=0.8, alpha=0.75, zorder=1)
for i, j in [(0, 2), (1, 3)]:
    ax.plot([right_pts[i][0], right_pts[j][0]], [right_pts[i][1], right_pts[j][1]],
            color=ORANGE, lw=0.8, alpha=0.75, zorder=1)
for i in (0, 2, 3):
    p, q = left_pts[i], right_pts[(i + 2) % len(right_pts)]
    ax.plot([p[0], q[0]], [p[1], q[1]], color=PURPLE, lw=0.8, alpha=0.75, zorder=1)
for x, y in left_pts:
    ax.add_patch(Circle((x, y), 0.014, facecolor=BLUE, edgecolor="white", lw=0.4, zorder=2))
for x, y in right_pts:
    ax.add_patch(Circle((x, y), 0.014, facecolor=ORANGE, edgecolor="white", lw=0.4, zorder=2))
ax.text(0.615, 0.72, r"$E_{AA}$", ha="center", va="center", fontsize=7.5, color=BLUE)
ax.text(0.905, 0.72, r"$E_{BB}$", ha="center", va="center", fontsize=7.5, color=ORANGE)
ax.text(0.76, 0.54, r"$E_{AB}$", ha="center", va="center", fontsize=8,
        color=PURPLE, fontweight="bold",
        bbox=dict(facecolor="white", edgecolor="none", pad=0.3, alpha=0.8))
ax.text(0.76, 0.18, "explicit $(i,j)$ sum\n$E_{\\rm NL}=E_{AA}+E_{BB}+E_{AB}$",
        ha="center", va="center", fontsize=7, color="0.25", linespacing=1.25)

fig.savefig(OUT, dpi=600, facecolor="white")
print(OUT)
