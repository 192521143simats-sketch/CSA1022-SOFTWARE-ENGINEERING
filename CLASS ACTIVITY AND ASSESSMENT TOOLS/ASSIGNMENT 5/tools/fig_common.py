"""Shared drawing helpers for the report figures (matplotlib, 250 dpi)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Polygon

DPI = 250
INK, MUTED, GRID = "#1b2330", "#5b6675", "#d7dce4"
BLUE, TEAL, AMBER, RED, GREEN, VIOLET, SLATE = ("#2457d6", "#0f766e", "#b45309", "#b91c1c",
                                                 "#15803d", "#6d28d9", "#64748b")
BLUE_L, TEAL_L, AMBER_L, RED_L, GREEN_L, VIOLET_L, SLATE_L = ("#e8eefc", "#dff3f0", "#fdf0dc", "#fde8e8",
                                                               "#e1f4e6", "#efe9fb", "#eef1f5")
ALT_COL = {"A": BLUE, "B": AMBER, "C": TEAL, "D": VIOLET}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "text.color": INK, "xtick.color": INK, "ytick.color": INK, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": DPI,
})


def canvas(w, h, size=(16, 9)):
    fig = plt.figure(figsize=size)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text="", fc="#fff", ec=INK, lw=1.4, fs=9, bold=False, ls="-",
        color=INK, rad=1.2, align="center", z=3, alpha=1.0):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={rad}", fc=fc, ec=ec,
                       lw=lw, ls=ls, zorder=z, alpha=alpha)
    ax.add_patch(p)
    if text:
        ha = "center" if align == "center" else "left"
        tx = x + w / 2 if align == "center" else x + 1.2
        ax.text(tx, y + h / 2, text, ha=ha, va="center", fontsize=fs, color=color,
                fontweight="bold" if bold else "normal", zorder=z + 1, linespacing=1.25)
    return p


def zone(ax, x, y, w, h, title, ec=SLATE, fc="none", fs=9.5, tcolor=None, lw=1.6):
    ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=lw, ls=(0, (6, 4)), zorder=1))
    ax.text(x + 1.2, y + h - 1.0, title, ha="left", va="top", fontsize=fs, fontweight="bold",
            color=tcolor or ec, zorder=2)


def route(ax, pts, color=INK, lw=1.5, ls="-", both=False, z=5, head=11):
    for a, b in zip(pts[:-2], pts[1:-1]):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=lw, ls=ls, zorder=z,
                solid_capstyle="butt")
    ap = dict(arrowstyle="-|>", color=color, lw=lw, ls=ls, shrinkA=0, shrinkB=0, mutation_scale=head)
    ax.annotate("", xy=pts[-1], xytext=pts[-2], arrowprops=ap, zorder=z)
    if both:
        ax.annotate("", xy=pts[0], xytext=pts[1], arrowprops=ap, zorder=z)


def tag(ax, x, y, text, fc=INK, color="#fff", r=1.6, fs=7.5):
    ax.add_patch(Circle((x, y), r, fc=fc, ec="#fff", lw=1.0, zorder=8))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=color, fontweight="bold", zorder=9)


def label(ax, x, y, text, fs=7.5, color=MUTED, ha="center", va="center", bold=False, bg=True):
    ax.text(x, y, text, ha=ha, va=va, fontsize=fs, color=color, zorder=7,
            fontweight="bold" if bold else "normal", linespacing=1.2,
            bbox=dict(fc="#ffffff", ec="none", pad=1.2, alpha=0.9) if bg else None)


def save(fig, path):
    fig.savefig(path, dpi=DPI, facecolor="#ffffff")
    plt.close(fig)
    print("wrote", path)
