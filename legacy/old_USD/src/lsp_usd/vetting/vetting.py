from __future__ import annotations

from lsp_usd.io.json_loader import load_parts_json

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Set, Union

class JsonVettingError(ValueError):
    pass

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

class VettingProc():
    def __init__(self,file: Union[str, List[Dict[str, Any]]]):
        self.parts = load_parts_json(source=file)

        if not isinstance(self.parts, list) or not self.parts:
            raise JsonVettingError("Top-level JSON must be a non-empty list of parts.")
        
        self.by_name = self.validate(self.parts)
        self.reconcile()
        self.biderectional()
        self.graph_val()

    def validate(self,parts: List[Dict[str, Any]]) -> Dict[str, VettedPart]:
        """
        This function performs Phase 1 of the vetting proccess. It validates that required keys exist, and saves them to 
        an extensible object, allowing scalable computations.

        Inputs: 
        parts : Compiled SysML v2 Parts from JSON file.

        Returns:
        by_name : Saved part information by name, to a dictionary Dict[str, VettedPart], where VettedPart is an extensible object containing part info.
        """
        
        by_name: Dict[str, VettedPart] = {} 

        for i, p in enumerate(parts):
            if not isinstance(p, dict):
                raise JsonVettingError(f"Part at index {i} is not an object/dict.")

            ctx = f"part[{i}]" # contexts string for errors
            
            name = _as_str(_require(p, "name", ctx), f"{ctx}.name") # checks name exist in p dictionary, check the value is not an empty string,strips whitespaces
            uid = _as_str(_require(p, "id", ctx), f"{ctx}.id") # same as name
            ptype = str(p.get("type", "Part"))

            if name in by_name:
                raise JsonVettingError(f"Duplicate part name '{name}' (names must be unique).")

            dims_obj = _require(p, "dimensions", ctx)
            if not isinstance(dims_obj, dict):
                raise JsonVettingError(f"{ctx}.dimensions must be an object/dict.")

            dims_list = _require(dims_obj, "dims_m", f"{ctx}.dimensions")
            if not (isinstance(dims_list, list) and len(dims_list) == 3):
                raise JsonVettingError(f"{ctx}.dimensions.dims_m must be a list of length 3.")
            
            dims_m = tuple(_as_float(dims_list[j], f"{ctx}.dimensions.dims_m[{j}]") for j in range(3))  # type: ignore
            if any(d <= 0 for d in dims_m):
                raise JsonVettingError(f"{ctx}.dimensions.dims_m must be > 0, got {dims_m}")

            meters_per_unit = _as_float(dims_obj.get("metersPerUnit", 1.0), f"{ctx}.dimensions.metersPerUnit")
            up_axis = str(dims_obj.get("upAxis", "Z")).upper()
            if up_axis not in ("Z", "Y"):
                raise JsonVettingError(f"{ctx}.dimensions.upAxis must be 'Z' or 'Y', got {up_axis!r}")

            tx = _as_float(dims_obj.get("X", 0.0), f"{ctx}.dimensions.X")
            ty = _as_float(dims_obj.get("Y", 0.0), f"{ctx}.dimensions.Y")
            tz = _as_float(dims_obj.get("Z", 0.0), f"{ctx}.dimensions.Z")
            translate = (tx, ty, tz)

            meta = _require(p, "metadata", ctx)
            if not isinstance(meta, dict):
                raise JsonVettingError(f"{ctx}.metadata must be an object/dict.")
            geom_path = _validate_asset_path(_require(meta, "geometry", f"{ctx}.metadata"), f"{ctx}.metadata.geometry")
            material_path = _validate_asset_path(_require(meta, "material", f"{ctx}.metadata"), f"{ctx}.metadata.material")

            parent = p.get("parent", None)
            parent = _as_str(parent, f"{ctx}.parent") if parent is not None else None

            children = p.get("children", [])
            if children is None:
                children = []
            if not isinstance(children, list) or not all(isinstance(c, str) for c in children):
                raise JsonVettingError(f"{ctx}.children must be a list of strings.")
            children = [c for c in children if c.strip()]

            by_name[name] = VettedPart(
                raw=p,
                name=name,
                uid=uid,
                ptype=ptype,
                dims_m=dims_m,
                meters_per_unit=meters_per_unit,
                up_axis=up_axis,
                translate=translate,
                geom_path=geom_path,
                material_path=material_path,
                parent=parent,
                children=children,
            )
        return by_name
    
    def reconcile(self):
        """
        ....
        
        Second pass: hierarchy reconciliation + existence checks
        Pass 2: Phase A -> Ensure all referenced parents/children exist.
        """
        for name, vp in self.by_name.items(): # this checks that every part the declares parent/childern, that pparent/children actually exists
            if vp.parent and vp.parent not in self.by_name:
                raise JsonVettingError(f"Part '{name}' references missing parent '{vp.parent}'.")

            for c in vp.children:
                if c not in self.by_name:
                    raise JsonVettingError(f"Part '{name}' lists missing child '{c}'.")

    def biderectional(self):
        """
        .....
        
        Pass 2 : Phase B -> Bidirectional reconciliation: make parent and children consistent
        Reconcile parent<->children bidirectionally
        (mutate dataclasses safely by reassigning)
        Add missing child links to parent based on child's parent
        If child says it has a parent, the parent’s children list must include the child
        Why by_name.items() ?
        You are mutating (appending to) children lists while iterating. Iterating a dict view while mutating nested objects 
        is usually okay, but converting to a list makes the iteration snapshot stable and avoids subtle issues.
        """

        for name, vp in list(self.by_name.items()):
            if vp.parent:
                p = self.by_name[vp.parent]
                if name not in p.children:
                    p.children.append(name)

        # Add missing parent links to child based on parent's children
        #If parent lists a child, ensure the child agrees:
        #if child has no parent set → set it to this parent.
        # If child already has a parent:
            #if it matches → OK
            #if it differs → contradiction → error

        for name, vp in list(self.by_name.items()):
            for c in vp.children:
                child = self.by_name[c]
                if child.parent is None:
                    child.parent = name
                elif child.parent != name:
                    raise JsonVettingError(
                        f"Child '{c}' has parent '{child.parent}' but is also listed under '{name}'."
                    )

    def graph_val(self):
        """
        .... 
        
        Pass 2: Phase C -> Global graph validity, Cycle check via DFS
        visiting : nodes currently on the recursion stack ("gray")
        visited : nodes fully processed ("black")
        """
        def dfs(node: str, visiting: Set[str], visited: Set[str]) -> None:

            if node in visiting:
                raise JsonVettingError(f"Cycle detected in hierarchy at '{node}'.")
            
            if node in visited:
                return
            
            visiting.add(node)
            for ch in self.by_name[node].children:
                dfs(ch, visiting, visited)

            visiting.remove(node)
            visited.add(node)

        roots = [n for n, vp in self.by_name.items() if vp.parent is None]
        if not roots:
            raise JsonVettingError("No root found (every part has a parent).")

        visited: Set[str] = set()
        for r in roots:
            dfs(r, set(), visited)
        
        if len(visited) != len(self.by_name):
            unreachable = [n for n in self.by_name if n not in visited]
            raise JsonVettingError(f"Unreachable parts (not under any root): {unreachable}")# Vetting logic (VettedPart, JsonVettingError, VettingProc)
