from __future__ import annotations

import ast
import re
from typing import Any, Dict, List, Optional, Union

from S24.sysml.ast import Model, PartNode


Number = Union[int, float]
_STR_RE = re.compile(r'"([^"]*)"')
_NUM_RE = re.compile(r"^-?\d+(\.\d+)?$")

def evaluate_attributes(model: Model, *, max_passes: int = 10, verbose: int = 0) -> None:
    """
    Fill PartNode.attributes_val by:
      1) initializing literals from attributes_raw
      2) iteratively evaluating numeric expressions using SafeEvaluator
    """
    def init_literals(part: PartNode) -> None:
        for name, raw in part.attributes_raw.items():
            part.attributes_val[name] = _parse_literal_token(raw)
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
                except Exception as e:
                    print(f"[WARN] Could not evaluate {name}: {raw} → {e}")

            for child in part.children.values():
                try_eval(child)

        for p in model.parts.values():
            try_eval(p)

        if not changed:
            break

        if verbose == 2:
            _print_model_with_values(model)

def _parse_literal_token(value_str: str) -> Any:
    """
    Parse a simple literal token:
      - "foo" -> "foo"
      - 1.23 or 42 -> number
      - otherwise -> raw string (expression or symbol)
    """
    s = value_str.strip()

    m = _STR_RE.fullmatch(s)
    if m:
        return m.group(1)

    if _NUM_RE.match(s):
        return float(s) if "." in s else int(s)

    return s

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
      - ChildName.attrName   <-- important for *_dims
    """
    if parent_chain is None:
        parent_chain = []

    env: Dict[str, float] = {}

    full_chain = parent_chain + [part.name]
    full_prefix = ".".join(full_chain)
    local_prefix = part.name

    # Current part attributes
    for name, val in part.attributes_val.items():
        if isinstance(val, (int, float)):
            v = float(val)

            env[name] = v
            env[f"{local_prefix}.{name}"] = v
            env[f"{full_prefix}.{name}"] = v

    for child_name, child in part.children.items():
        child_prefix = f"{part.name}.{child_name}"

        for attr_name, val in child.attributes_val.items():
            if isinstance(val, (int, float)):
                v = float(val)
                env[f"{child_name}.{attr_name}"] = v
                env[f"{child_prefix}.{attr_name}"] = v

    for child in part.children.values():
        env.update(_collect_env(child, parent_chain=full_chain))

    return env


def _print_model_with_values(model: Model):
    '''
    Debug priting def for observing changes and evaluated expressions.
    '''
    def print_part(part: PartNode, level=0):
        prefix = "  " * level

        print(f"{prefix}📦 Part: {part.name}")

        if part.attributes_raw:
            print(f"{prefix}  🔹 Attributes (raw → evaluated):")
            for k, raw in part.attributes_raw.items():
                val = part.attributes_val.get(k, None)
                print(f"{prefix}    - {k}: {raw}  →  {val}")

        if part.ports:
            print(f"{prefix}  🔌 Ports:")
            for pname, pinfo in part.ports.items():
                print(f"{prefix}    - {pname} (dir={pinfo['direction']})")

        if part.metadata:
            print(f"{prefix}  🏷 Metadata:")
            for k, v in part.metadata.items():
                print(f"{prefix}    - {k}: {v}")

        for child in part.children.values():
            print_part(child, level + 1)

    print("\n=========== MODEL (WITH EVALUATION) ===========")
    print(f"📁 Package: {model.package_name}\n")

    for part in model.parts.values():
        print_part(part)

    for part in model.parts.values():
        def check_part(p):
            for k, v in p.attributes_val.items():
                if isinstance(v, str) and "*" in v:
                    print("❌ Unevaluated expression:", k, v)
            for child in p.children.values():
                check_part(child)

    check_part(part)

    print("==============================================\n")
