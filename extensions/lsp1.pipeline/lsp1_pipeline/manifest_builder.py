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


def _round_point(point: tuple[float, float, float], digits: int = 3) -> list[float]:
    return [round(float(value), digits) for value in point]


def _point_in_triangle_height(
    x: float,
    y: float,
    triangle: tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]],
) -> float | None:
    (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = triangle
    denom = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
    if abs(denom) < 1e-12:
        return None

    a = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / denom
    b = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / denom
    c = 1.0 - a - b
    eps = 1e-7
    if a < -eps or b < -eps or c < -eps:
        return None
    return a * z1 + b * z2 + c * z3


class _TerrainSampler:
    def __init__(
        self,
        triangles: list[
            tuple[
                tuple[float, float, float],
                tuple[float, float, float],
                tuple[float, float, float],
            ]
        ],
        *,
        cell_size_m: float = 25.0,
    ) -> None:
        self.triangles = triangles
        self.cell_size_m = max(float(cell_size_m), 1.0)
        self.grid: dict[tuple[int, int], list[int]] = {}

        for idx, triangle in enumerate(triangles):
            xs = [point[0] for point in triangle]
            ys = [point[1] for point in triangle]
            ix_min = math.floor(min(xs) / self.cell_size_m)
            ix_max = math.floor(max(xs) / self.cell_size_m)
            iy_min = math.floor(min(ys) / self.cell_size_m)
            iy_max = math.floor(max(ys) / self.cell_size_m)

            for ix in range(ix_min, ix_max + 1):
                for iy in range(iy_min, iy_max + 1):
                    self.grid.setdefault((ix, iy), []).append(idx)

    def _candidate_indices(self, x: float, y: float) -> list[int]:
        ix = math.floor(x / self.cell_size_m)
        iy = math.floor(y / self.cell_size_m)

        candidates: list[int] = []
        seen: set[int] = set()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for idx in self.grid.get((ix + dx, iy + dy), []):
                    if idx not in seen:
                        candidates.append(idx)
                        seen.add(idx)

        return candidates

    def sample_height(self, x: float, y: float) -> float | None:
        candidate_indices = self._candidate_indices(x, y)
        if not candidate_indices:
            return None

        heights: list[float] = []
        for idx in candidate_indices:
            triangle = self.triangles[idx]
            height = _point_in_triangle_height(x, y, triangle)
            if height is not None:
                heights.append(height)
        if not heights:
            return None
        return max(heights)


def _build_terrain_sampler(
    *,
    terrain_usd_path: Path,
    terrain_config: dict[str, Any],
) -> _TerrainSampler | None:
    try:
        from pxr import Gf, Usd, UsdGeom
    except Exception:
        return None

    try:
        stage = Usd.Stage.Open(str(terrain_usd_path))
    except Exception:
        return None
    if not stage:
        return None

    translate = terrain_config.get("translate", [0.0, 0.0, 0.0])
    scale = terrain_config.get("scale", [1.0, 1.0, 1.0])
    if len(translate) < 3 or len(scale) < 3:
        return None

    def to_manifest_world(point: Gf.Vec3d) -> tuple[float, float, float]:
        return (
            float(point[0]) * float(scale[0]) + float(translate[0]),
            float(point[1]) * float(scale[1]) + float(translate[1]),
            float(point[2]) * float(scale[2]) + float(translate[2]),
        )

    xform_cache = UsdGeom.XformCache(Usd.TimeCode.Default())
    triangles: list[
        tuple[
            tuple[float, float, float],
            tuple[float, float, float],
            tuple[float, float, float],
        ]
    ] = []

    for prim in stage.Traverse():
        if not prim.IsA(UsdGeom.Mesh):
            continue

        mesh = UsdGeom.Mesh(prim)
        points = mesh.GetPointsAttr().Get() or []
        counts = mesh.GetFaceVertexCountsAttr().Get() or []
        indices = mesh.GetFaceVertexIndicesAttr().Get() or []
        if not points or not counts or not indices:
            continue

        local_to_stage = xform_cache.GetLocalToWorldTransform(prim)
        stage_points = [
            to_manifest_world(local_to_stage.Transform(Gf.Vec3d(point)))
            for point in points
        ]

        cursor = 0
        for count in counts:
            face_indices = indices[cursor:cursor + count]
            cursor += count
            if count < 3:
                continue

            first = stage_points[face_indices[0]]
            for idx in range(1, count - 1):
                triangles.append((
                    first,
                    stage_points[face_indices[idx]],
                    stage_points[face_indices[idx + 1]],
                ))

    if not triangles:
        return None
    return _TerrainSampler(triangles)


def _densify_waypoints(
    waypoints: list[list[float]],
    *,
    spacing_m: float,
) -> list[tuple[float, float, float]]:
    dense: list[tuple[float, float, float]] = []
    for idx, waypoint in enumerate(waypoints):
        if len(waypoint) < 2:
            continue

        current = (
            float(waypoint[0]),
            float(waypoint[1]),
            float(waypoint[2]) if len(waypoint) > 2 else 0.0,
        )
        if idx == 0:
            dense.append(current)
            continue

        previous = dense[-1]
        dx = current[0] - previous[0]
        dy = current[1] - previous[1]
        distance = math.hypot(dx, dy)
        if distance <= 1e-9:
            continue

        steps = max(1, int(math.ceil(distance / spacing_m)))
        for step in range(1, steps + 1):
            t = step / steps
            dense.append((
                previous[0] + dx * t,
                previous[1] + dy * t,
                previous[2] + (current[2] - previous[2]) * t,
            ))

    return dense


def _waypoint_tuple(waypoint: list[float]) -> tuple[float, float, float] | None:
    if len(waypoint) < 2:
        return None
    return (
        float(waypoint[0]),
        float(waypoint[1]),
        float(waypoint[2]) if len(waypoint) > 2 else 0.0,
    )


def _densify_segment(
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    *,
    spacing_m: float,
) -> list[tuple[float, float, float]]:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    dz = end[2] - start[2]
    distance = math.hypot(dx, dy)
    if distance <= 1e-9:
        return [start, end]

    steps = max(1, int(math.ceil(distance / spacing_m)))
    return [
        (
            start[0] + dx * (step / steps),
            start[1] + dy * (step / steps),
            start[2] + dz * (step / steps),
        )
        for step in range(steps + 1)
    ]


def _slope_color_rgb(max_slope_deg: float | None, out_of_bounds_count: int) -> list[float]:
    if out_of_bounds_count or max_slope_deg is None:
        return [0.65, 0.65, 0.65]
    if max_slope_deg > 15.0:
        return [1.0, 0.05, 0.0]
    if max_slope_deg > 10.0:
        return [1.0, 0.45, 0.0]
    if max_slope_deg > 5.0:
        return [1.0, 0.9, 0.0]
    return [0.0, 0.85, 0.2]


def _slope_status(max_slope_deg: float | None, out_of_bounds_count: int) -> str:
    if out_of_bounds_count:
        return "terrain_alignment_warning"
    if max_slope_deg is None:
        return "unavailable"
    if max_slope_deg > 15.0:
        return "terrain_alignment_warning"
    if max_slope_deg > 10.0:
        return "caution"
    return "ok"


def _slope_stats_from_sampled(
    sampled: list[tuple[float, float, float] | None],
) -> tuple[list[float], list[dict[str, Any]], tuple[float, float, float] | None, tuple[float, float, float] | None]:
    slopes: list[float] = []
    slope_segments: list[dict[str, Any]] = []
    valid_samples = [point for point in sampled if point is not None]
    previous: tuple[float, float, float] | None = None
    for point in sampled:
        if point is None:
            previous = None
            continue
        if previous is not None:
            horizontal = math.hypot(point[0] - previous[0], point[1] - previous[1])
            if horizontal > 1e-9:
                slope_deg = math.degrees(math.atan2(abs(point[2] - previous[2]), horizontal))
                slopes.append(slope_deg)
                slope_segments.append({
                    "slope_deg": slope_deg,
                    "from_m": previous,
                    "to_m": point,
                })
        previous = point

    start = valid_samples[0] if valid_samples else None
    end = valid_samples[-1] if valid_samples else None
    return slopes, slope_segments, start, end


def _build_original_segment_diagnostics(
    *,
    waypoints: list[list[float]],
    sampler: _TerrainSampler,
    sample_spacing_m: float,
) -> list[dict[str, Any]]:
    segments = []
    for idx in range(len(waypoints) - 1):
        start = _waypoint_tuple(waypoints[idx])
        end = _waypoint_tuple(waypoints[idx + 1])
        if start is None or end is None:
            continue

        dense = _densify_segment(start, end, spacing_m=sample_spacing_m)
        sampled: list[tuple[float, float, float] | None] = []
        out_of_bounds = 0
        for point in dense:
            z = sampler.sample_height(point[0], point[1])
            if z is None:
                sampled.append(None)
                out_of_bounds += 1
            else:
                sampled.append((point[0], point[1], z))

        slopes, slope_segments, projected_start, projected_end = _slope_stats_from_sampled(sampled)
        max_slope = max(slopes) if slopes else None
        mean_slope = sum(slopes) / len(slopes) if slopes else None
        max_slope_segment = max(
            slope_segments,
            key=lambda segment: segment["slope_deg"],
            default=None,
        )

        segments.append({
            "index": idx,
            "from_waypoint_index": idx,
            "to_waypoint_index": idx + 1,
            "status": _slope_status(max_slope, out_of_bounds),
            "color_rgb": _slope_color_rgb(max_slope, out_of_bounds),
            "sample_count": len(dense),
            "valid_sample_count": len([point for point in sampled if point is not None]),
            "out_of_bounds_count": out_of_bounds,
            "max_slope_deg": round(max_slope, 3) if max_slope is not None else None,
            "mean_slope_deg": round(mean_slope, 3) if mean_slope is not None else None,
            "from_m": _round_point(projected_start) if projected_start else None,
            "to_m": _round_point(projected_end) if projected_end else None,
            "max_slope_subsegment": {
                "slope_deg": round(max_slope_segment["slope_deg"], 3),
                "from_m": _round_point(max_slope_segment["from_m"]),
                "to_m": _round_point(max_slope_segment["to_m"]),
            } if max_slope_segment else None,
        })

    return segments


def _build_terrain_route_diagnostics(
    *,
    system_json: dict[str, Any],
    sampler: _TerrainSampler | None,
    scene_cad_footprints: dict[str, dict[str, Any]] | None = None,
    sample_spacing_m: float = 2.0,
) -> dict[str, Any]:
    if sampler is None:
        return {
            "status": "unavailable",
            "reason": "Terrain sampler unavailable. OpenUSD may be missing or the terrain mesh could not be read.",
            "sample_spacing_m": sample_spacing_m,
            "routes": {},
        }

    routes: dict[str, Any] = {}
    scene_cad_footprints = scene_cad_footprints or {}
    urban_planning = system_json.get("urban_planning") or {}
    route_geometry = urban_planning.get("route_geometry") or {}
    route_definitions = {
        route.get("key"): route
        for route in urban_planning.get("routes", [])
        if route.get("key")
    }

    # Urban planning is the authoritative source for the paths drawn on the
    # map.  It contains every generated road, including instance-level rover
    # routes, whereas the SysML connection list can also contain abstract
    # functional links and legacy duplicates.
    if isinstance(route_geometry, dict) and route_geometry:
        route_inputs = []
        for route_name, geometry in route_geometry.items():
            geometry = geometry if isinstance(geometry, dict) else {}
            definition = route_definitions.get(route_name) or {}
            route_inputs.append({
                "name": route_name,
                "flow": geometry.get("flow") or definition.get("flow"),
                "visible_in_scene": bool(definition),
                "path": geometry,
            })
    else:
        route_inputs = system_json.get("connections", [])

    for connection in route_inputs:
        path = connection.get("path") or {}
        waypoints = path.get("waypoints_m") or []
        if not waypoints:
            continue

        route_name = connection.get("name", "UnnamedRoute")
        dense = _densify_waypoints(waypoints, spacing_m=sample_spacing_m)
        original_segments = _build_original_segment_diagnostics(
            waypoints=waypoints,
            sampler=sampler,
            sample_spacing_m=sample_spacing_m,
        )
        sampled: list[tuple[float, float, float] | None] = []
        out_of_bounds = 0
        for point in dense:
            z = sampler.sample_height(point[0], point[1])
            if z is None:
                sampled.append(None)
                out_of_bounds += 1
            else:
                sampled.append((point[0], point[1], z))

        # Preserve each original route waypoint at its sampled terrain height.
        # This is consumed by Omniverse to color the same route segments the
        # user drew in the planning view.
        terrain_waypoints = []
        for waypoint in waypoints:
            point = _waypoint_tuple(waypoint)
            if point is None:
                continue
            z = sampler.sample_height(point[0], point[1])
            if z is not None:
                terrain_waypoints.append(_round_point((point[0], point[1], z)))

        slopes, slope_segments, _, _ = _slope_stats_from_sampled(sampled)
        valid_samples = [point for point in sampled if point is not None]
        rover_footprint = _rover_footprint_for_route(
            connection.get("flow"),
            scene_cad_footprints,
        )
        sampled_poses = _build_route_pose_samples(
            sampled_points=valid_samples,
            sampler=sampler,
            rover_footprint=rover_footprint,
        )
        max_slope = max(slopes) if slopes else None
        mean_slope = sum(slopes) / len(slopes) if slopes else None
        max_slope_segment = max(
            slope_segments,
            key=lambda segment: segment["slope_deg"],
            default=None,
        )

        routes[route_name] = {
            "flow": connection.get("flow"),
            "visible_in_scene": connection.get("visible_in_scene", True),
            "status": _slope_status(max_slope, out_of_bounds),
            "input_waypoint_count": len(waypoints),
            "original_waypoints_m": [_round_point(point) for point in waypoints],
            "terrain_waypoints_m": terrain_waypoints,
            "sample_count": len(dense),
            "valid_sample_count": len(valid_samples),
            "out_of_bounds_count": out_of_bounds,
            "max_slope_deg": round(max_slope, 3) if max_slope is not None else None,
            "mean_slope_deg": round(mean_slope, 3) if mean_slope is not None else None,
            "segment_color_basis": "original_waypoint_segments_by_max_slope",
            "original_segments": original_segments,
            "max_slope_segment": {
                "slope_deg": round(max_slope_segment["slope_deg"], 3),
                "from_m": _round_point(max_slope_segment["from_m"]),
                "to_m": _round_point(max_slope_segment["to_m"]),
            } if max_slope_segment else None,
            "max_allowed_slope_deg": 15.0,
            "rover_footprint_source": (rover_footprint or {}).get("source", "unavailable"),
            "rover_footprint_size_m": (rover_footprint or {}).get("size_m"),
            "rover_route_yaw_offset_deg": (rover_footprint or {}).get(
                "route_yaw_offset_deg",
                -90.0,
            ),
            "sampled_waypoints_m": [
                _round_point(point)
                for point in valid_samples
            ],
            "sampled_poses": sampled_poses,
        }

    warning_count = sum(
        1 for route in routes.values()
        if route.get("status") == "terrain_alignment_warning"
    )
    caution_count = sum(
        1 for route in routes.values()
        if route.get("status") == "caution"
    )

    return {
        "status": "terrain_alignment_warning" if warning_count else "ok",
        "sample_spacing_m": sample_spacing_m,
        "max_allowed_slope_deg": 15.0,
        "warning_count": warning_count,
        "caution_count": caution_count,
        "routes": routes,
    }


def _build_module_terrain_diagnostics(
    *,
    system_json: dict[str, Any],
    sampler: _TerrainSampler | None,
    scene_cad_footprints: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if sampler is None:
        return {
            "status": "unavailable",
            "reason": "Terrain sampler unavailable. OpenUSD may be missing or the terrain mesh could not be read.",
            "modules": {},
        }

    modules: dict[str, Any] = {}
    out_of_bounds = 0
    scene_cad_footprints = scene_cad_footprints or {}
    base_parts = {
        part.get("name"): part
        for part in system_json.get("parts", [])
        if part.get("name")
    }
    module_instances = (
        system_json.get("urban_planning", {}).get("module_instances", {})
    )
    parts_to_place: list[tuple[dict[str, Any], str, str]] = []
    if module_instances:
        for instance_name, instance in module_instances.items():
            source_name = instance.get("type") or re.sub(r"_\d+$", "", instance_name)
            source_part = base_parts.get(source_name)
            if not source_part:
                continue
            part = dict(source_part)
            part["name"] = instance_name
            part["transform"] = {
                "position_m": instance.get("position_m", [0.0, 0.0, 0.0]),
                "rotation_deg": instance.get("rotation_deg", [0.0, 0.0, 0.0]),
            }
            parts_to_place.append((part, instance_name, source_name))
    else:
        parts_to_place = [
            (part, part.get("name"), part.get("name"))
            for part in system_json.get("parts", [])
            if part.get("name")
        ]

    source_instance_counts: dict[str, int] = {}
    for part, name, source_name in parts_to_place:
        source_instance_counts[source_name] = source_instance_counts.get(source_name, 0) + 1
        source_index = source_instance_counts[source_name]
        prim_path = (
            f"/World/{source_name}"
            if source_index == 1
            else f"/World/{name}"
        )
        name = part.get("name")
        position = part.get("transform", {}).get("position_m")
        if not name or not isinstance(position, list) or len(position) < 2:
            continue

        x = float(position[0])
        y = float(position[1])
        authored_z = float(position[2]) if len(position) > 2 else 0.0
        footprint = scene_cad_footprints.get(source_name)
        footprint_samples = _module_footprint_sample_points(part, x, y, footprint)
        sampled_points = []
        missing_samples = 0
        for sample_x, sample_y, label, local_x, local_y in footprint_samples:
            terrain_z = sampler.sample_height(sample_x, sample_y)
            if terrain_z is None:
                missing_samples += 1
                sampled_points.append({
                    "label": label,
                    "local_xy_m": [round(local_x, 3), round(local_y, 3)],
                    "xy_m": [round(sample_x, 3), round(sample_y, 3)],
                    "terrain_z_m": None,
                })
            else:
                sampled_points.append({
                    "label": label,
                    "local_xy_m": [round(local_x, 3), round(local_y, 3)],
                    "xy_m": [round(sample_x, 3), round(sample_y, 3)],
                    "terrain_z_m": round(terrain_z, 3),
                })

        valid_z = [
            float(sample["terrain_z_m"])
            for sample in sampled_points
            if sample["terrain_z_m"] is not None
        ]
        if not valid_z:
            out_of_bounds += 1
            modules[name] = {
                "status": "out_of_terrain_bounds",
                "source_module": source_name,
                "prim_path": prim_path,
                "position_xy_m": [round(x, 3), round(y, 3)],
                "authored_z_m": round(authored_z, 3),
                "placement_z_m": None,
                "sample_strategy": "center_corners_edge_midpoints_grid_5x5_max",
                "footprint_source": (footprint or {}).get("source", "sysml_size_m"),
                "footprint_size_m": (footprint or {}).get("size_m"),
                "footprint_samples": sampled_points,
            }
            continue

        terrain_plane = _fit_module_terrain_plane(sampled_points)
        if terrain_plane:
            placement_z = terrain_plane["placement_z_m"]
            base_rotation = part.get("transform", {}).get("rotation_deg") or [0.0, 0.0, 0.0]
            while len(base_rotation) < 3:
                base_rotation.append(0.0)
            plane_rotation = terrain_plane["placement_rotation_deg"]
            placement_rotation = [
                round(float(base_rotation[0]) + plane_rotation[0], 3),
                round(float(base_rotation[1]) + plane_rotation[1], 3),
                round(float(base_rotation[2]), 3),
            ]
        else:
            placement_z = max(valid_z)
            placement_rotation = None

        modules[name] = {
            "status": "partial_footprint_out_of_bounds" if missing_samples else "ok",
            "source_module": source_name,
            "prim_path": prim_path,
            "position_xy_m": [round(x, 3), round(y, 3)],
            "authored_z_m": round(authored_z, 3),
            "placement_z_m": round(placement_z, 3),
            "delta_z_m": round(authored_z - placement_z, 3),
            "placement_rotation_deg": placement_rotation,
            "terrain_plane": terrain_plane,
            "sample_strategy": "center_corners_edge_midpoints_grid_5x5_max",
            "footprint_source": (footprint or {}).get("source", "sysml_size_m"),
            "footprint_size_m": (footprint or {}).get("size_m"),
            "footprint_sample_count": len(sampled_points),
            "missing_sample_count": missing_samples,
            "footprint_samples": sampled_points,
        }

    return {
        "status": "terrain_alignment_warning" if out_of_bounds else "ok",
        "out_of_bounds_count": out_of_bounds,
        "modules": modules,
    }


def _rover_footprint_for_route(
    flow: str | None,
    scene_cad_footprints: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    rover_name = "LOXRover" if flow == "LOX" else "RegolithRover"
    return scene_cad_footprints.get(rover_name)


def _build_route_pose_samples(
    *,
    sampled_points: list[tuple[float, float, float]],
    sampler: _TerrainSampler,
    rover_footprint: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    size_m = (rover_footprint or {}).get("size_m") or {}
    length = float(size_m.get("length") or 0.0)
    width = float(size_m.get("width") or 0.0)
    if length <= 0 or width <= 0 or len(sampled_points) < 2:
        return []

    route_yaw_offset = float((rover_footprint or {}).get("route_yaw_offset_deg", -90.0))

    poses = []
    for idx, point in enumerate(sampled_points):
        tangent = _route_sample_tangent(sampled_points, idx)
        if tangent is None:
            continue

        dx, dy, _ = tangent
        horizontal = math.hypot(dx, dy)
        if horizontal <= 1e-6:
            continue

        route_yaw = math.degrees(math.atan2(dy, dx))
        rover_yaw = route_yaw + route_yaw_offset
        samples = []
        for sample_x, sample_y, label, local_x, local_y in _oriented_footprint_sample_points(
            center_x=point[0],
            center_y=point[1],
            length=length,
            width=width,
            yaw_deg=rover_yaw,
            grid_count=3,
        ):
            terrain_z = sampler.sample_height(sample_x, sample_y)
            if terrain_z is None:
                continue
            samples.append({
                "label": label,
                "local_xy_m": [round(local_x, 3), round(local_y, 3)],
                "xy_m": [round(sample_x, 3), round(sample_y, 3)],
                "terrain_z_m": round(terrain_z, 3),
            })

        plane = _fit_module_terrain_plane(samples)
        if not plane:
            continue

        local_rotation = plane.get("placement_rotation_deg") or [0.0, 0.0, 0.0]
        poses.append({
            "position_m": [
                round(float(point[0]), 3),
                round(float(point[1]), 3),
                round(float(plane["placement_z_m"]), 3),
            ],
            "rotation_deg": [
                round(float(local_rotation[0]), 3),
                round(float(local_rotation[1]), 3),
                round(rover_yaw, 3),
            ],
            "terrain_plane": {
                "placement_strategy": plane.get("placement_strategy"),
                "min_clearance_m": plane.get("min_clearance_m"),
                "mean_clearance_m": plane.get("mean_clearance_m"),
                "max_clearance_m": plane.get("max_clearance_m"),
            },
        })

    return poses


def _route_sample_tangent(
    points: list[tuple[float, float, float]],
    idx: int,
) -> tuple[float, float, float] | None:
    if len(points) < 2:
        return None
    if idx <= 0:
        p0, p1 = points[0], points[1]
    elif idx >= len(points) - 1:
        p0, p1 = points[-2], points[-1]
    else:
        p0, p1 = points[idx - 1], points[idx + 1]
    return (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])


def _module_footprint_sample_points(
    part: dict[str, Any],
    center_x: float,
    center_y: float,
    footprint: dict[str, Any] | None = None,
) -> list[tuple[float, float, str, float, float]]:
    size_m = (footprint or {}).get("size_m")
    if not size_m:
        size_m = (part.get("dimensions") or {}).get("size_m") or {}
    length = float(size_m.get("length") or 0.0)
    width = float(size_m.get("width") or 0.0)
    if length <= 0 or width <= 0:
        return [(center_x, center_y, "center", 0.0, 0.0)]

    rotation = part.get("transform", {}).get("rotation_deg") or [0.0, 0.0, 0.0]
    yaw_deg = float(rotation[2]) if len(rotation) >= 3 else 0.0
    return _oriented_footprint_sample_points(
        center_x=center_x,
        center_y=center_y,
        length=length,
        width=width,
        yaw_deg=yaw_deg,
        grid_count=5,
    )


def _oriented_footprint_sample_points(
    *,
    center_x: float,
    center_y: float,
    length: float,
    width: float,
    yaw_deg: float,
    grid_count: int,
) -> list[tuple[float, float, str, float, float]]:
    yaw = math.radians(yaw_deg)
    cos_yaw = math.cos(yaw)
    sin_yaw = math.sin(yaw)
    half_l = length / 2.0
    half_w = width / 2.0

    named_samples = {
        (0.0, 0.0): "center",
        (-half_l, -half_w): "corner_front_left",
        (half_l, -half_w): "corner_front_right",
        (half_l, half_w): "corner_back_right",
        (-half_l, half_w): "corner_back_left",
        (0.0, -half_w): "edge_front_mid",
        (half_l, 0.0): "edge_right_mid",
        (0.0, half_w): "edge_back_mid",
        (-half_l, 0.0): "edge_left_mid",
    }

    local_samples = [
        (local_x, local_y, label)
        for (local_x, local_y), label in named_samples.items()
    ]
    for i in range(grid_count):
        local_x = -half_l + (length * i / (grid_count - 1))
        for j in range(grid_count):
            local_y = -half_w + (width * j / (grid_count - 1))
            key = (round(local_x, 9), round(local_y, 9))
            label = named_samples.get(key, f"grid_{i}_{j}")
            if not any(
                round(existing_x, 9) == key[0] and round(existing_y, 9) == key[1]
                for existing_x, existing_y, _ in local_samples
            ):
                local_samples.append((local_x, local_y, label))

    world_samples = []
    for local_x, local_y, label in local_samples:
        world_x = center_x + local_x * cos_yaw - local_y * sin_yaw
        world_y = center_y + local_x * sin_yaw + local_y * cos_yaw
        world_samples.append((world_x, world_y, label, local_x, local_y))

    return world_samples


def _load_scene_cad_footprints(
    scene_usd_path: Path,
) -> dict[str, dict[str, Any]]:
    footprints: dict[str, dict[str, Any]] = {}
    try:
        from pxr import Usd
    except Exception:
        return footprints

    try:
        stage = Usd.Stage.Open(str(scene_usd_path))
        if not stage:
            return footprints

        world = stage.GetPrimAtPath("/World")
        if not world or not world.IsValid():
            return footprints

        for prim in world.GetChildren():
            geom = stage.GetPrimAtPath(f"{prim.GetPath()}/Geometry")
            if not geom or not geom.IsValid():
                continue

            attr = geom.GetAttribute("cad:fittedBboxSize")
            value = attr.Get() if attr else None
            if value is None:
                continue

            length = abs(float(value[0]))
            width = abs(float(value[1]))
            if length <= 0 or width <= 0:
                continue

            source_front_attr = geom.GetAttribute("cad:userSourceFrontAxis")
            source_front = source_front_attr.Get() if source_front_attr else None
            route_yaw_offset = 0.0 if source_front else -90.0

            footprints[prim.GetName()] = {
                "source": "cad_fitted_bbox_xy",
                "size_m": {
                    "length": length,
                    "width": width,
                },
                "source_front_axis": str(source_front or ""),
                "route_yaw_offset_deg": route_yaw_offset,
            }

    except Exception:
        return footprints

    return footprints


def _fit_module_terrain_plane(
    sampled_points: list[dict[str, Any]],
) -> dict[str, Any] | None:
    valid = [
        sample for sample in sampled_points
        if sample.get("terrain_z_m") is not None and sample.get("local_xy_m")
    ]
    if len(valid) < 3:
        return None

    rows = []
    for sample in valid:
        local_x, local_y = sample["local_xy_m"]
        rows.append((float(local_x), float(local_y), float(sample["terrain_z_m"])))

    filtered_outlier_count = 0
    filtered_zero_floor_count = 0
    if len(rows) >= 5:
        non_floor_rows = [row for row in rows if row[2] > 1.0]
        floor_rows = [row for row in rows if row[2] <= 1.0]
        if len(non_floor_rows) >= 3 and floor_rows:
            high_z_values = sorted(row[2] for row in non_floor_rows)
            median_high_z = high_z_values[len(high_z_values) // 2]
            if median_high_z >= 20.0:
                filtered_zero_floor_count = len(floor_rows)
                rows = non_floor_rows

    if len(rows) >= 5:
        z_values = sorted(z for _, _, z in rows)
        median_z = z_values[len(z_values) // 2]
        deviations = sorted(abs(z - median_z) for z in z_values)
        median_abs_deviation = deviations[len(deviations) // 2]
        outlier_threshold = max(25.0, 8.0 * median_abs_deviation)
        filtered_rows = [
            row for row in rows
            if abs(row[2] - median_z) <= outlier_threshold
        ]
        if len(filtered_rows) >= 3 and len(filtered_rows) < len(rows):
            filtered_outlier_count = len(rows) - len(filtered_rows)
            rows = filtered_rows

    # Least-squares fit: z = a*x + b*y + c in module-local coordinates.
    sx = sy = sz = sxx = syy = sxy = sxz = syz = 0.0
    n = float(len(rows))
    for x, y, z in rows:
        sx += x
        sy += y
        sz += z
        sxx += x * x
        syy += y * y
        sxy += x * y
        sxz += x * z
        syz += y * z

    solution = _solve_3x3(
        [
            [sxx, sxy, sx],
            [sxy, syy, sy],
            [sx, sy, n],
        ],
        [sxz, syz, sz],
    )
    if solution is None:
        return None

    a, b, c_fit = solution
    placement_z = max(
        z - (a * x + b * y)
        for x, y, z in rows
    )
    clearances = [
        a * x + b * y + placement_z - z
        for x, y, z in rows
    ]
    roll_deg = math.degrees(math.atan(b))
    pitch_deg = math.degrees(math.atan(-a))

    min_clearance = min(clearances, default=0.0)
    mean_clearance = sum(clearances) / len(clearances) if clearances else 0.0
    max_clearance = max(clearances, default=0.0)
    rms_clearance = math.sqrt(
        sum(value * value for value in clearances) / len(clearances)
    ) if clearances else 0.0

    return {
        "model": "z = a*x_local + b*y_local + c",
        "a_dz_dx": round(a, 6),
        "b_dz_dy": round(b, 6),
        "least_squares_c_z_at_origin_m": round(c_fit, 3),
        "placement_z_m": round(placement_z, 3),
        "placement_strategy": "least_squares_orientation_max_grounding_offset",
        "placement_rotation_deg": [
            round(roll_deg, 3),
            round(pitch_deg, 3),
            0.0,
        ],
        "min_clearance_m": round(min_clearance, 3),
        "mean_clearance_m": round(mean_clearance, 3),
        "max_clearance_m": round(max_clearance, 3),
        "rms_clearance_m": round(rms_clearance, 3),
        "filtered_zero_floor_count": filtered_zero_floor_count,
        "filtered_outlier_count": filtered_outlier_count,
    }


def _solve_3x3(
    matrix: list[list[float]],
    vector: list[float],
) -> list[float] | None:
    a = [row[:] + [value] for row, value in zip(matrix, vector)]
    size = 3

    for col in range(size):
        pivot = max(range(col, size), key=lambda row: abs(a[row][col]))
        if abs(a[pivot][col]) < 1e-9:
            return None
        if pivot != col:
            a[col], a[pivot] = a[pivot], a[col]

        pivot_value = a[col][col]
        for item in range(col, size + 1):
            a[col][item] /= pivot_value

        for row in range(size):
            if row == col:
                continue
            factor = a[row][col]
            for item in range(col, size + 1):
                a[row][item] -= factor * a[col][item]

    return [a[row][size] for row in range(size)]


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
    des_data: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    part_names = _system_part_names(system_json)
    waypoint_routes = _route_names_from_waypoints(waypoints_path)

    movement_routes: dict[str, list[dict[str, Any]]] = {
        "Regolith": [],
        "LOX": [],
    }
    scenario_builder = (
        des_data.get("results", {})
        .get("Scenario_Config", {})
        .get("scenario_builder", {})
    ) or system_json.get("scenario_logic", {})
    for route in scenario_builder.get("resource_routes", []):
        flow = route.get("flow")
        if flow not in movement_routes:
            continue
        route_name = route.get("route_name") or (
            f"{route.get('from')}To{route.get('to')}_{flow}"
        )
        if route_name not in waypoint_routes:
            continue
        movement_routes[flow].append({
            "route_name": route_name,
            "from_module": route.get("from"),
            "to_module": route.get("to"),
            "flow": flow,
            "rover_id": route.get("rover_id"),
            "stops": route.get("stops", []),
            "distance_km": route.get("distance_km"),
            "type": "ScenarioRoute",
        })

    # Compatibility fallback for manifests generated before instance-level
    # resource routes were added to the scenario builder.
    for connection in system_json.get("connections", []):
        route_name = connection.get("name")
        flow = connection.get("flow")
        if not route_name or route_name not in waypoint_routes:
            continue
        if flow not in {"Regolith", "LOX"}:
            continue
        if movement_routes[flow]:
            continue

        from_module, to_module = _split_route_name(route_name, part_names)
        movement_routes[flow].append({
            "route_name": route_name,
            "from_module": from_module or connection.get("from", {}).get("part"),
            "to_module": to_module or connection.get("to", {}).get("part"),
            "flow": flow,
            "rover_id": None,
            "distance_km": (connection.get("path") or {}).get("distance_km"),
            "type": connection.get("type"),
        })

    return {flow: items for flow, items in movement_routes.items() if items}


def _rover_scenario_id(des_data: dict[str, Any], rover_name: str, rover_type: str) -> str:
    match = re.search(r"(\d+)$", rover_name)
    index = int(match.group(1)) if match else 1
    config = des_data.get("results", {}).get("Scenario_Config", {})
    count_key = "regolith" if rover_type == "RegolithRover" else "lox"
    count = int(config.get("rovers", {}).get(count_key, {}).get("count", 1) or 0)
    return rover_type if count == 1 else f"{rover_type}_{index}"


def _route_for_rover(
    routes: list[dict[str, Any]],
    rover_id: str,
) -> dict[str, Any] | None:
    assigned = next((route for route in routes if route.get("rover_id") == rover_id), None)
    if assigned:
        return assigned
    unassigned = next((route for route in routes if not route.get("rover_id")), None)
    return unassigned or (routes[0] if len(routes) == 1 else None)


def _get_rover_names(des_data: dict[str, Any], prefix: str) -> list[str]:
    log_items = _sorted_log_items(des_data)
    if log_items:
        first_snapshot = log_items[0][1]
        names = [name for name in first_snapshot if name.startswith(prefix)]
        if names:
            return sorted(names)

    results_key = "Regolith_Cargo_Rovers" if prefix == "Regolith Cargo Rover" else "LOX_Cargo_Rovers"
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

    if prefix == "LOX Cargo Rover":
        legacy_results = des_data.get("results", {}).get("LOX_Cargo_Rover", {})
        if isinstance(legacy_results, dict) and legacy_results.get("Name"):
            return [legacy_results["Name"]]

    return []


def _final_rover_distance(des_data: dict[str, Any], rover_name: str) -> float:
    results = des_data.get("results", {})

    regolith = results.get("Regolith_Cargo_Rovers", {})
    if rover_name in regolith:
        return float(regolith[rover_name].get("Total_Distance_km", 0.0))

    lox = results.get("LOX_Cargo_Rover", {})
    if lox.get("Name") == rover_name:
        return float(lox.get("Total_Distance_km", 0.0))

    lox_fleet = results.get("LOX_Cargo_Rovers", {})
    if rover_name in lox_fleet:
        return float(lox_fleet[rover_name].get("Total_Distance_km", 0.0))

    distance = 0.0
    for _, snapshot in _sorted_log_items(des_data):
        rover = snapshot.get(rover_name, {})
        distance = max(distance, float(rover.get("total_distance_traveled", 0.0)))
    return distance


def _build_regolith_movements(
    des_data: dict[str, Any],
    routes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    inputs = des_data.get("inputs", {})
    scenario_config = des_data.get("results", {}).get("Scenario_Config", {})
    routes_config = scenario_config.get("routes", {})
    rover_config = scenario_config.get("rovers", {})
    flat_speed_kph = float(rover_config.get("flat_speed_kph", 0.0) or 0.0)
    if flat_speed_kph <= 0:
        hours_per_km = float(rover_config.get("travel_time_hr_per_km", inputs.get("Rover_Travel_Time", 0.0)))
        flat_speed_kph = 1.0 / hours_per_km if hours_per_km > 0 else 0.0
    slope_penalty = float(rover_config.get("slope_speed_penalty_per_deg", 0.0) or 0.0)
    sim_end = _simulation_end_time(des_data)

    if sim_end <= 0:
        return []

    movements = []
    rover_names = _get_rover_names(des_data, "Regolith Cargo Rover")

    for rover_name in rover_names:
        rover_id = _rover_scenario_id(des_data, rover_name, "RegolithRover")
        route = _route_for_rover(routes, rover_id)
        if not route:
            continue
        distance = float(
            route.get("distance_km")
            or routes_config.get("regolith_distance_km", inputs.get("Regolith_Haul_Distance", 0.0))
        )
        mean_slope_deg = max(0.0, float(route.get("mean_slope_deg", 0.0) or 0.0))
        effective_speed = flat_speed_kph / (1.0 + slope_penalty * mean_slope_deg)
        duration = distance / effective_speed if effective_speed > 0 else 0.0
        total_distance = _final_rover_distance(des_data, rover_name)
        if total_distance <= 0 or distance <= 0 or duration <= 0:
            continue

        leg_count = max(1, int(math.ceil(total_distance / distance - 1e-9)))
        for leg_idx in range(leg_count):
            start_time = leg_idx * duration
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
                "reverse": bool(leg_idx % 2),
                "source": "des:flat_speed_kph adjusted by route mean_slope_deg",
            })

    return movements


def _build_lox_movements(
    des_data: dict[str, Any],
    routes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    log_items = _sorted_log_items(des_data)
    if not log_items:
        return []

    inputs = des_data.get("inputs", {})
    scenario_config = des_data.get("results", {}).get("Scenario_Config", {})
    routes_config = scenario_config.get("routes", {})
    rover_config = scenario_config.get("rovers", {})
    flat_speed_kph = float(rover_config.get("flat_speed_kph", 0.0) or 0.0)
    if flat_speed_kph <= 0:
        hours_per_km = float(rover_config.get("travel_time_hr_per_km", 0.0))
        flat_speed_kph = 1.0 / hours_per_km if hours_per_km > 0 else 0.0
    slope_penalty = float(rover_config.get("slope_speed_penalty_per_deg", 0.0) or 0.0)
    sim_end = _simulation_end_time(des_data)
    movements = []
    for rover_name in _get_rover_names(des_data, "LOX Cargo Rover"):
        rover_id = _rover_scenario_id(des_data, rover_name, "LOXRover")
        route = _route_for_rover(routes, rover_id)
        if not route:
            continue
        distance = float(
            route.get("distance_km")
            or routes_config.get("lox_distance_km", inputs.get("LOX_Haul_Distance", 0.0))
        )
        mean_slope_deg = max(0.0, float(route.get("mean_slope_deg", 0.0) or 0.0))
        effective_speed = flat_speed_kph / (1.0 + slope_penalty * mean_slope_deg)
        return_duration = distance / effective_speed if effective_speed > 0 else 0.0
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
                    "reverse": False,
                    "source": "des:LOX rover load episode",
                })
                return_end = min(t + return_duration, sim_end)
                if return_duration > 0 and return_end > t:
                    movements.append({
                        "actor_id": rover_name,
                        "route_name": route["route_name"],
                        "from_module": route.get("to_module"),
                        "to_module": route.get("from_module"),
                        "start_time": round(t, 3),
                        "end_time": round(return_end, 3),
                        "reverse": True,
                        "source": "des:LOX rover empty return",
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
                "reverse": False,
                "source": "des:LOX rover load episode",
            })

    return movements


def _actor_prim_path(actor_id: str) -> str:
    if actor_id.startswith("Regolith Cargo Rover"):
        match = re.search(r"(\d+)$", actor_id)
        index = int(match.group(1)) if match else 1
        return "/World/RegolithRover" if index == 1 else f"/World/RegolithRover_{index}"
    if actor_id.startswith("LOX Cargo Rover"):
        match = re.search(r"(\d+)$", actor_id)
        index = int(match.group(1)) if match else 1
        return "/World/LOXRover" if index == 1 else f"/World/LOXRover_{index}"
    return f"/World/{actor_id.replace(' ', '_')}"


def _actor_source_prim_path(actor_id: str) -> str:
    if actor_id.startswith("Regolith Cargo Rover"):
        return "/World/RegolithRover"
    if actor_id.startswith("LOX Cargo Rover"):
        return "/World/LOXRover"
    return _actor_prim_path(actor_id)


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
    scenario_slug: str | None = None,
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
    routes = _movement_connections(system_json, waypoints_usd_path, des_data)

    all_movements: list[dict[str, Any]] = []
    warnings: list[str] = []
    if routes.get("Regolith"):
        regolith_movements = _build_regolith_movements(des_data, routes["Regolith"])
        all_movements.extend(regolith_movements)
        if not regolith_movements:
            warnings.append("No regolith rover movements were generated from the DES output.")
    if routes.get("LOX"):
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
            "source_prim_path": _actor_source_prim_path(actor_id),
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
    print("[OMNI] Building terrain config...", flush=True)
    terrain_config = _build_terrain_config(
        terrain_usd_path=terrain_usd_path,
        output_dir=output_dir,
        system_json=system_json,
    )
    print("[OMNI] Building terrain sampler...", flush=True)
    terrain_sampler = _build_terrain_sampler(
        terrain_usd_path=terrain_usd_path,
        terrain_config=terrain_config,
    )
    sampler_info = (
        f"{len(terrain_sampler.triangles)} triangles, {len(terrain_sampler.grid)} grid cells"
        if terrain_sampler
        else "unavailable"
    )
    print(f"[OMNI] Terrain sampler: {sampler_info}", flush=True)
    print("[OMNI] Loading scene CAD footprints...", flush=True)
    scene_cad_footprints = _load_scene_cad_footprints(scene_usd_path)
    print("[OMNI] Building route terrain diagnostics...", flush=True)
    terrain_routes = _build_terrain_route_diagnostics(
        system_json=system_json,
        sampler=terrain_sampler,
        scene_cad_footprints=scene_cad_footprints,
    )
    print("[OMNI] Building module terrain diagnostics...", flush=True)
    terrain_modules = _build_module_terrain_diagnostics(
        system_json=system_json,
        sampler=terrain_sampler,
        scene_cad_footprints=scene_cad_footprints,
    )
    manifest = {
        "scenario": {
            "slug": scenario_slug or system_json_path.stem,
            "name": scenario_slug or system_json_path.stem,
        },
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
        "terrain": terrain_config,
        "terrain_projection": {
            "routes": terrain_routes,
            "modules": terrain_modules,
        },
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
    parser.add_argument("--scenario-slug")
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
        scenario_slug=args.scenario_slug,
    )
    write_manifest(manifest, args.output)
    print(f"Wrote Omniverse manifest: {args.output}")
    print(f"Actors: {len(manifest.get('actors', []))}")
    for actor in manifest.get("actors", []):
        print(f"- {actor['id']}: {len(actor.get('movements', []))} movement(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
