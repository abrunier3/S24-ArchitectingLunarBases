from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Tuple

from .errors import JsonVettingError
from .loader import load_parts_json

@dataclass
class VettedPart:
    raw: Dict[str, Any]

    name: str
    uid: str
    ptype: str

    dims_m: Tuple[float, float, float]
    meters_per_unit: float
    up_axis: str
    translate: Tuple[float, float, float]

    geom_path: str
    material_path: str

    parent: Optional[str]
    children: List[str]

def _require(d: dict, key: str, ctx: str):
    if key not in d:
        raise JsonVettingError(f"{ctx}: missing required key '{key}'")
    return d[key]


def _as_float(v: Any, ctx: str) -> float:
    try:
        return float(v)
    except Exception:
        raise JsonVettingError(f"{ctx}: expected float, got {v!r}")


def _as_str(v: Any, ctx: str) -> str:
    if not isinstance(v, str) or not v.strip():
        raise JsonVettingError(f"{ctx}: expected non-empty string")
    return v.strip()


def _validate_asset_path(p: Any, ctx: str) -> str:
    p = _as_str(p, ctx)
    if not p.endswith(".usd") and not p.endswith(".usda"):
        raise JsonVettingError(f"{ctx}: asset path must be .usd/.usda")
    return p

class VettingProc:
    def __init__(self, source):
        parts = load_parts_json(source)

        if not isinstance(parts, list) or not parts:
            raise JsonVettingError("Top-level JSON must be a non-empty list")

        self.by_name: Dict[str, VettedPart] = self._validate(parts)
        self._reconcile()
        self._bidirectional()
        self._validate_graph()

    def _validate(self, parts: List[dict]) -> Dict[str, VettedPart]:
        by_name: Dict[str, VettedPart] = {}

        for i, p in enumerate(parts):
            ctx = f"part[{i}]"

            name = _as_str(_require(p, "name", ctx), f"{ctx}.name")
            uid  = _as_str(_require(p, "id", ctx), f"{ctx}.id")
            ptype = str(p.get("type", "Part"))

            if name in by_name:
                raise JsonVettingError(f"Duplicate part name '{name}'")

            dims = _require(p, "dimensions", ctx)
            dims_m = _require(dims, "dims_m", f"{ctx}.dimensions")
            if not isinstance(dims_m, list) or len(dims_m) != 3:
                raise JsonVettingError(f"{ctx}.dimensions.dims_m must be length 3")

            dims_m = tuple(_as_float(dims_m[j], f"{ctx}.dims_m[{j}]") for j in range(3))

            translate = (
                _as_float(dims.get("X", 0.0), f"{ctx}.X"),
                _as_float(dims.get("Y", 0.0), f"{ctx}.Y"),
                _as_float(dims.get("Z", 0.0), f"{ctx}.Z"),
            )

            meta = _require(p, "metadata", ctx)
            geom = _validate_asset_path(_require(meta, "geometry", ctx), f"{ctx}.geometry")
            mat  = _validate_asset_path(_require(meta, "material", ctx), f"{ctx}.material")

            by_name[name] = VettedPart(
                raw=p,
                name=name,
                uid=uid,
                ptype=ptype,
                dims_m=dims_m,
                meters_per_unit=float(dims.get("metersPerUnit", 1.0)),
                up_axis=str(dims.get("upAxis", "Z")).upper(),
                translate=translate,
                geom_path=geom,
                material_path=mat,
                parent=p.get("parent"),
                children=list(p.get("children", [])),
            )

        return by_name

    def _reconcile(self):
        for name, vp in self.by_name.items():
            if vp.parent and vp.parent not in self.by_name:
                raise JsonVettingError(f"{name} references missing parent {vp.parent}")
            for c in vp.children:
                if c not in self.by_name:
                    raise JsonVettingError(f"{name} lists missing child {c}")

    def _bidirectional(self):
        for name, vp in list(self.by_name.items()):
            if vp.parent:
                p = self.by_name[vp.parent]
                if name not in p.children:
                    p.children.append(name)

        for name, vp in list(self.by_name.items()):
            for c in vp.children:
                child = self.by_name[c]
                if child.parent is None:
                    child.parent = name
                elif child.parent != name:
                    raise JsonVettingError(
                        f"Conflict: {c} has parent {child.parent} and {name}"
                    )

    def _validate_graph(self):
        visited = set()
        visiting = set()

        def dfs(n):
            if n in visiting:
                raise JsonVettingError(f"Cycle detected at {n}")
            if n in visited:
                return
            visiting.add(n)
            for c in self.by_name[n].children:
                dfs(c)
            visiting.remove(n)
            visited.add(n)

        roots = [n for n, vp in self.by_name.items() if vp.parent is None]
        if not roots:
            raise JsonVettingError("No root part found")

        for r in roots:
            dfs(r)

        if len(visited) != len(self.by_name):
            raise JsonVettingError("Unreachable parts exist")
