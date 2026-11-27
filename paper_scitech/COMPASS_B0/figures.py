"""Render scientific figure candidates from the archived B0 observations."""

import argparse
import gzip
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator


COLORS = {"ISRUPlant_1": "#176d9c", "ISRUPlant_2": "#bc521d"}
NAMES = {"ISRUPlant_1": "Plant 1", "ISRUPlant_2": "Plant 2"}
DEPOT = "#287454"
REFERENCE = "#61646c"


def save(fig, output):
    fig.savefig(output.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(output.with_suffix(".png"), dpi=180, bbox_inches="tight")
    plt.close(fig)


def ops_figure(result, configuration, reference, output):
    events = result["events"]
    fig, axes = plt.subplots(3, 1, figsize=(8.0, 8.1), sharex=True, layout="constrained")
    for ax in axes:
        ax.grid(axis="y", color="#d8e0e4", linewidth=.7)
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_xlim(0, 168)
        ax.xaxis.set_major_locator(MultipleLocator(24))

    for index, spec in enumerate(configuration["batch_operations"]["lines"]):
        plant = spec["plant_id"]
        color = COLORS[plant]
        feed_t, feed = [0], [spec["initial_feed_kg"]]
        misses = []
        for event in events:
            delta = 0
            if event["actor"] == plant and event["event"] == "batch_started":
                delta = -event["mass_kg"]
            elif event["event"] == "material_delivered" and event["resource"] == "Regolith" and event["destination"] == plant:
                delta = event["mass_kg"]
            elif event["actor"] == plant and event["event"] == "batch_missed":
                misses.append(event["slot_hr"])
            if delta:
                feed_t.append(event["time_hr"])
                feed.append(feed[-1] + delta)
        axes[0].step(feed_t + [168], feed + [feed[-1]], where="post", color=color, label=NAMES[plant])
        axes[0].plot(misses, [-4 - index * 5] * len(misses), "|", color=color, markersize=6)
    axes[0].set_ylim(-13, 137)
    axes[0].axhline(configuration["batch_operations"]["lines"][0]["batch_kg"], linestyle=":",
                    color=REFERENCE, label="Feed required per batch")
    axes[0].set(ylabel="Feed hopper [kg]", title="(a) Feed inventory and missed batch starts")
    axes[0].legend(loc="upper right", frameon=False, ncol=3)

    accum = dict.fromkeys(COLORS, 0.0)
    lox_t, lox_total = [0], [0]
    for event in events:
        if event["event"] == "liquid_available":
            accum[event["origin"]] += event["mass_kg"]
            lox_t.append(event["time_hr"])
            lox_total.append(sum(accum.values()))
    axes[1].step(lox_t + [168], lox_total + [lox_total[-1]], where="post", color="#1b2835",
                 linewidth=1.8, label="B0 total liquefied")
    ref_t, ref_y = [], []
    for sample in reference["time_series"]:
        ref_t.append(sample["time_hr"])
        ref_y.append(sum(sample["liquid_stocks_kg"].values()))
    axes[1].plot(ref_t, ref_y, linestyle="--", color=REFERENCE, label="COMPASS reference run")
    delivered_t, delivered = [0], [0]
    for event in events:
        if event["event"] == "material_delivered" and event["resource"] == "LOX":
            delivered_t.append(event["time_hr"])
            delivered.append(delivered[-1] + event["mass_kg"])
    axes[1].step(delivered_t + [168], delivered + [delivered[-1]], where="post", color=DEPOT,
                 label="B0 delivered to depot")
    axes[1].set(ylabel="Cumulative LOX [kg]", title="(b) Liquefaction and delivery")
    axes[1].legend(loc="upper left", frameon=False)

    for spec in configuration["batch_operations"]["lines"]:
        plant = spec["plant_id"]
        shuttle = spec["lox_rover"]["id"]
        liquid_t, liquid = [0], [0]
        for event in events:
            if event["event"] == "liquid_available" and event["origin"] == plant:
                delta = event["mass_kg"]
            elif event["actor"] == shuttle and event["event"] == "phase_end" and event["phase"] == "load_lox":
                delta = -event["mass_kg"]
            else:
                continue
            liquid_t.append(event["time_hr"])
            liquid.append(liquid[-1] + delta)
        axes[2].step(liquid_t + [168], liquid + [liquid[-1]], where="post",
                     color=COLORS[plant], label=NAMES[plant])
    axes[2].set_ylim(-.4, 18)
    axes[2].axhline(configuration["batch_operations"]["lines"][0]["lox_rover"]["dispatch_kg"],
                    linestyle=":", color=REFERENCE, label="Dispatch threshold")
    axes[2].set(xlabel="Elapsed time [h]", ylabel="Available LOX [kg]",
                title="(c) Plant liquid buffer inventories")
    axes[2].legend(loc="upper right", frameon=False, ncol=3)
    save(fig, output)


def route_figure(system, options, output):
    fig, ax = plt.subplots(figsize=(7.2, 5.6), layout="constrained")
    layout = system["urban_planning"]
    route_colors = {"Regolith": "#a05424", "LOX": "#176d9c"}
    labels = {**NAMES, "ISRUExcavation": "Excavation", "PropellantDepot": "Propellant depot",
              "LaunchLandingZone": "Landing / launch zone", "SolarPowerSystem": "Solar power"}
    offsets = {"ISRUPlant_2": (7, -16), "LaunchLandingZone": (-7, -17),
               "PropellantDepot": (7, -10), "ISRUExcavation": (-8, 10),
               "SolarPowerSystem": (-7, 5), "ISRUPlant_1": (-7, 12)}
    for route in options["scenario_builder"]["resource_routes"]:
        if route["flow"] not in route_colors:
            continue
        points = layout["route_geometry"][route["route_name"]]["waypoints_m"]
        x, y, _ = zip(*points)
        ax.plot([p / 1000 for p in x], [p / 1000 for p in y], color=route_colors[route["flow"]],
                lw=4.5 if route["flow"] == "Regolith" else 2, alpha=.9)
    for actor, item in layout["module_instances"].items():
        x, y, _ = item["position_m"]
        dx, dy = offsets[actor]
        ax.scatter(x / 1000, y / 1000, color="#1b2835", s=22, zorder=3)
        ax.annotate(labels[actor], (x / 1000, y / 1000), xytext=(dx, dy), textcoords="offset points",
                    ha="left" if dx > 0 else "right", fontsize=8.5)
    ax.legend(handles=[Line2D([0], [0], lw=2.3, color=color, label=flow)
                       for flow, color in route_colors.items()], loc="lower right", frameon=False)
    ax.set(xlabel="Local X [km]", ylabel="Local Y [km]", aspect="equal")
    ax.grid(color="#d8e0e4", linewidth=.7)
    ax.margins(.13)
    save(fig, output)


def main(folder):
    plt.rcParams.update({"font.size": 10, "axes.labelsize": 10, "pdf.fonttype": 42})
    folder = folder.resolve()
    target = folder / "figures"
    target.mkdir(exist_ok=True)
    scenario = json.loads((folder / "scenario.json").read_text())
    result = json.loads(gzip.decompress((folder / "results.json.gz").read_bytes()))
    system = json.loads((folder / "system.json").read_text())
    ref_source = Path(__file__).resolve().parents[1] / "COMPASS/runs/R-168h-01/results.json.gz"
    reference = json.loads(gzip.decompress(ref_source.read_bytes()))
    ops_figure(result, scenario, reference, target / "operations")
    route_figure(system, scenario, target / "routes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    main(parser.parse_args().run)
