from __future__ import annotations

from marple.arraymodel import APLArray, S
from marple.functions import (
    add,
    ceiling,
    divide,
    floor,
    maximum,
    minimum,
    multiply,
    negate,
    reciprocal,
    subtract,
)
from marple.parser import (
    Assignment,
    DyadicFunc,
    MonadicFunc,
    Num,
    Program,
    Var,
    Vector,
    parse,
)

MONADIC_FUNCTIONS: dict[str, object] = {
    "+": lambda omega: omega,  # conjugate (identity for reals)
    "-": negate,
    "×": lambda omega: S((-1 if omega.data[0] < 0 else 1 if omega.data[0] > 0 else 0)),  # signum
    "÷": reciprocal,
    "⌈": ceiling,
    "⌊": floor,
}

DYADIC_FUNCTIONS: dict[str, object] = {
    "+": add,
    "-": subtract,
    "×": multiply,
    "÷": divide,
    "⌈": maximum,
    "⌊": minimum,
}


def _evaluate(node: object, env: dict[str, APLArray]) -> APLArray:
    if isinstance(node, Num):
        return S(node.value)

    if isinstance(node, Vector):
        values = [el.value for el in node.elements]
        return APLArray([len(values)], list(values))

    if isinstance(node, Var):
        if node.name not in env:
            raise NameError(f"Undefined variable: {node.name}")
        return env[node.name]

    if isinstance(node, MonadicFunc):
        operand = _evaluate(node.operand, env)
        func = MONADIC_FUNCTIONS.get(node.function)
        if func is None:
            raise ValueError(f"Unknown monadic function: {node.function}")
        return func(operand)  # type: ignore[operator]

    if isinstance(node, DyadicFunc):
        left = _evaluate(node.left, env)
        right = _evaluate(node.right, env)
        func = DYADIC_FUNCTIONS.get(node.function)
        if func is None:
            raise ValueError(f"Unknown dyadic function: {node.function}")
        return func(left, right)  # type: ignore[operator]

    if isinstance(node, Assignment):
        value = _evaluate(node.value, env)
        env[node.name] = value
        return value

    if isinstance(node, Program):
        result = S(0)
        for stmt in node.statements:
            result = _evaluate(stmt, env)
        return result

    raise TypeError(f"Unknown AST node: {type(node)}")


def interpret(source: str, env: dict[str, APLArray] | None = None) -> APLArray:
    if env is None:
        env = {}
    tree = parse(source)
    return _evaluate(tree, env)
