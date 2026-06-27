from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import trimesh

from S24.cad.step_to_usd import write_usd_mesh


_MESH_UNIT_SCALES_TO_M = {
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


def _unit_scale_to_m(unit: str) -> float:
    normalized = str(unit or "m").strip().lower()
    if normalized not in _MESH_UNIT_SCALES_TO_M:
        raise ValueError(
            f"Unsupported mesh source unit '{unit}'. "
            f"Use one of: {', '.join(sorted(_MESH_UNIT_SCALES_TO_M))}"
        )
    return _MESH_UNIT_SCALES_TO_M[normalized]


def _load_meshes(path: Path) -> list[trimesh.Trimesh]:
    loaded = trimesh.load(path, force="scene", process=False)

    if isinstance(loaded, trimesh.Trimesh):
        meshes = [loaded]
    elif isinstance(loaded, trimesh.Scene):
        dumped = loaded.dump(concatenate=False)
        meshes = [mesh for mesh in dumped if isinstance(mesh, trimesh.Trimesh)]
    else:
        raise RuntimeError(f"Unsupported mesh object loaded from {path}: {type(loaded)}")

    clean_meshes: list[trimesh.Trimesh] = []
    for mesh in meshes:
        if mesh.vertices is None or mesh.faces is None:
            continue
        if len(mesh.vertices) == 0 or len(mesh.faces) == 0:
            continue
        clean_meshes.append(mesh)

    if not clean_meshes:
        raise RuntimeError(f"Mesh conversion produced no geometry: {path}")

    return clean_meshes


def _meshes_to_usd_arrays(
    meshes: list[trimesh.Trimesh],
) -> tuple[list[tuple[float, float, float]], list[int], list[int]]:
    points: list[tuple[float, float, float]] = []
    face_vertex_counts: list[int] = []
    face_vertex_indices: list[int] = []

    for mesh in meshes:
        vertices = np.asarray(mesh.vertices, dtype=float)
        faces = np.asarray(mesh.faces, dtype=int)
        base_index = len(points)

        points.extend(
            (float(vertex[0]), float(vertex[1]), float(vertex[2]))
            for vertex in vertices
        )

        for face in faces:
            if len(face) < 3:
                continue
            # Trimesh normally stores triangles, but keep fan triangulation for
            # safety if a loader ever gives us polygons.
            for item in range(1, len(face) - 1):
                face_vertex_counts.append(3)
                face_vertex_indices.extend([
                    base_index + int(face[0]),
                    base_index + int(face[item]),
                    base_index + int(face[item + 1]),
                ])

    if not points or not face_vertex_indices:
        raise RuntimeError("Mesh conversion produced empty USD arrays")

    return points, face_vertex_counts, face_vertex_indices


def convert_mesh_to_usd(
    input_path: str | Path,
    output_path: str | Path,
    *,
    source_unit: str = "m",
    source_up_axis: str = "Z",
) -> dict[str, Any]:
    input_path = Path(input_path)
    output_path = Path(output_path)
    source_format = input_path.suffix.lower().lstrip(".").upper()
    unit_scale = _unit_scale_to_m(source_unit)

    meshes = _load_meshes(input_path)
    points, counts, indices = _meshes_to_usd_arrays(meshes)

    usd_path = write_usd_mesh(
        output_path=output_path,
        points=points,
        face_vertex_counts=counts,
        face_vertex_indices=indices,
        source_path=input_path,
        unit_scale_to_m=unit_scale,
        source_up_axis=source_up_axis,
        source_format=source_format,
    )

    bounds = trimesh.Scene(meshes).bounds
    source_bbox = None
    if bounds is not None:
        source_bbox = {
            "min": [round(float(value), 4) for value in bounds[0]],
            "max": [round(float(value), 4) for value in bounds[1]],
            "size": [
                round(float(bounds[1][i] - bounds[0][i]), 4)
                for i in range(3)
            ],
        }

    return {
        "written_at": int(time.time() * 1000),
        "source_file": str(input_path),
        "file_name": input_path.name,
        "file_extension": input_path.suffix.lower(),
        "cad_format": source_format,
        "file_size_bytes": input_path.stat().st_size,
        "converted_usd_path": usd_path,
        "source_up_axis": str(source_up_axis).upper(),
        "target_up_axis": "Z",
        "orientation_correction_deg": (
            [90.0, 0.0, 0.0]
            if str(source_up_axis).upper() == "Y"
            else ([0.0, -90.0, 0.0] if str(source_up_axis).upper() == "X" else [0.0, 0.0, 0.0])
        ),
        "units": {
            "unit": str(source_unit).strip().lower() or "m",
            "scale_to_m": unit_scale,
            "source": "user/default mesh unit assumption",
        },
        "mesh": {
            "mesh_count": len(meshes),
            "point_count": len(points),
            "triangle_count": len(indices) // 3,
            "source_bbox": source_bbox,
        },
        "extraction_status": {
            "conversion": "success",
            "metadata": "success",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert STL/OBJ mesh CAD to USD mesh.")
    parser.add_argument("input", help="Input .stl/.obj file")
    parser.add_argument("--output", required=True, help="Output .usd/.usda/.usdc path")
    parser.add_argument("--metadata", help="Optional source metadata JSON output path")
    parser.add_argument("--source-unit", default="m", help="Source mesh length unit")
    parser.add_argument(
        "--source-up-axis",
        default="Z",
        choices=("X", "Y", "Z", "x", "y", "z"),
        help="Source CAD up axis to convert into USD Z-up",
    )
    args = parser.parse_args(argv)

    metadata = convert_mesh_to_usd(
        args.input,
        args.output,
        source_unit=args.source_unit,
        source_up_axis=args.source_up_axis,
    )

    if args.metadata:
        metadata_path = Path(args.metadata)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
