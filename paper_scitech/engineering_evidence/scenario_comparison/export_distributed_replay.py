"""Package the executed distributed storage case for the standard Kit selector."""

import argparse
from collections import Counter
import json
from pathlib import Path
import re

from pxr import Usd, UsdGeom, UsdUtils

from S24.usd.waypoints import write_connections_usda
from paper_scitech.engineering_evidence.scenario_comparison.run_comparison import (
    ROOT, REFERENCE, PORTAL_EXPORT, SLUG, STORAGE, LABELS, put, read, sha,
)

import sys

sys.path.insert(0, str(ROOT / "extensions/lsp1.pipeline"))
from lsp1_pipeline.manifest_builder import build_manifest


def main(out, result_dir):
    replay_source = ROOT / "outputs/scenarios/Lunar_Spaceport/omniverse"
    portal = read(PORTAL_EXPORT)
    config = read(result_dir / "configuration.json")
    assert config == portal["payload"]
    urban = portal["urban"]

    system = read(REFERENCE / "system.json")
    planning = system["urban_planning"]
    planning["module_instances"] = urban["modules"]
    planning["routes"] = urban["mst_edges"]
    planning["route_geometry"] = urban["connections"]
    logic = system["scenario_logic"]
    logic.update(config["scenario_builder"], batch_operations=config["batch_operations"])
    original_interfaces = [c for c in system["connections"] if c["type"] != "OperationalRoute"]
    routes = [r for r in logic["resource_routes"] if r["flow"] in {"LOX", "Regolith"}]
    system["connections"] = original_interfaces + [
        {"name": r["route_name"], "type": "OperationalRoute", "flow": r["flow"],
         "from": {"part": r["from"]}, "to": {"part": r["to"]}, "rover_id": r["rover_id"],
         "stops": r["stops"], "path": urban["connections"][r["route_name"]]}
        for r in routes
    ]
    system["metadata"].update(scenario_config=str((result_dir / "configuration.json").relative_to(ROOT)),
                              scope="Archived SysML types and interfaces; instances and routes from the executed portal export")
    out.mkdir(parents=True, exist_ok=False)
    omni = out / "omniverse"
    omni.mkdir()
    system_path = out / "system.json"
    put(system_path, system)
    scene_path = omni / "scene.usda"
    scene_path.write_text(re.sub(r"@assets/", "@../../Lunar_Spaceport/omniverse/assets/",
                                 (replay_source / "scene.usda").read_text()))
    waypoints = omni / "waypoints.usda"
    write_connections_usda(system_path, waypoints, curve_width=4.0, marker_radius=10.0, verbose=0)
    path = omni / "manifest.json"
    des_path = result_dir / "des_results.json"
    manifest = build_manifest(system_json_path=system_path, waypoints_usd_path=waypoints,
                              des_json_path=des_path, scene_usd_path=scene_path,
                              terrain_usd_path=replay_source / "assets/Lunar_surface_v4.usdc",
                              output_path=path, scenario_slug=SLUG)
    manifest["scenario"]["name"] = LABELS[STORAGE]
    path.write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")) + "\n")

    dependencies = set()
    for usd in [scene_path, waypoints, replay_source / "assets/Lunar_surface_v4.usdc"]:
        layers, files, unresolved = UsdUtils.ComputeAllDependencies(str(usd))
        assert not unresolved, unresolved
        dependencies.update(Path(layer.realPath) for layer in layers)
        dependencies.update(Path(filename.split("[")[0]) for filename in files)
    des = read(des_path)
    assert manifest["scenario"]["request_id"] == des["request_id"]
    assert manifest["playback"]["display_duration_hours"] == 168
    routes_by_id = {r["id"]: r for r in routes}
    drives = [e for e in des["operation_events"]
              if e["event"] == "phase_start" and e["phase"].startswith("drive_")]
    def movement_key(actor, route, start, end, source, target, reverse):
        return (actor, route, round(start, 9), round(end, 9), source, target, reverse)
    archived_moves = Counter(
        movement_key(e["actor"], routes_by_id[e["route_id"]]["route_name"], e["time_hr"],
                     e["time_hr"] + e["duration_hr"], e["origin"], e["destination"],
                     e["route_direction"] == "return")
        for e in drives
    )
    visual_moves = Counter(
        movement_key(a["id"], e["route_name"], e["start_time"], e["end_time"],
                     e["from_module"], e["to_module"], e["reverse"])
        for a in manifest["actors"] for e in a["movements"]
    )
    assert archived_moves == visual_moves and not manifest["warnings"]
    route_stage = Usd.Stage.Open(str(waypoints))
    route_prims = {r["route_name"]: f"{manifest['waypoint_root']}/{r['route_name']}" for r in routes}
    assert all(route_stage.GetPrimAtPath(p) for p in route_prims.values())

    modules = manifest["terrain_projection"]["modules"]["modules"]
    depot_ids = list(config["batch_operations"]["depots_kg"])
    scene = Usd.Stage.Open(str(scene_path))
    scene.SetEditTarget(scene.GetSessionLayer())
    for name in depot_ids:
        record = modules[name]
        assert record["source_module"] == "PropellantDepot"
        if not scene.GetPrimAtPath(record["prim_path"]):
            UsdGeom.Xform.Define(scene, record["prim_path"]).GetPrim().GetReferences().AddInternalReference(
                "/World/PropellantDepot")
        assert any(p.IsA(UsdGeom.Mesh) for p in Usd.PrimRange(scene.GetPrimAtPath(record["prim_path"])))
    at_26 = des["log"]["26.0"]
    check = {
        "request_id": des["request_id"], "checked": "Headless OpenUSD and DES data",
        "nvidia_kit": "Pending on workstation",
        "movement_intervals": sum(archived_moves.values()),
        "plant_intervals": sum(map(len, manifest["plant_operations"].values())),
        "route_prims": route_prims, "depots": {name: modules[name] for name in depot_ids},
        "hour_26": {
            "total_produced_kg": at_26["Batch_Operations"]["Total_LOX_Produced_kg"],
            "depot_inventory_kg": {name: at_26[name]["LOX_Stored"] for name in depot_ids},
            "in_transit_kg": at_26["Batch_Operations"]["In_Transit_LOX_kg"],
            "rover_operations": {a["id"]: at_26[a["id"]]["Operation"] for a in manifest["actors"]},
        },
        "route_projection": {r["route_name"]: {
            "status": manifest["terrain_projection"]["routes"]["routes"][r["route_name"]]["status"],
            "missing": manifest["terrain_projection"]["routes"]["routes"][r["route_name"]]["out_of_bounds_count"],
        } for r in routes},
        "dependencies_sha256": {str(p.relative_to(ROOT)): sha(p) for p in sorted(dependencies)},
        "files_sha256": {str(p.relative_to(ROOT)): sha(p) for p in (path, system_path, des_path, PORTAL_EXPORT)},
    }
    assert check["plant_intervals"] == 100
    assert all(r["missing"] == 0 for r in check["route_projection"].values())
    put(out / "openusd_checks.json", check)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="New scenario folder beside Lunar_Spaceport")
    parser.add_argument("run", type=Path, help="Distributed storage run directory")
    args = parser.parse_args()
    main(args.output.resolve(), args.run.resolve())
