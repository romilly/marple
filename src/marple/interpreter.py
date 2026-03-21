from __future__ import annotations

from typing import Any, Callable

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
    decode,
    drop,
    encode,
    grade_down,
    grade_up,
    index_of,
    iota,
    ravel,
    reshape,
    reverse,
    rotate,
    shape,
    take,
    transpose,
)
from marple.parser import (
    Alpha,
    AlphaDefault,
    Assignment,
    DerivedFunc,
    Dfn,
    DyadicDfnCall,
    DyadicFunc,
    Guard,
    InnerProduct,
    MonadicDfnCall,
    MonadicFunc,
    Nabla,
    Num,
    Omega,
    OuterProduct,
    Program,
    Var,
    Vector,
    parse,
)


class _DfnClosure:
    """A dfn paired with its defining environment."""

    def __init__(self, dfn: Dfn, env: dict[str, Any]) -> None:
        self.dfn = dfn
        self.env = env


class _GuardTriggered(Exception):
    """Raised when a guard condition is true to return its value."""

    def __init__(self, value: APLArray) -> None:
        self.value = value


MONADIC_FUNCTIONS: dict[str, object] = {
    "+": lambda omega: omega,
    "-": negate,
    "×": lambda omega: S((-1 if omega.data[0] < 0 else 1 if omega.data[0] > 0 else 0)),
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
    "⍉": transpose,
    "⍋": grade_up,
    "⍒": grade_down,
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
    "⊤": encode,
    "⊥": decode,
}


def _call_dfn(
    closure: _DfnClosure,
    omega: APLArray,
    alpha: APLArray | None = None,
) -> APLArray:
    """Execute a dfn with the given arguments."""
    # Lexical scope: start from the defining environment
    local_env: dict[str, Any] = dict(closure.env)
    local_env["⍵"] = omega
    if alpha is not None:
        local_env["⍺"] = alpha
    # Store self-reference for ∇
    local_env["∇"] = closure

    result = S(0)
    try:
        for stmt in closure.dfn.body:
            if isinstance(stmt, AlphaDefault):
                # ⍺←default: set ⍺ only if not already provided
                if "⍺" not in local_env:
                    local_env["⍺"] = _evaluate(stmt.default, local_env)
            elif isinstance(stmt, Guard):
                cond = _evaluate(stmt.condition, local_env)
                if cond.data[0]:
                    raise _GuardTriggered(_evaluate(stmt.body, local_env))
            else:
                result = _evaluate(stmt, local_env)
    except _GuardTriggered as g:
        return g.value
    return result


def _evaluate(node: object, env: dict[str, Any]) -> APLArray:
    if isinstance(node, Num):
        return S(node.value)

    if isinstance(node, Vector):
        values = [el.value for el in node.elements]
        return APLArray([len(values)], list(values))

    if isinstance(node, Var):
        if node.name not in env:
            raise NameError(f"Undefined variable: {node.name}")
        val = env[node.name]
        if isinstance(val, APLArray):
            return val
        if isinstance(val, _DfnClosure):
            return val  # type: ignore[return-value]
        raise TypeError(f"Unexpected value type for {node.name}: {type(val)}")

    if isinstance(node, Omega):
        if "⍵" not in env:
            raise NameError("⍵ used outside of dfn")
        return env["⍵"]

    if isinstance(node, Alpha):
        if "⍺" not in env:
            raise NameError("⍺ used outside of dfn")
        return env["⍺"]

    if isinstance(node, Nabla):
        if "∇" not in env:
            raise NameError("∇ used outside of dfn")
        return env["∇"]  # type: ignore[return-value]

    if isinstance(node, Dfn):
        return _DfnClosure(node, env)  # type: ignore[return-value]

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

    if isinstance(node, MonadicDfnCall):
        dfn_val = _evaluate(node.dfn, env)
        operand = _evaluate(node.operand, env)
        if not isinstance(dfn_val, _DfnClosure):
            raise TypeError(f"Expected dfn, got {type(dfn_val)}")
        return _call_dfn(dfn_val, operand)

    if isinstance(node, DyadicDfnCall):
        dfn_val = _evaluate(node.dfn, env)
        left = _evaluate(node.left, env)
        right = _evaluate(node.right, env)
        if not isinstance(dfn_val, _DfnClosure):
            raise TypeError(f"Expected dfn, got {type(dfn_val)}")
        return _call_dfn(dfn_val, right, alpha=left)

    if isinstance(node, Assignment):
        value = _evaluate(node.value, env)
        env[node.name] = value
        return value if isinstance(value, APLArray) else S(0)

    if isinstance(node, InnerProduct):
        left = _evaluate(node.left, env)
        right = _evaluate(node.right, env)
        left_fn = DYADIC_FUNCTIONS.get(node.left_fn)
        right_fn = DYADIC_FUNCTIONS.get(node.right_fn)
        if left_fn is None or right_fn is None:
            raise ValueError(f"Unknown function in inner product")
        reduce_fn: Callable[[APLArray, APLArray], APLArray] = left_fn  # type: ignore[assignment]
        apply_fn: Callable[[APLArray, APLArray], APLArray] = right_fn  # type: ignore[assignment]
        return _inner_product(reduce_fn, apply_fn, left, right)

    if isinstance(node, OuterProduct):
        left = _evaluate(node.left, env)
        right = _evaluate(node.right, env)
        func = DYADIC_FUNCTIONS.get(node.function)
        if func is None:
            raise ValueError(f"Unknown function in outer product: {node.function}")
        apply_fn_: Callable[[APLArray, APLArray], APLArray] = func  # type: ignore[assignment]
        return _outer_product(apply_fn_, left, right)

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
        result: APLArray | _DfnClosure = S(0)
        for stmt in node.statements:
            result = _evaluate(stmt, env)
        if isinstance(result, APLArray):
            return result
        return S(0)

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


def _inner_product(
    reduce_fn: Callable[[APLArray, APLArray], APLArray],
    apply_fn: Callable[[APLArray, APLArray], APLArray],
    alpha: APLArray,
    omega: APLArray,
) -> APLArray:
    # Vector inner product: reduce(apply(a, b))
    if len(alpha.shape) <= 1 and len(omega.shape) <= 1:
        paired = [apply_fn(S(a), S(b)) for a, b in zip(alpha.data, omega.data)]
        result = paired[-1]
        for i in range(len(paired) - 2, -1, -1):
            result = reduce_fn(paired[i], result)
        return result
    # Matrix inner product
    if len(alpha.shape) == 2 and len(omega.shape) == 2:
        m, k1 = alpha.shape
        k2, n = omega.shape
        if k1 != k2:
            raise ValueError(f"Inner product shape mismatch: {alpha.shape} vs {omega.shape}")
        result_data: list[object] = []
        for i in range(m):
            for j in range(n):
                row = [alpha.data[i * k1 + p] for p in range(k1)]
                col = [omega.data[p * n + j] for p in range(k2)]
                paired = [apply_fn(S(a), S(b)) for a, b in zip(row, col)]
                val = paired[-1]
                for idx in range(len(paired) - 2, -1, -1):
                    val = reduce_fn(paired[idx], val)
                result_data.append(val.data[0])
        return APLArray([m, n], result_data)
    # Vector × matrix or matrix × vector
    if len(alpha.shape) == 1 and len(omega.shape) == 2:
        k, n = omega.shape
        if len(alpha.data) != k:
            raise ValueError(f"Inner product shape mismatch")
        result_data = []
        for j in range(n):
            col = [omega.data[p * n + j] for p in range(k)]
            paired = [apply_fn(S(a), S(b)) for a, b in zip(alpha.data, col)]
            val = paired[-1]
            for idx in range(len(paired) - 2, -1, -1):
                val = reduce_fn(paired[idx], val)
            result_data.append(val.data[0])
        return APLArray([n], result_data)
    raise ValueError(f"Inner product not supported for shapes {alpha.shape} and {omega.shape}")


def _outer_product(
    func: Callable[[APLArray, APLArray], APLArray],
    alpha: APLArray,
    omega: APLArray,
) -> APLArray:
    a_data = alpha.data if not alpha.is_scalar() else [alpha.data[0]]
    b_data = omega.data if not omega.is_scalar() else [omega.data[0]]
    a_shape = alpha.shape if not alpha.is_scalar() else [1]
    b_shape = omega.shape if not omega.is_scalar() else [1]
    result_data: list[object] = []
    for a in a_data:
        for b in b_data:
            result_data.append(func(S(a), S(b)).data[0])
    return APLArray(a_shape + b_shape, result_data)


def interpret(source: str, env: dict[str, Any] | None = None) -> APLArray:
    if env is None:
        env = {}
    tree = parse(source)
    result = _evaluate(tree, env)
    if isinstance(result, _DfnClosure):
        return S(0)
    return result
