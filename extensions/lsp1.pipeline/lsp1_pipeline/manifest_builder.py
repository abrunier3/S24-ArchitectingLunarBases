from __future__ import annotations

import argparse
import json
import math
import os
import re
from pathlib import Path
from typing import Any


DEFAULT_DASHBOARD_FIELDS = [
    {"key": "current_load", "label": "Load", "unit": "kg"},
    {"key": "battery_charge", "label": "Battery", "unit": "kWh"},
    {"key": "total_distance_traveled", "label": "Distance", "unit": "km"},
]


def _load_json(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _repo_relative(path: Path, *, start: Path) -> str:
    return os.path.relpath(path.resolve(), start.resolve()).replace("\\", "/")


def _terrain_bbox(terrain_usd_path: Path) -> dict[str, Any] | None:
    try:
        from pxr import Usd, UsdGeom
    except Exception:
        return None

    try:
        stage = Usd.Stage.Open(str(terrain_usd_path))
    except Exception:
        return None

    if not stage:
        return None

    bound_prim = stage.GetDefaultPrim() or stage.GetPseudoRoot()
    bbox_cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
    bbox_range = bbox_cache.ComputeWorldBound(bound_prim).ComputeAlignedRange()
    mn = bbox_range.GetMin()
    mx = bbox_range.GetMax()

    return {
        "min": [float(mn[i]) for i in range(3)],
        "max": [float(mx[i]) for i in range(3)],
        "size": [float(mx[i] - mn[i]) for i in range(3)],
        "up_axis": str(UsdGeom.GetStageUpAxis(stage)),
        "meters_per_unit": float(UsdGeom.GetStageMetersPerUnit(stage) or 1.0),
    }


def _collect_system_xy_points(system_json: dict[str, Any]) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []

    for part in system_json.get("parts", []):
        pos = part.get("transform", {}).get("position_m")
        if isinstance(pos, list) and len(pos) >= 2:
            points.append((float(pos[0]), float(pos[1])))

    for connection in system_json.get("connections", []):
        waypoints = connection.get("path", {}).get("waypoints_m") or []
        for wp in waypoints:
            if isinstance(wp, list) and len(wp) >= 2:
                points.append((float(wp[0]), float(wp[1])))

    return points


def _map_frame_from_system(system_json: dict[str, Any]) -> dict[str, Any]:
    urban_planning = system_json.get("urban_planning") or {}
    frame = urban_planning.get("map_frame_m") or {}

    required = ("x_min", "x_max", "y_min", "y_max")
    if all(key in frame for key in required):
        x_min = float(frame["x_min"])
        x_max = float(frame["x_max"])
        y_min = float(frame["y_min"])
        y_max = float(frame["y_max"])
        return {
            **frame,
            "x_min": x_min,
            "x_max": x_max,
            "y_min": y_min,
            "y_max": y_max,
            "width_m": float(frame.get("width_m", x_max - x_min)),
            "height_m": float(frame.get("height_m", y_max - y_min)),
            "source": "urban_planning.map_frame_m",
        }

    points = _collect_system_xy_points(system_json)
    if points:
        max_abs = max(max(abs(x), abs(y)) for x, y in points)
        half_extent = max(1500.0, math.ceil((max_abs + 250.0) / 250.0) * 250.0)
    else:
        half_extent = 1500.0

    return {
        "center_m": [0.0, 0.0, 0.0],
        "x_min": -half_extent,
        "x_max": half_extent,
        "y_min": -half_extent,
        "y_max": half_extent,
        "width_m": half_extent * 2.0,
        "height_m": half_extent * 2.0,
        "source": "derived_from_system_extent",
    }


def _build_terrain_config(
    *,
    terrain_usd_path: Path,
    output_dir: Path,
    system_json: dict[str, Any],
) -> dict[str, Any]:
    frame = _map_frame_from_system(system_json)
    bbox = _terrain_bbox(terrain_usd_path)

    config: dict[str, Any] = {
        "usd": _repo_relative(terrain_usd_path, start=output_dir),
        "prim_path": "/World/Lunar_Surface_v4",
        "alignment": "ui_map_frame_grounded",
        "map_frame_m": frame,
    }

    if not bbox:
        config.update({
            "translate": [0.0, 0.0, 0.0],
            "scale": [1.0, 1.0, 1.0],
            "warning": "Terrain bbox unavailable; using identity transform.",
        })
        return config

    source_min = bbox["min"]
    source_max = bbox["max"]
    source_size = bbox["size"]
    target_width = float(frame["x_max"] - frame["x_min"])
    target_height = float(frame["y_max"] - frame["y_min"])

    scale_x = target_width / source_size[0] if source_size[0] else 1.0
    scale_y = target_height / source_size[1] if source_size[1] else scale_x
    scale_z = (abs(scale_x) + abs(scale_y)) / 2.0

    source_center_x = (source_min[0] + source_max[0]) / 2.0
    source_center_y = (source_min[1] + source_max[1]) / 2.0
    target_center_x = (float(frame["x_min"]) + float(frame["x_max"])) / 2.0
    target_center_y = (float(frame["y_min"]) + float(frame["y_max"])) / 2.0

    translate = [
        target_center_x - source_center_x * scale_x,
        target_center_y - source_center_y * scale_y,
        -source_min[2] * scale_z,
    ]

    config.update({
        "translate": [round(v, 6) for v in translate],
        "scale": [round(scale_x, 9), round(scale_y, 9), round(scale_z, 9)],
        "source_bbox": bbox,
        "world_bbox": {
            "min": [
                round(source_min[0] * scale_x + translate[0], 6),
                round(source_min[1] * scale_y + translate[1], 6),
                0.0,
            ],
            "max": [
                round(source_max[0] * scale_x + translate[0], 6),
                round(source_max[1] * scale_y + translate[1], 6),
                round((source_max[2] - source_min[2]) * scale_z, 6),
            ],
        },
    })

    return config


def _sorted_log_items(des_data: dict[str, Any]) -> list[tuple[float, dict[str, Any]]]:
    raw_log = des_data.get("log", des_data)
    if not isinstance(raw_log, dict):
        return []

    items: list[tuple[float, dict[str, Any]]] = []
    for key, value in raw_log.items():
        try:
            t = float(key)
        except (TypeError, ValueError):
            continue
        if isinstance(value, dict):
            items.append((t, value))

    return sorted(items, key=lambda item: item[0])


def _simulation_end_time(des_data: dict[str, Any]) -> float:
    log_items = _sorted_log_items(des_data)
    if log_items:
        return log_items[-1][0]
    return 0.0


def _system_part_names(system_json: dict[str, Any]) -> set[str]:
    return {
        part.get("name", "")
        for part in system_json.get("parts", [])
        if part.get("name")
    }


def _route_names_from_waypoints(waypoints_path: Path) -> set[str]:
    text = waypoints_path.read_text(encoding="utf-8", errors="ignore")
    marker = 'def Xform "ConnectionWaypoints"'
    start = text.find(marker)
    if start == -1:
        return set()

    route_names = set()
    for name in re.findall(r'def\s+Xform\s+"([^"]+)"', text[start:]):
        if not name.startswith("Waypoint_") and name != "ConnectionWaypoints":
            route_names.add(name)
    return route_names


def _split_route_name(route_name: str, part_names: set[str]) -> tuple[str | None, str | None]:
    ordered = sorted(part_names, key=len, reverse=True)
    for src in ordered:
        if not route_name.startswith(src):
            continue
        suffix = route_name[len(src):]
        if not suffix.startswith("To"):
            continue
        dst = suffix[2:]
        if dst in part_names:
            return src, dst
    return None, None


def _movement_connections(
    system_json: dict[str, Any],
    waypoints_path: Path,
) -> dict[str, dict[str, Any]]:
    part_names = _system_part_names(system_json)
    waypoint_routes = _route_names_from_waypoints(waypoints_path)

    movement_routes: dict[str, dict[str, Any]] = {}
    for connection in system_json.get("connections", []):
        route_name = connection.get("name")
        flow = connection.get("flow")
        if not route_name or route_name not in waypoint_routes:
            continue
        if flow not in {"Regolith", "LOX"}:
            continue

        from_module, to_module = _split_route_name(route_name, part_names)
        movement_routes[flow] = {
            "route_name": route_name,
            "from_module": from_module or connection.get("from", {}).get("part"),
            "to_module": to_module or connection.get("to", {}).get("part"),
            "flow": flow,
            "type": connection.get("type"),
        }

    return movement_routes


def _get_rover_names(des_data: dict[str, Any], prefix: str) -> list[str]:
    log_items = _sorted_log_items(des_data)
    if log_items:
        first_snapshot = log_items[0][1]
        names = [name for name in first_snapshot if name.startswith(prefix)]
        if names:
            return sorted(names)

    results_key = "Regolith_Cargo_Rovers" if prefix == "Regolith Cargo Rover" else "LOX_Cargo_Rover"
    results = des_data.get("results", {}).get(results_key, {})
    if isinstance(results, dict):
        names = [
            name
            for name, value in results.items()
            if name != "Fleet_Totals" and isinstance(value, dict)
        ]
        if names:
            return sorted(names)
        if results.get("Name"):
            return [results["Name"]]

    return []


def _final_rover_distance(des_data: dict[str, Any], rover_name: str) -> float:
    results = des_data.get("results", {})

    regolith = results.get("Regolith_Cargo_Rovers", {})
    if rover_name in regolith:
        return float(regolith[rover_name].get("Total_Distance_km", 0.0))

    lox = results.get("LOX_Cargo_Rover", {})
    if lox.get("Name") == rover_name:
        return float(lox.get("Total_Distance_km", 0.0))

    distance = 0.0
    for _, snapshot in _sorted_log_items(des_data):
        rover = snapshot.get(rover_name, {})
        distance = max(distance, float(rover.get("total_distance_traveled", 0.0)))
    return distance


def _build_regolith_movements(
    des_data: dict[str, Any],
    route: dict[str, Any],
) -> list[dict[str, Any]]:
    inputs = des_data.get("inputs", {})
    distance = float(inputs.get("Regolith_Haul_Distance", 0.0))
    hours_per_km = float(inputs.get("Rover_Travel_Time", 0.0))
    duration = distance * hours_per_km
    sim_end = _simulation_end_time(des_data)

    if distance <= 0 or duration <= 0 or sim_end <= 0:
        return []

    movements = []
    rover_names = _get_rover_names(des_data, "Regolith Cargo Rover")

    for rover_name in rover_names:
        total_distance = _final_rover_distance(des_data, rover_name)
        if total_distance <= 0:
            continue

        trip_count = max(1, int(math.ceil(total_distance / distance - 1e-9)))
        for trip_idx in range(trip_count):
            start_time = trip_idx * duration
            if start_time > sim_end:
                break

            end_time = min(start_time + duration, sim_end)
            movements.append({
                "actor_id": rover_name,
                "route_name": route["route_name"],
                "from_module": route.get("from_module"),
                "to_module": route.get("to_module"),
                "start_time": round(start_time, 3),
                "end_time": round(end_time, 3),
                "source": "des:Regolith_Haul_Distance*Rover_Travel_Time",
            })

    return movements


def _build_lox_movements(
    des_data: dict[str, Any],
    route: dict[str, Any],
) -> list[dict[str, Any]]:
    log_items = _sorted_log_items(des_data)
    if not log_items:
        return []

    movements = []
    for rover_name in _get_rover_names(des_data, "LOX Cargo Rover"):
        in_motion = False
        start_time = None

        for t, snapshot in log_items:
            rover = snapshot.get(rover_name, {})
            current_load = float(rover.get("current_load", 0.0) or 0.0)

            if not in_motion and current_load > 0:
                in_motion = True
                start_time = t

            if in_motion and current_load <= 0 and start_time is not None and t > start_time:
                movements.append({
                    "actor_id": rover_name,
                    "route_name": route["route_name"],
                    "from_module": route.get("from_module"),
                    "to_module": route.get("to_module"),
                    "start_time": round(start_time, 3),
                    "end_time": round(t, 3),
                    "source": "des:LOX rover load episode",
                })
                in_motion = False
                start_time = None

        if in_motion and start_time is not None:
            movements.append({
                "actor_id": rover_name,
                "route_name": route["route_name"],
                "from_module": route.get("from_module"),
                "to_module": route.get("to_module"),
                "start_time": round(start_time, 3),
                "end_time": round(log_items[-1][0], 3),
                "source": "des:LOX rover load episode",
            })

    return movements


def _actor_prim_path(actor_id: str) -> str:
    if actor_id.startswith("Regolith Cargo Rover"):
        return "/World/RegolithRover"
    if actor_id == "LOX Cargo Rover":
        return "/World/LOXRover"
    return f"/World/{actor_id.replace(' ', '_')}"


def _actor_label(actor_id: str) -> str:
    if actor_id.startswith("Regolith Cargo Rover"):
        return actor_id.replace(" Cargo Rover", " Rover")
    return actor_id.replace(" Cargo ", " ")


def build_manifest(
    *,
    system_json_path: str | Path,
    waypoints_usd_path: str | Path,
    des_json_path: str | Path,
    scene_usd_path: str | Path,
    terrain_usd_path: str | Path,
    output_path: str | Path,
) -> dict[str, Any]:
    system_json_path = Path(system_json_path).resolve()
    waypoints_usd_path = Path(waypoints_usd_path).resolve()
    des_json_path = Path(des_json_path).resolve()
    scene_usd_path = Path(scene_usd_path).resolve()
    terrain_usd_path = Path(terrain_usd_path).resolve()
    output_path = Path(output_path).resolve()
    output_dir = output_path.parent

    system_json = _load_json(system_json_path)
    des_data = _load_json(des_json_path)
    routes = _movement_connections(system_json, waypoints_usd_path)

    all_movements: list[dict[str, Any]] = []
    warnings: list[str] = []
    if "Regolith" in routes:
        regolith_movements = _build_regolith_movements(des_data, routes["Regolith"])
        all_movements.extend(regolith_movements)
        if not regolith_movements:
            warnings.append("No regolith rover movements were generated from the DES output.")
    if "LOX" in routes:
        lox_movements = _build_lox_movements(des_data, routes["LOX"])
        all_movements.extend(lox_movements)
        if not lox_movements:
            warnings.append("No LOX rover movements were generated from the DES output.")

    actors_by_id: dict[str, dict[str, Any]] = {}
    for movement in all_movements:
        actor_id = movement.pop("actor_id")
        actor = actors_by_id.setdefault(actor_id, {
            "id": actor_id,
            "label": _actor_label(actor_id),
            "prim_path": _actor_prim_path(actor_id),
            "dashboard_fields": DEFAULT_DASHBOARD_FIELDS,
            "movements": [],
        })
        actor["movements"].append(movement)

    for actor in actors_by_id.values():
        actor["movements"].sort(key=lambda movement: movement["start_time"])
        first = actor["movements"][0]
        actor["from_module"] = first.get("from_module")
        actor["to_module"] = first.get("to_module")
        actor["route_name"] = first.get("route_name")
        actor["start_time"] = first.get("start_time")
        actor["end_time"] = first.get("end_time")

    sim_end = _simulation_end_time(des_data)
    manifest = {
        "scene_usd": _repo_relative(scene_usd_path, start=output_dir),
        "waypoints_usd": _repo_relative(waypoints_usd_path, start=output_dir),
        "des_log": _repo_relative(des_json_path, start=output_dir),
        "system_json": _repo_relative(system_json_path, start=output_dir),
        "generated_from": {
            "system_json": _repo_relative(system_json_path, start=output_dir),
            "waypoints_usd": _repo_relative(waypoints_usd_path, start=output_dir),
            "des_json": _repo_relative(des_json_path, start=output_dir),
        },
        "warnings": warnings,
        "playback": {
            "seconds_per_sim_time_unit": 1.0,
            "display_duration_hours": sim_end,
        },
        "waypoint_root": "/World/ConnectionWaypoints",
        "follow_camera": {
            "path": "/World/DES_FollowCamera",
            "offset": [40.0, 10.0, 20.0],
            "rotateXYZ": [70.0, 0.0, 120.0],
            "focal_length": 12.0,
        },
        "terrain": _build_terrain_config(
            terrain_usd_path=terrain_usd_path,
            output_dir=output_dir,
            system_json=system_json,
        ),
        "actors": sorted(actors_by_id.values(), key=lambda actor: actor["id"]),
    }

    return manifest


def write_manifest(manifest: dict[str, Any], output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build an Omniverse visualization manifest from system JSON, waypoints, and DES output."
    )
    parser.add_argument("--system-json", required=True)
    parser.add_argument("--waypoints-usd", required=True)
    parser.add_argument("--des-json", required=True)
    parser.add_argument("--scene-usd", required=True)
    parser.add_argument("--terrain-usd", required=True)
    parser.add_argument("--output", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    manifest = build_manifest(
        system_json_path=args.system_json,
        waypoints_usd_path=args.waypoints_usd,
        des_json_path=args.des_json,
        scene_usd_path=args.scene_usd,
        terrain_usd_path=args.terrain_usd,
        output_path=args.output,
    )
    write_manifest(manifest, args.output)
    print(f"Wrote Omniverse manifest: {args.output}")
    print(f"Actors: {len(manifest.get('actors', []))}")
    for actor in manifest.get("actors", []):
        print(f"- {actor['id']}: {len(actor.get('movements', []))} movement(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
