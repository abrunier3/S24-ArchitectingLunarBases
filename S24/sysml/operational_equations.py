"""Identify DES equations declared as attributes of a SysML part."""

import ast
import re
from graphlib import CycleError, TopologicalSorter

from S24.sysml.ast import PartNode


def extract_operational_equations(part: PartNode) -> dict[str, str]:
    effects = {"ProcessingTime", "TravelTime", "EnergyConsumed", "EnergyGenerated", "PowerIn", "PowerOut"}
    runtime = {"SimulationTime", "Distance", "CargoMass", "RoverCapacity", "ResourceIn", "RequestedResource",
               "SlopeDeg", "FlatSpeedKph", "SlopeSpeedFactor", "EffectiveSpeedKph"}
    for port in part.ports.values():
        for direction, item in zip(port["direction"], port["items"]):
            flow = re.sub(r"(?:In|Out)$", "", item)
            if direction == "out":
                effects.add(f"{flow}Out")
            if direction == "in":
                effects.add(f"{flow}Stored")
            runtime.update((f"{flow}In", f"{flow}Stored", f"Requested{flow}"))

    roots = {
        name for name, rhs in part.attributes_raw.items()
        if name in effects and not rhs.startswith(('"', "'"))
    }
    if not roots:
        return {}

    # Static properties remain model parameters. Only dependencies of a DES
    # effect that themselves depend on runtime values become intermediate laws.
    dependencies = {}
    for name, rhs in part.attributes_raw.items():
        try:
            expression = ast.parse(rhs.replace("^", "**"), mode="eval")
        except SyntaxError:
            continue  # The DES reports malformed assignments for selected outputs.
        dependencies[name] = {node.id for node in ast.walk(expression) if isinstance(node, ast.Name)}

    dynamic = roots | runtime
    while True:
        additions = {name for name, refs in dependencies.items() if refs & dynamic} - dynamic
        if not additions:
            break
        dynamic.update(additions)

    ordered = TopologicalSorter()
    pending = list(reversed([name for name in part.attributes_raw if name in roots]))
    visited = set()
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)
        refs = dependencies.get(name, set()) & dynamic
        # ResourceStored on the right refers to the inventory before delivery.
        if name.endswith("Stored"):
            refs = refs - {name}
        inputs = [key for key in part.attributes_raw if key in refs and (key not in runtime or key in roots)]
        ordered.add(name, *inputs)
        pending.extend(reversed(inputs))
    try:
        return {name: part.attributes_raw[name] for name in ordered.static_order()}
    except CycleError as exc:
        raise ValueError(f"{part.name}: cyclic operational equations: {' -> '.join(exc.args[1])}") from exc
