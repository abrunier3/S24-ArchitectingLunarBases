import json
import os
from typing import List, Dict, Any

import omni.usd
from pxr import Usd, UsdGeom, UsdLux, Sdf


_UNIT_SCALE = {
    "m": 1.0, "meter": 1.0, "meters": 1.0,
    "cm": 0.01, "centimeter": 0.01, "centimeters": 0.01,
    "mm": 0.001, "millimeter": 0.001, "millimeters": 0.001,
    "in": 0.0254, "inch": 0.0254, "inches": 0.0254,
    "ft": 0.3048, "foot": 0.3048, "feet": 0.3048
}


def _abs_path(manifest_path: str, rel_path: str) -> str:
    """Resolve a manifest-relative path to an absolute path."""
    base = os.path.dirname(os.path.abspath(manifest_path))
    return os.path.normpath(os.path.join(base, rel_path))


def _rel_from_target(target_file: str, asset_file: str) -> str:
    """
    Compute a USD-friendly relative path from the generated world file
    to the referenced asset file.
    """
    target_dir = os.path.dirname(os.path.abspath(target_file))
    return os.path.relpath(os.path.abspath(asset_file), target_dir).replace("\\", "/")


def _validate_layer_schema(layer: Dict[str, Any], group_name: str) -> None:
    """Basic schema validation for each environment/assembly entry."""
    required_keys = ["name", "usd"]
    for key in required_keys:
        if key not in layer:
            raise ValueError(f"{group_name} layer missing required key '{key}': {layer}")

    if "xform" in layer:
        xform = layer["xform"]
        for key in ["translate", "rotateXYZ", "scale"]:
            if key in xform and len(xform[key]) != 3:
                raise ValueError(
                    f"{group_name} layer '{layer['name']}' has invalid xform['{key}']; expected 3 values."
                )


def _define_xform_with_reference(
    stage: Usd.Stage,
    parent_path: str,
    name: str,
    ref_path: str,
    translate=(0.0, 0.0, 0.0),
    rotate_xyz=(0.0, 0.0, 0.0),
    scale=(1.0, 1.0, 1.0),
    custom_data=None,
):
    xform_path = Sdf.Path(parent_path).AppendChild(name)
    prim = stage.DefinePrim(xform_path, "Xform")
    xf = UsdGeom.Xformable(prim)

    xf.ClearXformOpOrder()
    xf.AddTranslateOp().Set(tuple(translate))
    xf.AddRotateXYZOp().Set(tuple(rotate_xyz))
    xf.AddScaleOp().Set(tuple(scale))

    prim.GetReferences().AddReference(ref_path)

    if custom_data:
        for key, value in custom_data.items():
            prim.SetCustomDataByKey(key, value)

    return prim


def _add_layer_group(
    stage: Usd.Stage,
    manifest_path: str,
    world_usd: str,
    parent_path: str,
    layers: List[Dict[str, Any]],
    group_name: str,
) -> None:
    """
    Add a group of referenced layers under a grouping prim like:
    /World/Environment or /World/Assemblies
    """
    stage.DefinePrim(parent_path, "Xform")

    seen_names = set()

    for layer in layers:
        _validate_layer_schema(layer, group_name)

        name = layer["name"]
        if name in seen_names:
            raise ValueError(f"Duplicate layer name '{name}' in group '{group_name}'")
        seen_names.add(name)

        usd_abs = _abs_path(manifest_path, layer["usd"])
        if not os.path.exists(usd_abs):
            raise FileNotFoundError(
                f"{group_name} layer '{name}' references missing USD:\n{usd_abs}"
            )

        # Store relative path in the generated world USD
        usd_ref = _rel_from_target(world_usd, usd_abs)

        units = (layer.get("units") or "m").lower()
        unit_scale = _UNIT_SCALE.get(units)
        if unit_scale is None:
            raise ValueError(
                f"{group_name} layer '{name}' uses unsupported units '{units}'"
            )

        xform = layer.get("xform", {})
        translate = xform.get("translate", [0.0, 0.0, 0.0])
        rotate = xform.get("rotateXYZ", [0.0, 0.0, 0.0])
        scale = xform.get("scale", [1.0, 1.0, 1.0])

        final_scale = [
            scale[0] * unit_scale,
            scale[1] * unit_scale,
            scale[2] * unit_scale,
        ]

        metadata = layer.get("metadata", {}) or {}

        custom_data = {
            "s24:name": layer.get("name", ""),
            "s24:asset_id": layer.get("asset_id", ""),
            "s24:asset_type": layer.get("asset_type", ""),
            "s24:role": layer.get("role", ""),
            "s24:display_name": layer.get("display_name", layer.get("name", "")),
            "s24:source_usd": usd_ref,
        }

        # Preserve any arbitrary metadata keys automatically
        for k, v in metadata.items():
            custom_data[f"s24:{k}"] = v

        _define_xform_with_reference(
            stage=stage,
            parent_path=parent_path,
            name=name,
            ref_path=usd_ref,
            translate=translate,
            rotate_xyz=rotate,
            scale=final_scale,
            custom_data=custom_data,
        )

def _create_sun_light(stage: Usd.Stage, lighting_cfg: Dict[str, Any]) -> None:
    """Create optional distant sunlight."""
    if not lighting_cfg.get("enableSun", False):
        return

    sun = UsdLux.DistantLight.Define(stage, "/World/SunLight")
    sun.CreateIntensityAttr(float(lighting_cfg.get("sunIntensity", 50000.0)))

    sun_xf = UsdGeom.Xformable(sun.GetPrim())
    sun_xf.ClearXformOpOrder()
    sun_xf.AddRotateXYZOp().Set(
        tuple(lighting_cfg.get("sunRotateXYZ", [-35.0, 25.0, 0.0]))
    )


def build_world_from_manifest(manifest_path: str) -> str:
    """
    Build a composed world stage from a manifest.
    New architecture:
      - environment layers (terrain, etc.)
      - assembly layers (Arthur-generated consolidated assembly.usda, etc.)
    """
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest not found:\n{manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    if "world_usd" not in manifest:
        raise ValueError("Manifest missing required key 'world_usd'")

    world_usd = _abs_path(manifest_path, manifest["world_usd"])
    os.makedirs(os.path.dirname(world_usd), exist_ok=True)

    stage_cfg = manifest.get("stage", {})
    meters_per_unit = float(stage_cfg.get("metersPerUnit", 1.0))
    up_axis = stage_cfg.get("upAxis", "Z")

    if up_axis not in ("Y", "Z"):
        raise ValueError(f"Unsupported upAxis '{up_axis}'. Expected 'Y' or 'Z'.")

    environment_layers = manifest.get("environment", [])
    assembly_layers = manifest.get("assemblies", [])

    # Backward compatibility: if old "layers" exists and new groups are empty,
    # treat old layers as environment layers.
    legacy_layers = manifest.get("layers", [])
    if legacy_layers and not environment_layers and not assembly_layers:
        environment_layers = legacy_layers

    # Close current stage before recreating output
    omni.usd.get_context().close_stage()

    if os.path.exists(world_usd):
        os.remove(world_usd)

    stage = Usd.Stage.CreateNew(world_usd)

    # Stage settings
    UsdGeom.SetStageMetersPerUnit(stage, meters_per_unit)
    UsdGeom.SetStageUpAxis(stage, up_axis)

    # Root prim
    world_prim = stage.DefinePrim("/World", "Xform")
    stage.SetDefaultPrim(world_prim)

    # Logical groupings
    _add_layer_group(
        stage=stage,
        manifest_path=manifest_path,
        world_usd=world_usd,
        parent_path="/World/Environment",
        layers=environment_layers,
        group_name="environment",
    )

    _add_layer_group(
        stage=stage,
        manifest_path=manifest_path,
        world_usd=world_usd,
        parent_path="/World/Assemblies",
        layers=assembly_layers,
        group_name="assemblies",
    )

    # Optional light
    lighting = manifest.get("lighting", {})
    _create_sun_light(stage, lighting)

    stage.GetRootLayer().Save()

    # Open result in Kit
    omni.usd.get_context().open_stage(world_usd)
    return world_usd


def validate_metadata(manifest_path: str) -> str:
    """
    Minimal validator:
    Checks required customData keys on the wrapper prims generated by this builder.
    """
    if not os.path.exists(manifest_path):
        return f"Manifest not found: {manifest_path}"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    required = manifest.get("metadata_required_keys", [])
    if not required:
        return "No metadata_required_keys in manifest."

    stage = omni.usd.get_context().get_stage()
    if stage is None:
        return "No stage open. Build/Open first."

    problems: List[str] = []

    for group_path, items in [
        ("/World/Environment", manifest.get("environment", [])),
        ("/World/Assemblies", manifest.get("assemblies", [])),
    ]:
        for layer in items:
            name = layer.get("name", "<unnamed>")
            prim = stage.GetPrimAtPath(Sdf.Path(f"{group_path}/{name}"))
            if not prim or not prim.IsValid():
                problems.append(f"{name}: missing {group_path}/{name}")
                continue

            cd = prim.GetCustomData() or {}
            for key in required:
                if key not in cd:
                    problems.append(f"{name}: missing customData['{key}']")

    if problems:
        return "Metadata validation FAILED:\n- " + "\n- ".join(problems)

    return "Metadata validation PASSED."