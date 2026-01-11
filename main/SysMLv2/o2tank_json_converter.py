#!/usr/bin/env python3
"""
Future-proof SysML v2 → JSON converter.

Output schema per top-level part:
{
  "type": "Part",
  "id": "urn:<namespace>:part:<PartName>:001",
  "name": "<PartName>",
  "dimensions": { ... },
  "attributes": { ... },
  "metadata": { ... }
}

- Handles multiple top-level parts in a package
- Parses parts + nested parts
- Safely evaluates numeric expressions (no eval)
- Converts units to SI (where known)
- dimensions: derived from nested "*dims" parts
- attributes: ALL numeric attributes (evaluated), with SI unit suffixes
- metadata: ALL non-numeric attributes
"""

import json
import re
import sys
import ast
from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List, Union


# ----------------------------
# Data structures
# ----------------------------

@dataclass
class PartNode:
    name: str
    attributes_raw: Dict[str, str] = field(default_factory=dict)
    attributes_val: Dict[str, Any] = field(default_factory=dict)
    children: Dict[str, "PartNode"] = field(default_factory=dict)


@dataclass
class Model:
    package_name: Optional[str] = None
    parts: Dict[str, PartNode] = field(default_factory=dict)


# ----------------------------
# Helpers
# ----------------------------

_str_re = re.compile(r'"([^"]*)"')
_num_re = re.compile(r'^-?\d+(\.\d+)?$')


def _strip_comment(line: str) -> str:
    return line.split("//", 1)[0].rstrip()


def _parse_literal_token(value_str: str) -> Any:
    value_str = value_str.strip()

    m = _str_re.fullmatch(value_str)
    if m:
        return m.group(1)

    if _num_re.match(value_str):
        return float(value_str) if "." in value_str else int(value_str)

    return value_str


# ----------------------------
# SysML parser
# ----------------------------

def parse_sysml(text: str) -> Model:
    model = Model()
    current_stack: List[PartNode] = []
    brace_stack: List[str] = []

    for raw_line in text.splitlines():
        line = _strip_comment(raw_line).strip()
        if not line:
            continue

        # package
        m = re.match(r"package\s+'([^']+)'\s*\{", line)
        if m:
            model.package_name = m.group(1)
            brace_stack.append("package")
            continue

        # ignore requirement blocks
        if re.match(r"requirement\s+\w+\s*\{", line):
            brace_stack.append("ignore_req")
            continue

        # ignore satisfy statements
        if re.match(r"satisfy\s+\w+\s+by\s+\w+;", line):
            continue

        # part (top-level or nested)
        m = re.match(r"part\s+(\w+)\s*\{", line)
        if m:
            part_name = m.group(1)
            node = PartNode(name=part_name)
            if current_stack:
                current_stack[-1].children[part_name] = node
            else:
                model.parts[part_name] = node
            current_stack.append(node)
            brace_stack.append("part")
            continue

        # closing brace
        if line == "}":
            if brace_stack:
                ctx = brace_stack.pop()
                if ctx == "part" and current_stack:
                    current_stack.pop()
            continue

        # attributes
        if current_stack:
            m = re.match(r"attribute\s+(\w+)\s*=\s*(.+);", line)
            if m:
                attr_name = m.group(1)
                raw_val = m.group(2).strip().rstrip(";")
                current_stack[-1].attributes_raw[attr_name] = raw_val
                continue

    return model


# ----------------------------
# Safe expression evaluator
# ----------------------------

class SafeEvaluator(ast.NodeVisitor):
    allowed_nodes = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Load,
        ast.Name, ast.Attribute, ast.Constant, ast.Pow,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.USub, ast.UAdd
    )

    def __init__(self, env: Dict[str, Union[int, float]]):
        self.env = env

    def visit(self, node):
        if not isinstance(node, self.allowed_nodes):
            raise ValueError(f"Disallowed expression node: {type(node).__name__}")
        return super().visit(node)

    def eval(self, expr: str) -> Union[int, float]:
        expr = expr.replace("^", "**")
        tree = ast.parse(expr, mode="eval")
        return self.visit(tree.body)

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numeric constants allowed")

    def visit_Name(self, node: ast.Name):
        if node.id in self.env:
            return self.env[node.id]
        raise ValueError(f"Unknown variable: {node.id}")

    def visit_Attribute(self, node: ast.Attribute):
        parts = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
        full = ".".join(reversed(parts))
        if full in self.env:
            return self.env[full]
        raise ValueError(f"Unknown attribute reference: {full}")

    def visit_UnaryOp(self, node: ast.UnaryOp):
        val = self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            return -val
        if isinstance(node.op, ast.UAdd):
            return val
        raise ValueError("Unsupported unary operator")

    def visit_BinOp(self, node: ast.BinOp):
        l = self.visit(node.left)
        r = self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return l + r
        if isinstance(node.op, ast.Sub):
            return l - r
        if isinstance(node.op, ast.Mult):
            return l * r
        if isinstance(node.op, ast.Div):
            return l / r
        if isinstance(node.op, ast.Pow):
            return l ** r
        raise ValueError("Unsupported binary operator")


# ----------------------------
# Semantic evaluation (corrected)
# ----------------------------

def _collect_env(part: PartNode, parent_chain: List[str] | None = None) -> Dict[str, float]:
    """
    Collect evaluated numeric attributes into a flat environment with multiple reference styles:
    - unqualified: attrName
    - child-qualified: ChildPartName.attrName
    - fully-qualified: Parent.ChildPartName.attrName (for nested parts)
    """
    if parent_chain is None:
        parent_chain = []

    env: Dict[str, float] = {}

    # full chain including this part
    full_chain = parent_chain + [part.name]
    full_prefix = ".".join(full_chain)          # e.g. "O2Tank.O2Tank_dims"
    local_prefix = part.name                    # e.g. "O2Tank_dims"

    for name, val in part.attributes_val.items():
        if isinstance(val, (int, float)):
            v = float(val)

            # unqualified
            env[name] = v

            # child-qualified (part-local)
            env[f"{local_prefix}.{name}"] = v      # e.g. "O2Tank_dims.length"

            # fully-qualified (full chain)
            env[f"{full_prefix}.{name}"] = v       # e.g. "O2Tank.O2Tank_dims.length"

    # recurse into children
    for child in part.children.values():
        env.update(_collect_env(child, parent_chain=full_chain))

    return env


def evaluate_attributes(model: Model):
    # Initialize literals
    def init_literals(part: PartNode):
        for name, raw in part.attributes_raw.items():
            lit = _parse_literal_token(raw)
            part.attributes_val[name] = lit
        for child in part.children.values():
            init_literals(child)

    for p in model.parts.values():
        init_literals(p)

    # Iterative evaluation
    for _ in range(10):
        env = {}
        for p in model.parts.values():
            env.update(_collect_env(p))

        changed = False

        def try_eval(part: PartNode):
            nonlocal changed
            evaluator = SafeEvaluator(env)

            for name, raw in part.attributes_raw.items():
                current_val = part.attributes_val.get(name)

                # Skip if already numeric
                if isinstance(current_val, (int, float)):
                    continue

                # Skip quoted string literals
                if raw.startswith('"') and raw.endswith('"'):
                    continue

                # Try evaluating expression
                try:
                    val = evaluator.eval(raw)
                    part.attributes_val[name] = val
                    changed = True
                except Exception:
                    pass

            for child in part.children.values():
                try_eval(child)

        for p in model.parts.values():
            try_eval(p)

        if not changed:
            break


# ----------------------------
# Unit conversion
# ----------------------------

def _convert_numeric_with_units(name: str, value: float) -> tuple[str, float]:
    if name == "volume":
        return "volume_m3", value / 1000.0
    if name == "usableO2Capacity":
        return "usableO2Capacity_m3", value / 1000.0
    if name in ("maxPressure", "operatingPressure"):
        return f"{name}_Pa", value * 1000.0
    if name == "dryMass":
        return "dryMass_kg", value
    if name == "wallThickness":
        return "wallThickness_m", value

    return name, value


# ----------------------------
# JSON mapping
# ----------------------------

def build_part_json(model: Model, part: PartNode, namespace: str = "lunarspaceport1") -> Dict[str, Any]:
    part_id = f"urn:{namespace}:part:{part.name}:001"
    attrs = part.attributes_val

    dimensions = {}
    attributes = {}
    metadata = {}

    # --- dimensions from nested "*dims" part ---
    dims_part = next((c for n, c in part.children.items() if n.lower().endswith("dims")), None)
    if dims_part:
        dp = dims_part.attributes_val

        la = dp.get("length")
        wa = dp.get("width")
        ha = dp.get("height")
        mpu = dp.get("metersPerUnit", 1)

        if all(isinstance(v, (int, float)) for v in [la, wa, ha, mpu]):
            dimensions["dims_m"] = [la * mpu, wa * mpu, ha * mpu]

        for name, val in dp.items():
            if name not in ("length", "width", "height"):
                dimensions[name] = val

    # --- attributes: ALL numeric attributes ---
    for name, val in attrs.items():
        if isinstance(val, (int, float)):
            new_name, new_val = _convert_numeric_with_units(name, float(val))
            attributes[new_name] = new_val

    # --- metadata: ALL non-numeric attributes ---
    for name, val in attrs.items():
        if not isinstance(val, (int, float)):
            metadata[name] = val

    return {
        "type": "Part",
        "id": part_id,
        "name": part.name,
        "dimensions": dimensions,
        "attributes": attributes,
        "metadata": metadata,
    }


# ----------------------------
# Public API
# ----------------------------

def sysml_to_json(sysml_text: str, namespace: str = "lunarspaceport1") -> List[Dict[str, Any]]:
    model = parse_sysml(sysml_text)
    evaluate_attributes(model)
    return [build_part_json(model, part, namespace=namespace) for part in model.parts.values()]


# ----------------------------
# CLI
# ----------------------------

def main():
    if len(sys.argv) < 3:
        print("Usage: python o2tank_json_converter.py <input.sysml> <output.json> [namespace]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    namespace = sys.argv[3] if len(sys.argv) > 3 else "lunarspaceport1"

    # Read SysML file
    with open(input_path, "r", encoding="utf-8") as f:
        sysml_text = f.read()

    # Convert to JSON
    parts_json = sysml_to_json(sysml_text, namespace=namespace)

    # Write JSON file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(parts_json, f, indent=2)

    print(f"Converted '{input_path}' → '{output_path}' using namespace '{namespace}'")


if __name__ == "__main__":
    main()