"""Archive the Malapert B0 experiment without changing the benchmark or historical run."""

import argparse
from collections import defaultdict
import gzip
import hashlib
import json
import math
from pathlib import Path
import shutil
import platform

import simpy

from S24.DES_pipeline_version.batch_results import collect_result_fields
from S24.DES_pipeline_version.scenario_config import load_scenario_config
from S24.DES_pipeline_version.scenario_runner import check_scenario_validity, run_scenario
from paper_scitech.COMPASS.run_reference import archive_code, json_bytes, write_timeseries


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROPOSED = HERE.parent / "COMPASS/malapert_b0.proposed.json"
HISTORICAL = HERE.parent / "B0/run"
REFERENCE = HERE.parent / "COMPASS/runs/R-168h-01"

ARTIFACT_SOURCES = (
    "paper_scitech/COMPASS_B0/run_b0.py",
    "paper_scitech/COMPASS_B0/figures.py",
    "paper_scitech/B0/visualize_b0.py",
    "tests/test_batch_integration.py",
    "tests/test_batch_portal.js",
    "ScenarioIndex.html",
    ".github/workflows/run_des.yml",
    "extensions/lsp1.pipeline/lsp1_pipeline/manifest_builder.py",
    "extensions/lsp1.pipeline/lsp1_pipeline/extension.py",
    "S24/usd/scene_builder.py",
    "S24/usd/model_submission.py",
    "S24/usd/waypoints.py",
)


def read(path):
    return json.loads(path.read_text())


def verify_config(config, system):
    active = config["scenario"]["active_types"]
    if set(active) != {part["name"] for part in system["parts"]} or len(active) != 7:
        raise ValueError("Unexpected operational types in archived architecture")
    routes = config["scenario_builder"]["resource_routes"]
    official = system["scenario_logic"]["resource_routes"]
    if [route for route in routes if route["flow"] in {"Regolith", "LOX"}] != official:
        raise ValueError("Operational routes differ from the spatial archive")
    if config["simulation"]["duration_hr"] != 168:
        raise ValueError("B0 must span 168 hours")
    archive = system["urban_planning"]
    for item in config["scenario_builder"]["instances"]:
        if item["id"] not in archive["module_instances"]:
            raise ValueError(f"Missing placement for {item['id']}")
    for route in official:
        geo = archive["route_geometry"][route["route_name"]]
        points = geo["waypoints_m"]
        plan = sum(math.dist(left[:2], right[:2]) for left, right in zip(points, points[1:])) / 1000
        if (round(plan, 3) != route["distance_km"]
                or geo["rover_id"] != route["rover_id"]):
            raise ValueError(f"Geometry mismatch for {route['id']}")
    for line in config["batch_operations"]["lines"]:
        spec = line["regolith_rover"]
        by_flow = {r["flow"]: r for r in routes if r["rover_id"] == spec["id"]}
        haul, dump, back = (by_flow[key] for key in ("Regolith", "Residue", "ResidueReturn"))
        if not (haul["to"] == dump["from"] and dump["to"] == back["from"]
                and haul["from"] == back["to"]):
            raise ValueError(f"Disconnected residue route for {spec['id']}")


def analyse(config, result, nasa):
    final = result["summary"]
    horizon = final["time_hr"]
    events = result["events"]
    lines = final["lines"]
    routing = {r["id"]: r for r in config["scenario_builder"]["resource_routes"]}
    starts = {}
    phases = defaultdict(lambda: defaultdict(float))
    skipped = defaultdict(lambda: defaultdict(int))
    distances = defaultdict(float)
    deliveries = defaultdict(list)
    first_liquid = {}
    first_missed = {}
    available = defaultdict(float)
    peak_liquid = defaultdict(float)
    shuttle_origins = {spec["lox_rover"]["id"]: spec["plant_id"]
                       for spec in config["batch_operations"]["lines"]}
    for event in events:
        actor, time, kind = event["actor"], event["time_hr"], event["event"]
        if kind == "phase_start":
            phase = event["phase"]
            if actor in starts:
                raise ValueError(f"Overlapping rover phases for {actor}")
            starts[actor] = event
            phases[actor][phase] += min(event["duration_hr"], horizon - time)
            if phase.startswith("drive_"):
                route = routing[event["route_id"]]
                if route["rover_id"] != actor or route["distance_km"] != event["distance_km"]:
                    raise ValueError("Route in journal disagrees with assignment")
        elif kind == "phase_end":
            start = starts.pop(actor)
            if start["phase"] != event["phase"] or abs(time - start["time_hr"] - start["duration_hr"]) > 1e-8:
                raise ValueError("Inconsistent start and end for a rover phase")
            distances[actor] += event.get("distance_km", 0)
            if event["phase"] == "load_lox":
                available[shuttle_origins[actor]] -= event["mass_kg"]
        elif kind == "mission_missed":
            skipped[actor][f"{event['mission']}.{event['reason']}"] += 1
        elif kind == "material_delivered":
            deliveries[actor].append(event)
        elif kind == "liquid_available":
            plant = event["origin"]
            first_liquid.setdefault(plant, time)
            available[plant] += event["mass_kg"]
            peak_liquid[plant] = max(peak_liquid[plant], available[plant])
        elif kind == "batch_missed":
            first_missed.setdefault(actor, event["slot_hr"])

    by_plant = {}
    for spec in config["batch_operations"]["lines"]:
        plant, hauler, shuttle = spec["plant_id"], spec["regolith_rover"]["id"], spec["lox_rover"]["id"]
        stats = lines[plant]
        raw = sum(event["mass_kg"] for event in deliveries[hauler] if event["resource"] == "Regolith")
        lox = sum(event["mass_kg"] for event in deliveries[shuttle])
        if abs(spec["initial_feed_kg"] + raw - stats["feed_kg"] - stats["processed_kg"]
               - stats["solid_in_process_kg"]) > 1e-7:
            raise ValueError(f"Feed balance differs for {plant}")
        if abs(stats["liquid_kg"] - lox - final["liquid_stocks_kg"][plant]
               - final["vehicles"][shuttle]["cargo_kg"]) > 1e-7:
            raise ValueError(f"Liquid oxygen balance differs for {plant}")
        by_plant[plant] = {
            **stats, "regolith_delivered_kg": raw, "lox_delivered_kg": lox,
            "lox_in_buffer_kg": final["liquid_stocks_kg"][plant],
            "lox_in_transit_kg": final["vehicles"][shuttle]["cargo_kg"],
            "first_liquid_hr": first_liquid.get(plant),
            "first_delivery_hr": deliveries[shuttle][0]["time_hr"] if deliveries[shuttle] else None,
            "first_missed_batch_hr": first_missed.get(plant),
            "thermal_to_reactor_kwh": sum(
                min(event["duration_hr"], horizon - event["time_hr"])
                for event in events if event["actor"] == plant and event["event"] == "batch_started"
            ) * config["batch_operations"]["power"]["thermal_per_line_kw"],
            "peak_feed_kg": max(row["lines"][plant]["feed_kg"] for row in result["time_series"]),
            "peak_lox_buffer_kg": peak_liquid[plant],
        }

    vehicles = {}
    for actor, state in final["vehicles"].items():
        if not math.isclose(distances[actor], state["completed_distance_km"], abs_tol=1e-8):
            raise ValueError(f"Completed distance mismatch for {actor}")
        activity = phases[actor]
        moving = sum(hours for key, hours in activity.items() if key.startswith("drive_"))
        charge = activity.get("charge", 0)
        handling = sum(hours for key, hours in activity.items() if key.startswith(("load_", "unload_")))
        vehicles[actor] = {
            **state, "drive_hr": moving, "handling_hr": handling, "charge_hr": charge,
            "other_idle_or_wait_hr": horizon - moving - handling - charge,
            "transport_utilization_percent": (moving + handling) / horizon * 100,
            "deliveries": len(deliveries[actor]), "missed_slots": dict(skipped[actor]),
        }

    def comparable(state):
        return {
            "completed_batches": sum(line["completed"] for line in state["lines"].values()),
            "feed_processed_kg": sum(line["processed_kg"] for line in state["lines"].values()),
            "oxygen_extracted_kg": sum(line["oxygen_kg"] for line in state["lines"].values()),
            "lox_liquefied_kg": sum(line["liquid_kg"] for line in state["lines"].values()),
            "electric_core_kwh": state["energy"]["electric_core_kwh"],
            "electric_charging_kwh": state["energy"]["electric_charging_kwh"],
            "thermal_to_reactors_kwh": state["energy"]["thermal_to_reactors_kwh"],
        }

    energy = final["energy"]
    electric_error = (energy["electric_available_kwh"] + energy["electric_unserved_kwh"]
                      - energy["electric_curtailed_kwh"] - energy["electric_core_kwh"]
                      - energy["electric_charging_kwh"])
    if abs(electric_error) > 1e-7:
        raise ValueError("Electrical bus balance differs")
    comparison = {
        key: {"compass": value, "b0": actual, "delta_percent": 100 * (actual / value - 1)}
        for (key, value), actual in zip(comparable(nasa).items(), comparable(final).values())
    }
    return {
        "time_hr": horizon, "plants": by_plant, "vehicles": vehicles, "comparison": comparison,
        "b0": final, "max_event_mass_residual_kg": result["max_event_mass_residual_kg"],
        "electric_balance_residual_kwh": electric_error, "unfinished_rover_phases": starts,
    }


def portal_snapshot(config, archived_system, fields):
    scenario = config["scenario"]
    layout = archived_system["urban_planning"]
    frame = layout["map_frame_m"]
    side = frame["frame_px"]["size"]
    frame_x = frame["frame_px"]["x"]
    frame_y = frame["frame_px"]["y"]
    scale = frame["meters_per_pixel"]

    def canvas(points):
        return [{"x": x / scale + frame_x + side / 2,
                 "y": -y / scale + frame_y + side / 2} for x, y, _ in points]

    logic = config["scenario_builder"]
    routes = [{**route, "pts": canvas(layout["route_geometry"][route["route_name"]]["waypoints_m"])}
              for route in logic["resource_routes"] if route["flow"] in {"Regolith", "LOX"}]
    terrain = [{**edge, "pts": canvas(layout["route_geometry"][edge["key"]]["waypoints_m"])}
               for edge in layout["routes"]]
    return {
        "schema_version": 1,
        "id": scenario["slug"], "scenario_slug": scenario["slug"], "name": scenario["name"],
        "mode": "isru", "sysml_file": scenario["sysml_file"], "site_id": layout["site"],
        "active_nodes": scenario["active_types"], "instance_counts": {"ISRUPlant": 2},
        "placements": {item["id"]: item["position_canvas"] for item in logic["instances"]},
        "orientations": {item["id"]: item["orientation_deg"] for item in logic["instances"]},
        "terrain_routes": terrain,
        "scenario_logic": {
            "resourceRoutes": routes, "roverCounts": {"regolith": 2, "lox": 2},
            "moduleLogic": {}, "powerLinks": [], "comLinks": [],
            "sysmlInterfaces": archived_system["scenario_logic"]["sysml_interfaces"],
            "transportLinks": archived_system["scenario_logic"]["transport_links"],
            "moduleEquations": logic["module_equations"],
            "roverPayloadsKg": {"regolith": 35, "lox": 18},
        },
        "des_form": {
            "desSimDuration": str(config["simulation"]["duration_hr"]),
            "desBatchOperations": json.dumps({
                "batch_operations": config["batch_operations"],
                "auxiliary_routes": [route for route in logic["resource_routes"]
                                     if route["flow"] in {"Residue", "ResidueReturn"}],
            }),
        },
        "results": {
            "status": "success", "sysml_active_nodes": scenario["active_types"],
            "scenario_slug": scenario["slug"],
            "results": fields["results"], "log": fields["log"],
        },
    }


def main(out):
    config = read(PROPOSED)
    system = read(HISTORICAL / "system.json")
    verify_config(config, system)
    config["scenario"].update(status="executed", slug="Malapert_B0_Compass",
                              sysml_file="paper_scitech/B0/run/reference.sysml")
    options = {"scenario_config": config, "active_nodes": config["scenario"]["active_types"]}
    check_scenario_validity(options)
    resolved = load_scenario_config(options)
    result = run_scenario(options)
    summary = analyse(config, result, read(REFERENCE / "summary.json"))
    fields = collect_result_fields(options, result)
    out.mkdir(parents=True, exist_ok=False)
    revision, hashes = archive_code(out)
    for x in ARTIFACT_SOURCES:
        target = out / "source" / x
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / x, target)
        hashes[x] = hashlib.sha256(target.read_bytes()).hexdigest()
    for name in ("reference.sysml", "routing.json", "graph.json"):
        shutil.copyfile(HISTORICAL / name, out / name)
    system["metadata"]["scenario_config"] = "scenario.json"
    system["metadata"]["source_sysml_scope"] = "Topology and instance identity. Runtime laws are in scenario_logic."
    scenario_logic = system["scenario_logic"]
    scenario_logic["module_equations"] = config["scenario_builder"]["module_equations"]
    scenario_logic["rover_payloads_kg"] = {"regolith": 35, "lox": 18}
    scenario_logic["batch_operations"] = config["batch_operations"]
    scenario_logic["batch_auxiliary_routes"] = [
        route for route in config["scenario_builder"]["resource_routes"]
        if route["flow"] in {"Residue", "ResidueReturn"}
    ]
    for part in system["parts"]:
        part["attributes"] = {
            key: value for key, value in part.get("attributes", {}).items()
            if key.startswith("cad") or key.endswith("_volume_m3")
        }
    (out / "system.json").write_bytes(json_bytes(system))
    (out / "scenario.json").write_bytes(json_bytes(config))
    (out / "resolved.json").write_bytes(json_bytes(resolved))
    (out / "results.json.gz").write_bytes(gzip.compress(json_bytes(result), mtime=0))
    (out / "analysis.json").write_bytes(json_bytes(summary))
    (out / "des_results.json").write_text(json.dumps({
        "request_id": out.name, "status": "success", "scenario_slug": config["scenario"]["slug"],
        "scenario_name": config["scenario"]["name"], "sysml_file": config["scenario"]["sysml_file"],
        "sysml_active_nodes": options["active_nodes"], "des_active_nodes": options["active_nodes"],
        **fields,
    }, separators=(",", ":"), allow_nan=False) + "\n")
    write_timeseries(out, result["time_series"])
    (out / "portal_snapshot.json").write_text(json.dumps(
        portal_snapshot(config, system, fields), separators=(",", ":"), allow_nan=False
    ) + "\n")
    compass_config = read(REFERENCE / "reference.json")
    compass_data = json.loads(gzip.decompress((REFERENCE / "results.json.gz").read_bytes()))
    compass_fields = collect_result_fields({"scenario_config": compass_config}, compass_data)
    (out / "compass_portal_snapshot.json").write_text(json.dumps({
        "schema_version": 1, "id": "COMPASS_R_168h_01", "scenario_slug": "COMPASS_R_168h_01",
        "name": "COMPASS R-168h-01", "mode": "isru",
        "des_form": {"desSimDuration": "168"},
        "results": {"status": "success", "results": compass_fields["results"],
                    "log": compass_fields["log"]},
    }, separators=(",", ":"), allow_nan=False) + "\n")
    (out / "provenance.json").write_bytes(json_bytes({
        "run_id": out.name,
        "base_git_revision": revision,
        "python": platform.python_version(),
        "simpy": simpy.__version__,
        "platform": platform.platform(),
        "source_sha256": hashes,
        "published_inputs_sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (PROPOSED, REFERENCE / "summary.json", REFERENCE / "provenance.json",
                         REFERENCE / "reference.json", REFERENCE / "results.json.gz")
        },
        "artifact_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                            for path in sorted(out.iterdir()) if path.is_file()},
    }))
    print(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    main(parser.parse_args().output)
