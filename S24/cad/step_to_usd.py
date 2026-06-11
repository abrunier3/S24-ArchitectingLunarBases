from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any


_STEP_LENGTH_SCALES_TO_M = {
    "METRE": 1.0,
    "METER": 1.0,
    "CENTIMETRE": 0.01,
    "CENTIMETER": 0.01,
    "MILLIMETRE": 0.001,
    "MILLIMETER": 0.001,
    "INCH": 0.0254,
    "FOOT": 0.3048,
}

_SI_PREFIX_SCALES = {
    "EXA": 1e18,
    "PETA": 1e15,
    "TERA": 1e12,
    "GIGA": 1e9,
    "MEGA": 1e6,
    "KILO": 1e3,
    "HECTO": 1e2,
    "DECA": 1e1,
    "DECI": 1e-1,
    "CENTI": 1e-2,
    "MILLI": 1e-3,
    "MICRO": 1e-6,
    "NANO": 1e-9,
    "PICO": 1e-12,
    "FEMTO": 1e-15,
    "ATTO": 1e-18,
}


def _read_text(path: Path, max_chars: int = 500_000) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]


def _quoted_items(value: str) -> list[str]:
    return re.findall(r"'([^']*)'", value or "")


def extract_step_header(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    text = _read_text(path)
    header_match = re.search(r"HEADER;(.*?)ENDSEC;", text, re.DOTALL | re.IGNORECASE)
    header = header_match.group(1).strip() if header_match else ""

    file_description = re.search(
        r"FILE_DESCRIPTION\s*\(\s*\(\s*'([^']*)'",
        header,
        re.IGNORECASE,
    )
    file_name = re.search(r"FILE_NAME\s*\((.*?)\);", header, re.DOTALL | re.IGNORECASE)
    schema = re.search(
        r"FILE_SCHEMA\s*\(\s*\(\s*'([^']*)'",
        header,
        re.IGNORECASE,
    )

    file_name_items = _quoted_items(file_name.group(1) if file_name else "")

    return {
        "description": file_description.group(1) if file_description else None,
        "file_name": file_name_items[0] if len(file_name_items) >= 1 else None,
        "timestamp": file_name_items[1] if len(file_name_items) >= 2 else None,
        "preprocessor": file_name_items[4] if len(file_name_items) >= 5 else None,
        "authoring_tool": file_name_items[5] if len(file_name_items) >= 6 else None,
        "schema": schema.group(1) if schema else None,
        "raw_header": header or None,
    }


def detect_step_length_scale(path: str | Path, default_unit: str = "mm") -> dict[str, Any]:
    text = _read_text(Path(path)).upper()

    si_units = re.finditer(
        r"SI_UNIT\s*\(\s*(?:\.([A-Z]+)\.|\$)\s*,\s*\.([A-Z]+)\.\s*\)",
        text,
    )
    for si_unit in si_units:
        prefix, base = si_unit.groups()
        if base in {"METRE", "METER"}:
            prefix_scale = _SI_PREFIX_SCALES.get(prefix or "", 1.0)
            return {
                "unit": f"{prefix.lower()}metre" if prefix else "metre",
                "scale_to_m": prefix_scale,
                "source": "STEP SI_UNIT",
            }

    for token, scale in sorted(
        _STEP_LENGTH_SCALES_TO_M.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        if re.search(rf"\b{re.escape(token)}\b", text):
            return {
                "unit": token.lower(),
                "scale_to_m": scale,
                "source": "STEP text token",
            }

    normalized = default_unit.strip().lower()
    default_scales = {
        "m": 1.0,
        "meter": 1.0,
        "metre": 1.0,
        "cm": 0.01,
        "centimeter": 0.01,
        "centimetre": 0.01,
        "mm": 0.001,
        "millimeter": 0.001,
        "millimetre": 0.001,
        "in": 0.0254,
        "inch": 0.0254,
        "ft": 0.3048,
        "foot": 0.3048,
    }
    return {
        "unit": normalized,
        "scale_to_m": default_scales.get(normalized, 0.001),
        "source": "default",
    }


def _triangle_indices(triangle: Any) -> tuple[int, int, int]:
    try:
        return tuple(int(v) for v in triangle.Get())
    except TypeError:
        pass

    values: list[int] = []
    for attr in ("Value",):
        if hasattr(triangle, attr):
            try:
                return (
                    int(triangle.Value(1)),
                    int(triangle.Value(2)),
                    int(triangle.Value(3)),
                )
            except Exception:
                pass

    try:
        n1, n2, n3 = 0, 0, 0
        result = triangle.Get(n1, n2, n3)
        if result:
            return tuple(int(v) for v in result)
    except Exception:
        pass

    raise RuntimeError("Unable to read OpenCascade triangle indices")


def _load_step_shape(path: Path):
    try:
        from OCC.Core.IFSelect import IFSelect_RetDone
        from OCC.Core.STEPControl import STEPControl_Reader
    except ImportError as exc:
        raise ImportError(
            "STEP conversion requires pythonocc-core. Install it with conda-forge."
        ) from exc

    reader = STEPControl_Reader()
    status = reader.ReadFile(str(path))
    if status != IFSelect_RetDone:
        raise RuntimeError(f"Could not read STEP file: {path}")

    reader.TransferRoots()
    return reader.OneShape()


def _mesh_step_shape(shape: Any, *, linear_deflection: float, angular_deflection: float):
    from OCC.Core.BRep import BRep_Tool
    from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
    from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_REVERSED
    from OCC.Core.TopExp import TopExp_Explorer
    from OCC.Core.TopLoc import TopLoc_Location
    from OCC.Core.TopoDS import topods

    BRepMesh_IncrementalMesh(shape, linear_deflection, False, angular_deflection, True)

    points: list[tuple[float, float, float]] = []
    face_vertex_counts: list[int] = []
    face_vertex_indices: list[int] = []

    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    while explorer.More():
        face = topods.Face(explorer.Current())
        loc = TopLoc_Location()
        triangulation = BRep_Tool.Triangulation(face, loc)
        if triangulation:
            trsf = loc.Transformation()
            base_index = len(points)

            for i in range(1, triangulation.NbNodes() + 1):
                p = triangulation.Node(i).Transformed(trsf)
                points.append((float(p.X()), float(p.Y()), float(p.Z())))

            for i in range(1, triangulation.NbTriangles() + 1):
                n1, n2, n3 = _triangle_indices(triangulation.Triangle(i))
                if face.Orientation() == TopAbs_REVERSED:
                    n2, n3 = n3, n2
                face_vertex_counts.append(3)
                face_vertex_indices.extend([
                    base_index + n1 - 1,
                    base_index + n2 - 1,
                    base_index + n3 - 1,
                ])

        explorer.Next()

    if not points or not face_vertex_indices:
        raise RuntimeError("STEP tessellation produced no mesh geometry")

    return points, face_vertex_counts, face_vertex_indices


def write_usd_mesh(
    *,
    output_path: str | Path,
    points: list[tuple[float, float, float]],
    face_vertex_counts: list[int],
    face_vertex_indices: list[int],
    source_path: str | Path,
    unit_scale_to_m: float,
) -> str:
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    scaled_points = [
        Gf.Vec3f(
            float(x) * unit_scale_to_m,
            float(y) * unit_scale_to_m,
            float(z) * unit_scale_to_m,
        )
        for x, y, z in points
    ]

    stage = Usd.Stage.CreateNew(str(output_path))
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

    root = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(root.GetPrim())

    mesh = UsdGeom.Mesh.Define(stage, "/World/Geometry")
    mesh.CreatePointsAttr(scaled_points)
    mesh.CreateFaceVertexCountsAttr(face_vertex_counts)
    mesh.CreateFaceVertexIndicesAttr(face_vertex_indices)
    mesh.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
    mesh.CreateOrientationAttr(UsdGeom.Tokens.rightHanded)
    mesh.CreateDoubleSidedAttr(True)
    mesh.CreateDisplayColorAttr([Gf.Vec3f(0.78, 0.78, 0.74)])
    mesh.CreateDisplayOpacityAttr([1.0])

    mesh.GetPrim().SetCustomDataByKey("s24:source_format", "STEP")
    mesh.GetPrim().SetCustomDataByKey("s24:source_file", Path(source_path).name)
    mesh.GetPrim().SetCustomDataByKey("s24:unit_scale_to_m", float(unit_scale_to_m))

    min_point = Gf.Vec3f(
        min(point[0] for point in scaled_points),
        min(point[1] for point in scaled_points),
        min(point[2] for point in scaled_points),
    )
    max_point = Gf.Vec3f(
        max(point[0] for point in scaled_points),
        max(point[1] for point in scaled_points),
        max(point[2] for point in scaled_points),
    )
    mesh.CreateExtentAttr([min_point, max_point])

    UsdGeom.Scope.Define(stage, "/World/Materials")
    material = UsdShade.Material.Define(stage, "/World/Materials/DefaultCadMaterial")
    shader = UsdShade.Shader.Define(stage, "/World/Materials/DefaultCadMaterial/PreviewSurface")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
        Gf.Vec3f(0.78, 0.78, 0.74)
    )
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.45)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    material.CreateSurfaceOutput().ConnectToSource(
        shader.ConnectableAPI(),
        "surface",
    )
    UsdShade.MaterialBindingAPI(mesh.GetPrim()).Bind(material)

    stage.GetRootLayer().Save()
    return str(output_path)


def convert_step_to_usd(
    input_path: str | Path,
    output_path: str | Path,
    *,
    default_unit: str = "mm",
    linear_deflection: float = 0.1,
    angular_deflection: float = 0.5,
) -> dict[str, Any]:
    input_path = Path(input_path)
    output_path = Path(output_path)

    header = extract_step_header(input_path)
    units = detect_step_length_scale(input_path, default_unit=default_unit)
    shape = _load_step_shape(input_path)
    points, counts, indices = _mesh_step_shape(
        shape,
        linear_deflection=linear_deflection,
        angular_deflection=angular_deflection,
    )
    usd_path = write_usd_mesh(
        output_path=output_path,
        points=points,
        face_vertex_counts=counts,
        face_vertex_indices=indices,
        source_path=input_path,
        # OpenCascade's transferred BRep coordinates are expressed in its
        # working length unit (millimeters). Normalize the generated USD to
        # meters, and keep the STEP-declared unit separately as source metadata.
        unit_scale_to_m=0.001,
    )

    return {
        "written_at": int(time.time() * 1000),
        "source_file": str(input_path),
        "file_name": input_path.name,
        "file_extension": input_path.suffix.lower(),
        "cad_format": "STEP",
        "file_size_bytes": input_path.stat().st_size,
        "converted_usd_path": usd_path,
        "title": header.get("file_name"),
        "authoring_tool": header.get("authoring_tool"),
        "preprocessor": header.get("preprocessor"),
        "schema": header.get("schema"),
        "timestamp": header.get("timestamp"),
        "units": units,
        "occ_shape_unit": {
            "unit": "millimetre",
            "scale_to_m": 0.001,
            "source": "OpenCascade transferred shape coordinates",
        },
        "tessellation": {
            "linear_deflection": linear_deflection,
            "angular_deflection": angular_deflection,
            "point_count": len(points),
            "triangle_count": len(indices) // 3,
        },
        "raw_header": header,
        "extraction_status": {
            "conversion": "success",
            "metadata": "success",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert STEP/STP CAD to USD mesh.")
    parser.add_argument("input", help="Input .step/.stp file")
    parser.add_argument("--output", required=True, help="Output .usd/.usda/.usdc path")
    parser.add_argument("--metadata", help="Optional source metadata JSON output path")
    parser.add_argument("--default-unit", default="mm", help="Fallback STEP length unit")
    parser.add_argument("--linear-deflection", type=float, default=0.1)
    parser.add_argument("--angular-deflection", type=float, default=0.5)
    args = parser.parse_args(argv)

    metadata = convert_step_to_usd(
        args.input,
        args.output,
        default_unit=args.default_unit,
        linear_deflection=args.linear_deflection,
        angular_deflection=args.angular_deflection,
    )

    if args.metadata:
        metadata_path = Path(args.metadata)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
