from __future__ import annotations

import os, json
from pxr import Usd, UsdGeom, Gf
from typing import Any, Dict, Tuple, Union, List


def set_stage_metadata(stage: Usd.Stage, meters_per_unit: float = 1.0, up_axis: str = "Z") -> None:
    stage.SetMetadata("metersPerUnit", float(meters_per_unit))  # set scale
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z if str(up_axis).upper() == "Z" else UsdGeom.Tokens.y) # set up axis
    # stage.GetRootLayer().Save()     

def make_box_mesh_points_indices(dims_m: Tuple[float, float, float]):
    """
    Rectangular prism centered at origin with (L, W, H) in stage units (metersPerUnit applied at stage level).
    """
    L, W, H = dims_m
    hx, hy, hz = L / 2.0, W / 2.0, H / 2.0

    # 8 vertices of the box 
    pts = [
        Gf.Vec3f(-hx, -hy, -hz),
        Gf.Vec3f(+hx, -hy, -hz),
        Gf.Vec3f(+hx, +hy, -hz),
        Gf.Vec3f(-hx, +hy, -hz),
        Gf.Vec3f(-hx, -hy, +hz),
        Gf.Vec3f(+hx, -hy, +hz),
        Gf.Vec3f(+hx, +hy, +hz),
        Gf.Vec3f(-hx, +hy, +hz),
    ]

    counts = [4, 4, 4, 4, 4, 4] # vertices per face 

    indices = [
        0, 1, 2, 3,   # bottom (-z)
        4, 5, 6, 7,   # top (+z)
        0, 1, 5, 4,   # -y
        3, 2, 6, 7,   # +y
        0, 3, 7, 4,   # -x
        1, 2, 6, 5,   # +x
    ]

    extent = [Gf.Vec3f(-hx, -hy, -hz), Gf.Vec3f(+hx, +hy, +hz)]
    return pts, counts, indices, extent


class JsonVettingError(ValueError):
    pass


def _require(obj: Dict[str, Any], key: str, ctx: str) -> Any:
    if key not in obj:
        raise JsonVettingError(f"Missing required key '{key}' in {ctx}")
    return obj[key]


def _as_float(x: Any, ctx: str) -> float:
    if isinstance(x, (int, float)):
        return float(x)
    raise JsonVettingError(f"Expected number in {ctx}, got {type(x).__name__}: {x!r}")


def _as_str(x: Any, ctx: str) -> str:
    if isinstance(x, str) and x.strip():
        return x
    raise JsonVettingError(f"Expected non-empty string in {ctx}, got: {x!r}")


def _validate_asset_path(p: str, ctx: str) -> str:
    p = _as_str(p, ctx)
    ext = os.path.splitext(p)[1].lower()
    if ext not in [".usd", ".usda", ".usdz"]:
        raise JsonVettingError(f"Bad asset extension in {ctx}: {p!r}")
    return p

def ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def load_parts_json(source: Union[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Accepts:
      - list[dict]: already-parsed JSON
      - str path to a .json file
      - str containing JSON text (if it starts with '[' or '{')
    Returns: list[dict] (your parts array)
    """
    # Already parsed
    if isinstance(source, list):
        return source

    if not isinstance(source, str):
        raise JsonVettingError(f"Expected list or str for JSON source, got {type(source).__name__}")

    s = source.strip()

    # If it's a path to an existing file
    if os.path.exists(s) and os.path.isfile(s):
        with open(s, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        # Otherwise treat as JSON text
        if not (s.startswith("[") or s.startswith("{")):
            raise JsonVettingError(
                "JSON source is a string but is neither a valid file path nor JSON text."
            )
        data = json.loads(s)

    # Normalize top-level: if dict with "parts", use it; else require list
    if isinstance(data, dict) and "parts" in data:
        data = data["parts"]

    if not isinstance(data, list) or not data:
        raise JsonVettingError("Top-level JSON must be a non-empty list of parts (or dict with key 'parts').")

    # Ensure elements are dicts
    if not all(isinstance(x, dict) for x in data):
        raise JsonVettingError("Top-level list must contain only objects/dicts.")

    return data
