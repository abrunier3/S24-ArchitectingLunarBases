from __future__ import annotations

import json
import os
import time
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import trimesh
import trimesh.transformations as tf
from pxr import Usd, UsdGeom, UsdShade

from S24.cad.mesh_to_usd import convert_mesh_to_usd
from S24.cad.paths import scenario_slug_from_cad_path
from S24.cad.step_to_usd import convert_step_to_usd


def _normalise_up_axis(value: Any) -> str:
    axis = str(value or "Z").upper()
    if axis not in {"X", "Y", "Z"}:
        raise ValueError(f"Unsupported source up axis: {value}")
    return axis


def _workflow_jobs() -> list[dict[str, str]]:
    raw_batch = os.environ.get("BATCH_JOBS_JSON", "").strip()
    if raw_batch:
        jobs = json.loads(raw_batch)
        if not isinstance(jobs, list):
            raise ValueError("BATCH_JOBS_JSON must be a JSON list")
        return [
            {
                "module_name": str(job["module_name"]),
                "cad_path": str(job["cad_path"]),
                "source_up_axis": _normalise_up_axis(job.get("source_up_axis", "Z")),
            }
            for job in jobs
        ]

    module_name = os.environ.get("MODULE_NAME", "").strip()
    cad_path = os.environ.get("USD_PATH", "").strip()
    if not module_name or not cad_path:
        raise ValueError("Provide either BATCH_JOBS_JSON or MODULE_NAME/USD_PATH")

    return [
        {
            "module_name": module_name,
            "cad_path": cad_path,
            "source_up_axis": _normalise_up_axis(
                os.environ.get("SOURCE_UP_AXIS", "Z")
            ),
        }
    ]


def _to_json_val(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return round(value, 4)
    try:
        items = list(value)
        if all(isinstance(item, (int, float)) for item in items):
            return [round(float(item), 4) for item in items]
    except TypeError:
        pass
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return str(value)


def _actual_usd_path(usd_path: str) -> str:
    if not usd_path.endswith(".usdz"):
        return usd_path

    tmp_dir = "/tmp/usd_extract"
    os.makedirs(tmp_dir, exist_ok=True)
    with zipfile.ZipFile(usd_path, "r") as archive:
        archive.extractall(tmp_dir)

    for root, _, files in os.walk(tmp_dir):
        for file_name in files:
            if file_name.endswith((".usdc", ".usda", ".usd")):
                return os.path.join(root, file_name)

    return usd_path


def _extract_materials(stage: Usd.Stage) -> list[dict[str, Any]]:
    materials_found: list[dict[str, Any]] = []
    for prim in stage.Traverse():
        if not prim.IsA(UsdShade.Material):
            continue

        mat_data: dict[str, Any] = {"path": str(prim.GetPath()), "properties": {}}
        for child in prim.GetChildren():
            shader = UsdShade.Shader(child)
            if not shader:
                continue
            for shader_input in shader.GetInputs():
                value = shader_input.Get()
                if value is not None:
                    key = shader_input.GetFullName().replace("inputs:", "")
                    mat_data["properties"][key] = _to_json_val(value)
        materials_found.append(mat_data)

    return materials_found


def _extract_meshes(stage: Usd.Stage, meters_per_unit: float) -> list[trimesh.Trimesh]:
    meshes_data: list[trimesh.Trimesh] = []
    xform_cache = UsdGeom.XformCache(Usd.TimeCode.Default())

    for prim in stage.Traverse():
        if not prim.IsA(UsdGeom.Mesh):
            continue

        mesh = UsdGeom.Mesh(prim)
        points = mesh.GetPointsAttr().Get()
        indices = mesh.GetFaceVertexIndicesAttr().Get()
        counts = mesh.GetFaceVertexCountsAttr().Get()
        if not (points and indices and counts):
            continue

        world_xform = xform_cache.GetLocalToWorldTransform(prim)
        verts = np.array(
            [list(world_xform.Transform(point)) for point in points],
            dtype=np.float32,
        ) * meters_per_unit

        faces: list[list[int]] = []
        cursor = 0
        for count in counts:
            face = [indices[cursor + item] for item in range(count)]
            for item in range(1, len(face) - 1):
                faces.append([face[0], face[item], face[item + 1]])
            cursor += count

        if faces:
            meshes_data.append(
                trimesh.Trimesh(vertices=verts, faces=np.array(faces, dtype=np.int32))
            )

    return meshes_data


def _extract_usd_geometry_properties(meshes_data: list[trimesh.Trimesh]) -> dict[str, Any]:
    if not meshes_data:
        return {
            "extraction_status": "error",
            "message": "USD stage contains no readable mesh geometry",
        }

    try:
        combined = trimesh.util.concatenate(meshes_data)
    except Exception as exc:
        return {
            "extraction_status": "error",
            "message": str(exc),
        }

    if combined.vertices is None or len(combined.vertices) == 0:
        return {
            "extraction_status": "error",
            "message": "USD mesh has no vertices",
        }

    geometry: dict[str, Any] = {
        "extraction_status": "success",
        "surface_area_m2": float(combined.area),
        "center_of_mass_m": [float(value) for value in np.asarray(combined.centroid)],
        "center_of_mass_source": "centroid",
        "is_watertight": bool(combined.is_watertight),
    }

    if combined.is_watertight:
        geometry["volume_m3"] = abs(float(combined.volume))
        geometry["center_of_mass_m"] = [
            float(value) for value in np.asarray(combined.center_mass)
        ]
        geometry["center_of_mass_source"] = "mass_properties"

    return geometry


def _source_metadata_for_native_usd(
    *,
    source_cad_path: str,
    usd_path: str,
    stage: Usd.Stage,
    meshes_data: list[trimesh.Trimesh],
    meters_per_unit: float,
    up_axis: str,
) -> dict[str, Any]:
    source_path = Path(source_cad_path)
    source_format = source_path.suffix.lower().lstrip(".").upper() or "USD"
    root_layer = stage.GetRootLayer()

    return {
        "written_at": int(time.time() * 1000),
        "source_file": source_cad_path,
        "file_name": source_path.name,
        "file_extension": source_path.suffix.lower(),
        "cad_format": source_format,
        "file_size_bytes": source_path.stat().st_size if source_path.exists() else None,
        "converted_usd_path": usd_path,
        "authoring_tool": root_layer.customLayerData.get("creator")
        if root_layer and root_layer.customLayerData
        else None,
        "source_up_axis": str(up_axis).upper(),
        "source_front_axis": "+X",
        "target_up_axis": "Z",
        "orientation_correction_deg": [0.0, 0.0, 0.0],
        "units": {
            "unit": "metre",
            "scale_to_m": meters_per_unit,
            "source": "USD stage metersPerUnit",
        },
        "geometry": _extract_usd_geometry_properties(meshes_data),
        "extraction_status": {
            "conversion": "not_required",
            "metadata": "success",
        },
    }


def _write_glb(
    *,
    module_name: str,
    scenario_slug: str,
    meshes_data: list[trimesh.Trimesh],
    up_axis: str,
) -> str | None:
    if not meshes_data:
        return None

    scene = trimesh.Scene(meshes_data)
    # GLB viewers are Y-up while the generated USD is always Z-up. Convert
    # the preview into the same convention the browser uses, otherwise a
    # rover can look upright in Step 3 while lying down in Omniverse.
    if str(up_axis).upper() == "Z":
        scene.apply_transform(tf.rotation_matrix(-np.pi / 2, [1, 0, 0]))

    bounds = scene.bounds
    if bounds is not None:
        center = (bounds[0] + bounds[1]) / 2
        scene.apply_translation(-center)

    glb_path = f"outputs/cad_previews/{scenario_slug}/{module_name}.glb"
    Path(glb_path).parent.mkdir(parents=True, exist_ok=True)
    glb_bytes = scene.export(file_type="glb")
    with open(glb_path, "wb") as file:
        file.write(glb_bytes)
    print(f"[CONVERT] GLB written for {module_name}: {len(glb_bytes) // 1024} KB")
    return glb_path


def _convert_one(module_name: str, cad_path: str, *, source_up_axis: str) -> None:
    scenario_slug = scenario_slug_from_cad_path(cad_path)
    previews_dir = Path("outputs") / "cad_previews" / scenario_slug
    previews_dir.mkdir(parents=True, exist_ok=True)

    source_cad_path = cad_path
    usd_path = cad_path
    lower_path = cad_path.lower()

    if lower_path.endswith((".step", ".stp")):
        converted_usd_path = str(Path(cad_path).parent / f"{module_name}.usdc")
        source_meta_path = str(previews_dir / f"{module_name}_source_meta.json")
        print(f"[CONVERT] STEP detected. Converting {cad_path} -> {converted_usd_path}")
        source_metadata = convert_step_to_usd(
            cad_path,
            converted_usd_path,
            source_up_axis=source_up_axis,
        )
        Path(source_meta_path).write_text(
            json.dumps(source_metadata, indent=2),
            encoding="utf-8",
        )
        if "orientation_correction_deg" not in source_metadata:
            raise RuntimeError(f"{source_meta_path} is missing orientation_correction_deg")
        print(
            "[CONVERT] STEP orientation correction:",
            source_metadata["orientation_correction_deg"],
        )
        usd_path = converted_usd_path
    elif lower_path.endswith((".stl", ".obj")):
        converted_usd_path = str(Path(cad_path).parent / f"{module_name}.usdc")
        source_meta_path = str(previews_dir / f"{module_name}_source_meta.json")
        print(f"[CONVERT] Mesh CAD detected. Converting {cad_path} -> {converted_usd_path}")
        source_metadata = convert_mesh_to_usd(
            cad_path,
            converted_usd_path,
            source_unit=os.environ.get("MESH_SOURCE_UNIT", "m"),
            source_up_axis=source_up_axis,
        )
        Path(source_meta_path).write_text(
            json.dumps(source_metadata, indent=2),
            encoding="utf-8",
        )
        if "orientation_correction_deg" not in source_metadata:
            raise RuntimeError(f"{source_meta_path} is missing orientation_correction_deg")
        print(
            "[CONVERT] Mesh orientation correction:",
            source_metadata["orientation_correction_deg"],
        )
        usd_path = converted_usd_path

    actual_usd_path = _actual_usd_path(usd_path)
    print(f"[CONVERT] Opening {actual_usd_path}")
    stage = Usd.Stage.Open(actual_usd_path)
    if not stage:
        raise RuntimeError(f"Could not open USD stage: {actual_usd_path}")

    meters_per_unit = float(UsdGeom.GetStageMetersPerUnit(stage) or 1.0)
    up_axis = str(UsdGeom.GetStageUpAxis(stage))

    bbox_cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
    bbox_range = bbox_cache.ComputeWorldBound(stage.GetPseudoRoot()).ComputeAlignedRange()
    min_pt = bbox_range.GetMin()
    max_pt = bbox_range.GetMax()
    size_m = [round(abs(max_pt[i] - min_pt[i]) * meters_per_unit, 3) for i in range(3)]
    center_m = [
        round(((min_pt[i] + max_pt[i]) / 2) * meters_per_unit, 3)
        for i in range(3)
    ]
    print(f"[CONVERT] Size for {module_name} (m): {size_m}, up_axis: {up_axis}")

    meshes_data = _extract_meshes(stage, meters_per_unit)
    print(f"[CONVERT] Extracted {len(meshes_data)} mesh(es) for {module_name}")
    glb_path = _write_glb(
        module_name=module_name,
        scenario_slug=scenario_slug,
        meshes_data=meshes_data,
        up_axis=up_axis,
    )

    source_meta_path = previews_dir / f"{module_name}_source_meta.json"
    source_metadata = None
    if source_meta_path.exists():
        source_metadata = json.loads(source_meta_path.read_text(encoding="utf-8"))
    else:
        source_metadata = _source_metadata_for_native_usd(
            source_cad_path=source_cad_path,
            usd_path=usd_path,
            stage=stage,
            meshes_data=meshes_data,
            meters_per_unit=meters_per_unit,
            up_axis=up_axis,
        )
        source_meta_path.write_text(
            json.dumps(source_metadata, indent=2),
            encoding="utf-8",
        )

    metadata = {
        "written_at": int(time.time() * 1000),
        "module_name": module_name,
        "source_cad_path": source_cad_path,
        "usd_path": usd_path,
        "glb_path": glb_path,
        "up_axis": up_axis,
        "meters_per_unit": meters_per_unit,
        "size_m": size_m,
        "center_m": center_m,
        "mesh_count": len(meshes_data),
        "materials": _extract_materials(stage),
        "source_metadata": source_metadata,
    }

    out_path = previews_dir / f"{module_name}_meta.json"
    out_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"[CONVERT] Done - {out_path}")


def main() -> int:
    for job in _workflow_jobs():
        _convert_one(
            job["module_name"],
            job["cad_path"],
            source_up_axis=job["source_up_axis"],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
