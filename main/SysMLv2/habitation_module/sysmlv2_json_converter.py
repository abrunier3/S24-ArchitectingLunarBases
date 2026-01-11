#!/usr/bin/env python3
"""
Future-proof SysML v2 → JSON converter with nested parts.

Output schema per part (flat list):
{
  "type": "Part",
  "id": "urn:<namespace>:part:<PartName>:001",
  "name": "<PartName>",
  "parent": "<ParentName>",        # optional, omitted for top-level
  "children": ["Child1", "Child2"],# optional, only non-*dims parts
  "dimensions": { ... },           # from this part's *dims child, if any
  "attributes": { ... },
  "metadata": { ... }
}

Rules:
- Handles multiple top-level parts in a package
- Parses parts + nested parts
- Safely evaluates numeric expressions (no eval)
- Converts units to SI (where known)
- dimensions: derived from nested "*dims" part of THAT part
- attributes: ALL numeric attributes (evaluated), with SI unit suffixes
- metadata: ALL non-numeric attributes
- Nested parts:
    * Parts whose name ends with "dims" (case-insensitive) are NOT emitted
      as separate JSON objects; they only populate the parent.dimensions.
    * All other nested parts are emitted as their own JSON objects, with
      "parent" and "children" relationships added.
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
    """
    Parse a simple literal token:
    - "foo" -> "foo"
    - 1.23 or 42 -> number
    - otherwise, raw string (expression or symbol)
    """
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
    """
    Safe evaluator for simple arithmetic and attribute references.
    """

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
# Semantic evaluation
# ----------------------------

def _collect_env(part: PartNode, parent_chain: Optional[List[str]] = None) -> Dict[str, float]:
    """
    Collect evaluated numeric attributes into a flat environment with multiple reference styles:
    - unqualified: attrName
    - child-qualified: PartName.attrName
    - fully-qualified: Parent.Child.PartName.attrName
    """
    if parent_chain is None:
        parent_chain = []

    env: Dict[str, float] = {}

    full_chain = parent_chain + [part.name]
    full_prefix = ".".join(full_chain)   # e.g., "HabitationModule.O2Tank.O2Tank_dims"
    local_prefix = part.name             # e.g., "O2Tank_dims"

    for name, val in part.attributes_val.items():
        if isinstance(val, (int, float)):
            v = float(val)

            # unqualified
            env[name] = v

            # part-local qualified
            env[f"{local_prefix}.{name}"] = v

            # fully-qualified along the chain
            env[f"{full_prefix}.{name}"] = v

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
        env: Dict[str, float] = {}
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
    """
    Apply SI conversion and return (new_name, new_value).
    Only known physical attributes get renamed; others pass through.
    """
    if name.endswith("_volume"):
        # liters -> m^3
        return f"{name}_m3", value / 1000.0
    if name.endswith("_usableO2Capacity"):
        # liters -> m^3
        return f"{name}_m3", value / 1000.0
    if name.endswith("_operatingPressure") or name.endswith("_maxPressure"):
        # kPa -> Pa
        return f"{name}_Pa", value * 1000.0
    if name.endswith("_dryMass"):
        # kg stays kg
        return f"{name}_kg", value
    if name.endswith("_wallThickness"):
        # m stays m
        return f"{name}_m", value

    # Unknown unit / dimensionless: keep name as-is
    return name, value


# ----------------------------
# JSON mapping for a single part
# ----------------------------

def build_part_json(part: PartNode, namespace: str = "lunarspaceport1") -> Dict[str, Any]:
    part_id = f"urn:{namespace}:part:{part.name}:001"
    attrs = part.attributes_val

    dimensions: Dict[str, Any] = {}
    attributes: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

    # --- dimensions from nested "*dims" part (for THIS part only) ---
    dims_part = next(
        (c for n, c in part.children.items() if n.lower().endswith("dims")),
        None
    )
    if dims_part:
        dp = dims_part.attributes_val

        la = dp.get("length")
        wa = dp.get("width")
        ha = dp.get("height")
        mpu = dp.get("metersPerUnit", 1)

        if all(isinstance(v, (int, float)) for v in [la, wa, ha, mpu]):
            dimensions["dims_m"] = [la * mpu, wa * mpu, ha * mpu]

        for name, val in dp.items():
            if name in ("length", "width", "height"):
                continue
            dimensions[name] = val

    # --- attributes: ALL numeric attributes of THIS part ---
    for name, val in attrs.items():
        if isinstance(val, (int, float)):
            new_name, new_val = _convert_numeric_with_units(name, float(val))
            attributes[new_name] = new_val

    # --- metadata: ALL non-numeric attributes of THIS part ---
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
# Public API with nested parts
# ----------------------------

def sysml_to_json(sysml_text: str, namespace: str = "lunarspaceport1") -> List[Dict[str, Any]]:
    model = parse_sysml(sysml_text)
    evaluate_attributes(model)

    results: List[Dict[str, Any]] = []

    def emit_part(part: PartNode, parent: Optional[PartNode] = None):
        # Build base JSON for this part
        obj = build_part_json(part, namespace=namespace)

        # Parent link (if any)
        if parent is not None:
            obj["parent"] = parent.name

        # Children list: only non-*dims children
        child_names = [
            name for name in part.children.keys()
            if not name.lower().endswith("dims")
        ]
        if child_names:
            obj["children"] = child_names

        results.append(obj)

        # Recurse into non-*dims children
        for child_name, child in part.children.items():
            if child_name.lower().endswith("dims"):
                continue
            emit_part(child, parent=part)

    # Emit all top-level parts
    for top_part in model.parts.values():
        emit_part(top_part, parent=None)

    return results


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

    with open(input_path, "r", encoding="utf-8") as f:
        sysml_text = f.read()

    parts_json = sysml_to_json(sysml_text, namespace=namespace)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(parts_json, f, indent=2)

    print(f"Converted '{input_path}' → '{output_path}' using namespace '{namespace}'")


if __name__ == "__main__":
    main()