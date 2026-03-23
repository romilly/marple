
import os
import random as _random
try:
    from typing import Any, Callable
except ImportError:
    pass

from marple.arraymodel import APLArray, S
from marple.backend import is_numeric_array, np, to_list
from marple.cells import clamp_rank, decompose, reassemble, resolve_rank_spec
from marple.errors import APLError, ClassError, DomainError, IndexError_, LengthError, LimitError, RankError, SecurityError, SyntaxError_, ValueError_

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
        if node.name == "⎕TS":
            from datetime import datetime
            now = datetime.now()
            return APLArray([7], [now.year, now.month, now.day,
                                  now.hour, now.minute, now.second,
                                  now.microsecond // 1000])
        if node.name == "⎕VER":
            from marple import __version__
            import sys
            s = "MARPLE v" + __version__ + " on " + sys.platform
            return APLArray([len(s)], list(s))
        if node.name not in env:
            raise ValueError_(f"Undefined system variable: {node.name}")
        return env[node.name]

    if isinstance(node, Index):
        array = _evaluate(node.array, env)
        io = _get_io(env)
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
        operand = _evaluate(node.operand, env)
        return _dispatch_monadic(node.function, operand, env)

    if isinstance(node, DyadicFunc):
        right = _evaluate(node.right, env)
        left = _evaluate(node.left, env)
        return _dispatch_dyadic(node.function, left, right, env)

    if isinstance(node, MonadicDfnCall):
        if isinstance(node.dfn, SysVar):
            return _call_sys_function_monadic(node.dfn.name, node.operand, env)
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
        if isinstance(node.dfn, SysVar):
            return _call_sys_function_dyadic(node.dfn.name, node.left, node.right, env)
        if isinstance(node.dfn, IBeamDerived):
            right = _evaluate(node.right, env)
            left = _evaluate(node.left, env)
            fn = _resolve_ibeam(node.dfn.path)
            return _call_ibeam_dyadic(fn, left, right)
        if isinstance(node.dfn, RankDerived):
            return _apply_rank_dyadic(node.dfn, node.left, node.right, env)
        dfn_val = _evaluate(node.dfn, env)
        right = _evaluate(node.right, env)
        left = _evaluate(node.left, env)
        if isinstance(dfn_val, IBeamDerived):
            fn = _resolve_ibeam(dfn_val.path)
            return _call_ibeam_dyadic(fn, left, right)
        if not isinstance(dfn_val, _DfnClosure):
            raise DomainError(f"Expected dfn, got {type(dfn_val)}")
        return _call_dfn(dfn_val, right, alpha=left)

    if isinstance(node, Assignment):
        # Protect read-only quad-names
        _READONLY_QUADS = {"⎕A", "⎕D", "⎕TS", "⎕EN", "⎕DM"}
        if node.name in _READONLY_QUADS:
            raise DomainError(f"Cannot assign to read-only system variable {node.name}")
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
            raise ClassError("Cannot change class of " + node.name + " from " + str(name_table[node.name]) + " to " + str(new_class))
        name_table[node.name] = new_class
        env["__name_table__"] = name_table
        env[node.name] = value
        if node.name == "⎕RL" and isinstance(value, APLArray):
            _random.seed(int(value.data[0]))
        return value if isinstance(value, APLArray) else S(0)

    if isinstance(node, InnerProduct):
        right = _evaluate(node.right, env)
        left = _evaluate(node.left, env)
        left_fn = _lookup_dyadic(node.left_fn)
        right_fn = _lookup_dyadic(node.right_fn)
        if left_fn is None or right_fn is None:
            raise DomainError(f"Unknown function in inner product")
        reduce_fn: Callable[[APLArray, APLArray], APLArray] = left_fn  # type: ignore[assignment]
        apply_fn: Callable[[APLArray, APLArray], APLArray] = right_fn  # type: ignore[assignment]
        return _inner_product(reduce_fn, apply_fn, left, right)

    if isinstance(node, OuterProduct):
        right = _evaluate(node.right, env)
        left = _evaluate(node.left, env)
        # Fast path: numpy ufunc.outer
        ufunc_name = _GLYPH_UFUNC.get(node.function)
        if (
            ufunc_name
            and is_numeric_array(left.data)
            and is_numeric_array(right.data)
        ):
            ufunc = getattr(np, ufunc_name, None)
            if ufunc is not None and hasattr(ufunc, "outer"):
                a = np.reshape(left.data, left.shape) if len(left.shape) > 1 else left.data
                b = np.reshape(right.data, right.shape) if len(right.shape) > 1 else right.data
                result = ufunc.outer(a, b)
                if hasattr(result, "shape") and len(result.shape) == 0:  # type: ignore[union-attr]
                    return S(result.item())  # type: ignore[union-attr]
                result_flat = result.ravel() if hasattr(result, "ravel") else result  # type: ignore[union-attr]
                result_shape = list(result.shape) if hasattr(result, "shape") else []  # type: ignore[union-attr]
                return APLArray(result_shape, result_flat)
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


# Map glyphs to numpy ufunc names for fast outer product
_GLYPH_UFUNC: dict[str, str] = {
    "+": "add", "-": "subtract", "×": "multiply", "÷": "divide",
    "⌈": "maximum", "⌊": "minimum", "*": "power",
    "<": "less", "≤": "less_equal", "=": "equal",
    "≥": "greater_equal", ">": "greater", "≠": "not_equal",
}

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
                # Use float64 for multiply to avoid int64 overflow
                if func is multiply:
                    work_data = np.array(to_list(data), dtype=np.float64)
                else:
                    work_data = data
                if len(omega.shape) <= 1:
                    return S(ufunc.reduce(work_data).item())
                shaped = np.reshape(work_data, omega.shape)
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
    # Fast path: +.× is matrix multiply — use np.tensordot
    # (np.dot uses wrong axis pairing for rank > 2)
    if (
        reduce_fn is add
        and apply_fn is multiply
        and is_numeric_array(alpha.data)
        and is_numeric_array(omega.data)
        and hasattr(np, "tensordot")
    ):
        # Check compatible dimensions: last axis of A must match first axis of B
        if len(alpha.shape) <= 1 and len(omega.shape) <= 1:
            if len(alpha.data) != len(omega.data):
                raise LengthError(f"Inner product length error: {len(alpha.data)} vs {len(omega.data)}")
        a = np.reshape(alpha.data, alpha.shape) if len(alpha.shape) > 1 else alpha.data
        b = np.reshape(omega.data, omega.shape) if len(omega.shape) > 1 else omega.data
        result = np.tensordot(a, b, axes=([-1], [0]))
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
    result_data: list[object] = []
    for a in alpha.data:
        for b in omega.data:
            result_data.append(func(S(a), S(b)).data[0])
    result_shape = alpha.shape + omega.shape
    if not result_shape:
        return S(result_data[0])
    return APLArray(result_shape, result_data)


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
            raise ValueError_("Undefined: " + "::".join(parts))
        return result  # type: ignore[return-value]
    # User namespace — look in env namespaces
    ns = env.get("__namespaces__", {})
    if parts[0] in ns:
        result = ns[parts[0]].resolve(parts[1:])
        if result is None:
            raise ValueError_("Undefined: " + "::".join(parts))
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


def _get_io(env: dict[str, Any]) -> int:
    return int(env["⎕IO"].data[0])


def _get_ct(env: dict[str, Any]) -> float:
    return float(env["⎕CT"].data[0])


# ── Monadic handlers: (operand, env) → APLArray ──

def _m_execute(operand: APLArray, env: dict[str, Any]) -> APLArray:
    source = "".join(str(c) for c in operand.data)
    return _evaluate(parse(source, env.get("__name_table__")), env)


def _m_format(operand: APLArray, env: dict[str, Any]) -> APLArray:
    return _format_array(operand)


def _m_iota(operand: APLArray, env: dict[str, Any]) -> APLArray:
    io = _get_io(env)
    n = int(operand.data[0])
    return APLArray([n], list(range(io, n + io)))


def _m_tally(operand: APLArray, env: dict[str, Any]) -> APLArray:
    return S(1) if operand.is_scalar() else S(operand.shape[0])


def _m_grade_up(operand: APLArray, env: dict[str, Any]) -> APLArray:
    return grade_up(operand, _get_io(env))


def _m_grade_down(operand: APLArray, env: dict[str, Any]) -> APLArray:
    return grade_down(operand, _get_io(env))


def _roll(omega: APLArray, env: dict[str, Any]) -> APLArray:
    """Monadic ?: roll. ?N → random int ⎕IO..N, ?0 → random float [0,1)."""
    io = _get_io(env)
    data = to_list(omega.data)
    results: list[object] = []
    for x in data:
        n = int(x)
        if n == 0:
            results.append(_random.random())
        else:
            results.append(_random.randint(io, n - 1 + io))
    if omega.is_scalar():
        return S(results[0])
    return APLArray(list(omega.shape), results)


def _deal(left: APLArray, right: APLArray, env: dict[str, Any]) -> APLArray:
    """Dyadic ?: deal. N?M → N distinct random integers from ⎕IO..M."""
    io = _get_io(env)
    n = int(left.data[0])
    m = int(right.data[0])
    if n > m:
        raise LengthError(f"Deal: cannot choose {n} from {m}")
    result = _random.sample(range(io, m + io), n)
    return APLArray([n], result)


_MONADIC_DISPATCH: dict[str, Callable[[APLArray, dict[str, Any]], APLArray]] = {
    "⍎": _m_execute,
    "⍕": _m_format,
    "⍳": _m_iota,
    "≢": _m_tally,
    "⍋": _m_grade_up,
    "⍒": _m_grade_down,
    "?": _roll,
}


# ── Dyadic handlers: (left, right, env) → APLArray ──

def _d_format(left: APLArray, right: APLArray, env: dict[str, Any]) -> APLArray:
    return _dyadic_format(left, right)


def _d_index_of(left: APLArray, right: APLArray, env: dict[str, Any]) -> APLArray:
    return index_of(left, right, _get_io(env), _get_ct(env))


def _d_membership(left: APLArray, right: APLArray, env: dict[str, Any]) -> APLArray:
    return membership(left, right, _get_ct(env))


def _d_from(left: APLArray, right: APLArray, env: dict[str, Any]) -> APLArray:
    return from_array(left, right, _get_io(env))


def _d_match(left: APLArray, right: APLArray, env: dict[str, Any]) -> APLArray:
    return S(1 if left == right else 0)


def _d_not_match(left: APLArray, right: APLArray, env: dict[str, Any]) -> APLArray:
    return S(0 if left == right else 1)


def _d_ct_compare(left: APLArray, right: APLArray, env: dict[str, Any], glyph: str) -> APLArray:
    return _CT_COMPARISONS[glyph](left, right, _get_ct(env))  # type: ignore[operator]


_DYADIC_DISPATCH: dict[str, Callable[[APLArray, APLArray, dict[str, Any]], APLArray]] = {
    "⍕": _d_format,
    "⍳": _d_index_of,
    "∈": _d_membership,
    "?": _deal,
    "⌷": _d_from,
    "≡": _d_match,
    "≢": _d_not_match,
}


def _dispatch_monadic(glyph: str, operand: APLArray, env: dict[str, Any]) -> APLArray:
    """Dispatch a monadic primitive function."""
    handler = _MONADIC_DISPATCH.get(glyph)
    if handler is not None:
        return handler(operand, env)
    func = MONADIC_FUNCTIONS.get(glyph)
    if func is not None:
        return func(operand)  # type: ignore[operator]
    raise DomainError(f"Unknown monadic function: {glyph}")


def _dispatch_dyadic(glyph: str, left: APLArray, right: APLArray, env: dict[str, Any]) -> APLArray:
    """Dispatch a dyadic primitive function."""
    handler = _DYADIC_DISPATCH.get(glyph)
    if handler is not None:
        return handler(left, right, env)
    if glyph in _CT_COMPARISONS:
        return _d_ct_compare(left, right, env, glyph)
    func = _lookup_dyadic(glyph)
    if func is not None:
        return func(left, right)  # type: ignore[operator]
    raise DomainError(f"Unknown dyadic function: {glyph}")


def _call_sys_function_monadic(name: str, operand_node: object, env: dict[str, Any]) -> APLArray:
    """Dispatch a monadic system function call."""
    operand = _evaluate(operand_node, env)
    if name == "⎕UCS":
        if all(isinstance(x, str) for x in operand.data):
            # Chars to codepoints
            return APLArray(list(operand.shape), [ord(c) for c in operand.data])
        else:
            # Codepoints to chars
            data = to_list(operand.data)
            if operand.is_scalar():
                return APLArray([], [chr(int(data[0]))])
            return APLArray(list(operand.shape), [chr(int(x)) for x in data])
    if name == "⎕NC":
        # Expect a character vector (name)
        nc_name = "".join(str(c) for c in operand.data)
        name_table = env.get("__name_table__", {})
        return S(name_table.get(nc_name, 0))
    if name == "⎕EX":
        ex_name = "".join(str(c) for c in operand.data)
        name_table = env.get("__name_table__", {})
        if ex_name in env:
            del env[ex_name]
            if ex_name in name_table:
                del name_table[ex_name]
            return S(1)
        return S(0)
    if name == "⎕SIGNAL":
        code = int(operand.data[0])
        _ERROR_MAP = {
            1: SyntaxError_, 2: ValueError_, 3: DomainError, 4: LengthError,
            5: RankError, 6: IndexError_, 7: LimitError, 9: SecurityError,
        }
        err_class = _ERROR_MAP.get(code, DomainError)
        raise err_class(f"Signalled by ⎕SIGNAL {code}")
    raise DomainError(f"Unknown system function: {name}")


def _call_sys_function_dyadic(name: str, left_node: object, right_node: object, env: dict[str, Any]) -> APLArray:
    """Dispatch a dyadic system function call."""
    if name == "⎕EA":
        right = _evaluate(right_node, env)
        left = _evaluate(left_node, env)
        right_str = "".join(str(c) for c in right.data)
        try:
            return interpret(right_str, env)
        except APLError as e:
            env["⎕EN"] = S(e.code)
            env["⎕DM"] = APLArray([len(str(e))], list(str(e)))
            left_str = "".join(str(c) for c in left.data)
            return interpret(left_str, env)
    raise DomainError(f"Unknown dyadic system function: {name}")


def _apply_func_monadic(
    func: object,
    omega: APLArray,
    env: dict[str, Any],
) -> APLArray:
    """Apply a function monadically. Used by rank operator."""
    if isinstance(func, str):
        return _dispatch_monadic(func, omega, env)
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
        return _dispatch_dyadic(func, alpha, omega, env)
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
    data = to_list(array.data)

    def product(*lists):
        """Simple replacement for itertools.product."""
        if not lists:
            yield ()
            return
        for item in lists[0]:
            for rest in product(*lists[1:]):
                yield (item,) + rest
    # Build 0-based index lists for each axis
    axis_indices: list[list[int]] = []
    for axis, idx_node in enumerate(indices):
        if idx_node is None:
            axis_indices.append(list(range(array.shape[axis])))
        else:
            idx = _evaluate(idx_node, env)
            vals = to_list(idx.data) if not idx.is_scalar() else [idx.data[0]]
            axis_indices.append([int(v) - io for v in vals])
    # Pad missing axes with full range
    for axis in range(len(indices), len(array.shape)):
        axis_indices.append(list(range(array.shape[axis])))
    # Compute strides
    strides = [1] * len(array.shape)
    for i in range(len(array.shape) - 2, -1, -1):
        strides[i] = strides[i + 1] * array.shape[i + 1]
    # Gather results
    result: list[object] = []
    for combo in product(*axis_indices):
        flat = sum(i * s for i, s in zip(combo, strides))
        result.append(data[flat])
    # Result shape: drop singleton axes
    result_shape = [len(ai) for ai in axis_indices if len(ai) > 1]
    if not result_shape:
        return S(result[0])
    return APLArray(result_shape, result)


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


_SYSTEM_DEFAULTS: dict[str, Any] = {
    "⎕IO": S(1),
    "⎕CT": S(1e-14),
    "⎕PP": S(10),
    "⎕EN": S(0),
    "⎕DM": APLArray([0], []),
    "⎕A": APLArray([26], list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")),
    "⎕D": APLArray([10], list("0123456789")),
    "⎕WSID": APLArray([8], list("CLEAR WS")),
    "⎕RL": S(1),
}


def default_env() -> dict[str, Any]:
    """Create a fresh environment with all system variable defaults."""
    env = dict(_SYSTEM_DEFAULTS)
    _random.seed(1)
    return env


def interpret(source: str, env: dict[str, Any] | None = None) -> APLArray:
    env = env or default_env()
    # Handle #import directives
    if source.strip().startswith("#import"):
        return _handle_import(source.strip(), env)
    name_table = env.get("__name_table__", {})
    # System functions are always classified as functions
    for qfn in ("⎕EA", "⎕UCS", "⎕NC", "⎕EX", "⎕SIGNAL"):
        name_table[qfn] = NC_FUNCTION
    env["__name_table__"] = name_table
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
