from __future__ import annotations
import json
from pxr import Usd, UsdShade, Sdf

def generate_material_library(materials_json_path: str, output_usda_path: str) -> str:
    """
    Read materials.json and generate a USD material library with customData.
    """
    with open(materials_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    materials = data.get("materials", [])

    stage = Usd.Stage.CreateNew(output_usda_path)
    stage.SetMetadata("defaultPrim", "Materials")

    scope = stage.DefinePrim("/Materials", "Scope")

    for mat in materials:
        mat_id = mat["materialId"]
        prim_path = f"/Materials/{mat_id}"
        mat_prim = UsdShade.Material.Define(stage, prim_path).GetPrim()

        # Write all properties as customData
        for key, value in mat.items():
            if key == "materialId":
                continue
            if isinstance(value, (int, float)):
                mat_prim.SetCustomDataByKey(key, float(value))
            elif isinstance(value, str):
                mat_prim.SetCustomDataByKey(key, value)

    stage.GetRootLayer().Save()
    return output_usda_path