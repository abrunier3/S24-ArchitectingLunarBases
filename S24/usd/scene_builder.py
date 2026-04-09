from typing import Dict, Any
from pxr import Usd, UsdGeom, Sdf, Gf


def build_usd_scene_from_manifest(
    manifest: Dict[str, Any],
    *,
    output_path: str,
    stage_name: str = "World",
    verbose: int = 1,
) -> str:

    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)

    root = UsdGeom.Xform.Define(stage, f"/{stage_name}")

    for part in manifest["parts"]:
        name = part["name"]
        prim_path = f"/{stage_name}/{name}"

        xform = UsdGeom.Xform.Define(stage, prim_path)
        prim = xform.GetPrim()

        cad_path = part.get("cad_path")

        if cad_path:
            prim.GetReferences().AddReference(cad_path)

        pos = part.get("position_m", [0, 0, 0])
        rot = part.get("rotation_deg", [0, 0, 0])

        xform.AddTranslateOp().Set(Gf.Vec3d(*pos))
        xform.AddRotateXYZOp().Set(Gf.Vec3f(*rot))

        prim.CreateAttribute("part:name", Sdf.ValueTypeNames.String).Set(name)

        if part.get("material"):
            prim.CreateAttribute("material", Sdf.ValueTypeNames.String).Set(part["material"])

        if part.get("attributes"):
            prim.CreateAttribute("attributes", Sdf.ValueTypeNames.String).Set(str(part["attributes"]))

        if part.get("dimensions"):
            prim.CreateAttribute("dimensions", Sdf.ValueTypeNames.String).Set(str(part["dimensions"]))


        if verbose >= 2:
            print(f"[USD] Added {name}")
            print(f"  CAD: {cad_path if cad_path else 'None'}")
            print(f"  Pos: {pos} | Rot: {rot}")

    stage.GetRootLayer().Save()

    if verbose >= 1:
        print("\n" + "="*50)
        print(f"[USD] Scene written → {output_path}")
        print("="*50)

    return output_path


def add_connection_lines(stage, connections, stage_name="World"):

    for i, c in enumerate(connections):
        src = c["from"]["part"]
        dst = c["to"]["part"]

        src_path = f"/{stage_name}/{src}"
        dst_path = f"/{stage_name}/{dst}"

        src_prim = stage.GetPrimAtPath(src_path)
        dst_prim = stage.GetPrimAtPath(dst_path)

        if not src_prim or not dst_prim:
            continue

        # crude placement (center to center)
        src_pos = Gf.Vec3d(*src_prim.GetAttribute("xformOp:translate").Get())
        dst_pos = Gf.Vec3d(*dst_prim.GetAttribute("xformOp:translate").Get())

        line_path = f"/{stage_name}/Connection_{i}"
        line = UsdGeom.BasisCurves.Define(stage, line_path)

        line.CreatePointsAttr([src_pos, dst_pos])
        line.CreateCurveVertexCountsAttr([2])