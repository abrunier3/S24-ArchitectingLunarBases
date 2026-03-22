from S24.sysml.ast import Model
from typing import List

def validate_connections(model: Model) -> List[str]:
    errors = []

    for iface in model.interfaces:
        src = iface["from"].split(".")
        dst = iface["to"].split(".")

        if len(src) != 2 or len(dst) != 2:
            errors.append(f"Invalid interface format: {iface}")
            continue

        src_part, src_port = src
        dst_part, dst_port = dst

        if src_part not in model.parts:
            errors.append(f"Unknown source part: {src_part}")
            continue

        if dst_part not in model.parts:
            errors.append(f"Unknown target part: {dst_part}")
            continue

        sp = model.parts[src_part].ports.get(src_port)
        dp = model.parts[dst_part].ports.get(dst_port)

        if not sp:
            errors.append(f"Missing source port: {src_port}")
        if not dp:
            errors.append(f"Missing target port: {dst_port}")

        if sp and dp:
            if "out" not in sp["direction"] or "in" not in dp["direction"]:
                errors.append(
                    f"Direction mismatch: {src_part}.{src_port} → {dst_part}.{dst_port}"
                )

    return errors