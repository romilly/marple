from __future__ import annotations

import os
from typing import Any, Callable

from marple.arraymodel import APLArray, S
from marple.backend import is_numeric_array, np, to_list
from marple.cells import clamp_rank, decompose, reassemble, resolve_rank_spec
from marple.errors import ClassError, DomainError, LengthError, RankError, SecurityError, ValueError_

# Name classes (following Dyalog ⎕NC convention)
NC_UNKNOWN = 0
NC_ARRAY = 2
NC_FUNCTION = 3
NC_OPERATOR = 4
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
    circular,
    logical_not,
    logical_or,
    pi_times,
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
    expand,
    from_array,
    grade_down,
    grade_up,
    index_of,
    iota,
    matrix_divide,
    matrix_inverse,
    membership,
    ravel,
    replicate,
    reshape,
    reverse,
    rotate,
    shape,
    take,
    transpose,
)
from marple.namespace import Namespace, load_system_workspace
from marple.parser import (
    Alpha,
    AlphaDefault,
    Assignment,
    DerivedFunc,
    Dfn,
    DyadicDfnCall,
    DyadicFunc,
    Guard,
    IBeamDerived,
    Index,
    InnerProduct,
    MonadicDfnCall,
    MonadicFunc,
    Nabla,
    Num,
    Omega,
    OuterProduct,
    Program,
    QualifiedVar,
    RankDerived,
    ReduceOp,
    ScanOp,
    Str,
    SysVar,
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
    "⌹": matrix_inverse,
    "○": pi_times,
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
    "∧": logical_and,
    "∨": logical_or,
    "⍴": reshape,
    ",": catenate,
    "↑": take,
    "↓": drop,
    "⌽": rotate,
    "⊤": encode,
    "⊥": decode,
    "/": replicate,
    "\\": expand,
    "⌹": matrix_divide,
    "○": circular,
}


def _format_array(omega: APLArray) -> APLArray:
    """Monadic ⍕: format an array as a character vector."""
    if omega.is_scalar():
        s = str(omega.data[0])
    else:
        parts = []
        for val in omega.data:
            parts.append(str(val))
        s = " ".join(parts)
    chars = list(s)
    return APLArray([len(chars)], chars)


def _dyadic_format(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic ⍕: format with width (scalar left) or width+precision (2-element left)."""
    if alpha.is_scalar():
        width = int(alpha.data[0])
        precision = None
    else:
        width = int(alpha.data[0])
        precision = int(alpha.data[1]) if len(alpha.data) > 1 else None
    values = omega.data if not omega.is_scalar() else [omega.data[0]]
    result_chars: list[str] = []
    for v in values:
        if precision is not None:
            formatted = f"{float(v):.{precision}f}"
        else:
            formatted = str(v)
        formatted = formatted.rjust(width)
        result_chars.extend(list(formatted))
    return APLArray([len(result_chars)], result_chars)


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

    if isinstance(node, Str):
        chars = list(node.value)
        return APLArray([len(chars)], chars)

    if isinstance(node, Vector):
        values = [el.value for el in node.elements]
        return APLArray([len(values)], list(values))

    if isinstance(node, Var):
        if node.name not in env:
            raise ValueError_(f"Undefined variable: {node.name}")
        val = env[node.name]
        if isinstance(val, APLArray):
            return val
        if isinstance(val, (_DfnClosure, IBeamDerived)):
            return val  # type: ignore[return-value]
        raise DomainError(f"Unexpected value type for {node.name}: {type(val)}")

    if isinstance(node, QualifiedVar):
        return _resolve_qualified(node.parts, env)

    if isinstance(node, SysVar):
        if node.name not in env:
            raise ValueError_(f"Undefined system variable: {node.name}")
        return env[node.name]

    if isinstance(node, Index):
        array = _evaluate(node.array, env)
        io = int(env.get("⎕IO", S(1)).data[0])
        return _bracket_index(array, node.indices, env, io)

    if isinstance(node, Omega):
        if "⍵" not in env:
            raise ValueError_("⍵ used outside of dfn")
        return env["⍵"]

    if isinstance(node, Alpha):
        if "⍺" not in env:
            raise ValueError_("⍺ used outside of dfn")
        return env["⍺"]

    if isinstance(node, Nabla):
        if "∇" not in env:
            raise ValueError_("∇ used outside of dfn")
        return env["∇"]  # type: ignore[return-value]

    if isinstance(node, Dfn):
        return _DfnClosure(node, env)  # type: ignore[return-value]

    if isinstance(node, IBeamDerived):
        return node  # type: ignore[return-value]

    if isinstance(node, MonadicFunc):
        if node.function == "⍎":
            operand = _evaluate(node.operand, env)
            source = "".join(str(c) for c in operand.data)
            return _evaluate(parse(source, env.get("__name_table__")), env)
        if node.function == "⍕":
            operand = _evaluate(node.operand, env)
            return _format_array(operand)
        if node.function == "⍳":
            operand = _evaluate(node.operand, env)
            io = int(env.get("⎕IO", S(1)).data[0])
            n = int(operand.data[0])
            return APLArray([n], list(range(io, n + io)))
        if node.function == "≢":
            operand = _evaluate(node.operand, env)
            if operand.is_scalar():
                return S(1)
            return S(operand.shape[0])
        if node.function in ("⍋", "⍒"):
            operand = _evaluate(node.operand, env)
            io = int(env.get("⎕IO", S(1)).data[0])
            if node.function == "⍋":
                return grade_up(operand, io)
            return grade_down(operand, io)
        operand = _evaluate(node.operand, env)
        func = MONADIC_FUNCTIONS.get(node.function)
        if func is None:
            raise DomainError(f"Unknown monadic function: {node.function}")
        return func(operand)  # type: ignore[operator]

    if isinstance(node, DyadicFunc):
        if node.function == "⍕":
            left = _evaluate(node.left, env)
            right = _evaluate(node.right, env)
            return _dyadic_format(left, right)
        if node.function == "⍳":
            left = _evaluate(node.left, env)
            right = _evaluate(node.right, env)
            io = int(env.get("⎕IO", S(1)).data[0])
            ct = float(env.get("⎕CT", S(1e-14)).data[0])
            return index_of(left, right, io, ct)
        if node.function in _CT_COMPARISONS:
            left = _evaluate(node.left, env)
            right = _evaluate(node.right, env)
            ct = float(env.get("⎕CT", S(1e-14)).data[0])
            return _CT_COMPARISONS[node.function](left, right, ct)  # type: ignore[operator]
        if node.function == "∈":
            left = _evaluate(node.left, env)
            right = _evaluate(node.right, env)
            ct = float(env.get("⎕CT", S(1e-14)).data[0])
            return membership(left, right, ct)
        if node.function == "⌷":
            left = _evaluate(node.left, env)
            right = _evaluate(node.right, env)
            io = int(env.get("⎕IO", S(1)).data[0])
            return from_array(left, right, io)
        if node.function == "≡":
            left = _evaluate(node.left, env)
            right = _evaluate(node.right, env)
            return S(1 if left == right else 0)
        if node.function == "≢":
            left = _evaluate(node.left, env)
            right = _evaluate(node.right, env)
            return S(0 if left == right else 1)
        left = _evaluate(node.left, env)
        right = _evaluate(node.right, env)
        func = DYADIC_FUNCTIONS.get(node.function)
        if func is None:
            raise DomainError(f"Unknown dyadic function: {node.function}")
        return func(left, right)  # type: ignore[operator]

    if isinstance(node, MonadicDfnCall):
        if isinstance(node.dfn, IBeamDerived):
            operand = _evaluate(node.operand, env)
            fn = _resolve_ibeam(node.dfn.path)
            return _call_ibeam(fn, operand)
        if isinstance(node.dfn, RankDerived):
            return _apply_rank_monadic(node.dfn, node.operand, env)
        dfn_val = _evaluate(node.dfn, env)
        operand = _evaluate(node.operand, env)
        if isinstance(dfn_val, IBeamDerived):
            fn = _resolve_ibeam(dfn_val.path)
            return _call_ibeam(fn, operand)
        if not isinstance(dfn_val, _DfnClosure):
            raise DomainError(f"Expected dfn, got {type(dfn_val)}")
        return _call_dfn(dfn_val, operand)

    if isinstance(node, DyadicDfnCall):
        if isinstance(node.dfn, IBeamDerived):
            left = _evaluate(node.left, env)
            right = _evaluate(node.right, env)
            fn = _resolve_ibeam(node.dfn.path)
            return _call_ibeam_dyadic(fn, left, right)
        if isinstance(node.dfn, RankDerived):
            return _apply_rank_dyadic(node.dfn, node.left, node.right, env)
        dfn_val = _evaluate(node.dfn, env)
        left = _evaluate(node.left, env)
        right = _evaluate(node.right, env)
        if isinstance(dfn_val, IBeamDerived):
            fn = _resolve_ibeam(dfn_val.path)
            return _call_ibeam_dyadic(fn, left, right)
        if not isinstance(dfn_val, _DfnClosure):
            raise DomainError(f"Expected dfn, got {type(dfn_val)}")
        return _call_dfn(dfn_val, right, alpha=left)

    if isinstance(node, Assignment):
        value = _evaluate(node.value, env)
        # Classify and check name class
        if isinstance(value, (_DfnClosure, IBeamDerived)):
            new_class = NC_FUNCTION
        elif isinstance(value, APLArray):
            new_class = NC_ARRAY
        else:
            new_class = NC_UNKNOWN
        name_table = env.get("__name_table__", {})
        if node.name in name_table and name_table[node.name] != new_class:
            raise ClassError(f"Cannot change class of '{node.name}' from {name_table[node.name]} to {new_class}")
        name_table[node.name] = new_class
        env["__name_table__"] = name_table
        env[node.name] = value
        return value if isinstance(value, APLArray) else S(0)

    if isinstance(node, InnerProduct):
        left = _evaluate(node.left, env)
        right = _evaluate(node.right, env)
        left_fn = _lookup_dyadic(node.left_fn)
        right_fn = _lookup_dyadic(node.right_fn)
        if left_fn is None or right_fn is None:
            raise DomainError(f"Unknown function in inner product")
        reduce_fn: Callable[[APLArray, APLArray], APLArray] = left_fn  # type: ignore[assignment]
        apply_fn: Callable[[APLArray, APLArray], APLArray] = right_fn  # type: ignore[assignment]
        return _inner_product(reduce_fn, apply_fn, left, right)

    if isinstance(node, OuterProduct):
        left = _evaluate(node.left, env)
        right = _evaluate(node.right, env)
        func = _lookup_dyadic(node.function)
        if func is None:
            raise DomainError(f"Unknown function in outer product: {node.function}")
        apply_fn_: Callable[[APLArray, APLArray], APLArray] = func  # type: ignore[assignment]
        return _outer_product(apply_fn_, left, right)

    if isinstance(node, DerivedFunc):
        operand = _evaluate(node.operand, env)
        func = _lookup_dyadic(node.function)
        if func is None:
            raise DomainError(f"Unknown function for operator: {node.function}")
        if node.operator == "/":
            return _reduce(func, operand)  # type: ignore[arg-type]
        if node.operator == "\\":
            return _scan(func, operand)  # type: ignore[arg-type]
        raise DomainError(f"Unknown operator: {node.operator}")

    if isinstance(node, Program):
        result: APLArray | _DfnClosure = S(0)
        for stmt in node.statements:
            result = _evaluate(stmt, env)
        if isinstance(result, APLArray):
            return result
        return S(0)

    raise DomainError(f"Unknown AST node: {type(node)}")


# Map function objects to numpy ufunc names for fast reduce/scan
_UFUNC_MAP: dict[object, str] = {
    add: "add",
    subtract: "subtract",
    multiply: "multiply",
    divide: "divide",
    maximum: "maximum",
    minimum: "minimum",
    power: "power",
}

# Commutative ops where right-to-left = left-to-right
_COMMUTATIVE = {add, multiply, maximum, minimum}


def _reduce_vector(
    func: Callable[[APLArray, APLArray], APLArray],
    data: list[Any],
) -> Any:
    """Reduce a flat list right-to-left, returning a scalar value."""
    result = S(data[-1])
    for i in range(len(data) - 2, -1, -1):
        result = func(S(data[i]), result)
    return result.data[0]


def _reduce(
    func: Callable[[APLArray, APLArray], APLArray],
    omega: APLArray,
) -> APLArray:
    data = omega.data
    if len(data) == 0:
        raise DomainError("Cannot reduce empty array")

    # Fast path: use numpy ufunc.reduce (commutative ops only)
    if func in _COMMUTATIVE:
        ufunc_name = _UFUNC_MAP.get(func)
        if ufunc_name and is_numeric_array(data):
            ufunc = getattr(np, ufunc_name, None)
            if ufunc is not None and hasattr(ufunc, "reduce"):
                if len(omega.shape) <= 1:
                    return S(ufunc.reduce(data).item())
                shaped = np.reshape(data, omega.shape)
                result = ufunc.reduce(shaped, axis=-1)
                return APLArray(list(result.shape), result.ravel())

    # Fallback: Python loop
    # Reduce along last axis
    if len(omega.shape) <= 1:
        return S(_reduce_vector(func, to_list(data)))
    # Higher rank: reduce each row (last-axis slice)
    last = omega.shape[-1]
    new_shape = omega.shape[:-1]
    data_list = to_list(data)
    n_rows = len(data_list) // last
    results: list[Any] = []
    for i in range(n_rows):
        row = data_list[i * last : (i + 1) * last]
        results.append(_reduce_vector(func, row))
    return APLArray(new_shape, results)


def _scan(
    func: Callable[[APLArray, APLArray], APLArray],
    omega: APLArray,
) -> APLArray:
    if len(omega.shape) <= 1:
        data = omega.data
        if len(data) == 0:
            return APLArray([0], [])
        results = [data[0]]
        acc = S(data[0])
        for i in range(1, len(data)):
            acc = func(acc, S(data[i]))
            results.append(acc.data[0])
        return APLArray([len(results)], results)
    # Higher rank: scan along last axis
    last = omega.shape[-1]
    n_rows = len(omega.data) // last
    results: list[Any] = []
    for i in range(n_rows):
        row = omega.data[i * last : (i + 1) * last]
        acc = S(row[0])
        results.append(row[0])
        for j in range(1, last):
            acc = func(acc, S(row[j]))
            results.append(acc.data[0])
    return APLArray(list(omega.shape), results)


def _inner_product(
    reduce_fn: Callable[[APLArray, APLArray], APLArray],
    apply_fn: Callable[[APLArray, APLArray], APLArray],
    alpha: APLArray,
    omega: APLArray,
) -> APLArray:
    # Fast path: +.× is matrix multiply — use np.dot
    if (
        reduce_fn is add
        and apply_fn is multiply
        and is_numeric_array(alpha.data)
        and is_numeric_array(omega.data)
    ):
        # Check compatible dimensions
        if len(alpha.shape) <= 1 and len(omega.shape) <= 1:
            if len(alpha.data) != len(omega.data):
                raise LengthError(f"Inner product length error: {len(alpha.data)} vs {len(omega.data)}")
        a = np.reshape(alpha.data, alpha.shape) if len(alpha.shape) > 1 else alpha.data
        b = np.reshape(omega.data, omega.shape) if len(omega.shape) > 1 else omega.data
        result = np.dot(a, b)
        if hasattr(result, "shape") and len(result.shape) == 0:
            return S(result.item())
        result_flat = result.ravel() if hasattr(result, "ravel") else result
        result_shape = list(result.shape) if hasattr(result, "shape") else [len(result_flat)]
        return APLArray(result_shape, result_flat)

    # Vector inner product: reduce(apply(a, b))
    if len(alpha.shape) <= 1 and len(omega.shape) <= 1:
        if len(alpha.data) != len(omega.data):
            raise LengthError(f"Inner product length error: {len(alpha.data)} vs {len(omega.data)}")
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
            raise LengthError(f"Inner product shape mismatch: {alpha.shape} vs {omega.shape}")
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
            raise LengthError(f"Inner product shape mismatch")
        result_data = []
        for j in range(n):
            col = [omega.data[p * n + j] for p in range(k)]
            paired = [apply_fn(S(a), S(b)) for a, b in zip(alpha.data, col)]
            val = paired[-1]
            for idx in range(len(paired) - 2, -1, -1):
                val = reduce_fn(paired[idx], val)
            result_data.append(val.data[0])
        return APLArray([n], result_data)
    raise RankError(f"Inner product not supported for shapes {alpha.shape} and {omega.shape}")


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


_CT_COMPARISONS: dict[str, object] = {
    "<": less_than,
    "≤": less_equal,
    "=": equal,
    "≥": greater_equal,
    ">": greater_than,
    "≠": not_equal,
}

def _lookup_dyadic(name: str) -> object | None:
    """Look up a dyadic function by glyph, including CT comparisons."""
    f = DYADIC_FUNCTIONS.get(name)
    if f is not None:
        return f
    return _CT_COMPARISONS.get(name)


_sys_workspace: Namespace | None = None


def _get_sys_workspace() -> Namespace:
    global _sys_workspace
    if _sys_workspace is None:
        import marple.stdlib
        stdlib_path = os.path.dirname(marple.stdlib.__file__)
        _sys_workspace = load_system_workspace(stdlib_path)
    return _sys_workspace


def _resolve_qualified(parts: list[str], env: dict[str, Any]) -> Any:
    """Resolve a qualified name like ['$', 'str', 'upper']."""
    if parts[0] == "$":
        sys_ws = _get_sys_workspace()
        result = sys_ws.resolve(parts[1:])
        if result is None:
            raise ValueError_(f"Undefined: {'::'.join(parts)}")
        return result  # type: ignore[return-value]
    # User namespace — look in env namespaces
    ns = env.get("__namespaces__", {})
    if parts[0] in ns:
        result = ns[parts[0]].resolve(parts[1:])
        if result is None:
            raise ValueError_(f"Undefined: {'::'.join(parts)}")
        return result  # type: ignore[return-value]
    raise ValueError_(f"Undefined namespace: {parts[0]}")


_ibeam_cache: dict[str, Any] = {}


def _resolve_ibeam(path: str) -> Any:
    """Resolve an i-beam path string to a Python callable."""
    if path in _ibeam_cache:
        return _ibeam_cache[path]
    # Check allowlist
    allowed = os.environ.get("MARPLE_IBEAM_ALLOW")
    if allowed is not None:
        prefixes = [p.strip() for p in allowed.split(",")]
        if not any(path.startswith(p) for p in prefixes):
            raise SecurityError(f"i-beam path not allowed: {path}")
    # Resolve
    parts = path.rsplit(".", 1)
    if len(parts) != 2:
        raise DomainError(f"invalid i-beam path: {path}")
    module_path, func_name = parts
    try:
        import importlib
        module = importlib.import_module(module_path)
        fn = getattr(module, func_name)
    except (ImportError, AttributeError) as e:
        raise DomainError(f"{e}") from e
    _ibeam_cache[path] = fn
    return fn


def _call_ibeam(fn: Any, right: APLArray) -> APLArray:
    """Call a Python function monadically via i-beam."""
    try:
        result = fn(right)
    except Exception as e:
        raise DomainError(f"{e}") from e
    if not isinstance(result, APLArray):
        raise DomainError(f"i-beam function must return APLArray, got {type(result)}")
    return result


def _call_ibeam_dyadic(fn: Any, left: APLArray, right: APLArray) -> APLArray:
    """Call a Python function dyadically via i-beam."""
    try:
        result = fn(left, right)
    except Exception as e:
        raise DomainError(f"{e}") from e
    if not isinstance(result, APLArray):
        raise DomainError(f"i-beam function must return APLArray, got {type(result)}")
    return result


def _apply_func_monadic(
    func: object,
    omega: APLArray,
    env: dict[str, Any],
) -> APLArray:
    """Apply a function monadically. Used by rank operator."""
    if isinstance(func, str):
        # Primitive glyph — build a MonadicFunc node and evaluate
        from marple.parser import MonadicFunc as MF, Num as N
        # Create a dummy AST and evaluate
        node = MF(func, N(0))  # dummy operand, won't be used
        # Instead, directly look up and apply
        if func == "⍳":
            io = int(env.get("⎕IO", S(1)).data[0])
            n = int(omega.data[0])
            return APLArray([n], list(range(io, n + io)))
        if func in ("⍋", "⍒"):
            io = int(env.get("⎕IO", S(1)).data[0])
            if func == "⍋":
                return grade_up(omega, io)
            return grade_down(omega, io)
        f = MONADIC_FUNCTIONS.get(func)
        if f is not None:
            return f(omega)  # type: ignore[operator]
        raise DomainError(f"Unknown monadic function: {func}")
    if isinstance(func, ReduceOp):
        f = _lookup_dyadic(func.function)
        if f is None:
            raise DomainError(f"Unknown function for reduce: {func.function}")
        return _reduce(f, omega)  # type: ignore[arg-type]
    if isinstance(func, ScanOp):
        f = _lookup_dyadic(func.function)
        if f is None:
            raise DomainError(f"Unknown function for scan: {func.function}")
        return _scan(f, omega)  # type: ignore[arg-type]
    if isinstance(func, (Dfn, Var)):
        val = _evaluate(func, env)
        if isinstance(val, _DfnClosure):
            return _call_dfn(val, omega)
        raise DomainError(f"Expected dfn, got {type(val)}")
    raise DomainError(f"Cannot apply as monadic function: {type(func)}")


def _apply_func_dyadic(
    func: object,
    alpha: APLArray,
    omega: APLArray,
    env: dict[str, Any],
) -> APLArray:
    """Apply a function dyadically. Used by rank operator."""
    if isinstance(func, str):
        if func == "⌷":
            io = int(env.get("⎕IO", S(1)).data[0])
            return from_array(alpha, omega, io)
        if func in _CT_COMPARISONS:
            ct = float(env.get("⎕CT", S(1e-14)).data[0])
            return _CT_COMPARISONS[func](alpha, omega, ct)  # type: ignore[operator]
        if func == "∈":
            ct = float(env.get("⎕CT", S(1e-14)).data[0])
            return membership(alpha, omega, ct)
        f = DYADIC_FUNCTIONS.get(func)
        if f is not None:
            return f(alpha, omega)  # type: ignore[operator]
        raise DomainError(f"Unknown dyadic function: {func}")
    if isinstance(func, (Dfn, Var)):
        val = _evaluate(func, env)
        if isinstance(val, _DfnClosure):
            return _call_dfn(val, omega, alpha=alpha)
        raise DomainError(f"Expected dfn, got {type(val)}")
    raise DomainError(f"Cannot apply as dyadic function: {type(func)}")


def _apply_rank_monadic(
    rank_node: RankDerived,
    operand_node: object,
    env: dict[str, Any],
) -> APLArray:
    omega = _evaluate(operand_node, env)
    rank_spec_val = _evaluate(rank_node.rank_spec, env)
    a, _, _ = resolve_rank_spec(rank_spec_val)
    k = clamp_rank(a, len(omega.shape))
    frame_shape, cells = decompose(omega, k)
    results = [_apply_func_monadic(rank_node.function, cell, env) for cell in cells]
    return reassemble(frame_shape, results)


def _apply_rank_dyadic(
    rank_node: RankDerived,
    left_node: object,
    right_node: object,
    env: dict[str, Any],
) -> APLArray:
    alpha = _evaluate(left_node, env)
    omega = _evaluate(right_node, env)
    rank_spec_val = _evaluate(rank_node.rank_spec, env)
    _, b_rank, c_rank = resolve_rank_spec(rank_spec_val)
    b = clamp_rank(b_rank, len(alpha.shape))
    c = clamp_rank(c_rank, len(omega.shape))
    left_frame, left_cells = decompose(alpha, b)
    right_frame, right_cells = decompose(omega, c)
    # Frame agreement
    if left_frame == right_frame:
        pairs = list(zip(left_cells, right_cells))
        frame = left_frame
    elif left_frame == []:
        pairs = [(left_cells[0], rc) for rc in right_cells]
        frame = right_frame
    elif right_frame == []:
        pairs = [(lc, right_cells[0]) for lc in left_cells]
        frame = left_frame
    else:
        raise LengthError(f"Frame mismatch: {left_frame} vs {right_frame}")
    results = [_apply_func_dyadic(rank_node.function, lc, rc, env) for lc, rc in pairs]
    return reassemble(frame, results)


def _bracket_index(
    array: APLArray,
    indices: list[object | None],
    env: dict[str, Any],
    io: int,
) -> APLArray:
    if len(array.shape) <= 1:
        # Vector indexing: v[idx]
        idx_node = indices[0]
        if idx_node is None:
            return APLArray(list(array.shape), list(array.data))
        idx = _evaluate(idx_node, env)
        if idx.is_scalar():
            i = int(idx.data[0]) - io
            return S(array.data[i])
        result = [array.data[int(i) - io] for i in idx.data]
        return APLArray([len(result)], result)
    if len(array.shape) == 2:
        rows, cols = array.shape
        row_idx = indices[0] if len(indices) > 0 else None
        col_idx = indices[1] if len(indices) > 1 else None
        # Evaluate indices
        row_vals: list[int] | None = None
        col_vals: list[int] | None = None
        if row_idx is not None:
            r = _evaluate(row_idx, env)
            row_vals = [int(x) - io for x in (r.data if not r.is_scalar() else [r.data[0]])]
        if col_idx is not None:
            c = _evaluate(col_idx, env)
            col_vals = [int(x) - io for x in (c.data if not c.is_scalar() else [c.data[0]])]
        if row_vals is None:
            row_vals = list(range(rows))
        if col_vals is None:
            col_vals = list(range(cols))
        result: list[object] = []
        for r in row_vals:
            for c in col_vals:
                result.append(array.data[r * cols + c])
        if len(row_vals) == 1 and len(col_vals) == 1:
            return S(result[0])
        if len(row_vals) == 1:
            return APLArray([len(col_vals)], result)
        if len(col_vals) == 1:
            return APLArray([len(row_vals)], result)
        return APLArray([len(row_vals), len(col_vals)], result)
    raise RankError(f"Bracket indexing not supported for rank {len(array.shape)}")


def _handle_import(source: str, env: dict[str, Any]) -> APLArray:
    """Handle #import directive."""
    parts = source.split()
    # #import qualified::name [as alias]
    if len(parts) < 2:
        raise DomainError("Invalid #import directive")
    qualified = parts[1]
    alias = None
    if len(parts) >= 4 and parts[2] == "as":
        alias = parts[3]
    name_parts = qualified.split("::")
    # Resolve the value
    if name_parts[0] == "$":
        sys_ws = _get_sys_workspace()
        result = sys_ws.resolve(name_parts[1:])
        if result is None:
            raise ValueError_(f"Undefined: {qualified}")
    else:
        raise ValueError_(f"Import from non-system namespace not yet supported: {qualified}")
    # Bind in env and classify
    bind_name = alias if alias else name_parts[-1]
    env[bind_name] = result
    name_table = env.get("__name_table__", {})
    if isinstance(result, (_DfnClosure, IBeamDerived)):
        name_table[bind_name] = NC_FUNCTION
    elif isinstance(result, APLArray):
        name_table[bind_name] = NC_ARRAY
    env["__name_table__"] = name_table
    return S(0)


def interpret(source: str, env: dict[str, Any] | None = None) -> APLArray:
    if env is None:
        env = {}
    if "⎕IO" not in env:
        env["⎕IO"] = S(1)
    if "⎕CT" not in env:
        env["⎕CT"] = S(1e-14)
    # Set env for error handling (ea/en)
    from marple.stdlib.error_impl import set_env as _set_error_env
    _set_error_env(env)
    # Handle #import directives
    if source.strip().startswith("#import"):
        return _handle_import(source.strip(), env)
    name_table = env.get("__name_table__", {})
    tree = parse(source, name_table)
    result = _evaluate(tree, env)
    # Track source for dfn assignments so workspace save can reconstruct them
    if isinstance(tree, Assignment):
        value = env.get(tree.name)
        if isinstance(value, _DfnClosure):
            if "__sources__" not in env:
                env["__sources__"] = {}
            env["__sources__"][tree.name] = source.strip()
    if isinstance(result, _DfnClosure):
        return S(0)
    return result
