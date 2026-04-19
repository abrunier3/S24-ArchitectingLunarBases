from __future__ import annotations
from typing import Any, Dict, List, Optional

from S24.sysml.ast import Model, PartNode
from S24.sysml.parser import parse_sysml, _print_model_un
from S24.sysml.evaluator import evaluate_attributes, _print_model_with_values
#-----
from S24.jsonio.json_parser import build_part_json_representation, build_connections_json, validate_connections

def sysml_to_json_transformer(
    verbose: int,
    sysml_text: str,
    namespace: str = "lunarspaceport1",
    validate: bool = True,
) -> Dict[str, Any]:

    # parse the sysml text into a structured python object: Model 
    model: Model = parse_sysml(sysml_text)
    # evaluate model's expressions
    evaluate_attributes(model)

    parts: List[Dict[str, Any]] = []
    for top in model.parts.values():
        _emit_part_recursive(top, parts, namespace=namespace)

    connections = build_connections_json(model)

    # validate connections and interfaces
    validation_errors = []
    if validate:
        validation_errors = validate_connections(model)

    # print parsed model 
    if verbose>1:
        _print_model_un(model=model)
        _print_model_with_values(model=model)
        
    return {
        "metadata": {
            "package": model.package_name,
            "num_parts": len(parts),
            "num_connections": len(connections),
            "validation_errors": validation_errors,
        },
        "parts": parts,
        "connections": connections,
    }

#-------------------------------------------------------------------------------------------------
# Helpers
def _emit_part_recursive(
    part: PartNode,
    parts: List[Dict[str, Any]],
    *,
    namespace: str,
    parent: Optional[PartNode] = None,
) -> None:

    obj = build_part_json_representation(part, namespace=namespace)

    if parent is not None:
        obj["parent"] = parent.name

    child_names = [
        n for n in part.children.keys()
        if not n.lower().endswith("dims")
    ]
    if child_names:
        obj["children"] = child_names

    parts.append(obj)

    for child_name, child in part.children.items():
        if child_name.lower().endswith("dims"):
            continue
        _emit_part_recursive(child, parts, namespace=namespace, parent=part)

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



