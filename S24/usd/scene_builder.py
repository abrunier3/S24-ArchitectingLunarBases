from typing import Dict, Any
from pathlib import Path
import os

from pxr import Usd, UsdGeom, Sdf, Gf

from S24.utils.setup_paths import _find_project_root


def _make_usd_reference_path(
    asset_path: str,
    *,
    output_path: str,
    repo_root: Path,
) -> str:
    """
    Convert a manifest CAD path into a USD reference path.

    Important:
    USD references are resolved relative to the USD layer that contains them,
    not relative to the repository root.

    Example
    -------
    If output_path is:
        clean_database/usd/scenes/Assembly.usda

    and asset_path is:
        clean_database/cad_models/RegolithRover/RegolithRover.usdc

    this returns:
        ../../cad_models/RegolithRover/RegolithRover.usdc
    """

    repo_root = repo_root.resolve()
    output_dir = Path(output_path).resolve().parent

    asset = Path(asset_path)

    if asset.is_absolute():
        asset_abs = asset.resolve()
    else:
        asset_abs = (repo_root / asset).resolve()

    ref_path = os.path.relpath(asset_abs, start=output_dir)

    # USD paths should use forward slashes even on Windows.
    return ref_path.replace("\\", "/")


def _resolve_asset_path(asset_path: str, *, repo_root: Path) -> Path:
    asset = Path(asset_path)
    if asset.is_absolute():
        return asset.resolve()
    return (repo_root / asset).resolve()


def _transform_bbox_corners(min_pt, max_pt, *, rotate_xyz, scale):
    corners = []
    for x in (min_pt[0], max_pt[0]):
        for y in (min_pt[1], max_pt[1]):
            for z in (min_pt[2], max_pt[2]):
                vec = Gf.Vec3d(x * scale[0], y * scale[1], z * scale[2])
                matrix = Gf.Matrix4d(1.0).SetRotate(Gf.Rotation(Gf.Vec3d(1, 0, 0), rotate_xyz[0]))
                matrix = matrix * Gf.Matrix4d(1.0).SetRotate(Gf.Rotation(Gf.Vec3d(0, 1, 0), rotate_xyz[1]))
                matrix = matrix * Gf.Matrix4d(1.0).SetRotate(Gf.Rotation(Gf.Vec3d(0, 0, 1), rotate_xyz[2]))
                corners.append(matrix.Transform(vec))
    return corners


def _target_size_from_dimensions(dimensions: Dict[str, Any]) -> list[float] | None:
    size_m = (dimensions or {}).get("size_m") or {}
    values = [
        size_m.get("length"),
        size_m.get("width"),
        size_m.get("height"),
    ]
    if not all(isinstance(value, (int, float)) and value > 0 for value in values):
        return None
    return [float(value) for value in values]


def _cad_normalization(
    cad_path: str,
    *,
    repo_root: Path,
    dimensions: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Return a universal placement transform for a referenced CAD layer.

    The assembly scene is Z-up and meters-based. Uploaded CAD files can be
    authored with their own stage upAxis/metersPerUnit. The CAD's authored
    orientation is preserved under a child reference prim; this wrapper only
    applies unit scale and grounding.
    """

    cad_abs = _resolve_asset_path(cad_path, repo_root=repo_root)
    stage = Usd.Stage.Open(str(cad_abs))
    if not stage:
        return {
            "up_axis": "Z",
            "meters_per_unit": 1.0,
            "rotate_xyz": [0.0, 0.0, 0.0],
            "scale": [1.0, 1.0, 1.0],
            "translate": [0.0, 0.0, 0.0],
            "bbox_min": [0.0, 0.0, 0.0],
            "bbox_max": [0.0, 0.0, 0.0],
            "bbox_size": [0.0, 0.0, 0.0],
            "has_authored_xforms": False,
            "authored_xform_ops": [],
        }

    up_axis = str(UsdGeom.GetStageUpAxis(stage)).upper()
    meters_per_unit = float(UsdGeom.GetStageMetersPerUnit(stage) or 1.0)

    # Do not rotate from stage upAxis alone. Several Sketchfab/Omniverse USDs
    # already encode their visual orientation in authored xformOps.
    rotate_xyz = [0.0, 0.0, 0.0]

    unit_scale = [meters_per_unit, meters_per_unit, meters_per_unit]

    default_prim = stage.GetDefaultPrim()
    bound_prim = default_prim if default_prim else stage.GetPseudoRoot()

    authored_xform_ops = []
    for prim in stage.Traverse():
        if not prim.IsA(UsdGeom.Xformable):
            continue
        xformable = UsdGeom.Xformable(prim)
        ops = xformable.GetOrderedXformOps()
        if not ops:
            continue
        authored_xform_ops.append(
            f"{prim.GetPath()}:{','.join(op.GetOpName() for op in ops)}"
        )

    bbox_cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
    bbox = bbox_cache.ComputeWorldBound(bound_prim)
    # ComputeWorldBound can return a box with a non-identity matrix. Using only
    # GetRange() ignores that matrix, which is exactly how CAD-internal offsets
    # can slip through and leave a referenced model below the terrain.
    bbox_range = bbox.ComputeAlignedRange()
    min_pt = bbox_range.GetMin()
    max_pt = bbox_range.GetMax()
    bbox_min = [float(min_pt[i]) * meters_per_unit for i in range(3)]
    bbox_max = [float(max_pt[i]) * meters_per_unit for i in range(3)]
    bbox_size = [
        bbox_max[0] - bbox_min[0],
        bbox_max[1] - bbox_min[1],
        bbox_max[2] - bbox_min[2],
    ]
    target_size = _target_size_from_dimensions(dimensions or {})
    fit_scale = [1.0, 1.0, 1.0]
    scale_mode = "cad_native_units"
    if target_size and all(size > 0 for size in bbox_size):
        target_variants = [
            target_size,
            [target_size[1], target_size[0], target_size[2]],
        ]
        fit_ratio = max(
            min(target[i] / bbox_size[i] for i in range(3))
            for target in target_variants
        )
        fit_scale = [fit_ratio, fit_ratio, fit_ratio]
        scale_mode = "sysml_size_m_uniform_bbox_fit_xy_interchangeable"

    scale = [unit_scale[i] * fit_scale[i] for i in range(3)]
    fitted_bbox_size = [bbox_size[i] * fit_scale[i] for i in range(3)]

    corners = _transform_bbox_corners(
        bbox_range.GetMin(),
        bbox_range.GetMax(),
        rotate_xyz=rotate_xyz,
        scale=scale,
    )
    min_z = min((corner[2] for corner in corners), default=0.0)
    min_x = min((corner[0] for corner in corners), default=0.0)
    max_x = max((corner[0] for corner in corners), default=0.0)
    min_y = min((corner[1] for corner in corners), default=0.0)
    max_y = max((corner[1] for corner in corners), default=0.0)
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0

    return {
        "up_axis": up_axis,
        "meters_per_unit": meters_per_unit,
        "rotate_xyz": rotate_xyz,
        "scale": scale,
        "unit_scale": unit_scale,
        "fit_scale": fit_scale,
        "scale_mode": scale_mode,
        "target_size": target_size or [0.0, 0.0, 0.0],
        "translate": [-center_x, -center_y, -min_z],
        "bbox_center_xy_offset": [center_x, center_y],
        "bbox_min": bbox_min,
        "bbox_max": bbox_max,
        "bbox_size": bbox_size,
        "fitted_bbox_size": fitted_bbox_size,
        "has_authored_xforms": bool(authored_xform_ops),
        "authored_xform_ops": authored_xform_ops[:20],
    }


def build_usd_scene_from_manifest(
    manifest: Dict[str, Any],
    *,
    output_path: str,
    stage_name: str = "World",
    verbose: int = 1,
) -> str:
    """
    Build a USD assembly scene from the Step 3 submission manifest.

    Path convention
    ---------------
    manifest["parts"][i]["cad_path"] should be repo-relative, e.g.:

        clean_database/cad_models/RegolithRover/RegolithRover.usdc

    This function converts that path into a USD-layer-relative reference
    before calling AddReference(...).
    """

    repo_root = _find_project_root().resolve()

    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    stage = Usd.Stage.CreateNew(str(output_path_obj))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)

    root = UsdGeom.Xform.Define(stage, f"/{stage_name}")
    stage.SetDefaultPrim(root.GetPrim())

    for part in manifest["parts"]:
        name = part["name"]
        prim_path = f"/{stage_name}/{name}"

        xform = UsdGeom.Xform.Define(stage, prim_path)
        prim = xform.GetPrim()

        cad_path = part.get("cad_path")
        cad_ref_path = None

        normalization = None

        if cad_path:
            cad_ref_path = _make_usd_reference_path(
                cad_path,
                output_path=str(output_path_obj),
                repo_root=repo_root,
            )
            normalization = _cad_normalization(
                cad_path,
                repo_root=repo_root,
                dimensions=part.get("dimensions"),
            )

        pos = part.get("position_m", [0, 0, 0])
        rot = part.get("rotation_deg", [0, 0, 0])
        scale = part.get("scale", [1.0, 1.0, 1.0])

        # Use XformCommonAPI to avoid duplicate xformOp conflicts with referenced CAD.
        xform_api = UsdGeom.XformCommonAPI(xform)
        xform_api.SetTranslate(Gf.Vec3d(*pos))
        xform_api.SetRotate(
            Gf.Vec3f(*rot),
            UsdGeom.XformCommonAPI.RotationOrderXYZ,
        )
        xform_api.SetScale(Gf.Vec3f(*scale))

        if cad_ref_path:
            geom_path = f"{prim_path}/Geometry"
            geom_xform = UsdGeom.Xform.Define(stage, geom_path)
            geom_prim = geom_xform.GetPrim()

            norm = normalization or {}
            geom_xform.ClearXformOpOrder()
            translate_op = geom_xform.AddTranslateOp(UsdGeom.XformOp.PrecisionDouble)
            rotate_op = geom_xform.AddRotateXYZOp(UsdGeom.XformOp.PrecisionFloat)
            scale_op = geom_xform.AddScaleOp(UsdGeom.XformOp.PrecisionFloat)
            translate_op.Set(Gf.Vec3d(*norm.get("translate", [0.0, 0.0, 0.0])))
            rotate_op.Set(Gf.Vec3f(*norm.get("rotate_xyz", [0.0, 0.0, 0.0])))
            scale_op.Set(Gf.Vec3f(*norm.get("scale", [1.0, 1.0, 1.0])))

            geom_prim.CreateAttribute("cad:sourceUpAxis", Sdf.ValueTypeNames.String).Set(
                str(norm.get("up_axis", "Z"))
            )
            geom_prim.CreateAttribute("cad:metersPerUnit", Sdf.ValueTypeNames.Double).Set(
                float(norm.get("meters_per_unit", 1.0))
            )
            geom_prim.CreateAttribute("cad:scaleMode", Sdf.ValueTypeNames.String).Set(
                str(norm.get("scale_mode", "cad_native_units"))
            )
            geom_prim.CreateAttribute("cad:unitScale", Sdf.ValueTypeNames.Double3).Set(
                Gf.Vec3d(*norm.get("unit_scale", [1.0, 1.0, 1.0]))
            )
            geom_prim.CreateAttribute("cad:fitScale", Sdf.ValueTypeNames.Double3).Set(
                Gf.Vec3d(*norm.get("fit_scale", [1.0, 1.0, 1.0]))
            )
            geom_prim.CreateAttribute("cad:targetSizeM", Sdf.ValueTypeNames.Double3).Set(
                Gf.Vec3d(*norm.get("target_size", [0.0, 0.0, 0.0]))
            )
            geom_prim.CreateAttribute("cad:groundingTranslate", Sdf.ValueTypeNames.Double3).Set(
                Gf.Vec3d(*norm.get("translate", [0.0, 0.0, 0.0]))
            )
            geom_prim.CreateAttribute("cad:bboxCenterXYOffset", Sdf.ValueTypeNames.Double2).Set(
                Gf.Vec2d(*norm.get("bbox_center_xy_offset", [0.0, 0.0]))
            )
            geom_prim.CreateAttribute("cad:bboxMin", Sdf.ValueTypeNames.Double3).Set(
                Gf.Vec3d(*norm.get("bbox_min", [0.0, 0.0, 0.0]))
            )
            geom_prim.CreateAttribute("cad:bboxMax", Sdf.ValueTypeNames.Double3).Set(
                Gf.Vec3d(*norm.get("bbox_max", [0.0, 0.0, 0.0]))
            )
            geom_prim.CreateAttribute("cad:bboxSize", Sdf.ValueTypeNames.Double3).Set(
                Gf.Vec3d(*norm.get("bbox_size", [0.0, 0.0, 0.0]))
            )
            geom_prim.CreateAttribute("cad:fittedBboxSize", Sdf.ValueTypeNames.Double3).Set(
                Gf.Vec3d(*norm.get("fitted_bbox_size", [0.0, 0.0, 0.0]))
            )
            geom_prim.CreateAttribute("cad:hasAuthoredXforms", Sdf.ValueTypeNames.Bool).Set(
                bool(norm.get("has_authored_xforms", False))
            )
            geom_prim.CreateAttribute("cad:authoredXformOps", Sdf.ValueTypeNames.String).Set(
                "; ".join(norm.get("authored_xform_ops", []))
            )
            geom_prim.CreateAttribute("cad:normalizationMode", Sdf.ValueTypeNames.String).Set(
                "preserve_authored_xforms_sysml_size_uniform_bbox_fit_xy_interchangeable_centered_ground_aligned"
            )

            model_path = f"{geom_path}/Model"
            model_xform = UsdGeom.Xform.Define(stage, model_path)
            model_xform.GetPrim().GetReferences().AddReference(cad_ref_path)

        prim.CreateAttribute("part:name", Sdf.ValueTypeNames.String).Set(name)

        if part.get("material"):
            prim.CreateAttribute("material", Sdf.ValueTypeNames.String).Set(part["material"])

        if part.get("attributes"):
            prim.CreateAttribute("attributes", Sdf.ValueTypeNames.String).Set(str(part["attributes"]))

        if part.get("dimensions"):
            prim.CreateAttribute("dimensions", Sdf.ValueTypeNames.String).Set(str(part["dimensions"]))

        if verbose >= 2:
            print(f"[USD] Added {name}")
            print(f"  CAD manifest path : {cad_path if cad_path else 'None'}")
            print(f"  CAD USD ref path  : {cad_ref_path if cad_ref_path else 'None'}")
            print(f"  Pos               : {pos}")
            print(f"  Rot               : {rot}")
            if normalization:
                print(f"  CAD upAxis        : {normalization['up_axis']}")
                print(f"  CAD correction    : rotate={normalization['rotate_xyz']} translate={normalization['translate']}")
                print(f"  CAD scale mode    : {normalization['scale_mode']} scale={normalization['scale']}")
                print(f"  CAD bbox min/max  : {normalization['bbox_min']} / {normalization['bbox_max']}")
                print(f"  CAD fitted size   : {normalization['fitted_bbox_size']}")
                print(f"  CAD authored ops  : {len(normalization['authored_xform_ops'])}")

    stage.GetRootLayer().Save()

    if verbose >= 1:
        print("\n" + "=" * 50)
        print(f"[USD] Scene written → {output_path_obj}")
        print("=" * 50)

    return str(output_path_obj)


def add_connection_lines(stage, connections, stage_name="World"):
    """
    Add simple connection lines between already-instantiated parts.

    Assumes each part prim has an xformOp:translate attribute.
    """

    for i, c in enumerate(connections):
        src = c["from"]["part"]
        dst = c["to"]["part"]

        src_path = f"/{stage_name}/{src}"
        dst_path = f"/{stage_name}/{dst}"

        src_prim = stage.GetPrimAtPath(src_path)
        dst_prim = stage.GetPrimAtPath(dst_path)

        if not src_prim or not dst_prim:
            continue

        src_translate = src_prim.GetAttribute("xformOp:translate").Get()
        dst_translate = dst_prim.GetAttribute("xformOp:translate").Get()

        if src_translate is None or dst_translate is None:
            continue

        src_pos = Gf.Vec3d(*src_translate)
        dst_pos = Gf.Vec3d(*dst_translate)

        line_path = f"/{stage_name}/Connection_{i}"
        line = UsdGeom.BasisCurves.Define(stage, line_path)

        line.CreatePointsAttr([src_pos, dst_pos])
        line.CreateCurveVertexCountsAttr([2])

# from typing import Dict, Any
# from pxr import Usd, UsdGeom, Sdf, Gf


# def build_usd_scene_from_manifest(
#     manifest: Dict[str, Any],
#     *,
#     output_path: str,
#     stage_name: str = "World",
#     verbose: int = 1,
# ) -> str:

#     stage = Usd.Stage.CreateNew(output_path)
#     UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
#     UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    
#     root = UsdGeom.Xform.Define(stage, f"/{stage_name}")

#     for part in manifest["parts"]:
#         name = part["name"]
#         prim_path = f"/{stage_name}/{name}"

#         xform = UsdGeom.Xform.Define(stage, prim_path)
#         prim = xform.GetPrim()

#         cad_path = part.get("cad_path")

#         if cad_path:
#             prim.GetReferences().AddReference(cad_path)

#         pos = part.get("position_m", [0, 0, 0])
#         rot = part.get("rotation_deg", [0, 0, 0])
        
#         # Use XformCommonAPI to avoid duplicate xformOp conflicts with referenced CAD
#         xform_api = UsdGeom.XformCommonAPI(xform)
#         xform_api.SetTranslate(Gf.Vec3d(*pos))
#         xform_api.SetRotate(Gf.Vec3f(*rot), UsdGeom.XformCommonAPI.RotationOrderXYZ)

#         prim.CreateAttribute("part:name", Sdf.ValueTypeNames.String).Set(name)

#         if part.get("material"):
#             prim.CreateAttribute("material", Sdf.ValueTypeNames.String).Set(part["material"])

#         if part.get("attributes"):
#             prim.CreateAttribute("attributes", Sdf.ValueTypeNames.String).Set(str(part["attributes"]))

#         if part.get("dimensions"):
#             prim.CreateAttribute("dimensions", Sdf.ValueTypeNames.String).Set(str(part["dimensions"]))


#         if verbose >= 2:
#             print(f"[USD] Added {name}")
#             print(f"  CAD: {cad_path if cad_path else 'None'}")
#             print(f"  Pos: {pos} | Rot: {rot}")

#     stage.GetRootLayer().Save()

#     if verbose >= 1:
#         print("\n" + "="*50)
#         print(f"[USD] Scene written → {output_path}")
#         print("="*50)

#     return output_path


# def add_connection_lines(stage, connections, stage_name="World"):

#     for i, c in enumerate(connections):
#         src = c["from"]["part"]
#         dst = c["to"]["part"]

#         src_path = f"/{stage_name}/{src}"
#         dst_path = f"/{stage_name}/{dst}"

#         src_prim = stage.GetPrimAtPath(src_path)
#         dst_prim = stage.GetPrimAtPath(dst_path)

#         if not src_prim or not dst_prim:
#             continue

#         # crude placement (center to center)
#         src_pos = Gf.Vec3d(*src_prim.GetAttribute("xformOp:translate").Get())
#         dst_pos = Gf.Vec3d(*dst_prim.GetAttribute("xformOp:translate").Get())

#         line_path = f"/{stage_name}/Connection_{i}"
#         line = UsdGeom.BasisCurves.Define(stage, line_path)

#         line.CreatePointsAttr([src_pos, dst_pos])
#         line.CreateCurveVertexCountsAttr([2])
