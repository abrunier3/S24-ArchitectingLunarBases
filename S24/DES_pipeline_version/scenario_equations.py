import ast
import math
import operator


class ScenarioEquationError(ValueError):
    pass


_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}

_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_FUNCTIONS = {
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "sqrt": math.sqrt,
}


def _normalize_equation(equation):
    return equation.strip().replace("^", "**")


def parse_equations(equations):
    parsed = []
    for line_number, raw_line in enumerate(str(equations or "").splitlines(), start=1):
        equation = _normalize_equation(raw_line)
        if not equation:
            continue
        try:
            tree = ast.parse(equation, mode="exec")
        except SyntaxError as exc:
            raise ScenarioEquationError(
                f"Invalid equation on line {line_number}: {raw_line!r}"
            ) from exc
        if len(tree.body) != 1 or not isinstance(tree.body[0], ast.Assign):
            raise ScenarioEquationError(
                f"Line {line_number} must contain one assignment: output = expression"
            )
        assignment = tree.body[0]
        if len(assignment.targets) != 1 or not isinstance(assignment.targets[0], ast.Name):
            raise ScenarioEquationError(
                f"Line {line_number} must assign to one output variable"
            )
        parsed.append((assignment.targets[0].id, assignment.value, line_number))
    return parsed


def validate_effect_outputs(equations, effect_outputs):
    """Reject terminal equation outputs that no DES process consumes."""
    parsed = parse_equations(equations)
    allowed = set(effect_outputs or ())
    unsupported = []
    for index, (output_name, _, line_number) in enumerate(parsed):
        referenced_later = any(
            any(isinstance(node, ast.Name) and node.id == output_name for node in ast.walk(expression))
            for _, expression, _ in parsed[index + 1:]
        )
        if not referenced_later and output_name not in allowed:
            unsupported.append(f"{output_name} (line {line_number})")
    if unsupported:
        raise ScenarioEquationError(
            "Equation output has no DES effect: " + ", ".join(unsupported)
        )


def _evaluate_node(node, variables):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ScenarioEquationError("Only numeric constants are allowed")
        return node.value
    if isinstance(node, ast.Name):
        if node.id not in variables:
            raise ScenarioEquationError(f"Unknown equation variable: {node.id}")
        return variables[node.id]
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        return _BINARY_OPERATORS[type(node.op)](
            _evaluate_node(node.left, variables),
            _evaluate_node(node.right, variables),
        )
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _UNARY_OPERATORS[type(node.op)](_evaluate_node(node.operand, variables))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        function = _FUNCTIONS.get(node.func.id)
        if function is None:
            raise ScenarioEquationError(f"Unsupported equation function: {node.func.id}")
        if node.keywords:
            raise ScenarioEquationError("Keyword arguments are not allowed in equations")
        return function(*[_evaluate_node(argument, variables) for argument in node.args])
    raise ScenarioEquationError(f"Unsupported equation syntax: {type(node).__name__}")


def evaluate_equations(equations, context, effect_outputs=None):
    if effect_outputs is not None:
        validate_effect_outputs(equations, effect_outputs)
    variables = dict(context or {})
    outputs = {}
    for output_name, expression, line_number in parse_equations(equations):
        try:
            value = float(_evaluate_node(expression, variables))
        except ScenarioEquationError:
            raise
        except (ArithmeticError, TypeError, ValueError) as exc:
            raise ScenarioEquationError(
                f"Equation for {output_name} failed on line {line_number}: {exc}"
            ) from exc
        if not math.isfinite(value):
            raise ScenarioEquationError(f"Equation for {output_name} produced a non-finite value")
        variables[output_name] = value
        outputs[output_name] = value
    return outputs
