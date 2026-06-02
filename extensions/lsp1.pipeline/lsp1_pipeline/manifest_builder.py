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
    ) -> None:
        self.triangles = triangles

    def sample_height(self, x: float, y: float) -> float | None:
        for triangle in self.triangles:
            height = _point_in_triangle_height(x, y, triangle)
            if height is not None:
                return height
        return None


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
    for connection in system_json.get("connections", []):
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

        slopes, slope_segments, _, _ = _slope_stats_from_sampled(sampled)
        valid_samples = [point for point in sampled if point is not None]
        max_slope = max(slopes) if slopes else None
        mean_slope = sum(slopes) / len(slopes) if slopes else None
        max_slope_segment = max(
            slope_segments,
            key=lambda segment: segment["slope_deg"],
            default=None,
        )

        routes[route_name] = {
            "flow": connection.get("flow"),
            "status": _slope_status(max_slope, out_of_bounds),
            "input_waypoint_count": len(waypoints),
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
            "sampled_waypoints_m": [
                _round_point(point)
                for point in valid_samples
            ],
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
) -> dict[str, Any]:
    if sampler is None:
        return {
            "status": "unavailable",
            "reason": "Terrain sampler unavailable. OpenUSD may be missing or the terrain mesh could not be read.",
            "modules": {},
        }

    modules: dict[str, Any] = {}
    out_of_bounds = 0
    for part in system_json.get("parts", []):
        name = part.get("name")
        position = part.get("transform", {}).get("position_m")
        if not name or not isinstance(position, list) or len(position) < 2:
            continue

        x = float(position[0])
        y = float(position[1])
        authored_z = float(position[2]) if len(position) > 2 else 0.0
        footprint_samples = _module_footprint_sample_points(part, x, y)
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
                "position_xy_m": [round(x, 3), round(y, 3)],
                "authored_z_m": round(authored_z, 3),
                "placement_z_m": None,
                "sample_strategy": "center_corners_edge_midpoints_grid_5x5_max",
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
            "position_xy_m": [round(x, 3), round(y, 3)],
            "authored_z_m": round(authored_z, 3),
            "placement_z_m": round(placement_z, 3),
            "delta_z_m": round(authored_z - placement_z, 3),
            "placement_rotation_deg": placement_rotation,
            "terrain_plane": terrain_plane,
            "sample_strategy": "center_corners_edge_midpoints_grid_5x5_max",
            "footprint_sample_count": len(sampled_points),
            "missing_sample_count": missing_samples,
            "footprint_samples": sampled_points,
        }

    return {
        "status": "terrain_alignment_warning" if out_of_bounds else "ok",
        "out_of_bounds_count": out_of_bounds,
        "modules": modules,
    }


def _module_footprint_sample_points(
    part: dict[str, Any],
    center_x: float,
    center_y: float,
) -> list[tuple[float, float, str, float, float]]:
    size_m = (part.get("dimensions") or {}).get("size_m") or {}
    length = float(size_m.get("length") or 0.0)
    width = float(size_m.get("width") or 0.0)
    if length <= 0 or width <= 0:
        return [(center_x, center_y, "center", 0.0, 0.0)]

    rotation = part.get("transform", {}).get("rotation_deg") or [0.0, 0.0, 0.0]
    yaw_deg = float(rotation[2]) if len(rotation) >= 3 else 0.0
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
    grid_count = 5
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

    a, b, c = solution
    roll_deg = math.degrees(math.atan(b))
    pitch_deg = math.degrees(math.atan(-a))

    residuals = []
    max_grounding_z = None
    for x, y, z in rows:
        tilted_bottom_z = a * x + b * y
        required_origin_z = z - tilted_bottom_z
        if max_grounding_z is None or required_origin_z > max_grounding_z:
            max_grounding_z = required_origin_z
        residuals.append(z - (a * x + b * y + c))

    max_abs_residual = max((abs(value) for value in residuals), default=0.0)
    rms_residual = math.sqrt(
        sum(value * value for value in residuals) / len(residuals)
    ) if residuals else 0.0

    return {
        "model": "z = a*x_local + b*y_local + c",
        "a_dz_dx": round(a, 6),
        "b_dz_dy": round(b, 6),
        "c_z_at_origin_m": round(c, 3),
        "placement_z_m": round(max_grounding_z if max_grounding_z is not None else c, 3),
        "placement_rotation_deg": [
            round(roll_deg, 3),
            round(pitch_deg, 3),
            0.0,
        ],
        "max_abs_residual_m": round(max_abs_residual, 3),
        "rms_residual_m": round(rms_residual, 3),
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
    terrain_config = _build_terrain_config(
        terrain_usd_path=terrain_usd_path,
        output_dir=output_dir,
        system_json=system_json,
    )
    terrain_sampler = _build_terrain_sampler(
        terrain_usd_path=terrain_usd_path,
        terrain_config=terrain_config,
    )
    terrain_routes = _build_terrain_route_diagnostics(
        system_json=system_json,
        sampler=terrain_sampler,
    )
    terrain_modules = _build_module_terrain_diagnostics(
        system_json=system_json,
        sampler=terrain_sampler,
    )
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
