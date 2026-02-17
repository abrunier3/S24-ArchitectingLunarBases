from __future__ import annotations

from typing import Dict, Optional

from pxr import Usd, UsdGeom, Sdf, Gf

from .utils import set_stage_metadata, ref_path
import os


def author_assembly_scene(
    *,
    scene_path: str,
    root_name: str,
    by_name: Dict[str, object],
    comp_path_for,
    meters_per_unit: float,
    up_axis: str,
    include_root_as_instance: bool = True,
    instanceable: bool = False,
    debug_refs: bool = False,
) -> str:
    """
    Create an assembly scene:
      /World/<root>/<child>/...
    Each placed Xform references the part component layer at /<part_name>.

    Parameters
    ----------
    by_name:
        Dict[name -> VettedPart-like], must expose: .translate, .children, .parent
    comp_path_for:
        Callable(vp) -> absolute component file path
    """
    if os.path.exists(scene_path):
        os.remove(scene_path)
    # Clear USD layer cache
    old_layer = Sdf.Layer.Find(scene_path)
    if old_layer:
        old_layer.Clear()
    
    stage = Usd.Stage.CreateNew(scene_path)
    set_stage_metadata(stage, meters_per_unit=meters_per_unit, up_axis=up_axis)
    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())
    root_part = by_name[root_name]
    root_path = Sdf.Path(f"/World/{root_name}")
    root_xf = UsdGeom.Xform.Define(stage, root_path)
    root_xf.AddTranslateOp().Set(Gf.Vec3d(*root_part.translate))
    root_xf.AddRotateXYZOp().Set(Gf.Vec3f(*root_part.rotation_deg))

    def add_ref(prim, comp_abs: str, prim_name: str, prim_path: Sdf.Path) -> None:
        comp_abs_resolved = os.path.abspath(comp_abs)
        comp_rel = os.path.relpath(comp_abs_resolved, os.path.dirname(os.path.abspath(scene_path)))
        if debug_refs:
            print(f"[REF] {prim_path} -> {comp_rel} :/{prim_name}")
        prim.GetReferences().AddReference(comp_rel, f"/{prim_name}")

    if include_root_as_instance:
        prim = root_xf.GetPrim()
        if instanceable:
            prim.SetInstanceable(True)
        add_ref(prim, comp_path_for(root_part), root_name, root_path)

    def place(node_name: str, parent_path: Sdf.Path) -> None:
        node = by_name[node_name]
        prim_path = parent_path.AppendChild(node_name)

        x = UsdGeom.Xform.Define(stage, prim_path)
        x.AddTranslateOp().Set(Gf.Vec3d(*node.translate))
        x.AddRotateXYZOp().Set(Gf.Vec3f(*node.rotation_deg))

        prim = x.GetPrim()
        if instanceable:
            prim.SetInstanceable(True)

        add_ref(prim, comp_path_for(node), node_name, prim_path)

        for ch in node.children:
            place(ch, prim_path)

    for ch in root_part.children:
        place(ch, root_path)

    stage.GetRootLayer().Save()
    return scene_path