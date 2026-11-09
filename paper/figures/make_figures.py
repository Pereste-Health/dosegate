import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
INK = "#1a1a1a"
GRAY = "#8a8a8a"
LIGHT = "#c8c8c8"
ACCENT = "#3b6e8f"

plt.rcParams.update({
    "font.family": "Times New Roman",
    "font.size": 9,
    "text.color": INK,
    "axes.edgecolor": INK,
    "axes.labelcolor": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
})


def save(fig, name):
    for ext in ("pdf", "png", "tiff"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=600, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


def box(ax, x, y, w, h, title, body, dashed=False, mono=False):
    ax.add_patch(Rectangle((x, y), w, h, fill=False, lw=0.8, ec=INK, ls=(0, (3, 2)) if dashed else "-"))
    ax.text(x + 0.12, y + h - 0.14, title, ha="left", va="top", fontweight="bold")
    ax.text(x + 0.12, y + h - 0.42, body, ha="left", va="top", linespacing=1.35,
            family="Courier New" if mono else None, fontsize=8)


def arrow(ax, a, b, label=None, lx=0, ly=0):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=9, lw=0.8, color=INK, shrinkA=0, shrinkB=0))
    if label:
        ax.text((a[0] + b[0]) / 2 + lx, (a[1] + b[1]) / 2 + ly, label, ha="center", va="center", fontsize=8.5,
                color=INK, bbox=dict(fc="white", ec="none", pad=1))


def figure_layer():
    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    ax.set_xlim(0, 15.3)
    ax.set_ylim(0, 8.8)
    ax.axis("off")

    box(ax, 0.1, 5.7, 4.4, 2.9, "Patient's FHIR orders",
        "Order m1, active:\nmetformin 500 mg by mouth\ntwice a day\n\nConverted by the FHIR reader\n(tested, not proved)", dashed=True)
    box(ax, 0.1, 1.0, 4.4, 4.0, "Model output with slots",
        "Here is your medicine.\nTake {{drug:m1}} {{dose:m1}}\n{{route:m1}} {{frequency:m1}}.\n\nThe model's words may not\ncontain a digit. Doses, routes,\nand frequencies come only\nfrom the orders.")

    box(ax, 5.3, 1.0, 4.5, 7.6, "The layer (render)",
        "Its behavior is proved in Lean 4.\nAmong its checks, it blocks unless:\n\n1. Every character and word\n    is allowed\n2. Each value sentence has\n    one of four shapes\n3. Each slot names one active\n    order that has that field\n4. Every active order is named\n    (default setting)\n5. No instruction is repeated\n    and no sign precedes a slot")

    box(ax, 10.7, 5.0, 4.5, 3.6, "Released text",
        "Here is your medicine.\nTake metformin 500 mg\nby mouth twice a day.\n\nThe model's words are\nunchanged, and each slot is\nfilled from the order it names.")
    box(ax, 10.7, 0.4, 4.5, 3.9, "Blocked",
        "No model text reaches the\npatient. A fallback command\nprints one line per active\norder through the same\nproved formatting code.")

    arrow(ax, (4.5, 7.1), (5.3, 6.4))
    arrow(ax, (4.5, 3.0), (5.3, 3.7))
    arrow(ax, (9.8, 5.8), (10.7, 6.8), "pass", lx=0.0, ly=0.35)
    arrow(ax, (9.8, 3.2), (10.7, 2.3), "fail", lx=0.0, ly=-0.35)

    ax.text(0.1, 0.0, "Dashed outline: the FHIR reader, tested but not proved.", fontsize=8, color=GRAY)
    save(fig, "figure1_layer")


def misstatement_counts():
    s = json.loads((ROOT / "eval/data/labels_summary.json").read_text())
    replay = json.loads((ROOT / "eval/data/replay_v23/summary.json").read_text())["table"]
    rows = []
    for key, name, n, tested in (("h2", "Round h2", 138, "Version 2"),
                                 ("h3", "Round h3", 156, "Version 2.1"),
                                 ("h4", "Round h4", 145, "Version 2.2"),
                                 ("h5", "Round h5", 144, "Version 2.3 (held out)")):
        rows.append((f"{name} ({n} requests)", tested,
                     s[key]["layer"]["labels"]["misstates_order"],
                     s[key]["baseline"]["labels"]["misstates_order"],
                     replay[key]["misstates_order"] if key in replay else None))
    return rows


def figure_misstatements():
    rows = misstatement_counts()
    fig, ax = plt.subplots(figsize=(6.0, 4.4))
    y = 0
    ticks, labels = [], []
    for group, tested, layer, base, replay in rows:
        ax.text(-0.34, y - 0.1, group, ha="left", va="center", fontweight="bold", transform=ax.get_yaxis_transform())
        y -= 1
        bars = [(tested, layer, ACCENT if tested.startswith("Version 2.3") else GRAY), ("Comparison filter", base, LIGHT)]
        if replay is not None:
            bars.append(("Version 2.3 (replay)", replay, ACCENT))
        for label, val, color in bars:
            ax.barh(y, val, 0.72, color=color, edgecolor="none")
            hi = label.startswith("Version 2.3")
            ax.text(val + 0.8, y, str(val), va="center", fontsize=8.5, color=ACCENT if hi else INK, fontweight="bold" if hi else None)
            ticks.append(y)
            labels.append(label)
            y -= 1
        y -= 0.6
    ax.set_yticks(ticks, labels)
    ax.set_ylim(y + 0.9, 0.9)
    ax.set_xlim(0, 60)
    ax.set_xlabel("Released outputs that misstate an order")
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_linewidth(0.8)
    ax.tick_params(axis="y", length=0, labelsize=8.5)
    ax.tick_params(axis="x", width=0.8, labelsize=8.5)
    save(fig, "figure2_misstatements")


if __name__ == "__main__":
    figure_layer()
    figure_misstatements()
