from __future__ import annotations

from typing import Any, Dict, Tuple

from pxr import Usd, UsdGeom, UsdShade, Sdf, Gf

from .utils import set_stage_metadata, ref_path


def author_component_layer(
    *,
    comp_path: str,
    part_name: str,
    uid: str,
    ptype: str,
    dims_m: Tuple[float, float, float],
    meters_per_unit: float,
    up_axis: str,
    raw_attributes: Dict[str, Any],
    geom_layer_path: str,
    geom_prim_path: str,
    mat_layer_path: str,
    material_prim_path: str,
) -> str:
    """
    Create a component definition layer at comp_path, defining /<part_name> and:
      - metadata attributes (asset:*, spatial:*, attr:*)
      - /<part_name>/geom references geom layer prim
      - /<part_name>/materials references mat layer
      - binds material to geom if resolvable
    Returns written comp_path.
    """
    stage = Usd.Stage.CreateNew(comp_path)
    set_stage_metadata(stage, meters_per_unit=meters_per_unit, up_axis=up_axis)

    root = UsdGeom.Xform.Define(stage, f"/{part_name}")
    root_prim = root.GetPrim()
    stage.SetDefaultPrim(root_prim)

    # Identity
    root_prim.CreateAttribute("asset:id", Sdf.ValueTypeNames.String).Set(str(uid))
    root_prim.CreateAttribute("asset:type", Sdf.ValueTypeNames.String).Set(str(ptype))

    # Spatial
    root_prim.CreateAttribute("spatial:dims_m", Sdf.ValueTypeNames.Double3).Set(
        Gf.Vec3d(float(dims_m[0]), float(dims_m[1]), float(dims_m[2]))
    )
    root_prim.CreateAttribute("spatial:metersPerUnit", Sdf.ValueTypeNames.Double).Set(float(meters_per_unit))
    root_prim.CreateAttribute("spatial:upAxis", Sdf.ValueTypeNames.String).Set(str(up_axis))

    # Raw numeric/string attrs
    for k, v in raw_attributes.items():
        if isinstance(v, (int, float)):
            root_prim.CreateAttribute(f"attr:{k}", Sdf.ValueTypeNames.Double).Set(float(v))
        else:
            root_prim.CreateAttribute(f"attr:{k}", Sdf.ValueTypeNames.String).Set(str(v))

    # Relative refs
    geom_ref = ref_path(geom_layer_path, comp_path)
    mat_ref = ref_path(mat_layer_path, comp_path)

    # Geometry reference
    geom_mesh = UsdGeom.Mesh.Define(stage, f"/{part_name}/geom")
    geom_mesh.GetPrim().GetReferences().AddReference(geom_ref, geom_prim_path)

    # Material reference + binding
    materials_scope = UsdGeom.Scope.Define(stage, f"/{part_name}/materials")
    materials_scope.GetPrim().GetReferences().AddReference(mat_ref)

    bound_mat = UsdShade.Material.Get(stage, Sdf.Path(f"/{part_name}/materials{material_prim_path}"))
    if bound_mat and bound_mat.GetPrim().IsValid():
        UsdShade.MaterialBindingAPI.Apply(geom_mesh.GetPrim()).Bind(bound_mat)
    else:
        geom_mesh.GetPrim().SetCustomDataByKey("materialHint", f"{mat_ref}:{material_prim_path}")

    stage.GetRootLayer().Save()
    return comp_path
