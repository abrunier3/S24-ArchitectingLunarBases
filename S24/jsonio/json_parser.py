from typing import Dict, Any, Tuple
from S24.sysml.ast import PartNode

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
        if not isinstance(v, (int, float)) and k not in ("material", "materialRef"):
            metadata[k] = v

    material_ref = attrs.get("materialRef")
    if isinstance(material_ref, str) and material_ref.strip():
        obj_material_ref = material_ref.strip()
    else:
        obj_material_ref = None


    return {
        "type": "Part",
        "id": part_id,
        "name": part.name,
        "dimensions": dimensions,
        "attributes": attributes,
        "metadata": metadata,
        "materialRef": obj_material_ref,
    }


def convert_numeric_with_units(name: str, value: float) -> Tuple[str, float]:
    """
    Convert known attributes to SI and rename with suffix.
    """
    v = float(value)
    
    if name == "volume":
        return "volume_m3", v / 1000.0

    if name.endswith("_volume"):
        # liters -> m^3
        return f"{name}_m3", v / 1000.0

    if name.endswith("_usableO2Capacity"):
        # liters -> m^3
        return f"{name}_m3", v / 1000.0

    if name.endswith("_operatingPressure") or name.endswith("_maxPressure"):
        # kPa -> Pa
        return f"{name}_Pa", v * 1000.0

    if name.endswith("_dryMass"):
        # kg stays kg
        return f"{name}_kg", v

    if name.endswith("_wallThickness"):
        # m stays m
        return f"{name}_m", v

    return name, v