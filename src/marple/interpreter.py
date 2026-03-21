from __future__ import annotations

from typing import Callable

from marple.arraymodel import APLArray, S
from marple.functions import (
    absolute_value,
    add,
    ceiling,
    divide,
    equal,
    exponential,
    floor,
    greater_equal,
    greater_than,
    less_equal,
    less_than,
    logarithm,
    logical_and,
    logical_not,
    logical_or,
    maximum,
    minimum,
    multiply,
    natural_log,
    negate,
    not_equal,
    power,
    reciprocal,
    residue,
    subtract,
)
from marple.structural import (
    catenate,
    drop,
    index_of,
    iota,
    ravel,
    reshape,
    reverse,
    rotate,
    shape,
    take,
)
from marple.parser import (
    Assignment,
    DerivedFunc,
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
    "*": exponential,
    "⍟": natural_log,
    "|": absolute_value,
    "~": logical_not,
    "⍴": shape,
    "⍳": iota,
    ",": ravel,
    "⌽": reverse,
}

DYADIC_FUNCTIONS: dict[str, object] = {
    "+": add,
    "-": subtract,
    "×": multiply,
    "÷": divide,
    "⌈": maximum,
    "⌊": minimum,
    "*": power,
    "⍟": logarithm,
    "|": residue,
    "<": less_than,
    "≤": less_equal,
    "=": equal,
    "≥": greater_equal,
    ">": greater_than,
    "≠": not_equal,
    "∧": logical_and,
    "∨": logical_or,
    "⍴": reshape,
    "⍳": index_of,
    ",": catenate,
    "↑": take,
    "↓": drop,
    "⌽": rotate,
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

    if isinstance(node, DerivedFunc):
        operand = _evaluate(node.operand, env)
        func = DYADIC_FUNCTIONS.get(node.function)
        if func is None:
            raise ValueError(f"Unknown function for operator: {node.function}")
        if node.operator == "/":
            return _reduce(func, operand)  # type: ignore[arg-type]
        if node.operator == "\\":
            return _scan(func, operand)  # type: ignore[arg-type]
        raise ValueError(f"Unknown operator: {node.operator}")

    if isinstance(node, Program):
        result = S(0)
        for stmt in node.statements:
            result = _evaluate(stmt, env)
        return result

    raise TypeError(f"Unknown AST node: {type(node)}")


def _reduce(
    func: Callable[[APLArray, APLArray], APLArray],
    omega: APLArray,
) -> APLArray:
    data = omega.data
    if len(data) == 0:
        raise ValueError("Cannot reduce empty array")
    result = S(data[-1])
    for i in range(len(data) - 2, -1, -1):
        result = func(S(data[i]), result)
    return result


def _scan(
    func: Callable[[APLArray, APLArray], APLArray],
    omega: APLArray,
) -> APLArray:
    data = omega.data
    if len(data) == 0:
        return APLArray([0], [])
    results = [data[0]]
    acc = S(data[0])
    for i in range(1, len(data)):
        acc = func(acc, S(data[i]))
        results.append(acc.data[0])
    return APLArray([len(results)], results)


def interpret(source: str, env: dict[str, APLArray] | None = None) -> APLArray:
    if env is None:
        env = {}
    tree = parse(source)
    return _evaluate(tree, env)
