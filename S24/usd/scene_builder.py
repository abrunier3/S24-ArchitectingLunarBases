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

        if cad_path:
            cad_ref_path = _make_usd_reference_path(
                cad_path,
                output_path=str(output_path_obj),
                repo_root=repo_root,
            )
            prim.GetReferences().AddReference(cad_ref_path)

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
