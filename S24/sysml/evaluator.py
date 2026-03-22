from __future__ import annotations

import ast
import re 
from typing import Any, Dict, List, Optional, Union

from S24.sysml.ast import Model, PartNode
from S24.sysml.utils import convert_numeric_with_units, parse_literal_token, strip_comment


Number = Union[int, float]


class SafeEvaluator(ast.NodeVisitor):
    """
    Safe evaluator for simple arithmetic and attribute references.
    Supports:
      - +, -, *, /, ** (and ^ mapped to **)
      - unary +/- 
      - Name and Attribute references (e.g. A, Part.attr, Root.Child.attr)
    """

    allowed_nodes = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Load,
        ast.Name, ast.Attribute, ast.Constant, ast.Pow,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.USub, ast.UAdd
    )

    def __init__(self, env: Dict[str, Number]) -> None:
        self.env = env

    def visit(self, node: ast.AST) -> Any:
        if not isinstance(node, self.allowed_nodes):
            raise ValueError(f"Disallowed expression node: {type(node).__name__}")
        return super().visit(node)

    def eval(self, expr: str) -> Number:
        expr = expr.replace("^", "**")
        tree = ast.parse(expr, mode="eval")
        return self.visit(tree.body)

    def visit_Constant(self, node: ast.Constant) -> Number:
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numeric constants allowed")

    def visit_Name(self, node: ast.Name) -> Number:
        if node.id in self.env:
            return self.env[node.id]
        raise ValueError(f"Unknown variable: {node.id}")

    def visit_Attribute(self, node: ast.Attribute) -> Number:
        parts: List[str] = []
        cur: ast.AST = node

        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value

        if isinstance(cur, ast.Name):
            parts.append(cur.id)

        full = ".".join(reversed(parts))
        if full in self.env:
            return self.env[full]
        raise ValueError(f"Unknown attribute reference: {full}")

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Number:
        val = self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            return -val
        if isinstance(node.op, ast.UAdd):
            return val
        raise ValueError("Unsupported unary operator")

    def visit_BinOp(self, node: ast.BinOp) -> Number:
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


def _collect_env(part: PartNode, parent_chain: Optional[List[str]] = None) -> Dict[str, float]:
    """
    Collect evaluated numeric attributes into env with reference styles:
      - attrName
      - PartName.attrName
      - Parent.Child.PartName.attrName
    """
    if parent_chain is None:
        parent_chain = []

    env: Dict[str, float] = {}
    full_chain = parent_chain + [part.name]
    full_prefix = ".".join(full_chain)
    local_prefix = part.name

    for name, val in part.attributes_val.items():
        if isinstance(val, (int, float)):
            v = float(val)
            env[name] = v
            env[f"{local_prefix}.{name}"] = v
            env[f"{full_prefix}.{name}"] = v

    for child in part.children.values():
        env.update(_collect_env(child, parent_chain=full_chain))

    return env


def evaluate_attributes(model: Model, *, max_passes: int = 10) -> None:
    """
    Fill PartNode.attributes_val by:
      1) initializing literals from attributes_raw
      2) iteratively evaluating numeric expressions using SafeEvaluator
    """
    def init_literals(part: PartNode) -> None:
        for name, raw in part.attributes_raw.items():
            part.attributes_val[name] = parse_literal_token(raw)
        for child in part.children.values():
            init_literals(child)

    for p in model.parts.values():
        init_literals(p)

    for _ in range(max_passes):
        env: Dict[str, float] = {}
        for p in model.parts.values():
            env.update(_collect_env(p))

        changed = False
        evaluator = SafeEvaluator(env)

        def try_eval(part: PartNode) -> None:
            nonlocal changed
            for name, raw in part.attributes_raw.items():
                current = part.attributes_val.get(name)

                # already numeric
                if isinstance(current, (int, float)):
                    continue

                # quoted string stays string
                if raw.strip().startswith('"') and raw.strip().endswith('"'):
                    continue

                # try eval
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


def parse_sysml(text: str) -> Model:
    model = Model()
    current_stack: List[PartNode] = []
    brace_stack: List[str] = []

    for raw_line in text.splitlines():
        line = strip_comment(raw_line).strip()
        if not line:
            continue

        # package (with or without quotes)
        m = re.match(r"package\s+(?:'([^']+)'|(\w+))\s*\{", line)
        if m:
            model.package_name = m.group(1) or m.group(2)
            brace_stack.append("package")
            continue

        # ignore private import lines
        if line.startswith("private import"):
            continue

        # ignore requirement blocks
        if re.match(r"requirement\s+\w+\s*\{", line):
            brace_stack.append("ignore_req")
            continue

        # ignore satisfy statements
        if re.match(r"satisfy\s+\w+\s+by\s+\w+;", line):
            continue

        # part (top-level or nested), with optional 'def' and inheritance
        m = re.match(r"part\s+(?:def\s+)?(\w+)(?:\s*:\s*\w+)?\s*\{", line)
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
