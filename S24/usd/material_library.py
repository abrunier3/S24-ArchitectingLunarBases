from __future__ import annotations
import json
import os
from pxr import Usd, UsdShade, Sdf

def generate_material_library(materials_json_path: str, output_usda_path: str) -> str:
    with open(materials_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    materials = data.get("materials", [])

    # Work in memory to avoid USD layer cache issues
    stage = Usd.Stage.CreateInMemory()
    stage.SetMetadata("defaultPrim", "Materials")

    scope = stage.DefinePrim("/Materials", "Scope")

    for mat in materials:
        mat_id = mat["materialId"]
        prim_path = f"/Materials/{mat_id}"
        mat_prim = UsdShade.Material.Define(stage, prim_path).GetPrim()

        for key, value in mat.items():
            if key == "materialId":
                continue
            if isinstance(value, (int, float)):
                mat_prim.SetCustomDataByKey(key, float(value))
            elif isinstance(value, str):
                mat_prim.SetCustomDataByKey(key, value)

    # Export to file (overwrites safely)
    stage.GetRootLayer().Export(output_usda_path)
    return output_usda_path