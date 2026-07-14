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
    outputs = set()
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
        output_name = assignment.targets[0].id
        if output_name in outputs:
            raise ScenarioEquationError(
                f"Output {output_name} is assigned more than once"
            )
        outputs.add(output_name)
        parsed.append((output_name, assignment.value, line_number))
    return parsed


def get_equation_contract(equations):
    """Return assigned outputs and external input names in evaluation order."""
    parsed = parse_equations(equations)
    assigned = set()
    external_inputs = set()
    for output_name, expression, _ in parsed:
        for node in ast.walk(expression):
            if not isinstance(node, ast.Name):
                continue
            if node.id in _FUNCTIONS or node.id in assigned:
                continue
            external_inputs.add(node.id)
        assigned.add(output_name)
    return {
        "outputs": {output for output, _, _ in parsed},
        "inputs": external_inputs,
    }


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


def evaluate_selected_equations(equations, context, selected_outputs):
    """Evaluate only assignments required to produce selected outputs.

    This lets a runtime evaluate a module's power law without also evaluating
    unrelated resource equations whose event inputs are not available yet.
    Dependencies between assignments are retained automatically.
    """
    parsed = parse_equations(equations)
    wanted = set(selected_outputs or ())
    if not wanted:
        return {}

    selected_indexes = set()
    for index in range(len(parsed) - 1, -1, -1):
        output_name, expression, _ = parsed[index]
        if output_name not in wanted:
            continue
        selected_indexes.add(index)
        wanted.update(
            node.id
            for node in ast.walk(expression)
            if isinstance(node, ast.Name)
        )

    variables = dict(context or {})
    outputs = {}
    for index, (output_name, expression, line_number) in enumerate(parsed):
        if index not in selected_indexes:
            continue
        try:
            value = float(_evaluate_node(expression, variables))
        except ScenarioEquationError:
            raise
        except (ArithmeticError, TypeError, ValueError) as exc:
            raise ScenarioEquationError(
                f"Equation for {output_name} failed on line {line_number}: {exc}"
            ) from exc
        if not math.isfinite(value):
            raise ScenarioEquationError(
                f"Equation for {output_name} produced a non-finite value"
            )
        variables[output_name] = value
        outputs[output_name] = value
    return outputs
