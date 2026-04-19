from typing import Dict, Any, Tuple, List

from S24.sysml.ast import Model, PartNode

def build_part_json_representation(part: PartNode, *, namespace: str) -> Dict[str, Any]:
    part_id = f"urn:{namespace}:part:{part.name}:001"
    attrs = part.attributes_val

    dimensions: Dict[str, Any] = {}
    transform: Dict[str, Any] = {}
    attributes: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    ports: list = []

    dims_part = next(
        (c for n, c in part.children.items() if n.lower().endswith("dims")),
        None
    )

    if dims_part:
        dp = dims_part.attributes_val

        la, wa, ha = dp.get("length"), dp.get("width"), dp.get("height")
        mpu = dp.get("metersPerUnit", 1)

        if all(isinstance(v, (int, float)) for v in [la, wa, ha, mpu]):
            dimensions["size_m"] = {
                "length": float(la) * float(mpu),
                "width": float(wa) * float(mpu),
                "height": float(ha) * float(mpu),
            }

        transform = {
            "position_m": [
                float(dp.get("X", 0)),
                float(dp.get("Y", 0)),
                float(dp.get("Z", 0)),
            ],
            "rotation_deg": [
                float(dp.get("rX_deg", 0)),
                float(dp.get("rY_deg", 0)),
                float(dp.get("rZ_deg", 0)),
            ],
        }

        for k, v in dp.items():
            if k in ("length", "width", "height", "X", "Y", "Z", "rX_deg", "rY_deg", "rZ_deg"):
                continue
            dimensions[k] = v

    for k, v in attrs.items():
        if isinstance(v, (int, float)):
            nk, nv = _convert_numeric_with_units(k, float(v))
            attributes[nk] = nv

    for k, v in attrs.items():
        if not isinstance(v, (int, float)) and k not in ("material", "materialRef"):
            if k.startswith("metadata"):
                metadata.setdefault("definitions", []).append(v)
            elif k == "geometry":
                metadata["geometryRef"] = v
            else:
                metadata[k] = v

    material_ref = attrs.get("materialRef")
    obj_material_ref = material_ref.strip() if isinstance(material_ref, str) and material_ref.strip() else None

    if getattr(part, "ports", None):
        for pname, pinfo in part.ports.items():
            ports.append({
                "name": pname,
                "direction": pinfo.get("direction", []),
                "items": pinfo.get("items", []),
            })

    return {
        "type": "Part",
        "id": part_id,
        "name": part.name,
        "dimensions": dimensions,
        "transform": transform,
        "attributes": attributes,
        "metadata": metadata,
        "materialRef": obj_material_ref,
        "ports": ports,
    }

def build_connections_json(model: Model) -> List[Dict[str, Any]]:
    connections: List[Dict[str, Any]] = []

    for iface in getattr(model, "interfaces", []):
        conn = {
            "name": iface.get("name"),
            "type": iface.get("type"),
            "flow": iface.get("flow"),
            "from": _split_endpoint(iface.get("from")),
            "to": _split_endpoint(iface.get("to")),
        }
        connections.append(conn)

    return connections

def validate_connections(model: Model) -> List[str]:
    errors = []
    part_index: Dict[str, PartNode] = {}

    def walk(part: PartNode) -> None:
        part_index[part.name] = part
        for child_name, child in part.children.items():
            if child_name.lower().endswith("dims"):
                continue
            walk(child)

    for top in model.parts.values():
        walk(top)

    for iface in model.interfaces:
        src = _split_endpoint(iface["from"])
        dst = _split_endpoint(iface["to"])

        src_part = src["part"]
        src_port = src["port"]
        dst_part = dst["part"]
        dst_port = dst["port"]

        if not src_part or not src_port or not dst_part or not dst_port:
            errors.append(f"Invalid interface format: {iface}")
            continue

        if src_part not in part_index:
            errors.append(f"Unknown source part: {src_part}")
            continue

        if dst_part not in part_index:
            errors.append(f"Unknown target part: {dst_part}")
            continue

        sp = part_index[src_part].ports.get(src_port)
        dp = part_index[dst_part].ports.get(dst_port)

        if not sp:
            errors.append(f"Missing source port: {src_part}.{src_port}")
        if not dp:
            errors.append(f"Missing target port: {dst_part}.{dst_port}")

        if sp and dp:
            if "out" not in sp["direction"] or "in" not in dp["direction"]:
                errors.append(
                    f"Direction mismatch: {src_part}.{src_port} -> {dst_part}.{dst_port}"
                )

    return errors

#--------------------------------------------------------------------------------------------------
# Helpers

def _convert_numeric_with_units(name: str, value: float) -> Tuple[str, float]:
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

def _split_endpoint(endpoint: str) -> Dict[str, str]:
    """
    "LSP1::Rover.RoverFleet_LOXPortInOut" ->
    {"part": "Rover", "port": "RoverFleet_LOXPortInOut"}
    """
    if not endpoint:
        return {"part": None, "port": None}

    normalized = endpoint.replace("::", ".")
    tokens = [token for token in normalized.split(".") if token]

    if len(tokens) >= 2:
        return {"part": tokens[-2], "port": tokens[-1]}

    if len(tokens) == 1:
        return {"part": tokens[0], "port": None}

    return {"part": None, "port": None}
