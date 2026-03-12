"""
Lunar Spaceport DES Simulation Plotter
=======================================
Interactive tool to explore and plot variables from your simulation log.

Usage:
    python lunar_spaceport_plotter.py                          # interactive mode
    python lunar_spaceport_plotter.py --json path/to/log.json  # custom file path
"""

import json
import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np


# ─────────────────────────────────────────────
# Data loading & parsing
# ─────────────────────────────────────────────

def load_log(path: str) -> dict:
    with open(path, "r") as f:
        raw = json.load(f)

    # Keys are time values (hours). Sort numerically.
    data = {}
    for k, v in raw.items():
        try:
            data[float(k)] = v
        except ValueError:
            pass  # skip non-numeric top-level keys

    return dict(sorted(data.items()))


def get_entities(data: dict) -> list[str]:
    """Return sorted list of all entity names found across all timesteps."""
    entities = set()
    for snapshot in data.values():
        entities.update(snapshot.keys())
    return sorted(entities)


def get_numeric_attributes(data: dict, entity: str) -> list[str]:
    """Return sorted list of numeric attributes for a given entity."""
    attrs = set()
    for snapshot in data.values():
        if entity in snapshot:
            for k, v in snapshot[entity].items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    attrs.add(k)
    return sorted(attrs)


def extract_series(data: dict, entity: str, attribute: str):
    """Return (times, values) arrays for the chosen entity/attribute."""
    times, values = [], []
    for t, snapshot in data.items():
        if entity in snapshot and attribute in snapshot[entity]:
            val = snapshot[entity][attribute]
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                times.append(t)
                values.append(val)
    return np.array(times), np.array(values)


# ─────────────────────────────────────────────
# Plotting
# ─────────────────────────────────────────────

COLORS = plt.rcParams["axes.prop_cycle"].by_key()["color"]


def plot_series(times, values, entity, attribute, ax=None, color=None, label=None):
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(12, 5))

    c = color or COLORS[0]
    lbl = label or f"{entity} — {attribute}"
    ax.plot(times, values, linewidth=1.5, color=c, label=lbl)
    ax.set_xlabel("Simulation Time (hours)", fontsize=11)
    ax.set_ylabel(attribute, fontsize=11)
    ax.set_title(f"{entity}  ›  {attribute}", fontsize=13, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f} h"))

    if standalone:
        plt.tight_layout()
        plt.show()
        return None
    return ax


def plot_multi(series_list):
    """Plot multiple (entity, attribute) pairs on one or two axes."""
    n = len(series_list)
    fig, axes = plt.subplots(n, 1, figsize=(12, 4 * n), sharex=True)
    if n == 1:
        axes = [axes]

    for i, (times, values, entity, attr) in enumerate(series_list):
        axes[i].plot(times, values, linewidth=1.5, color=COLORS[i % len(COLORS)])
        axes[i].set_ylabel(attr, fontsize=10)
        axes[i].set_title(f"{entity}  ›  {attr}", fontsize=11, fontweight="bold")
        axes[i].grid(True, alpha=0.3)

    axes[-1].set_xlabel("Simulation Time (hours)", fontsize=11)
    axes[-1].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f} h"))
    plt.tight_layout()
    plt.show()


# ─────────────────────────────────────────────
# Interactive UI helpers
# ─────────────────────────────────────────────

def numbered_menu(title: str, options: list[str], allow_multi=False) -> list[int]:
    """Print a numbered list and return selected index/indices (0-based)."""
    print(f"\n{'─'*50}")
    print(f"  {title}")
    print(f"{'─'*50}")
    for i, opt in enumerate(options, 1):
        print(f"  [{i:>3}]  {opt}")
    print(f"{'─'*50}")

    while True:
        prompt = "  Select number(s), separated by commas: " if allow_multi else "  Select number: "
        raw = input(prompt).strip()
        try:
            indices = [int(x.strip()) - 1 for x in raw.split(",")]
            if all(0 <= idx < len(options) for idx in indices):
                return indices
            print("  ✗ Out of range. Try again.")
        except ValueError:
            print("  ✗ Invalid input. Enter number(s) only.")


def ask_yes_no(question: str) -> bool:
    while True:
        ans = input(f"  {question} [y/n]: ").strip().lower()
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False
        print("  ✗ Please type y or n.")


# ─────────────────────────────────────────────
# Main interactive loop
# ─────────────────────────────────────────────

def run_interactive(data: dict):
    entities = get_entities(data)
    times_all = list(data.keys())
    print(f"\n✓ Loaded {len(data)} timesteps  |  t = {times_all[0]:.1f} → {times_all[-1]:.1f} h  |  {len(entities)} entities found")

    while True:
        print("\n" + "═" * 50)
        print("  LUNAR SPACEPORT SIMULATION PLOTTER")
        print("═" * 50)
        print("  [1]  Plot a single attribute")
        print("  [2]  Compare multiple attributes (stacked)")
        print("  [3]  Quit")
        print("─" * 50)
        choice = input("  Select mode: ").strip()

        if choice == "3":
            print("\n  Goodbye 👋\n")
            break

        elif choice == "1":
            [ei] = numbered_menu("Select Entity", entities)
            entity = entities[ei]

            attrs = get_numeric_attributes(data, entity)
            if not attrs:
                print(f"  ✗ No numeric attributes found for '{entity}'.")
                continue

            [ai] = numbered_menu(f"Select Attribute  ({entity})", attrs)
            attr = attrs[ai]

            times, values = extract_series(data, entity, attr)
            if len(times) == 0:
                print("  ✗ No data points found for this combination.")
                continue

            print(f"\n  Plotting {entity} › {attr}  ({len(times)} points)")
            print(f"  Value range: {values.min():.4g}  →  {values.max():.4g}")
            plot_series(times, values, entity, attr)

        elif choice == "2":
            series_list = []
            while True:
                [ei] = numbered_menu("Select Entity", entities)
                entity = entities[ei]

                attrs = get_numeric_attributes(data, entity)
                if not attrs:
                    print(f"  ✗ No numeric attributes for '{entity}'.")
                    continue

                [ai] = numbered_menu(f"Select Attribute  ({entity})", attrs)
                attr = attrs[ai]

                times, values = extract_series(data, entity, attr)
                if len(times) == 0:
                    print("  ✗ No data points.")
                else:
                    series_list.append((times, values, entity, attr))
                    print(f"  ✓ Added: {entity} › {attr}")

                if not ask_yes_no("Add another series?"):
                    break

            if series_list:
                plot_multi(series_list)
            else:
                print("  ✗ Nothing to plot.")

        else:
            print("  ✗ Invalid choice.")


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

DEFAULT_JSON = "lunar_spaceport_log.json"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lunar Spaceport DES Simulation Plotter")
    parser.add_argument("--json", default=DEFAULT_JSON, help="Path to simulation JSON log file")
    args = parser.parse_args()

    json_path = Path(args.json)
    if not json_path.exists():
        print(f"\n✗ File not found: {json_path}")
        print(f"  Place your JSON log in the same folder as this script, or pass --json <path>\n")
        sys.exit(1)

    print(f"\n  Loading: {json_path}")
    data = load_log(str(json_path))
    run_interactive(data)