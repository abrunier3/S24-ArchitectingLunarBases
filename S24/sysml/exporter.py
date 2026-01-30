from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .parser import Model, PartNode, parse_sysml
from .evaluator import evaluate_attributes
from .units import convert_numeric_with_units


def build_part_json(part: PartNode, *, namespace: str) -> Dict[str, Any]:
    """
    Convert one PartNode to JSON object (no parent/children linking here).
    """
    part_id = f"urn:{namespace}:part:{part.name}:001"
    attrs = part.attributes_val

    dimensions: Dict[str, Any] = {}
    attributes: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

    # dimensions from *dims child of THIS part
    dims_part = next((c for n, c in part.children.items() if n.lower().endswith("dims")), None)
    if dims_part:
        dp = dims_part.attributes_val
        la, wa, ha = dp.get("length"), dp.get("width"), dp.get("height")
        mpu = dp.get("metersPerUnit", 1)

        if all(isinstance(v, (int, float)) for v in [la, wa, ha, mpu]):
            dimensions["dims_m"] = [float(la) * float(mpu), float(wa) * float(mpu), float(ha) * float(mpu)]

        for k, v in dp.items():
            if k in ("length", "width", "height"):
                continue
            dimensions[k] = v

    # numeric -> attributes (with SI conversion where known)
    for k, v in attrs.items():
        if isinstance(v, (int, float)):
            nk, nv = convert_numeric_with_units(k, float(v))
            attributes[nk] = nv

    # non-numeric -> metadata
    for k, v in attrs.items():
        if not isinstance(v, (int, float)):
            metadata[k] = v

    return {
        "type": "Part",
        "id": part_id,
        "name": part.name,
        "dimensions": dimensions,
        "attributes": attributes,
        "metadata": metadata,
    }


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


def write_json(parts: List[Dict[str, Any]], output_path: str) -> str:
    """
    Write a parts list to disk as pretty JSON.
    Returns output_path.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(parts, f, indent=2)
    return output_path
