"""One typographic sheet for every figure in the paper.

Why this module exists: the seven figures were written one at a time, so each carried its
own figsize, its own font sizes (7.0-9.5 pt), its own dpi (200 or 300) and its own way of
labelling panels.  Nothing was wrong with the data, but as a set they read as seven
different papers.  Every figure now imports this module, so one change moves all of them
together and a reviewer sees a single hand.

Nothing here touches data: callers keep their arrays and their printed guards untouched.
"""
import matplotlib

INK = "#1a1a1a"
BLUE = "#2b6cb0"
ORANGE = "#c05621"
SLATE = "#4a5568"
GREEN = "#2f855a"
GRID = "#e2e2e2"


def rc():
    matplotlib.rcParams.update({
        "font.family": "serif",
        "font.serif": ["DejaVu Serif"],
        "mathtext.fontset": "cm",
        "font.size": 8.0,
        "axes.titlesize": 8.6,
        "axes.labelsize": 8.4,
        "xtick.labelsize": 7.6,
        "ytick.labelsize": 7.6,
        "legend.fontsize": 7.4,
        "axes.linewidth": 0.6,
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 3.0,
        "ytick.major.size": 3.0,
        "xtick.minor.width": 0.5,
        "ytick.minor.width": 0.5,
        "xtick.minor.size": 1.6,
        "ytick.minor.size": 1.6,
        "axes.grid": False,
        "figure.dpi": 120,
        "savefig.dpi": 300,
        "legend.frameon": False,
        "legend.handlelength": 1.8,
        "legend.handletextpad": 0.6,
        "legend.borderaxespad": 0.35,
        "legend.labelspacing": 0.45,
        "lines.linewidth": 1.2,
        "lines.markersize": 3.8,
        "lines.markeredgewidth": 0.9,
    })


def panel(ax, letter, title, pad=5.0):
    """Panel tag and short title as one left-aligned string above the axes."""
    ax.set_title("(%s) %s" % (letter, title), loc="left", pad=pad)


def tidy(ax):
    """Full four-sided frame, no grid lines.

    The author's call, 2026-10-30: the box stays (he reads an open right/top edge as an
    unfinished figure), the light grid does not.  Everything else in the sheet is shared.
    """
    ax.grid(False)
    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_visible(True)


def legend(ax, **kw):
    kw.setdefault("frameon", False)
    return ax.legend(**kw)
