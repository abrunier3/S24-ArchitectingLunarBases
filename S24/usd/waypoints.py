import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from pxr import Usd, UsdGeom, Sdf, Gf


def read_system_json(json_path: str | Path) -> Dict[str, Any]:
    json_path = Path(json_path)

    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def flow_color(flow: str) -> Gf.Vec3f:
    flow = str(flow).strip().lower()

    if flow == "lox":
        return Gf.Vec3f(0.0, 0.25, 1.0)

    if flow == "power":
        return Gf.Vec3f(1.0, 0.0, 0.0)

    if flow == "regolith":
        return Gf.Vec3f(0.45, 0.25, 0.05)

    return Gf.Vec3f(0.5, 0.5, 0.5)


def sanitize_usd_name(name: str) -> str:
    return (
        str(name)
        .replace(" ", "_")
        .replace("-", "_")
        .replace(".", "_")
        .replace(":", "_")
        .replace("/", "_")
    )


def get_part_lookup(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        part["name"]: part
        for part in data.get("parts", [])
    }


def get_part_position(
    part_lookup: Dict[str, Dict[str, Any]],
    part_name: str,
) -> List[float]:
    part = part_lookup.get(part_name, {})
    transform = part.get("transform", {})
    return transform.get("position_m", [0.0, 0.0, 0.0])


def get_connection_waypoints(
    connection: Dict[str, Any],
    part_lookup: Dict[str, Dict[str, Any]],
) -> List[List[float]]:

    path_data = connection.get("path", {})
    waypoints = path_data.get("waypoints_m")

    if waypoints:
        return waypoints

    src_part = connection["from"]["part"]
    dst_part = connection["to"]["part"]

    return [
        get_part_position(part_lookup, src_part),
        get_part_position(part_lookup, dst_part),
    ]


def create_connection_curve(
    stage: Usd.Stage,
    connection: Dict[str, Any],
    part_lookup: Dict[str, Dict[str, Any]],
    *,
    root_path: str = "/World/Connections",
    curve_width: float = 3.0,
) -> None:

    name = sanitize_usd_name(connection.get("name", "UnnamedConnection"))
    prim_path = f"{root_path}/{name}"

    curve = UsdGeom.BasisCurves.Define(stage, prim_path)
    prim = curve.GetPrim()

    waypoints = get_connection_waypoints(connection, part_lookup)
    points = [Gf.Vec3f(float(x), float(y), float(z)) for x, y, z in waypoints]

    curve.CreateTypeAttr("linear")
    curve.CreateBasisAttr("bezier")
    curve.CreateCurveVertexCountsAttr([len(points)])
    curve.CreatePointsAttr(points)
    curve.CreateWidthsAttr([curve_width])

    flow = connection.get("flow", "Unknown")
    color = flow_color(flow)

    curve.CreateDisplayColorAttr([color])

    prim.CreateAttribute("connection:name", Sdf.ValueTypeNames.String).Set(
        connection.get("name", "")
    )
    prim.CreateAttribute("connection:type", Sdf.ValueTypeNames.String).Set(
        connection.get("type", "")
    )
    prim.CreateAttribute("connection:flow", Sdf.ValueTypeNames.String).Set(
        str(flow)
    )
    prim.CreateAttribute("connection:sourcePart", Sdf.ValueTypeNames.String).Set(
        connection["from"]["part"]
    )
    prim.CreateAttribute("connection:sourcePort", Sdf.ValueTypeNames.String).Set(
        connection["from"]["port"]
    )
    prim.CreateAttribute("connection:targetPart", Sdf.ValueTypeNames.String).Set(
        connection["to"]["part"]
    )
    prim.CreateAttribute("connection:targetPort", Sdf.ValueTypeNames.String).Set(
        connection["to"]["port"]
    )

    distance_km = connection.get("path", {}).get("distance_km")
    if distance_km is not None:
        prim.CreateAttribute("connection:distanceKm", Sdf.ValueTypeNames.Double).Set(
            float(distance_km)
        )

    prim.CreateAttribute("connection:numWaypoints", Sdf.ValueTypeNames.Int).Set(
        len(points)
    )


def create_waypoint_markers(
    stage: Usd.Stage,
    connection: Dict[str, Any],
    part_lookup: Dict[str, Dict[str, Any]],
    *,
    root_path: str = "/World/ConnectionWaypoints",
    marker_radius: float = 8.0,
) -> None:

    connection_name = sanitize_usd_name(connection.get("name", "UnnamedConnection"))
    connection_root = UsdGeom.Xform.Define(stage, f"{root_path}/{connection_name}")

    waypoints = get_connection_waypoints(connection, part_lookup)
    color = flow_color(connection.get("flow", "Unknown"))

    for i, wp in enumerate(waypoints):
        marker_path = f"{root_path}/{connection_name}/Waypoint_{i:03d}"
        sphere = UsdGeom.Sphere.Define(stage, marker_path)

        sphere.CreateRadiusAttr(marker_radius)
        sphere.CreateDisplayColorAttr([color])

        xformable = UsdGeom.Xformable(sphere.GetPrim())
        xformable.AddTranslateOp().Set(
            Gf.Vec3d(float(wp[0]), float(wp[1]), float(wp[2]))
        )

        sphere.GetPrim().CreateAttribute(
            "waypoint:index",
            Sdf.ValueTypeNames.Int
        ).Set(i)


def write_connections_usda(
    json_path: str | Path,
    output_usda_path: str | Path,
    *,
    stage_root: str = "World",
    curve_width: float = 3.0,
    write_waypoints: bool = True,
    marker_radius: float = 8.0,
    verbose: int = 1,
) -> str:

    json_path = Path(json_path)
    output_usda_path = Path(output_usda_path)

    if output_usda_path.suffix not in [".usd", ".usda"]:
        raise ValueError("output_usda_path must end with .usd or .usda")

    output_usda_path.parent.mkdir(parents=True, exist_ok=True)

    data = read_system_json(json_path)
    part_lookup = get_part_lookup(data)
    connections = data.get("connections", [])

    stage = Usd.Stage.CreateNew(str(output_usda_path))

    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)

    UsdGeom.Xform.Define(stage, f"/{stage_root}")
    UsdGeom.Xform.Define(stage, f"/{stage_root}/Connections")

    if write_waypoints:
        UsdGeom.Xform.Define(stage, f"/{stage_root}/ConnectionWaypoints")

    for connection in connections:
        create_connection_curve(
            stage,
            connection,
            part_lookup,
            root_path=f"/{stage_root}/Connections",
            curve_width=curve_width,
        )

        if write_waypoints:
            create_waypoint_markers(
                stage,
                connection,
                part_lookup,
                root_path=f"/{stage_root}/ConnectionWaypoints",
                marker_radius=marker_radius,
            )

    stage.GetRootLayer().Save()

    if verbose >= 1:
        print(f"[USD] Wrote connection USD file: {output_usda_path}")
        print(f"[USD] Connections written: {len(connections)}")

    if verbose >= 2:
        for connection in connections:
            src = f"{connection['from']['part']}.{connection['from']['port']}"
            dst = f"{connection['to']['part']}.{connection['to']['port']}"
            flow = connection.get("flow", "Unknown")
            path = connection.get("path", {})
            n_wp = len(path.get("waypoints_m", [])) if path else 0
            dist = path.get("distance_km", None)

            print(f"\n[CONNECTION] {connection.get('name')}")
            print(f"  Flow      : {flow}")
            print(f"  Type      : {connection.get('type')}")
            print(f"  From      : {src}")
            print(f"  To        : {dst}")
            print(f"  Waypoints : {n_wp if n_wp else 'generated from part positions'}")
            print(f"  Distance  : {dist if dist is not None else 'N/A'} km")

    return str(output_usda_path)