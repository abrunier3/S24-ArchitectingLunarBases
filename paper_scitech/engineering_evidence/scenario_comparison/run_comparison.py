"""Run the two SciTech contrasts with the ECLIPSE DES and archive their evidence."""

import argparse
from collections import Counter
from copy import deepcopy
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess

import simpy

from paper_scitech.COMPASS.run_reference import json_bytes
from S24.DES_pipeline_version.batch_results import collect_result_fields
from S24.DES_pipeline_version.scenario_config import load_scenario_config
from S24.DES_pipeline_version.scenario_runner import check_scenario_validity, run_scenario


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REFERENCE = ROOT / "paper_scitech/COMPASS_B0/runs/B0-168h-01"
PREFLIGHT = HERE.parent / "distributed_storage_preflight"
PORTAL_EXPORT = PREFLIGHT / "portal_export.json"
DEPOT = "PropellantDepot"
SLUG = "Distributed_LOX_storage"
THRESHOLD = "reduced_dispatch_threshold"
STORAGE = "distributed_storage"
LABELS = {
    "reference": "Lunar Spaceport case study",
    THRESHOLD: "Reduced LOX dispatch threshold",
    STORAGE: "Distributed LOX storage",
}


def read(path):
    return json.loads(path.read_bytes())


def put(path, value):
    path.write_bytes(json_bytes(value))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def csv_rows(path, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def prepare_configs(base, system, portal):
    threshold = deepcopy(base)
    for line in threshold["batch_operations"]["lines"]:
        assert line["lox_rover"]["dispatch_kg"] == 15
        line["lox_rover"]["dispatch_kg"] = 10
    threshold["scenario"].update(name=LABELS[THRESHOLD], slug=THRESHOLD)

    distributed = portal["payload"]
    assert portal["validation"]["errors"] == []
    assert distributed["simulation"] == base["simulation"] == {"duration_hr": 168, "sample_hr": 1}
    assert distributed["routes"] == base["routes"]
    assert distributed["scenario_builder"]["module_equations"] == base["scenario_builder"]["module_equations"]
    new_batch = deepcopy(base["batch_operations"])
    assert new_batch["depots_kg"] == {DEPOT: 250}
    new_batch["depots_kg"] = {f"{DEPOT}_1": 125, f"{DEPOT}_2": 125}
    assert distributed["batch_operations"] == new_batch
    baseline_urban = system["urban_planning"]
    urban = portal["urban"]
    assert urban["site"] == baseline_urban["site"]
    assert urban["map_frame_m"] == baseline_urban["map_frame_m"]
    expected_modules = deepcopy(baseline_urban["module_instances"])
    expected_modules[f"{DEPOT}_1"] = expected_modules.pop(DEPOT)
    expected_modules[f"{DEPOT}_2"] = {"type": DEPOT, "position_m": [245, 760, 0], "rotation_deg": [0, 0, 0]}
    assert urban["modules"] == expected_modules

    original_routes = {r["id"]: r for r in base["scenario_builder"]["resource_routes"]}
    variant_routes = {r["id"]: r for r in distributed["scenario_builder"]["resource_routes"]}
    assert len(original_routes) == len(variant_routes) == 8 and original_routes.keys() == variant_routes.keys()
    audit = []
    for key, original in original_routes.items():
        variant = variant_routes[key]
        if original["flow"] != "LOX":
            assert original == variant
        elif original["rover_id"] == "LOXRover_1":
            assert variant == {**original, "to": f"{DEPOT}_1",
                               "route_name": f"ISRUPlant_1To{DEPOT}_1_LOX"}
        else:
            assert original["distance_km"] == 2.817 and variant["distance_km"] == .254
            assert variant == {**original, "to": f"{DEPOT}_2",
                               "route_name": f"ISRUPlant_2To{DEPOT}_2_LOX", "distance_km": .254,
                               "mean_slope_deg": 11.897, "max_slope_deg": 12.422}
        if original["flow"] in {"LOX", "Regolith"}:
            before = baseline_urban["route_geometry"][original["route_name"]]["waypoints_m"]
            after = urban["connections"][variant["route_name"]]["waypoints_m"]
            length = sum(math.dist(a[:2], b[:2]) for a, b in zip(after, after[1:])) / 1000
            assert round(length, 3) == variant["distance_km"]
            identical = before == after
            assert identical == (variant["rover_id"] != "LOXRover_2")
            audit.append({"route_id": key, "before": original, "executed": variant,
                          "identical_waypoints": identical, "measured_plan_distance_km": length})
    return threshold, distributed, audit


def delivery_events(result):
    return [event for event in result["events"]
            if event["event"] == "material_delivered" and event["resource"] == "LOX"]


def summarize(result):
    final = result["summary"]
    times = {row["time_hr"]: row for row in result["time_series"]}
    deliveries = delivery_events(result)
    final_buffers = final["liquid_stocks_kg"]
    assert all(final["depots_kg"][depot] == sum(e["mass_kg"] for e in deliveries if e["destination"] == depot)
               for depot in final["depots_kg"])
    assert len(times) == 169 and final["time_hr"] == 168
    produced = sum(line["liquid_kg"] for line in final["lines"].values())
    assert abs(produced - sum(final_buffers.values()) - sum(final["depots_kg"].values())
               - final["mass_in_transit_kg"]["lox"]) < 1e-7
    assert result["max_event_mass_residual_kg"] < 1e-7
    assert all(abs(x) < 1e-7 for x in final["mass_residual_kg"].values())

    missed = Counter()
    berth_entries = {}
    berth_wait_hr = []
    for event in result["events"]:
        if event["event"] == "mission_missed":
            missed[(event["actor"], event["mission"], event["reason"])] += 1
        if event["event"] == "depot_wait_started":
            berth_entries[event["actor"]] = event["time_hr"]
        if event["event"] == "depot_wait_ended":
            berth_wait_hr.append(event["time_hr"] - berth_entries.pop(event["actor"]))
    vehicles = {}
    for name in ("LOXRover_1", "LOXRover_2"):
        relevant = [e for e in deliveries if e["actor"] == name]
        assert relevant
        vehicles[name] = {
            "first_delivery_hr": relevant[0]["time_hr"],
            "destination": relevant[0]["destination"],
            "delivered_kg": sum(e["mass_kg"] for e in relevant),
            "delivery_count": len(relevant),
            "mean_delivered_payload_kg": sum(e["mass_kg"] for e in relevant) / len(relevant),
            "completed_distance_km": final["vehicles"][name]["completed_distance_km"],
            "final_phase": final["vehicles"][name]["phase"],
        }
    return {
        "batches_by_plant": {name: {"completed": line["completed"], "missed": line["missed"],
                                    "liquid_kg": line["liquid_kg"], "regolith_kg": line["processed_kg"]}
                             for name, line in final["lines"].items()},
        "liquid_produced_kg": produced,
        "depot_inventory_kg": {str(h): times[h]["depots_kg"] for h in (24, 48, 168)},
        "final_buffer_kg": final_buffers,
        "final_lox_in_transit_kg": final["mass_in_transit_kg"]["lox"],
        "vehicles": vehicles,
        "depot_wait_max_hr": max(berth_wait_hr, default=0),
        "open_depot_waits": berth_entries,
        "mission_misses": [{"actor": a, "mission": m, "reason": r, "count": n}
                           for (a, m, r), n in sorted(missed.items())],
        "residue_final_kg": {name: line["residue_kg"] for name, line in final["lines"].items()},
        "energy": final["energy"],
        "final_mass_residual_kg": final["mass_residual_kg"],
        "max_event_mass_residual_kg": result["max_event_mass_residual_kg"],
    }


def time_rows(result):
    for state in result["time_series"]:
        yield {"time_hr": state["time_hr"], "liquid_produced_kg": sum(
            p["liquid_kg"] for p in state["lines"].values()),
            **{f"{d}_kg": mass for d, mass in state["depots_kg"].items()},
            **{f"{p}_buffer_kg": mass for p, mass in state["liquid_stocks_kg"].items()},
            "in_transit_lox_kg": state["mass_in_transit_kg"]["lox"],
            **{f"{p}_batches": value["completed"] for p, value in state["lines"].items()},
            **{f"{r}_{metric}": vehicle[metric] for r, vehicle in state["vehicles"].items()
               for metric in ("phase", "cargo_kg", "completed_distance_km")}}


def archive_run(folder, key, config, active, baseline, baseline_result, revision):
    folder.mkdir()
    opts = {"scenario_config": config, "active_nodes": active}
    check_scenario_validity(opts)
    resolved = load_scenario_config(opts)
    run_id = f"{key}-168h-01"
    result = run_scenario(opts)
    summary = summarize(result)
    # Compare upstream event histories in order, including their timing.
    fixed_actors = {"ISRUPlant_1", "ISRUPlant_2", "RegolithRover_1", "RegolithRover_2",
                    "Liquefier_1", "Liquefier_2"}
    def upstream(data):
        return [e for e in data["events"] if e["actor"] in fixed_actors]
    assert upstream(result) == upstream(baseline_result)
    assert result["summary"]["energy"] == baseline_result["summary"]["energy"]
    fields = collect_result_fields(opts, result)
    assert fields["results"]["Scenario_Config"] == resolved
    put(folder / "configuration.json", config)
    put(folder / "resolved.json", resolved)
    put(folder / "summary.json", summary)
    (folder / "results.json.gz").write_bytes(gzip.compress(json_bytes(result), mtime=0))
    (folder / "des_results.json").write_text(json.dumps({
        "request_id": run_id, "scenario_slug": config["scenario"]["slug"],
        "scenario_name": LABELS[key], "status": "success", **fields,
    }, separators=(",", ":"), allow_nan=False) + "\n")
    csv_rows(folder / "hourly.csv", list(time_rows(result)))
    csv_rows(folder / "lox_deliveries.csv", delivery_events(result))
    assert sha(REFERENCE / "scenario.json") == baseline
    source_files = [*sorted((ROOT / "S24/DES_pipeline_version").glob("*.py")),
                    ROOT / "clean_database/des/scenario_config.json",
                    Path(__file__).resolve(), REFERENCE / "scenario.json",
                    REFERENCE / "results.json.gz", REFERENCE / "system.json"]
    if key == STORAGE:
        source_files.extend([PORTAL_EXPORT, PREFLIGHT / "input_snapshot.json"])
    put(folder / "provenance.json", {
        "run_id": run_id, "code_revision": revision, "python": platform.python_version(),
        "platform": platform.platform(), "simpy": simpy.__version__,
        "entry_point": "S24.DES_pipeline_version.scenario_runner.run_scenario",
        "execution": "Local Python dispatcher, with the archived portal payload for distributed storage",
        "upstream_event_history_equal_to_reference": True,
        "upstream_event_count": len(upstream(result)),
        "source_and_input_sha256": {str(f.relative_to(ROOT)): sha(f) for f in source_files},
        "artifact_sha256": {f.name: sha(f) for f in sorted(folder.iterdir())},
    })
    return summary


def main(folder):
    base = read(REFERENCE / "scenario.json")
    system = read(REFERENCE / "system.json")
    baseline_result = json.loads(gzip.decompress((REFERENCE / "results.json.gz").read_bytes()))
    threshold, distributed, route_audit = prepare_configs(base, system, read(PORTAL_EXPORT))
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    fixed_hashes = read(REFERENCE / "provenance.json")["source_sha256"]
    for f, digest in fixed_hashes.items():
        if f.startswith("S24/DES_pipeline_version/") or f == "clean_database/des/scenario_config.json":
            assert sha(ROOT / f) == digest, f
    folder.mkdir(parents=True, exist_ok=False)
    put(folder / "route_audit.json", route_audit)
    summaries = {"reference": summarize(baseline_result)}
    for name, config in [(THRESHOLD, threshold), (STORAGE, distributed)]:
        summaries[name] = archive_run(folder / name, name, config, base["scenario"]["active_types"],
                                      sha(REFERENCE / "scenario.json"), baseline_result, revision)
    put(folder / "comparison.json", summaries)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="New directory for the two 168 h runs")
    main(parser.parse_args().output)
