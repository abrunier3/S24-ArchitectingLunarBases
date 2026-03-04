import json
import os
from typing import Dict, Tuple, List

import omni.usd
from pxr import Usd, UsdGeom, Sdf


_UNIT_SCALE = {
    "m": 1.0, "meter": 1.0, "meters": 1.0,
    "cm": 0.01, "centimeter": 0.01, "centimeters": 0.01,
    "mm": 0.001, "millimeter": 0.001, "millimeters": 0.001,
    "in": 0.0254, "inch": 0.0254,
    "ft": 0.3048, "foot": 0.3048
}


def _abs_path(manifest_path: str, rel_path: str) -> str:
    base = os.path.dirname(os.path.abspath(manifest_path))
    return os.path.normpath(os.path.join(base, rel_path))


def _define_xform_with_reference(
    stage: Usd.Stage,
    parent_path: str,
    name: str,
    ref_path: str,
    translate=(0.0, 0.0, 0.0),
    rotate_xyz=(0.0, 0.0, 0.0),
    scale=(1.0, 1.0, 1.0),
):
    xform_path = Sdf.Path(parent_path).AppendChild(name)
    prim = stage.DefinePrim(xform_path, "Xform")
    xf = UsdGeom.Xformable(prim)

    xf.ClearXformOpOrder()
    t = xf.AddTranslateOp()
    r = xf.AddRotateXYZOp()
    s = xf.AddScaleOp()

    t.Set(tuple(translate))
    r.Set(tuple(rotate_xyz))
    s.Set(tuple(scale))

    prim.GetReferences().AddReference(ref_path)
    return prim


def build_world_from_manifest(manifest_path: str) -> str:
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    world_usd = _abs_path(manifest_path, manifest["world_usd"])

    stage_cfg = manifest.get("stage", {})
    meters_per_unit = float(stage_cfg.get("metersPerUnit", 1.0))
    up_axis = stage_cfg.get("upAxis", "Z")

    # Create/overwrite world stage (will write USDA text)
    stage = Usd.Stage.CreateNew(world_usd)

    # Stage metadata
    UsdGeom.SetStageMetersPerUnit(stage, meters_per_unit)
    UsdGeom.SetStageUpAxis(stage, up_axis)

    stage.DefinePrim("/World", "Xform")

    # Layers (terrain, assembly, rovers, etc.)
    for layer in manifest.get("layers", []):
        name = layer["name"]
        usd_file = _abs_path(manifest_path, layer["usd"])
        units = (layer.get("units") or "m").lower()
        unit_scale = _UNIT_SCALE.get(units, 1.0)

        xform = layer.get("xform", {})
        translate = xform.get("translate", [0, 0, 0])
        rotate = xform.get("rotateXYZ", [0, 0, 0])
        scale = xform.get("scale", [1, 1, 1])

        # Multiply wrapper scale by unit conversion
        scale = [scale[0] * unit_scale, scale[1] * unit_scale, scale[2] * unit_scale]

        _define_xform_with_reference(
            stage,
            "/World",
            name,
            usd_file,
            translate=translate,
            rotate_xyz=rotate,
            scale=scale,
        )

    # Optional lighting
    lighting = manifest.get("lighting", {})
    if lighting.get("enableSun", False):
        sun = stage.DefinePrim("/World/SunLight", "DistantLight")
        sun.CreateAttribute("intensity", Sdf.ValueTypeNames.Float).Set(float(lighting.get("sunIntensity", 50000.0)))
        sun_xf = UsdGeom.Xformable(sun)
        sun_xf.ClearXformOpOrder()
        rot = sun_xf.AddRotateXYZOp()
        rot.Set(tuple(lighting.get("sunRotateXYZ", [-35.0, 25.0, 0.0])))

    stage.GetRootLayer().Save()

    # Open the stage in Kit
    omni.usd.get_context().open_stage(world_usd)
    return world_usd


def validate_metadata(manifest_path: str) -> str:
    """
    Minimal validator: checks for required customData keys on /World/<LayerName> wrapper prims.
    You can later tighten this to check the referenced prim roots inside each asset.
    """
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    required = manifest.get("metadata_required_keys", [])
    if not required:
        return "No metadata_required_keys in manifest."

    stage = omni.usd.get_context().get_stage()
    if stage is None:
        return "No stage open. Build/Open first."

    problems: List[str] = []
    for layer in manifest.get("layers", []):
        name = layer["name"]
        prim = stage.GetPrimAtPath(Sdf.Path(f"/World/{name}"))
        if not prim or not prim.IsValid():
            problems.append(f"{name}: missing /World/{name}")
            continue

        cd = prim.GetCustomData() or {}
        for k in required:
            if k not in cd:
                problems.append(f"{name}: missing customData['{k}']")

    if problems:
        return "Metadata validation FAILED:\n- " + "\n- ".join(problems)
    return "Metadata validation PASSED."
