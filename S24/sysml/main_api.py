from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from S24.sysml.ast import Model, PartNode

from S24.sysml.parser import parse_sysml
from S24.sysml.evaluator import evaluate_attributes
from S24.jsonio.json_parser import build_part_json

def sysml_to_json(sysml_text: str, *, namespace: str = "lunarspaceport1") -> List[Dict[str, Any]]:
    """
    High-level API:
      SysML text -> parsed model -> evaluated -> flat list JSON with parent/children.
    """
    model: Model = parse_sysml(sysml_text)
    evaluate_attributes(model)

    results: List[Dict[str, Any]] = []

    def emit_part(part: PartNode, parent: Optional[PartNode] = None) -> None:
        obj = build_part_json(part, namespace=namespace)

        if parent is not None:
            obj["parent"] = parent.name

        child_names = [n for n in part.children.keys() if not n.lower().endswith("dims")]
        if child_names:
            obj["children"] = child_names

        results.append(obj)

        for child_name, child in part.children.items():
            if child_name.lower().endswith("dims"):
                continue
            emit_part(child, parent=part)

    for top in model.parts.values():
        emit_part(top, parent=None)

    return results


# def write_json(parts: List[Dict[str, Any]], output_path: str) -> str:
#     """
#     Write a parts list to disk as pretty JSON.
#     Returns output_path.
#     """
#     with open(output_path, "w", encoding="utf-8") as f:
#         json.dump(parts, f, indent=2)
#     return output_path

# ----------------------------------------------------------------------------------------------------------------------------------------

# def sysml_to_materials(sysml_text: str) -> List[Dict[str, Any]]:
#     """
#     Extract materials from SysML as a list of dicts.

#     Heuristic: any PartNode that has attribute 'materialId' is treated as a material entry.
#     (This avoids needing special parsing for 'part def' vs 'part'.)
#     """
#     model: Model = parse_sysml(sysml_text)
#     evaluate_attributes(model)

#     materials: List[Dict[str, Any]] = []

#     def walk(part: PartNode) -> None:
#         attrs = part.attributes_val

#         # Identify a "material" by presence of materialId
#         mat_id = attrs.get("materialId")
#         if isinstance(mat_id, str) and mat_id.strip():
#             mat_obj: Dict[str, Any] = {"materialId": mat_id.strip()}

#             # Export all numeric properties as-is (already in SI in your SysML)
#             for k, v in attrs.items():
#                 if k == "materialId":
#                     continue
#                 if isinstance(v, (int, float)):
#                     mat_obj[k] = float(v)
#                 elif isinstance(v, str) and v.strip():
#                     # keep traceability fields like standard/source
#                     mat_obj[k] = v.strip()

#             materials.append(mat_obj)

#         # Walk children (in case materials are nested, or you later structure them differently)
#         for child_name, child in part.children.items():
#             # ignore dims-like nodes if any
#             if child_name.lower().endswith("dims"):
#                 continue
#             walk(child)

#     for top in model.parts.values():
#         walk(top)

#     return materials


# def write_materials_json(materials: List[Dict[str, Any]], output_path: str) -> str:
#     """
#     Write materials list to disk as pretty JSON.
#     Returns output_path.
#     """
#     with open(output_path, "w", encoding="utf-8") as f:
#         json.dump({"materials": materials}, f, indent=2)
#     return output_path
