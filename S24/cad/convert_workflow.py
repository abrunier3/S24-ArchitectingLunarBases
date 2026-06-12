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

from S24.cad.step_to_usd import convert_step_to_usd


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
            }
            for job in jobs
        ]

    module_name = os.environ.get("MODULE_NAME", "").strip()
    cad_path = os.environ.get("USD_PATH", "").strip()
    if not module_name or not cad_path:
        raise ValueError("Provide either BATCH_JOBS_JSON or MODULE_NAME/USD_PATH")

    return [{"module_name": module_name, "cad_path": cad_path}]


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


def _write_glb(
    *,
    module_name: str,
    meshes_data: list[trimesh.Trimesh],
    up_axis: str,
) -> str | None:
    if not meshes_data:
        return None

    scene = trimesh.Scene(meshes_data)
    if str(up_axis) == "Y":
        scene.apply_transform(tf.rotation_matrix(-np.pi / 2, [1, 0, 0]))

    bounds = scene.bounds
    if bounds is not None:
        center = (bounds[0] + bounds[1]) / 2
        scene.apply_translation(-center)

    glb_path = f"outputs/cad_previews/{module_name}.glb"
    glb_bytes = scene.export(file_type="glb")
    with open(glb_path, "wb") as file:
        file.write(glb_bytes)
    print(f"[CONVERT] GLB written for {module_name}: {len(glb_bytes) // 1024} KB")
    return glb_path


def _convert_one(module_name: str, cad_path: str) -> None:
    os.makedirs("outputs/cad_previews", exist_ok=True)

    source_cad_path = cad_path
    usd_path = cad_path
    lower_path = cad_path.lower()

    if lower_path.endswith((".step", ".stp")):
        converted_usd_path = f"clean_database/cad_models/{module_name}/{module_name}.usdc"
        source_meta_path = f"outputs/cad_previews/{module_name}_source_meta.json"
        print(f"[CONVERT] STEP detected. Converting {cad_path} -> {converted_usd_path}")
        source_metadata = convert_step_to_usd(
            cad_path,
            converted_usd_path,
            source_up_axis=os.environ.get("STEP_SOURCE_UP_AXIS", "Y"),
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
        meshes_data=meshes_data,
        up_axis=up_axis,
    )

    source_meta_path = Path(f"outputs/cad_previews/{module_name}_source_meta.json")
    source_metadata = None
    if source_meta_path.exists():
        source_metadata = json.loads(source_meta_path.read_text(encoding="utf-8"))

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

    out_path = Path(f"outputs/cad_previews/{module_name}_meta.json")
    out_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"[CONVERT] Done - {out_path}")


def main() -> int:
    for job in _workflow_jobs():
        _convert_one(job["module_name"], job["cad_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
