from __future__ import annotations

from pxr import Usd, UsdShade, Sdf, Gf


def author_preview_material_layer(
    *,
    mat_path: str,
    material_name: str,
    meters_per_unit: float,
    up_axis: str,
    diffuse: tuple[float, float, float] = (0.7, 0.7, 0.7),
    metallic: float = 0.9,
    roughness: float = 0.35,
) -> str:
    """
    Create a material layer with a single UsdPreviewSurface material at:
      /Materials/<material_name>
    Returns written mat_path.
    """
    stage = Usd.Stage.CreateNew(mat_path)

    from .utils import set_stage_metadata
    set_stage_metadata(stage, meters_per_unit=meters_per_unit, up_axis=up_axis)

    mat_prim_path = Sdf.Path(f"/Materials/{material_name}")
    material = UsdShade.Material.Define(stage, mat_prim_path)

    shader = UsdShade.Shader.Define(stage, mat_prim_path.AppendChild("PreviewSurface"))
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*diffuse))
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(float(metallic))
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(float(roughness))

    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")

    stage.SetDefaultPrim(material.GetPrim())
    stage.GetRootLayer().Save()
    return mat_path
