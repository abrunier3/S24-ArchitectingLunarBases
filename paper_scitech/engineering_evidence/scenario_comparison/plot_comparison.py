"""Render the LOX logistics trade-offs from the archived summary."""
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch


HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "results/comparison.json").read_bytes())
labels = ["Lunar Spaceport", "10 kg dispatch", "Two depots"]
colors = ["#3C4D5A", "#15777C", "#A75625"]

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8,
                     "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.labelcolor": "#142A39", "text.color": "#142A39"})
fig, (timing, stocks) = plt.subplots(1, 2, figsize=(7.2, 2.9), layout="constrained",
                                     gridspec_kw={"width_ratios": [1.05, 1]})

for index, (case, label, color) in enumerate(zip(data.values(), labels, colors)):
    for j, v in enumerate(case["vehicles"].values()):
        x, y = v["completed_distance_km"], v["first_delivery_hr"]
        timing.scatter(x, y, marker=["o", "^"][j], s=42, color=color, edgecolor="white",
                       linewidth=.55, label=label if j == 0 else None, zorder=4-index)
timing.set(xlabel="Distance traveled over 168 h per rover (km)",
           ylabel="First delivery per rover (h)", xlim=(0, 25), ylim=(16, 29.7),
           xticks=[0, 5, 10, 15, 20, 25], yticks=[16, 20, 24, 28])
timing.set_title("(a) First delivery and travel", loc="left", fontsize=9, fontweight="bold")
timing.grid(alpha=.22, linewidth=.55)
timing.legend(loc="lower right", frameon=True, framealpha=.95, fontsize=7)
timing.text(.03, .98, "○  Rover 1    △  Rover 2", transform=timing.transAxes,
            ha="left", va="top", fontsize=7)
timing.annotate("Same rover 1 result\nin two cases", xy=(5.568, 25.5293),
                xytext=(8.0, 23.5), arrowprops={"arrowstyle": "-", "color": "#536373", "lw": .7},
                fontsize=7, color="#405463", va="center")

inventory_colors = ["#205B7A", "#B8612B", "#BFCCD1"]
for index, case in enumerate(data.values()):
    dest = list(case["depot_inventory_kg"]["168"].values())
    primary = dest[0]
    secondary = dest[1] if len(dest) > 1 else 0
    buffer = sum(case["final_buffer_kg"].values())
    baseline = 0
    for amount, color in zip((primary, secondary, buffer), inventory_colors):
        if amount:
            stocks.bar(index, amount, bottom=baseline, width=.58, color=color, zorder=3)
        if amount > 12:
            stocks.text(index, baseline+amount/2, f"{amount:.1f}", ha="center", va="center",
                        color="#142A39" if color == inventory_colors[-1] else "white", fontsize=7.5)
        baseline += amount
stocks.set(xticks=[0, 1, 2], xticklabels=["Lunar\nSpaceport", "10 kg\ndispatch", "Two\ndepots"],
           ylabel="LOX inventory at 168 h (kg)", ylim=(0, 134), yticks=[0, 25, 50, 75, 100, 125])
stocks.set_title("(b) Final inventory by location", loc="left", fontsize=9, fontweight="bold")
stocks.grid(axis="y", alpha=.22, linewidth=.55)
stocks.legend(handles=[Patch(facecolor=c, label=n) for c, n in zip(
    inventory_colors, ["Original depot site", "Second depot", "Plant buffers"])],
    loc="upper center", ncol=3, fontsize=6.2, frameon=False, columnspacing=.7,
    handlelength=1.05, borderaxespad=.35)

fig.savefig(HERE / "lox_logistics_tradeoffs.pdf")
fig.savefig(HERE / "lox_logistics_tradeoffs.png", dpi=280)
