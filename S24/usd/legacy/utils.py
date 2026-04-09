from __future__ import annotations

import os
from typing import Tuple

from pxr import Usd, UsdGeom


def set_stage_metadata(stage: Usd.Stage, *, meters_per_unit: float, up_axis: str) -> None:
    """
    Set stage-level metadata (units + up axis).
    """
    stage.SetMetadata("metersPerUnit", float(meters_per_unit))
    up = up_axis.upper()
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z if up == "Z" else UsdGeom.Tokens.y)


def ensure_can_write(path: str, *, overwrite: bool) -> None:
    """
    Ensure parent directory exists. If overwrite=False and file exists, raise.
    """
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    if (not overwrite) and os.path.exists(path):
        raise FileExistsError(f"File exists and overwrite=False: {path}")


def ref_path(target_path: str, authored_layer_path: str) -> str:
    """
    Return a path to target_path relative to authored_layer_path directory.
    Keeps USD references stable regardless of working directory.
    """
    base_dir = os.path.dirname(os.path.abspath(authored_layer_path))
    return os.path.relpath(os.path.abspath(target_path), start=base_dir)


def sanitize_usd_name(name: str) -> str:
    """
    Minimal name sanitizer for prim names (USD is strict).
    """
    out = []
    for ch in name:
        if ch.isalnum() or ch == "_":
            out.append(ch)
        else:
            out.append("_")
    s = "".join(out)
    if not s:
        return "Prim"
    if s[0].isdigit():
        s = "_" + s
    return s


def split_dims(dims_m: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """
    Ensure dims are floats.
    """
    return (float(dims_m[0]), float(dims_m[1]), float(dims_m[2]))
