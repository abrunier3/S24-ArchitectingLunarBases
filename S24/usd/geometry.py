from __future__ import annotations

from typing import Tuple, List

from pxr import Usd, UsdGeom, Gf


def make_box_mesh(dims_m: Tuple[float, float, float]):
    """
    Make a simple box mesh centered at origin.
    Returns: (points, face_counts, face_indices, extent)
    """
    L, W, H = float(dims_m[0]), float(dims_m[1]), float(dims_m[2])
    hx, hy, hz = L / 2.0, W / 2.0, H / 2.0

    points = [
        Gf.Vec3f(-hx, -hy, -hz),
        Gf.Vec3f(+hx, -hy, -hz),
        Gf.Vec3f(+hx, +hy, -hz),
        Gf.Vec3f(-hx, +hy, -hz),
        Gf.Vec3f(-hx, -hy, +hz),
        Gf.Vec3f(+hx, -hy, +hz),
        Gf.Vec3f(+hx, +hy, +hz),
        Gf.Vec3f(-hx, +hy, +hz),
    ]

    face_counts: List[int] = [4, 4, 4, 4, 4, 4]
    face_indices: List[int] = [
        0, 1, 2, 3,   # bottom
        4, 5, 6, 7,   # top
        0, 1, 5, 4,   # -y
        3, 2, 6, 7,   # +y
        0, 3, 7, 4,   # -x
        1, 2, 6, 5,   # +x
    ]

    extent = [Gf.Vec3f(-hx, -hy, -hz), Gf.Vec3f(+hx, +hy, +hz)]
    return points, face_counts, face_indices, extent


def author_box_geom_layer(
    *,
    geom_path: str,
    prim_name: str,
    dims_m: Tuple[float, float, float],
    meters_per_unit: float,
    up_axis: str,
) -> str:
    """
    Create a geometry layer that defines a single Mesh at /<prim_name>.
    Returns the written geom_path.
    """
    stage = Usd.Stage.CreateNew(geom_path)

    from .utils import set_stage_metadata
    set_stage_metadata(stage, meters_per_unit=meters_per_unit, up_axis=up_axis)

    pts, counts, indices, extent = make_box_mesh(dims_m)

    mesh = UsdGeom.Mesh.Define(stage, f"/{prim_name}")
    mesh.CreatePointsAttr(pts)
    mesh.CreateFaceVertexCountsAttr(counts)
    mesh.CreateFaceVertexIndicesAttr(indices)
    mesh.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
    mesh.CreateExtentAttr(extent)

    stage.SetDefaultPrim(mesh.GetPrim())
    stage.GetRootLayer().Save()
    return geom_path
