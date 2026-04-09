from __future__ import annotations
from typing import Dict, List, Optional
from pxr import Usd, UsdGeom, Sdf, Gf
from .utils import set_stage_metadata, ref_path
import os


def _sanitize_token(value: str) -> str:
    value = (value or "").strip().lower()
    cleaned = []
    prev_underscore = False

    for ch in value:
        if ch.isalnum():
            cleaned.append(ch)
            prev_underscore = False
        else:
            if not prev_underscore:
                cleaned.append("_")
                prev_underscore = True

    result = "".join(cleaned).strip("_")
    return result or "unnamed"


def _derive_asset_id(prim_path: Sdf.Path, node_name: str) -> str:
    """
    Derive a stable asset_id from the assembly prim path.
    Example:
      /World/ISRU_PLANT/Rover -> world_isru_plant_rover
    """
    return _sanitize_token(str(prim_path))


def _derive_display_name(node_name: str) -> str:
    return node_name or "Unnamed"


def _derive_asset_type_and_role(node_name: str) -> tuple[str, str]:
    """
    Generic backend inference from the node name only.
    This is intentionally generic and non-stakeholder-facing.
    """
    n = (node_name or "").lower()

    if "rover" in n:
        return "vehicle", "transporter"
    if "plant" in n or "isru" in n:
        return "plant", "producer"
    if "depot" in n or "tank" in n or "storage" in n:
        return "storage_asset", "storage"
    if "terrain" in n or "surface" in n or "lunar" in n:
        return "environment_asset", "environment"

    return "generic_asset", "assembly_member"


def _stamp_generic_metadata(prim, prim_path: Sdf.Path, node_name: str, comp_abs: str) -> None:
    asset_id = _derive_asset_id(prim_path, node_name)
    asset_type, role = _derive_asset_type_and_role(node_name)
    display_name = _derive_display_name(node_name)

    prim.SetCustomDataByKey("s24:name", node_name)
    prim.SetCustomDataByKey("s24:asset_id", asset_id)
    prim.SetCustomDataByKey("s24:asset_type", asset_type)
    prim.SetCustomDataByKey("s24:role", role)
    prim.SetCustomDataByKey("s24:display_name", display_name)
    prim.SetCustomDataByKey("s24:source_component", os.path.abspath(comp_abs))


def author_assembly_scene(
    *,
    scene_path: str,
    root_names: List[str],
    by_name: Dict[str, object],
    comp_path_for,
    meters_per_unit: float,
    up_axis: str,
    include_root_as_instance: bool = True,
    instanceable: bool = False,
    debug_refs: bool = False,
) -> str:
    """
    Create an assembly scene with one or multiple roots:
      /World/<root1>/<child>/...
      /World/<root2>/<child>/...

    Each placed Xform references the part component layer at /<part_name>.
    """
    if os.path.exists(scene_path):
        os.remove(scene_path)

    old_layer = Sdf.Layer.Find(scene_path)
    if old_layer:
        old_layer.Clear()

    stage = Usd.Stage.CreateNew(scene_path)
    set_stage_metadata(stage, meters_per_unit=meters_per_unit, up_axis=up_axis)

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    def add_ref(prim, comp_abs: str, prim_name: str, prim_path: Sdf.Path) -> None:
        comp_abs_resolved = os.path.abspath(comp_abs)
        comp_rel = os.path.relpath(
            comp_abs_resolved, os.path.dirname(os.path.abspath(scene_path))
        )
        if debug_refs:
            print(f"[REF] {prim_path} -> {comp_rel} :/{prim_name}")
        prim.GetReferences().AddReference(comp_rel, f"/{prim_name}")

    def place(node_name: str, parent_path: Sdf.Path) -> None:
        node = by_name[node_name]
        prim_path = parent_path.AppendChild(node_name)
        x = UsdGeom.Xform.Define(stage, prim_path)
        x.AddTranslateOp().Set(Gf.Vec3d(*node.translate))
        x.AddRotateXYZOp().Set(Gf.Vec3f(*node.rotation_deg))
        prim = x.GetPrim()

        comp_abs = comp_path_for(node)

        if instanceable:
            prim.SetInstanceable(True)

        add_ref(prim, comp_abs, node_name, prim_path)
        _stamp_generic_metadata(prim, prim_path, node_name, comp_abs)

        for ch in node.children:
            place(ch, prim_path)

    for rn in root_names:
        root_part = by_name[rn]
        root_path = Sdf.Path(f"/World/{rn}")
        root_xf = UsdGeom.Xform.Define(stage, root_path)
        root_xf.AddTranslateOp().Set(Gf.Vec3d(*root_part.translate))
        root_xf.AddRotateXYZOp().Set(Gf.Vec3f(*root_part.rotation_deg))

        prim = root_xf.GetPrim()
        comp_abs = comp_path_for(root_part)

        if include_root_as_instance:
            if instanceable:
                prim.SetInstanceable(True)
            add_ref(prim, comp_abs, rn, root_path)

        _stamp_generic_metadata(prim, root_path, rn, comp_abs)

        for ch in root_part.children:
            place(ch, root_path)

    stage.GetRootLayer().Save()
    return scene_path
