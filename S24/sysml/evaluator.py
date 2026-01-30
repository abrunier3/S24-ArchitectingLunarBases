from __future__ import annotations

import ast
from typing import Any, Dict, List, Optional, Union

from .parser import Model, PartNode, parse_literal_token


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
