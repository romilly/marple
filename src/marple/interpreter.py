
import os
import random as _random
try:
    from typing import Any, Callable
except ImportError:
    pass

from marple.arraymodel import APLArray, S
from marple.backend import (
    _DOWNCAST_CT, is_numeric_array, maybe_downcast, maybe_downcast_scalar,
    maybe_upcast, np, to_list,
)
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
    replicate_first,
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
    AlphaAlpha,
    AlphaDefault,
    Assignment,
    BoundOperator,
    FmtArgs,
    FunctionRef,
    DerivedFunc,
    Dfn,
    DyadicDfnCall,
    DyadicDopCall,
    DyadicFunc,
    Guard,
    IBeamDerived,
    Index,
    InnerProduct,
    MonadicDfnCall,
    MonadicDopCall,
    MonadicFunc,
    OmegaOmega,
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
    "⌿": replicate_first,
    "\\": expand,
    "⌹": matrix_divide,
    "○": circular,
}


def _format_array(omega: APLArray) -> APLArray:
    """Monadic ⍕: format an array as a character vector."""
    from marple.formatting import format_num
    if omega.is_scalar():
        s = format_num(omega.data[0])
    else:
        parts = []
        for val in omega.data:
            parts.append(format_num(val))
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
    alpha_alpha: object | None = None,
    omega_omega: object | None = None,
) -> APLArray:
    """Execute a dfn with the given arguments."""
    # Lexical scope: start from the defining environment
    local_env: dict[str, Any] = dict(closure.env)
    local_env["⍵"] = omega
    if alpha is not None:
        local_env["⍺"] = alpha
    if alpha_alpha is not None:
        local_env["⍺⍺"] = alpha_alpha
    if omega_omega is not None:
        local_env["⍵⍵"] = omega_omega
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


def _eval_num(node: Num, env: dict[str, Any]) -> APLArray:
    value = node.value
    if isinstance(value, float) and int(env.get("⎕FR", S(645)).data[0]) == 1287:
        from decimal import Decimal
        value = Decimal(str(node.value))
    return S(value)


def _eval_str(node: Str, env: dict[str, Any]) -> APLArray:
    chars = list(node.value)
    return APLArray([len(chars)], chars)


def _eval_vector(node: Vector, env: dict[str, Any]) -> APLArray:
    values = [el.value for el in node.elements]
    return APLArray([len(values)], list(values))


def _eval_var(node: Var, env: dict[str, Any]) -> APLArray:
    if node.name not in env:
        raise ValueError_(f"Undefined variable: {node.name}")
    val = env[node.name]
    if isinstance(val, APLArray):
        return val
    if isinstance(val, (_DfnClosure, IBeamDerived)):
        return val  # type: ignore[return-value]
    raise DomainError(f"Unexpected value type for {node.name}: {type(val)}")


def _eval_qualified(node: QualifiedVar, env: dict[str, Any]) -> APLArray:
    return _resolve_qualified(node.parts, env)


def _eval_sysvar(node: SysVar, env: dict[str, Any]) -> APLArray:
    if node.name == "⎕TS":
        import time
        now = time.time()
        t = time.localtime(now)
        ms = int((now % 1) * 1000)
        return APLArray([7], [t[0], t[1], t[2], t[3], t[4], t[5], ms])
    if node.name == "⎕VER":
        from marple import __version__
        import sys
        s = "MARPLE v" + __version__ + " on " + sys.platform
        return APLArray([len(s)], list(s))
    if node.name not in env:
        raise ValueError_(f"Undefined system variable: {node.name}")
    return env[node.name]


def _eval_index(node: Index, env: dict[str, Any]) -> APLArray:
    array = _evaluate(node.array, env)
    io = _get_io(env)
    return _bracket_index(array, node.indices, env, io)


def _eval_omega(node: Omega, env: dict[str, Any]) -> APLArray:
    if "⍵" not in env:
        raise ValueError_("⍵ used outside of dfn")
    return env["⍵"]


def _eval_alpha(node: Alpha, env: dict[str, Any]) -> APLArray:
    if "⍺" not in env:
        raise ValueError_("⍺ used outside of dfn")
    return env["⍺"]


def _eval_alpha_alpha(node: AlphaAlpha, env: dict[str, Any]) -> APLArray:
    if "⍺⍺" not in env:
        raise ValueError_("⍺⍺ used outside of dop")
    return env["⍺⍺"]  # type: ignore[return-value]


def _eval_omega_omega(node: OmegaOmega, env: dict[str, Any]) -> APLArray:
    if "⍵⍵" not in env:
        raise ValueError_("⍵⍵ used outside of dop")
    return env["⍵⍵"]  # type: ignore[return-value]


def _eval_nabla(node: Nabla, env: dict[str, Any]) -> APLArray:
    if "∇" not in env:
        raise ValueError_("∇ used outside of dfn")
    return env["∇"]  # type: ignore[return-value]


def _eval_function_ref(node: FunctionRef, env: dict[str, Any]) -> APLArray:
    return node  # type: ignore[return-value]


def _eval_dfn(node: Dfn, env: dict[str, Any]) -> APLArray:
    return _DfnClosure(node, env)  # type: ignore[return-value]


def _eval_ibeam(node: IBeamDerived, env: dict[str, Any]) -> APLArray:
    return node  # type: ignore[return-value]


def _eval_monadic_func(node: MonadicFunc, env: dict[str, Any]) -> APLArray:
    operand = _evaluate(node.operand, env)
    return _dispatch_monadic(node.function, operand, env)


def _eval_dyadic_func(node: DyadicFunc, env: dict[str, Any]) -> APLArray:
    right = _evaluate(node.right, env)
    left = _evaluate(node.left, env)
    return _dispatch_dyadic(node.function, left, right, env)


def _eval_monadic_dfn_call(node: MonadicDfnCall, env: dict[str, Any]) -> APLArray:
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
    if isinstance(dfn_val, FunctionRef):
        return _dispatch_monadic(dfn_val.glyph, operand, env)
    if not isinstance(dfn_val, _DfnClosure):
        raise DomainError(f"Expected dfn, got {type(dfn_val)}")
    return _call_dfn(dfn_val, operand)


def _eval_monadic_dop_call(node: MonadicDopCall, env: dict[str, Any]) -> APLArray:
    dop_val = _evaluate(node.op_name, env)
    if not isinstance(dop_val, _DfnClosure):
        raise DomainError(f"Expected operator, got {type(dop_val)}")
    operand = _evaluate(node.operand, env)
    argument = _evaluate(node.argument, env)
    alpha = _evaluate(node.alpha, env) if node.alpha is not None else None
    return _call_dfn(dop_val, argument, alpha_alpha=operand, alpha=alpha)


def _eval_dyadic_dop_call(node: DyadicDopCall, env: dict[str, Any]) -> APLArray:
    dop_val = _evaluate(node.op_name, env)
    if not isinstance(dop_val, _DfnClosure):
        raise DomainError(f"Expected operator, got {type(dop_val)}")
    left_operand = _evaluate(node.operand, env)   # ⍺⍺
    right_operand = _evaluate(node.left, env)      # ⍵⍵
    argument = _evaluate(node.right, env)           # ⍵
    return _call_dfn(dop_val, argument,
                     alpha_alpha=left_operand, omega_omega=right_operand)


def _eval_dyadic_dfn_call(node: DyadicDfnCall, env: dict[str, Any]) -> APLArray:
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
    if isinstance(dfn_val, FunctionRef):
        return _dispatch_dyadic(dfn_val.glyph, left, right, env)
    if not isinstance(dfn_val, _DfnClosure):
        raise DomainError(f"Expected dfn, got {type(dfn_val)}")
    return _call_dfn(dfn_val, right, alpha=left)


_READONLY_QUADS = frozenset({"⎕A", "⎕D", "⎕TS", "⎕EN", "⎕DM"})


def _eval_assignment(node: Assignment, env: dict[str, Any]) -> APLArray:
    if node.name in _READONLY_QUADS:
        raise DomainError(f"Cannot assign to read-only system variable {node.name}")
    value = _evaluate(node.value, env)
    if isinstance(value, (_DfnClosure, IBeamDerived)):
        new_class = NC_FUNCTION
    elif isinstance(value, APLArray):
        new_class = NC_ARRAY
    else:
        new_class = NC_UNKNOWN
    name_table = env.get("__name_table__", {})
    if node.name in name_table and name_table[node.name] != new_class:
        raise ClassError("Cannot change class of " + node.name +
                         " from " + str(name_table[node.name]) +
                         " to " + str(new_class))
    name_table[node.name] = new_class
    env["__name_table__"] = name_table
    env[node.name] = value
    if node.name == "⎕RL" and isinstance(value, APLArray):
        _random.seed(int(value.data[0]))
    if node.name == "⎕FR" and isinstance(value, APLArray):
        fr_val = int(value.data[0])
        if fr_val not in (645, 1287):
            raise DomainError("⎕FR must be 645 or 1287")
    return value if isinstance(value, APLArray) else S(0)


def _eval_inner_product(node: InnerProduct, env: dict[str, Any]) -> APLArray:
    right = _evaluate(node.right, env)
    left = _evaluate(node.left, env)
    left_fn = _lookup_dyadic(node.left_fn)
    right_fn = _lookup_dyadic(node.right_fn)
    if left_fn is None or right_fn is None:
        raise DomainError("Unknown function in inner product")
    return _inner_product(left_fn, right_fn, left, right)  # type: ignore[arg-type]


def _eval_outer_product(node: OuterProduct, env: dict[str, Any]) -> APLArray:
    right = _evaluate(node.right, env)
    left = _evaluate(node.left, env)
    ufunc_name = _GLYPH_UFUNC.get(node.function)
    if (ufunc_name and is_numeric_array(left.data)
            and is_numeric_array(right.data)):
        ufunc = getattr(np, ufunc_name, None)
        if ufunc is not None and hasattr(ufunc, "outer"):
            from marple.backend import _OVERFLOW_UFUNCS
            a = np.reshape(left.data, left.shape) if len(left.shape) > 1 else left.data
            b = np.reshape(right.data, right.shape) if len(right.shape) > 1 else right.data
            if ufunc_name in _OVERFLOW_UFUNCS:
                a = maybe_upcast(a)
                b = maybe_upcast(b)
            result = ufunc.outer(a, b)
            if hasattr(result, "shape") and len(result.shape) == 0:  # type: ignore[union-attr]
                raw = result.item()  # type: ignore[union-attr]
                if ufunc_name in _OVERFLOW_UFUNCS:
                    raw = maybe_downcast_scalar(raw, _DOWNCAST_CT)
                return S(raw)
            result_shape = list(result.shape) if hasattr(result, "shape") else []  # type: ignore[union-attr]
            result_flat = result.ravel() if hasattr(result, "ravel") else result  # type: ignore[union-attr]
            if ufunc_name in _OVERFLOW_UFUNCS:
                result_flat = maybe_downcast(result_flat, _DOWNCAST_CT)
            return APLArray(result_shape, result_flat)
    func = _lookup_dyadic(node.function)
    if func is None:
        raise DomainError(f"Unknown function in outer product: {node.function}")
    return _outer_product(func, left, right)  # type: ignore[arg-type]


def _eval_derived_func(node: DerivedFunc, env: dict[str, Any]) -> APLArray:
    operand = _evaluate(node.operand, env)
    func: Any = None
    if isinstance(node.function, str):
        func = _lookup_dyadic(node.function)
    elif isinstance(node.function, (AlphaAlpha, OmegaOmega)):
        fn_val = _evaluate(node.function, env)
        if isinstance(fn_val, FunctionRef):
            func = _lookup_dyadic(fn_val.glyph)
        elif isinstance(fn_val, _DfnClosure):
            func = lambda a, o, _c=fn_val: _call_dfn(_c, o, alpha=a)
        else:
            raise DomainError("⍺⍺ is not a function in this context")
    elif isinstance(node.function, (Dfn, Var)):
        fn_val = _evaluate(node.function, env)
        if isinstance(fn_val, _DfnClosure):
            func = lambda a, o, _c=fn_val: _call_dfn(_c, o, alpha=a)
        else:
            raise DomainError(f"Expected function for operator, got {type(fn_val)}")
    elif isinstance(node.function, FunctionRef):
        func = _lookup_dyadic(node.function.glyph)
    if func is None:
        raise DomainError(f"Unknown function for operator: {node.function}")
    _REDUCE_OPS: dict[str, Any] = {
        "/": _reduce, "⌿": _reduce_first,
        "\\": _scan, "⍀": _scan_first,
    }
    op_fn = _REDUCE_OPS.get(node.operator)
    if op_fn is None:
        raise DomainError(f"Unknown operator: {node.operator}")
    return op_fn(func, operand)  # type: ignore[arg-type]


def _eval_program(node: Program, env: dict[str, Any]) -> APLArray:
    result: APLArray | _DfnClosure = S(0)
    for stmt in node.statements:
        result = _evaluate(stmt, env)
    return result if isinstance(result, APLArray) else S(0)


_EVAL_DISPATCH: dict[type, Any] = {
    Num: _eval_num,
    Str: _eval_str,
    Vector: _eval_vector,
    Var: _eval_var,
    QualifiedVar: _eval_qualified,
    SysVar: _eval_sysvar,
    Index: _eval_index,
    Omega: _eval_omega,
    Alpha: _eval_alpha,
    AlphaAlpha: _eval_alpha_alpha,
    OmegaOmega: _eval_omega_omega,
    Nabla: _eval_nabla,
    FunctionRef: _eval_function_ref,
    Dfn: _eval_dfn,
    IBeamDerived: _eval_ibeam,
    MonadicFunc: _eval_monadic_func,
    DyadicFunc: _eval_dyadic_func,
    MonadicDfnCall: _eval_monadic_dfn_call,
    MonadicDopCall: _eval_monadic_dop_call,
    DyadicDopCall: _eval_dyadic_dop_call,
    DyadicDfnCall: _eval_dyadic_dfn_call,
    Assignment: _eval_assignment,
    InnerProduct: _eval_inner_product,
    OuterProduct: _eval_outer_product,
    DerivedFunc: _eval_derived_func,
    Program: _eval_program,
}


def _evaluate(node: object, env: dict[str, Any]) -> APLArray:
    handler = _EVAL_DISPATCH.get(type(node))
    if handler is not None:
        return handler(node, env)
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
                work_data = maybe_upcast(data)
                if len(omega.shape) <= 1:
                    raw = ufunc.reduce(work_data).item()
                    return S(maybe_downcast_scalar(raw, _DOWNCAST_CT))
                shaped = np.reshape(work_data, omega.shape)
                result = ufunc.reduce(shaped, axis=-1)
                result = maybe_downcast(result, _DOWNCAST_CT)
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


def _reduce_first(
    func: Callable[[APLArray, APLArray], APLArray],
    omega: APLArray,
) -> APLArray:
    """Reduce along the first axis (⌿)."""
    if len(omega.shape) <= 1:
        return _reduce(func, omega)
    # Extract major cells and reduce pairwise
    first = omega.shape[0]
    cell_shape = omega.shape[1:]
    cell_size = 1
    for s in cell_shape:
        cell_size *= s
    data_list = to_list(omega.data)
    # Start with first major cell
    acc = data_list[:cell_size]
    for i in range(1, first):
        cell = data_list[i * cell_size : (i + 1) * cell_size]
        paired = []
        for a, b in zip(acc, cell):
            paired.append(func(S(a), S(b)).data[0])
        acc = paired
    return APLArray(cell_shape, acc)


def _scan_first(
    func: Callable[[APLArray, APLArray], APLArray],
    omega: APLArray,
) -> APLArray:
    """Scan along the first axis (⍀)."""
    if len(omega.shape) <= 1:
        return _scan(func, omega)
    first = omega.shape[0]
    cell_shape = omega.shape[1:]
    cell_size = 1
    for s in cell_shape:
        cell_size *= s
    data_list = to_list(omega.data)
    # First major cell is unchanged
    acc = data_list[:cell_size]
    results = list(acc)
    for i in range(1, first):
        cell = data_list[i * cell_size : (i + 1) * cell_size]
        new_acc = []
        for a, b in zip(acc, cell):
            new_acc.append(func(S(a), S(b)).data[0])
        acc = new_acc
        results.extend(acc)
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
        a = maybe_upcast(a)
        b = maybe_upcast(b)
        result = np.tensordot(a, b, axes=([-1], [0]))
        if hasattr(result, "shape") and len(result.shape) == 0:
            return S(maybe_downcast_scalar(result.item(), _DOWNCAST_CT))
        result_shape = list(result.shape) if hasattr(result, "shape") else []
        result_flat = result.ravel() if hasattr(result, "ravel") else result
        if is_numeric_array(result_flat):
            result_flat = maybe_downcast(result_flat, _DOWNCAST_CT)
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
    # Vector × matrix
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
    # Matrix × vector
    if len(alpha.shape) == 2 and len(omega.shape) == 1:
        m, k1 = alpha.shape
        if k1 != len(omega.data):
            raise LengthError(f"Inner product shape mismatch")
        a_data = to_list(alpha.data)
        b_data = to_list(omega.data)
        result_data = []
        for i in range(m):
            row = [a_data[i * k1 + p] for p in range(k1)]
            paired = [apply_fn(S(a), S(b)) for a, b in zip(row, b_data)]
            val = paired[-1]
            for idx in range(len(paired) - 2, -1, -1):
                val = reduce_fn(paired[idx], val)
            result_data.append(val.data[0])
        return APLArray([m], result_data)
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
        f = marple.stdlib.__file__
        # Get directory: strip filename from path
        stdlib_path = f[:f.rfind("/")]  if "/" in f else f[:f.rfind("\\")]
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
    try:
        allowed = os.environ.get("MARPLE_IBEAM_ALLOW")
    except AttributeError:
        allowed = None
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
        module = __import__(module_path)
        # __import__ returns the top-level module; traverse to the leaf
        for part in module_path.split(".")[1:]:
            module = getattr(module, part)
        fn = getattr(module, func_name)
    except (ImportError, AttributeError) as e:
        raise DomainError(str(e)) from e
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


def _monadic_dr(operand: APLArray) -> APLArray:
    """Monadic ⎕DR: query internal data representation."""
    from marple.backend import _is_int_dtype, _is_float_dtype
    # Character data
    if len(operand.data) > 0 and isinstance(to_list(operand.data)[0], str):
        return S(80)
    # Numeric array with dtype
    if is_numeric_array(operand.data):
        dtype_str = str(operand.data.dtype)
        if "uint8" in dtype_str:
            return S(11)  # boolean
        if "int8" in dtype_str:
            return S(83)
        if "int16" in dtype_str:
            return S(163)
        if "int32" in dtype_str:
            return S(323)
        if "int64" in dtype_str:
            return S(645)  # treat as float-equivalent width
        if _is_float_dtype(operand.data):
            return S(645)
    # Python list fallback
    vals = to_list(operand.data)
    if vals:
        v = vals[0]
        if isinstance(v, str):
            return S(80)
        if isinstance(v, float):
            return S(645)
        if isinstance(v, int):
            return S(323)
    return S(0)


def _dyadic_dr(left: APLArray, right: APLArray) -> APLArray:
    """Dyadic ⎕DR: convert data representation."""
    target = int(left.data[0])
    vals = to_list(right.data)
    if target == 645:
        # Convert to float
        new_data = [float(v) for v in vals]
        return APLArray(list(right.shape), new_data)
    if target in (323, 163, 83):
        # Convert to integer
        new_data = [int(round(v)) for v in vals]
        return APLArray(list(right.shape), new_data)
    if target == 11:
        # Convert to boolean (uint8)
        from marple.backend import to_bool_array
        new_data = to_bool_array([int(bool(v)) for v in vals])
        return APLArray(list(right.shape), new_data)
    if target == 80:
        # Convert to character (via UCS)
        new_data = [chr(int(v)) for v in vals]
        return APLArray(list(right.shape), new_data)
    raise DomainError("Invalid ⎕DR type code: " + str(target))


def _sys_ucs(operand: APLArray, env: dict[str, Any]) -> APLArray:
    if all(isinstance(x, str) for x in operand.data):
        return APLArray(list(operand.shape), [ord(c) for c in operand.data])
    data = to_list(operand.data)
    if operand.is_scalar():
        return APLArray([], [chr(int(data[0]))])
    return APLArray(list(operand.shape), [chr(int(x)) for x in data])


def _sys_nc(operand: APLArray, env: dict[str, Any]) -> APLArray:
    nc_name = "".join(str(c) for c in operand.data)
    name_table = env.get("__name_table__", {})
    return S(name_table.get(nc_name, 0))


def _sys_ex(operand: APLArray, env: dict[str, Any]) -> APLArray:
    ex_name = "".join(str(c) for c in operand.data)
    name_table = env.get("__name_table__", {})
    if ex_name in env:
        del env[ex_name]
        if ex_name in name_table:
            del name_table[ex_name]
        return S(1)
    return S(0)


def _sys_signal(operand: APLArray, env: dict[str, Any]) -> APLArray:
    code = int(operand.data[0])
    _ERROR_MAP = {
        1: SyntaxError_, 2: ValueError_, 3: DomainError, 4: LengthError,
        5: RankError, 6: IndexError_, 7: LimitError, 9: SecurityError,
    }
    err_class = _ERROR_MAP.get(code, DomainError)
    raise err_class(f"Signalled by ⎕SIGNAL {code}")


def _sys_nread(operand: APLArray, env: dict[str, Any]) -> APLArray:
    path = "".join(str(c) for c in operand.data)
    with open(path) as f:
        text = f.read()
    chars = list(text)
    return APLArray([len(chars)], chars) if chars else APLArray([0], [])


def _sys_nexists(operand: APLArray, env: dict[str, Any]) -> APLArray:
    import os as _os
    path = "".join(str(c) for c in operand.data)
    try:
        _os.stat(path)
        return S(1)
    except OSError:
        return S(0)


def _sys_ndelete(operand: APLArray, env: dict[str, Any]) -> APLArray:
    import os as _os
    path = "".join(str(c) for c in operand.data)
    try:
        _os.remove(path)
    except OSError:
        raise DomainError("File not found: " + path)
    return S(0)


def _sys_cr(operand: APLArray, env: dict[str, Any]) -> APLArray:
    fn_name = "".join(str(c) for c in operand.data)
    sources = env.get("__sources__", {})
    if fn_name not in sources:
        raise DomainError("Not a defined function: " + fn_name)
    source = sources[fn_name]
    if isinstance(source, list):
        lines = source
    else:
        lines = [source]
    max_len = max(len(l) for l in lines) if lines else 0
    flat: list[object] = []
    for line in lines:
        flat.extend(list(line.ljust(max_len)))
    return APLArray([len(lines), max_len], flat)


def _sys_fx(operand: APLArray, env: dict[str, Any]) -> APLArray:
    if len(operand.shape) == 2:
        rows, cols = operand.shape
        lines = []
        for r in range(rows):
            row_chars = operand.data[r * cols : (r + 1) * cols]
            lines.append("".join(str(c) for c in row_chars).rstrip())
        text = "\n".join(lines)
    else:
        text = "".join(str(c) for c in operand.data)
    parts = text.split("←", 1)
    if len(parts) < 2:
        raise DomainError("⎕FX requires an assignment: name←{body}")
    fn_name = parts[0].strip()
    try:
        interpret(text, env)
    except APLError:
        raise DomainError("⎕FX: invalid function definition")
    if fn_name not in env or not isinstance(env[fn_name], _DfnClosure):
        raise DomainError("⎕FX did not produce a function")
    if len(operand.shape) == 2:
        sources = env.get("__sources__", {})
        sources[fn_name] = [
            "".join(str(c) for c in operand.data[r * cols : (r + 1) * cols]).rstrip()
            for r in range(rows)
        ]
        env["__sources__"] = sources
    chars = list(fn_name)
    return APLArray([len(chars)], chars)


def _sys_dl(operand: APLArray, env: dict[str, Any]) -> APLArray:
    import time as _time
    secs = float(operand.data[0])
    t0 = _time.time()
    _time.sleep(secs)
    return S(_time.time() - t0)


def _sys_nl(operand: APLArray, env: dict[str, Any]) -> APLArray:
    nc = int(operand.data[0])
    name_table = env.get("__name_table__", {})
    names = sorted(n for n, c in name_table.items()
                   if c == nc and not n.startswith("⎕") and not n.startswith("__"))
    if not names:
        return APLArray([0, 0], [])
    max_len = max(len(n) for n in names)
    chars: list[object] = []
    for n in names:
        chars.extend(list(n.ljust(max_len)))
    return APLArray([len(names), max_len], chars)


def _csv_import(operand: APLArray, env: dict[str, Any]) -> APLArray:
    """⎕CSV 'filename': read CSV, create variables from header columns."""
    import csv as _csv
    path = "".join(str(c) for c in operand.data)
    with open(path, newline="") as f:
        reader = _csv.reader(f)
        headers = next(reader)
        col_names = []
        for h in headers:
            name = h.strip().replace(" ", "_")
            name = "".join(c if c.isalnum() or c == "_" else "_" for c in name)
            col_names.append(name)
        columns: list[list[str]] = [[] for _ in col_names]
        row_count = 0
        for row in reader:
            row_count += 1
            for i, val in enumerate(row):
                if i < len(columns):
                    columns[i].append(val.strip())
    name_table = env.get("__name_table__", {})
    for col_name, col_data in zip(col_names, columns):
        try:
            nums = []
            for v in col_data:
                if "." in v:
                    nums.append(float(v))
                else:
                    nums.append(int(v))
            env[col_name] = APLArray([len(nums)], nums)
        except (ValueError, TypeError):
            max_len = max((len(v) for v in col_data), default=0)
            chars: list[object] = []
            for v in col_data:
                chars.extend(list(v.ljust(max_len)))
            env[col_name] = APLArray([len(col_data), max_len], chars)
        name_table[col_name] = NC_ARRAY
    env["__name_table__"] = name_table
    return S(row_count)


_MONADIC_SYS: dict[str, Any] = {
    "⎕UCS": _sys_ucs,
    "⎕NC": _sys_nc,
    "⎕EX": _sys_ex,
    "⎕DR": lambda op, env: _monadic_dr(op),
    "⎕SIGNAL": _sys_signal,
    "⎕NREAD": _sys_nread,
    "⎕NEXISTS": _sys_nexists,
    "⎕NDELETE": _sys_ndelete,
    "⎕CR": _sys_cr,
    "⎕FX": _sys_fx,
    "⎕DL": _sys_dl,
    "⎕NL": _sys_nl,
    "⎕CSV": _csv_import,
}


def _call_sys_function_monadic(name: str, operand_node: object, env: dict[str, Any]) -> APLArray:
    """Dispatch a monadic system function call."""
    # ⎕FMT needs the raw operand_node (for FmtArgs), not the evaluated operand
    if name == "⎕FMT":
        if isinstance(operand_node, FmtArgs):
            values = [_evaluate(arg, env) for arg in operand_node.args]
            parts = [_monadic_fmt(v) for v in values]
            all_chars: list[object] = []
            for p in parts:
                all_chars.extend(p.data)
                all_chars.append(" ")
            if all_chars:
                all_chars.pop()
            return APLArray([len(all_chars)], all_chars)
        return _monadic_fmt(_evaluate(operand_node, env))
    operand = _evaluate(operand_node, env)
    handler = _MONADIC_SYS.get(name)
    if handler is not None:
        return handler(operand, env)
    raise DomainError(f"Unknown system function: {name}")


def _monadic_fmt(operand: APLArray) -> APLArray:
    """Monadic ⎕FMT: default formatting as character vector."""
    from marple.formatting import format_num
    if operand.shape == []:
        # Scalar
        text = format_num(operand.data[0])
    elif len(operand.shape) == 1:
        # Vector
        if len(operand.data) > 0 and isinstance(operand.data[0], str):
            text = "".join(str(c) for c in operand.data)
        else:
            text = " ".join(format_num(x) for x in operand.data)
    else:
        text = str(operand)
    return APLArray([len(text)], list(text))


class _FmtGroup:
    """A format group: one data column's format, or a text insertion.

    For data groups: code is I/F/E/A/G, repeat is how many times to apply
    (e.g. 5A1 → code='A', width=1, repeat=5). Total chars = repeat * width.
    For text: code is 'TEXT', text holds the literal.
    """
    def __init__(self, code: str, width: int = 0, decimals: int = 0,
                 repeat: int = 1, text: str = "") -> None:
        self.code = code
        self.width = width
        self.decimals = decimals
        self.repeat = repeat
        self.text = text


def _parse_fmt_spec(spec: str) -> list[_FmtGroup]:
    """Parse a format specification string like 'I5,F8.2,⊂ => ⊃,5A1'.

    Each format code (with optional repetition) is ONE group consuming
    ONE data column. Text insertions don't consume columns.
    Supports both ⊂text⊃ and <text> delimiters.
    """
    groups: list[_FmtGroup] = []
    i = 0
    while i < len(spec):
        if spec[i] in " ,":
            i += 1
            continue
        # Text insertion: ⊂text⊃ or <text>
        if spec[i] in ("⊂", "<"):
            close = "⊃" if spec[i] == "⊂" else ">"
            i += 1
            end = spec.index(close, i)
            groups.append(_FmtGroup("TEXT", text=spec[i:end]))
            i = end + 1
            continue
        # Optional repetition count
        rep = 0
        while i < len(spec) and spec[i].isdigit():
            rep = rep * 10 + int(spec[i])
            i += 1
        if i >= len(spec):
            break
        code = spec[i].upper()
        if code not in "IFEAG":
            raise DomainError(f"Unknown format code: {spec[i]}")
        i += 1
        # G format with pattern: G⊂pattern⊃ or G<pattern>
        if code == "G" and i < len(spec) and spec[i] in ("⊂", "<"):
            close = "⊃" if spec[i] == "⊂" else ">"
            i += 1
            end = spec.index(close, i)
            pattern = spec[i:end]
            i = end + 1
            groups.append(_FmtGroup("G", text=pattern, repeat=max(rep, 1)))
            continue
        # Width
        width = 0
        while i < len(spec) and spec[i].isdigit():
            width = width * 10 + int(spec[i])
            i += 1
        # Decimals
        decimals = 0
        if i < len(spec) and spec[i] == ".":
            i += 1
            while i < len(spec) and spec[i].isdigit():
                decimals = decimals * 10 + int(spec[i])
                i += 1
        # Validate: F format requires d <= w-2, E format requires d <= w-2
        if code == "F" and width > 0 and decimals > width - 2:
            raise DomainError(f"F format: decimals ({decimals}) > width-2 ({width - 2})")
        if code == "E" and width > 0 and decimals > width - 2:
            raise DomainError(f"E format: decimals ({decimals}) > width-2 ({width - 2})")
        groups.append(_FmtGroup(code, width, decimals, max(rep, 1)))
    return groups


def _format_one_value(code: str, width: int, decimals: int,
                      value: object) -> str:
    """Format a single value with a format code."""
    if value is None:
        return " " * width if width > 0 else ""
    if code == "A":
        text = value if isinstance(value, str) else str(value)
        return text.ljust(width) if width > 0 else text
    num = float(value) if not isinstance(value, (int, float)) else value
    if code == "I":
        text = str(int(num))
    elif code == "F":
        text = f"{num:.{decimals}f}"
    elif code == "E":
        text = f"{num:.{decimals}E}"
    elif code == "G":
        from marple.formatting import format_num
        text = format_num(num)
    else:
        text = str(num)
    text = text.replace("-", "¯")
    return text.rjust(width) if width > 0 else text


def _apply_g_pattern(pattern: str, value: object) -> str:
    """Apply a G-format pattern. '9' placeholders are filled with digits,
    other characters pass through literally."""
    num = abs(int(float(value) if not isinstance(value, (int, float)) else value))
    digit_count = pattern.count("9")
    digits = str(num).zfill(digit_count)
    result: list[str] = []
    di = 0
    for ch in pattern:
        if ch == "9":
            result.append(digits[di] if di < len(digits) else "0")
            di += 1
        else:
            result.append(ch)
    return "".join(result)


def _apply_group(group: _FmtGroup, value: APLArray | None,
                 row: int) -> str:
    """Apply a format group to one row of a column's data."""
    if group.code == "TEXT":
        return group.text
    if value is None:
        return " " * (group.width * group.repeat)

    # Type checking: A format requires character data, others require numeric
    if value is not None:
        is_char = (len(value.data) > 0 and isinstance(value.data[0], str))
        if group.code == "A" and not is_char:
            raise DomainError("A format requires character data")
        if group.code != "A" and is_char:
            raise DomainError(f"{group.code} format requires numeric data, got character")

    if group.code == "A":
        # Character data: extract repeat*width chars from row
        total_chars = group.repeat * group.width
        if len(value.shape) >= 2:
            # Matrix: extract chars from this row
            cols = value.shape[1]
            start = row * cols
            if start >= len(value.data):
                return " " * total_chars
            row_chars = [str(c) for c in value.data[start:start + cols]]
        elif len(value.data) > 0 and isinstance(value.data[0], str):
            # Character vector: one string, only valid for row 0
            row_chars = [str(c) for c in value.data] if row == 0 else []
        else:
            row_chars = []
        # Pad or truncate to total_chars
        while len(row_chars) < total_chars:
            row_chars.append(" ")
        # Format each repeated sub-field
        parts: list[str] = []
        for r in range(group.repeat):
            ch = row_chars[r * group.width:(r + 1) * group.width]
            field = "".join(ch)
            parts.append(field.ljust(group.width) if group.width > 0 else field)
        return "".join(parts)
    else:
        # Numeric: extract scalar for this row
        if len(value.shape) == 0:
            scalar = value.data[0] if row == 0 else None
        elif row < value.shape[0]:
            scalar = value.data[row]
        else:
            scalar = None
        # G format with pattern: replace 9s with digits
        if group.code == "G" and group.text:
            if scalar is None:
                return " " * len(group.text)
            return _apply_g_pattern(group.text, scalar)
        return _format_one_value(group.code, group.width, group.decimals,
                                scalar)


def _column_row_count(value: APLArray, is_alpha: bool) -> int:
    """How many output rows does a column argument produce?"""
    if len(value.shape) == 0:
        return 1
    if len(value.shape) >= 2:
        return value.shape[0]
    if is_alpha and len(value.data) > 0 and isinstance(value.data[0], str):
        return 1  # character vector = one string
    return value.shape[0]


def _dyadic_fmt(fmt_str: str, values: list[APLArray]) -> APLArray:
    """Dyadic ⎕FMT: format values according to specification.

    Each format group (e.g. I5, 5A1, ⊂text⊃) is one unit. Data groups
    consume one value column each. Text groups insert literals.
    Groups cycle to cover all value columns.
    """
    groups = _parse_fmt_spec(fmt_str)
    if not groups:
        raise DomainError("Empty format specification")

    # Build a template: match groups to value columns, cycling groups.
    # Each entry: (group, value_index_or_None)
    template: list[tuple[_FmtGroup, int | None]] = []
    group_idx = 0
    val_idx = 0
    while val_idx < len(values):
        g = groups[group_idx % len(groups)]
        group_idx += 1
        if g.code == "TEXT":
            template.append((g, None))
            continue
        template.append((g, val_idx))
        val_idx += 1
    # Add any trailing text groups from the cycle
    while True:
        g = groups[group_idx % len(groups)]
        if g.code != "TEXT":
            break
        template.append((g, None))
        group_idx += 1

    # Determine number of rows
    num_rows = 1
    for g, vi in template:
        if vi is not None:
            num_rows = max(num_rows,
                           _column_row_count(values[vi], g.code == "A"))

    # Build each row
    rows: list[str] = []
    for row_idx in range(num_rows):
        parts: list[str] = []
        for g, vi in template:
            v = values[vi] if vi is not None else None
            parts.append(_apply_group(g, v, row_idx))
        rows.append("".join(parts))

    # Pad to equal width for character matrix
    max_width = max(len(r) for r in rows) if rows else 0
    all_chars: list[object] = []
    for r in rows:
        all_chars.extend(list(r.ljust(max_width)))
    return APLArray([len(rows), max_width], all_chars)


def _sys_ea(left: APLArray, right: APLArray, env: dict[str, Any]) -> APLArray:
    right_str = "".join(str(c) for c in right.data)
    try:
        return interpret(right_str, env)
    except APLError as e:
        env["⎕EN"] = S(e.code)
        env["⎕DM"] = APLArray([len(str(e))], list(str(e)))
        left_str = "".join(str(c) for c in left.data)
        return interpret(left_str, env)


def _sys_nwrite(left: APLArray, right: APLArray, env: dict[str, Any]) -> APLArray:
    path = "".join(str(c) for c in right.data)
    text = "".join(str(c) for c in left.data)
    with open(path, "w") as f:
        f.write(text)
    return APLArray([0], [])


_DYADIC_SYS: dict[str, Any] = {
    "⎕EA": _sys_ea,
    "⎕DR": lambda l, r, env: _dyadic_dr(l, r),
    "⎕NWRITE": _sys_nwrite,
}


def _call_sys_function_dyadic(name: str, left_node: object, right_node: object, env: dict[str, Any]) -> APLArray:
    """Dispatch a dyadic system function call."""
    # ⎕FMT needs the raw right_node (for FmtArgs)
    if name == "⎕FMT":
        left = _evaluate(left_node, env)
        fmt_str = "".join(str(c) for c in left.data)
        if isinstance(right_node, FmtArgs):
            values = [_evaluate(arg, env) for arg in right_node.args]
        else:
            right = _evaluate(right_node, env)
            values = [right]
        return _dyadic_fmt(fmt_str, values)
    left = _evaluate(left_node, env)
    right = _evaluate(right_node, env)
    handler = _DYADIC_SYS.get(name)
    if handler is not None:
        return handler(left, right, env)
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
    if isinstance(func, FunctionRef):
        return _dispatch_monadic(func.glyph, omega, env)
    if isinstance(func, BoundOperator):
        # A derived verb from operator binding, used inside rank
        node = func  # type: ignore[assignment]
        if isinstance(node.operator, str) and node.operator in ("/", "⌿"):
            inner = _lookup_dyadic(node.left_operand) if isinstance(node.left_operand, str) else None
            if inner and node.operator == "/":
                return _reduce(inner, omega)  # type: ignore[arg-type]
            if inner and node.operator == "⌿":
                return _reduce_first(inner, omega)  # type: ignore[arg-type]
        if isinstance(node.operator, str) and node.operator in ("\\", "⍀"):
            inner = _lookup_dyadic(node.left_operand) if isinstance(node.left_operand, str) else None
            if inner and node.operator == "\\":
                return _scan(inner, omega)  # type: ignore[arg-type]
            if inner and node.operator == "⍀":
                return _scan_first(inner, omega)  # type: ignore[arg-type]
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
    # Build 0-based index lists for each axis, tracking index shapes
    axis_indices: list[list[int]] = []
    idx_shapes: list[list[int]] = []  # shape of each index expression
    for axis, idx_node in enumerate(indices):
        if idx_node is None:
            axis_indices.append(list(range(array.shape[axis])))
            idx_shapes.append([array.shape[axis]])
        else:
            idx = _evaluate(idx_node, env)
            vals = to_list(idx.data) if not idx.is_scalar() else [idx.data[0]]
            axis_indices.append([int(v) - io for v in vals])
            idx_shapes.append(idx.shape if not idx.is_scalar() else [])
    # Pad missing axes with full range
    for axis in range(len(indices), len(array.shape)):
        axis_indices.append(list(range(array.shape[axis])))
        idx_shapes.append([array.shape[axis]])
    # Compute strides
    strides = [1] * len(array.shape)
    for i in range(len(array.shape) - 2, -1, -1):
        strides[i] = strides[i + 1] * array.shape[i + 1]
    # Gather results
    result: list[object] = []
    for combo in product(*axis_indices):
        flat = sum(i * s for i, s in zip(combo, strides))
        result.append(data[flat])
    # Result shape: concatenation of each index expression's shape
    # (scalar indices are dropped, matching APL semantics)
    result_shape: list[int] = []
    for s in idx_shapes:
        result_shape.extend(s)
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
    "⎕FR": S(645),
}


def default_env() -> dict[str, Any]:
    """Create a fresh environment with all system variable defaults."""
    env = dict(_SYSTEM_DEFAULTS)
    _random.seed(1)
    return env


def _newlines_to_diamonds(source: str) -> str:
    """Convert newlines to ⋄ (statement separator), preserving strings."""
    result: list[str] = []
    in_string = False
    for ch in source:
        if ch == "'" and not in_string:
            in_string = True
            result.append(ch)
        elif ch == "'" and in_string:
            in_string = False
            result.append(ch)
        elif ch == "\n" and not in_string:
            result.append("⋄")
        else:
            result.append(ch)
    return "".join(result)


def interpret(source: str, env: dict[str, Any] | None = None) -> APLArray:
    env = env or default_env()
    # Handle #import directives
    if source.strip().startswith("#import"):
        return _handle_import(source.strip(), env)
    name_table = env.get("__name_table__", {})
    # System functions are always classified as functions
    for qfn in ("⎕EA", "⎕UCS", "⎕NC", "⎕EX", "⎕SIGNAL", "⎕DR",
                 "⎕NREAD", "⎕NWRITE", "⎕NEXISTS", "⎕NDELETE",
                 "⎕CR", "⎕FX"):
        name_table[qfn] = NC_FUNCTION
    env["__name_table__"] = name_table
    op_arity = env.get("__operator_arity__", {})
    # Convert newlines to diamonds (statement separators) outside strings
    source = _newlines_to_diamonds(source)
    tree = parse(source, name_table, op_arity)
    result = _evaluate(tree, env)
    # Track source for dfn assignments so workspace save can reconstruct them
    if isinstance(tree, Assignment):
        value = env.get(tree.name)
        if isinstance(value, _DfnClosure):
            if "__sources__" not in env:
                env["__sources__"] = {}
            env["__sources__"][tree.name] = source.strip()
            # Fix name class and arity: dops use ⍺⍺ or ⍵⍵
            if "⍺⍺" in source or "⍵⍵" in source:
                name_table = env.get("__name_table__", {})
                name_table[tree.name] = NC_OPERATOR
                env["__name_table__"] = name_table
                arity = 2 if "⍵⍵" in source else 1
                op_ar = env.get("__operator_arity__", {})
                op_ar[tree.name] = arity
                env["__operator_arity__"] = op_ar
    if isinstance(result, _DfnClosure):
        return S(0)
    return result
