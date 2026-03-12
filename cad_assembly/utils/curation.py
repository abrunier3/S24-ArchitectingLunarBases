import sys, os
sys.path.insert(0, "/home/ang/usd_ang/lib/python")
os.environ["LD_LIBRARY_PATH"] = "/home/ang/usd_ang/lib"

import argparse
from pxr import Usd, UsdGeom, UsdShade, Sdf, Gf

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def stage_meters_per_unit(stage: Usd.Stage) -> float:
    """
    This function returns the 
    """
    mpu = UsdGeom.GetStageMetersPerUnit(stage)
    return float(mpu) if mpu else 1.0


def find_first_mesh_prims_under_defaultprim(stage: Usd.Stage):
    """
    This function locates the defult prim and all the Usd.Geom Meshes prims.
    """
    dp = stage.GetDefaultPrim()
    if not dp:
        # fallback: first child of pseudo-root
        kids = stage.GetPseudoRoot().GetChildren()
        if not kids:
            raise RuntimeError("Stage has no defaultPrim and no root children.")
        dp = kids[0]

    meshes = []
    for prim in Usd.PrimRange(dp):
        if prim.IsA(UsdGeom.Mesh):
            meshes.append(prim)
    if not meshes:
        raise RuntimeError("No UsdGeom.Mesh prims found under defaultPrim.")
    return dp, meshes

def bake_mesh_points_to_world(stage: Usd.Stage, mesh_prim: Usd.Prim, xfcache: UsdGeom.XformCache):
    """
    Returns baked world-space points (as list of Gf.Vec3f) and copy of topology/primvars.
    """
    mesh = UsdGeom.Mesh(mesh_prim)
    pts = mesh.GetPointsAttr().Get()
    if pts is None:
        raise RuntimeError(f"{mesh_prim.GetPath()} has no points.")

    M = xfcache.GetLocalToWorldTransform(mesh_prim)  # Gf.Matrix4d

    baked_pts = []
    for p in pts:
        pw = M.Transform(Gf.Vec3d(p[0], p[1], p[2]))
        baked_pts.append(Gf.Vec3f(float(pw[0]), float(pw[1]), float(pw[2])))

    # Topology
    fvc = mesh.GetFaceVertexCountsAttr().Get()
    fvi = mesh.GetFaceVertexIndicesAttr().Get()
    if fvc is None or fvi is None:
        raise RuntimeError(f"{mesh_prim.GetPath()} missing face topology.")

    # Common attrs to preserve
    extent = mesh.GetExtentAttr().Get()
    subdiv = mesh.GetSubdivisionSchemeAttr().Get()
    doublesided = mesh.GetDoubleSidedAttr().Get()

    # Primvars (UVs etc)
    primvars_api = UsdGeom.PrimvarsAPI(mesh_prim)
    primvars = {}
    for pv in primvars_api.GetPrimvars():
        name = pv.GetName()
        primvars[name] = {
            "typeName": pv.GetTypeName(),
            "interpolation": pv.GetInterpolation(),
            "elementSize": pv.GetElementSize(),
            "value": pv.Get(),
            "indices": pv.GetIndices() if pv.IsIndexed() else None,
        }

    return {
        "points": baked_pts,
        "faceVertexCounts": fvc,
        "faceVertexIndices": fvi,
        "extent": extent,
        "subdivisionScheme": subdiv,
        "doubleSided": doublesided,
        "primvars": primvars,
    }


def scale_points_inplace(points, s: float):
    # points: list[Gf.Vec3f]
    for i in range(len(points)):
        p = points[i]
        points[i] = Gf.Vec3f(p[0] * s, p[1] * s, p[2] * s)



def find_texture_by_keywords(stage, material_path, keywords):
    """
    Search for a UsdUVTexture shader under the material whose name
    contains one of the provided keywords.
    """

    for prim in stage.Traverse():

        if not prim.GetPath().HasPrefix(material_path):
            continue

        if prim.GetTypeName() != "Shader":
            continue

        id_attr = prim.GetAttribute("info:id")
        if not id_attr:
            continue

        if id_attr.Get() != "UsdUVTexture":
            continue

        name = prim.GetName().lower()

        for k in keywords:
            if k in name:
                attr = prim.GetAttribute("inputs:file")
                if attr:
                    return attr.Get()

    return None

def build_preview_surface_material_from_source(
    source_stage,
    source_material_path,
    dest_stage,
    dest_material_path,
    uv_primvar_name="st",
):
    src_mat_prim = source_stage.GetPrimAtPath(source_material_path)
    if not src_mat_prim.IsValid():
        raise RuntimeError(f"Source material not found: {source_material_path}")

    def get_tex_file(shader_name: str):
        sp = source_stage.GetPrimAtPath(f"{source_material_path}/{shader_name}")
        if not sp.IsValid():
            return None
        a = sp.GetAttribute("inputs:file")
        return a.Get() if a else None
    
    base_tex = find_texture_by_keywords(
        source_stage,
        src_mat_prim.GetPath(),
        ["base", "diff", "albedo", "color"]
    )

    metal_tex = find_texture_by_keywords(
        source_stage,
        src_mat_prim.GetPath(),
        ["metal"]
    )

    rough_tex = find_texture_by_keywords(
        source_stage,
        src_mat_prim.GetPath(),
        ["rough"]
    )

    norm_tex = find_texture_by_keywords(
        source_stage,
        src_mat_prim.GetPath(),
        ["normal"]
    )

    occ_tex = find_texture_by_keywords(
        source_stage,
        src_mat_prim.GetPath(),
        ["occlusion", "ao"]
)

    if base_tex is None:
        print(f"[WARNING] No base color texture found in {source_material_path}. Using gray.")

    # Material
    dest_mat = UsdShade.Material.Define(dest_stage, dest_material_path)

    # Primvar reader
    st_reader = UsdShade.Shader.Define(dest_stage, f"{dest_material_path}/stReader")
    st_reader.CreateIdAttr("UsdPrimvarReader_float2")
    st_reader.CreateInput("varname", Sdf.ValueTypeNames.Token).Set(uv_primvar_name)
    st_reader.CreateOutput("result", Sdf.ValueTypeNames.Float2)   # <-- IMPORTANT

    def make_uvtex(name: str, file_asset, is_normal=False):
        sh = UsdShade.Shader.Define(dest_stage, f"{dest_material_path}/{name}")
        sh.CreateIdAttr("UsdUVTexture")
        sh.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(file_asset)

        st_input = sh.CreateInput("st", Sdf.ValueTypeNames.Float2)
        st_input.ConnectToSource(st_reader.GetOutput("result"))

        sh.CreateInput("wrapS", Sdf.ValueTypeNames.Token).Set("repeat")
        sh.CreateInput("wrapT", Sdf.ValueTypeNames.Token).Set("repeat")

        if is_normal:
            sh.CreateInput("sourceColorSpace", Sdf.ValueTypeNames.Token).Set("raw")
            sh.CreateInput("bias", Sdf.ValueTypeNames.Float4).Set(Gf.Vec4f(-1, -1, -1, -1))
            sh.CreateInput("scale", Sdf.ValueTypeNames.Float4).Set(Gf.Vec4f(2, 2, 2, 2))

        # Create outputs explicitly
        sh.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)
        sh.CreateOutput("r", Sdf.ValueTypeNames.Float)
        sh.CreateOutput("a", Sdf.ValueTypeNames.Float)

        return sh

    tex_base = None
    if base_tex:
        tex_base = make_uvtex("tex_base", base_tex, is_normal=False)    
    tex_metal = make_uvtex("tex_metallic", metal_tex, is_normal=False) if metal_tex else None
    tex_rough = make_uvtex("tex_roughness", rough_tex, is_normal=False) if rough_tex else None
    tex_norm  = make_uvtex("tex_normal", norm_tex, is_normal=True) if norm_tex else None
    tex_occ   = make_uvtex("tex_occlusion", occ_tex, is_normal=False) if occ_tex else None

    # Preview surface
    pbr = UsdShade.Shader.Define(dest_stage, f"{dest_material_path}/pbr")
    pbr.CreateIdAttr("UsdPreviewSurface")

    pbr.CreateOutput("surface", Sdf.ValueTypeNames.Token)  # explicit output

    diff = pbr.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f)

    if base_tex:
        diff.ConnectToSource(tex_base.GetOutput("rgb"))
    else:
        diff.Set(Gf.Vec3f(0.7, 0.7, 0.7))

    if tex_metal:
        metal = pbr.CreateInput("metallic", Sdf.ValueTypeNames.Float)
        metal.ConnectToSource(tex_metal.GetOutput("r"))
    else:
        pbr.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)

    if tex_rough:
        rough = pbr.CreateInput("roughness", Sdf.ValueTypeNames.Float)
        rough.ConnectToSource(tex_rough.GetOutput("r"))
    else:
        pbr.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(1.0)

    if tex_norm:
        norm = pbr.CreateInput("normal", Sdf.ValueTypeNames.Normal3f)
        norm.ConnectToSource(tex_norm.GetOutput("rgb"))
    else:
        pbr.CreateInput("normal", Sdf.ValueTypeNames.Normal3f).Set(Gf.Vec3f(0, 0, 1))

    if tex_occ:
        occ = pbr.CreateInput("occlusion", Sdf.ValueTypeNames.Float)
        occ.ConnectToSource(tex_occ.GetOutput("r"))
    else:
        pbr.CreateInput("occlusion", Sdf.ValueTypeNames.Float).Set(1.0)

    pbr.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0, 0, 0))

    # Bind the material output
    dest_mat.CreateSurfaceOutput().ConnectToSource(pbr.GetOutput("surface"))

    return dest_mat

def find_first_material(stage):
    for prim in stage.Traverse():
        if prim.IsA(UsdShade.Material):
            return prim.GetPath()
    raise RuntimeError("No material found in stage.")


def curate_asset(input_usda: str, out_dir: str, name: str):

    ensure_dir(out_dir)

    geo_path = os.path.join(out_dir, f"{name}_geometry.usda")
    mat_path = os.path.join(out_dir, f"{name}_material.usda")
    cmp_path = os.path.join(out_dir, f"{name}_component.usda")

    src = Usd.Stage.Open(input_usda)
    if not src:
        raise RuntimeError(f"Failed to open {input_usda}")

    src_mpu = stage_meters_per_unit(src)

    # find meshes
    default_prim, meshes = find_first_mesh_prims_under_defaultprim(src)

    # transform cache
    xfcache = UsdGeom.XformCache(Usd.TimeCode.Default())

    geo = Usd.Stage.CreateNew(geo_path)
    UsdGeom.SetStageUpAxis(geo, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(geo, 1.0)

    geo.SetDefaultPrim(geo.DefinePrim("/geo", "Xform"))

    for i, mprim in enumerate(meshes):

        baked = bake_mesh_points_to_world(src, mprim, xfcache)

        scale_points_inplace(baked["points"], src_mpu)

        mesh_name = mprim.GetName()

        if not mesh_name:
            mesh_name = f"part_{i+1}"
        
        mesh_name = mesh_name.replace(" ", "_")

        dst_mesh = UsdGeom.Mesh.Define(geo, f"/geo/{mesh_name}")

        dst_mesh.GetPointsAttr().Set(baked["points"])
        dst_mesh.GetFaceVertexCountsAttr().Set(baked["faceVertexCounts"])
        dst_mesh.GetFaceVertexIndicesAttr().Set(baked["faceVertexIndices"])

        if baked["doubleSided"] is not None:
            dst_mesh.GetDoubleSidedAttr().Set(bool(baked["doubleSided"]))

        if baked["subdivisionScheme"] is not None:
            dst_mesh.GetSubdivisionSchemeAttr().Set(baked["subdivisionScheme"])

        # compute extent
        pts = baked["points"]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        zs = [p[2] for p in pts]

        dst_mesh.GetExtentAttr().Set([
            Gf.Vec3f(min(xs), min(ys), min(zs)),
            Gf.Vec3f(max(xs), max(ys), max(zs))
        ])

        # copy primvars
        pv_api = UsdGeom.PrimvarsAPI(dst_mesh.GetPrim())

        for pv_name, pv in baked["primvars"].items():

            if pv["value"] is None:
                continue

            primvar = pv_api.CreatePrimvar(
                pv_name,
                pv["typeName"],
                pv["interpolation"],
                pv["elementSize"]
            )

            primvar.Set(pv["value"])

            if pv["indices"] is not None:
                primvar.SetIndices(pv["indices"])

    geo.GetRootLayer().Save()

    mat = Usd.Stage.CreateNew(mat_path)

    UsdGeom.SetStageUpAxis(mat, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(mat, 1.0)

    mat.SetDefaultPrim(mat.DefinePrim("/materials", "Scope"))

    build_preview_surface_material_from_source(
        source_stage=src,
        source_material_path = find_first_material(src),
        dest_stage=mat,
        dest_material_path="/materials/surface",
        uv_primvar_name="st",
    )

    mat.GetRootLayer().Save()

    cmp = Usd.Stage.CreateNew(cmp_path)

    UsdGeom.SetStageUpAxis(cmp, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(cmp, 1.0)

    root = UsdGeom.Xform.Define(cmp, f"/{name}").GetPrim()

    cmp.SetDefaultPrim(root)

    geo_prim = cmp.DefinePrim(f"/{name}/geo", "Xform")
    geo_prim.GetReferences().AddReference(os.path.basename(geo_path))

    mat_prim = cmp.DefinePrim(f"/{name}/materials", "Scope")
    mat_prim.GetReferences().AddReference(os.path.basename(mat_path))

    mat_path_in_component = Sdf.Path(f"/{name}/materials/surface")
    mat_obj = UsdShade.Material(cmp.GetPrimAtPath(mat_path_in_component))

    if not mat_obj or not mat_obj.GetPrim().IsValid():
        raise RuntimeError(f"Material not found in component stage at {mat_path_in_component}")

    for p in Usd.PrimRange(cmp.GetPrimAtPath(f"/{name}/geo")):
        if p.IsA(UsdGeom.Mesh):
            UsdShade.MaterialBindingAPI.Apply(p).Bind(mat_obj)

    cmp.GetRootLayer().Save()

    print("Wrote:")
    print(" ", geo_path)
    print(" ", mat_path)
    print(" ", cmp_path)