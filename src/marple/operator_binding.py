"""Operator bindings (reduce, scan) for MARPLE."""

from typing import Any, Callable

from marple.numpy_array import APLArray, S
from marple.backend_functions import (
    _DOWNCAST_CT, is_char_array, is_numeric_array, maybe_downcast, to_list,
)
from marple.dyadic_functions import DyadicFunctionBinding
from marple.errors import DomainError
from marple.get_numpy import np
from marple.parser import FunctionRef


# Glyphs whose meaning on character data is undefined: arithmetic and
# logical operators. Comparison operators (= ≠ < ≤ > ≥) and min/max
# (⌈ ⌊) are well-defined on chars (compare codepoints) and are NOT
# guarded.
_ARITHMETIC_GLYPHS_REJECTING_CHARS: frozenset[str] = frozenset({
    "+", "-", "×", "÷", "*", "⍟", "|", "∧", "∨",
})


def _reject_chars_for_op(omega: APLArray, glyph: str | None, op_name: str) -> None:
    """Raise DomainError if reducing/scanning an arithmetic operator
    over character data."""
    if glyph in _ARITHMETIC_GLYPHS_REJECTING_CHARS and is_char_array(omega.data):
        raise DomainError(f"{glyph} {op_name} is not defined on character data")


# Glyph-keyed maps for reduce/scan

_IDENTITY_ELEMENTS: dict[str, int | float] = {
    "+": 0,
    "-": 0,
    "×": 1,
    "÷": 1,
    "⌈": float("-inf"),
    "⌊": float("inf"),
    "∧": 1,
    "∨": 0,
    "=": 1,
    "≠": 0,
    "<": 0,
    "≤": 1,
    ">": 0,
    "≥": 1,
}


def _reduce_row(op: Any, data: Any, start: int, length: int) -> Any:
    """Right-to-left reduce of a row, using numpy indexing.

    Follows Dyalog's "upcast when you must" rule: try the reduce in the
    current dtype; if numpy signals overflow, retry with the row
    upcast to float64. A float64 result that lands at ±inf or nan is
    reported as a DomainError — the arithmetic cannot represent the
    answer and silently returning a wrong value is worse than raising.
    """
    try:
        with np.errstate(over="raise", invalid="raise"):
            acc = data[start + length - 1]
            for i in range(start + length - 2, start - 1, -1):
                acc = op(data[i], acc)
        return acc
    except FloatingPointError:
        float_data = data[start : start + length].astype(np.float64)
        with np.errstate(over="ignore", invalid="ignore"):
            acc = float_data[-1]
            for i in range(len(float_data) - 2, -1, -1):
                acc = op(float_data[i], acc)
        if np.isinf(acc) or np.isnan(acc):
            raise DomainError("arithmetic overflow in reduce")
        return acc


def _reduce(
    func: Callable[[APLArray, APLArray], APLArray],
    omega: APLArray,
    glyph: str | None = None,
) -> APLArray:
    """Reduce along the last axis."""
    _reject_chars_for_op(omega, glyph, "reduce")
    data = omega.data
    flat = data.flatten() if is_numeric_array(data) else data
    n = len(flat)
    if n == 0:
        if glyph is not None:
            identity = _IDENTITY_ELEMENTS.get(glyph)
            if identity is not None:
                return S(identity)
        raise DomainError("Cannot reduce empty array")
    op = _SCALAR_OPS.get(glyph) if glyph is not None else None
    if op is None:
        raise DomainError(f"Unknown function for reduce: {glyph}")
    if len(omega.shape) <= 1:
        return S(_reduce_row(op, flat, 0, n))
    last = omega.shape[-1]
    new_shape = omega.shape[:-1]
    n_rows = n // last
    result = np.zeros(n_rows, dtype=flat.dtype)
    for i in range(n_rows):
        result[i] = _reduce_row(op, flat, i * last, last)
    return APLArray(new_shape, result.reshape(new_shape))


_ACCUMULATE_UFUNCS: dict[str, Any] = {}
if hasattr(np, 'add') and hasattr(np.add, 'accumulate'):
    _ACCUMULATE_UFUNCS = {
        "+": np.add,
        "×": np.multiply,
        "⌈": np.maximum,
        "⌊": np.minimum,
    }

_SCALAR_OPS: dict[str, Any] = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "×": lambda a, b: a * b,
    "÷": lambda a, b: a / b,
    "⌈": lambda a, b: max(a, b),
    "⌊": lambda a, b: min(a, b),
    "*": lambda a, b: a ** b,
    "⍟": lambda a, b: np.log(b) / np.log(a),
    "|": lambda a, b: b % a,
    "∧": lambda a, b: int(bool(a) and bool(b)),
    "∨": lambda a, b: int(bool(a) or bool(b)),
    "≠": lambda a, b: int(a != b),
    "=": lambda a, b: int(a == b),
    "<": lambda a, b: int(a < b),
    "≤": lambda a, b: int(a <= b),
    ">": lambda a, b: int(a > b),
    "≥": lambda a, b: int(a >= b),
}


def _scan_row_accumulate(ufunc: Any, data: Any, row_len: int) -> Any:
    """Apply ufunc.accumulate to each row of length row_len in flat data."""
    n = len(data)
    result = np.empty(n, dtype=data.dtype)
    for i in range(0, n, row_len):
        result[i:i + row_len] = ufunc.accumulate(data[i:i + row_len])
    return result


def _scan_row_general(op: Any, data: Any, row_len: int) -> Any:
    """O(n²) right-to-left reduce per prefix, row by row."""
    n = len(data)
    result = np.zeros(n, dtype=data.dtype)
    for i in range(0, n, row_len):
        row = data[i:i + row_len]
        result[i] = row[0]
        for k in range(1, row_len):
            acc = row[k]
            for j in range(k - 1, -1, -1):
                acc = op(row[j], acc)
            result[i + k] = acc
    return result


def _scan(
    func: Callable[[APLArray, APLArray], APLArray],
    omega: APLArray,
    glyph: str | None = None,
) -> APLArray:
    """Scan along the last axis."""
    _reject_chars_for_op(omega, glyph, "scan")
    flat = omega.data.flatten() if is_numeric_array(omega.data) else omega.data
    n = len(flat)
    if n == 0:
        return APLArray.array([0], [])
    row_len = omega.shape[-1] if len(omega.shape) > 0 else n

    # `np.multiply.accumulate` silently wraps on int64 overflow and
    # does not honor np.errstate. For × on integer data, upcast to
    # float64 before the scan so overflow becomes detectable as inf.
    # Integer-valued float results are downcasted back at the end.
    scan_data = flat
    if glyph == "×" and is_numeric_array(flat) and "int" in str(flat.dtype):
        scan_data = flat.astype(np.float64)

    def _do_scan(data: Any) -> Any:
        if glyph is not None:
            ufunc = _ACCUMULATE_UFUNCS.get(glyph)
            if ufunc is not None:
                return _scan_row_accumulate(ufunc, data, row_len)
        op = _SCALAR_OPS.get(glyph) if glyph is not None else None
        if op is not None:
            return _scan_row_general(op, data, row_len)
        raise DomainError(f"Unknown function for scan: {glyph}")

    try:
        with np.errstate(over="raise", invalid="raise"):
            result = _do_scan(scan_data)
    except FloatingPointError:
        with np.errstate(over="ignore", invalid="ignore"):
            result = _do_scan(scan_data.astype(np.float64))

    # Detect float overflow (inf/nan) whichever path we took.
    if hasattr(result, "dtype") and "float" in str(result.dtype):
        if np.any(np.isinf(result)) or np.any(np.isnan(result)):
            raise DomainError("arithmetic overflow in scan")
        if scan_data is not flat:  # we eagerly upcasted — try to downcast
            result = maybe_downcast(result, _DOWNCAST_CT)

    return APLArray(list(omega.shape), result.reshape(omega.shape))


def _reduce_first(
    func: Callable[[APLArray, APLArray], APLArray],
    omega: APLArray,
    glyph: str | None = None,
) -> APLArray:
    """Reduce along the first axis (⌿)."""
    _reject_chars_for_op(omega, glyph, "reduce")
    if len(omega.shape) <= 1:
        return _reduce(func, omega, glyph)
    op = _SCALAR_OPS.get(glyph) if glyph is not None else None
    if op is None:
        raise DomainError(f"Unknown function for reduce: {glyph}")
    first = omega.shape[0]
    cell_shape = omega.shape[1:]
    flat = omega.data.flatten() if is_numeric_array(omega.data) else omega.data
    cell_size = 1
    for s in cell_shape:
        cell_size *= s

    def _do_reduce(data: Any) -> Any:
        acc = np.array(data[:cell_size], dtype=data.dtype)
        for i in range(1, first):
            cell = data[i * cell_size : (i + 1) * cell_size]
            for j in range(cell_size):
                acc[j] = op(acc[j], cell[j])
        return acc

    try:
        with np.errstate(over="raise", invalid="raise"):
            acc = _do_reduce(flat)
    except FloatingPointError:
        with np.errstate(over="ignore", invalid="ignore"):
            acc = _do_reduce(flat.astype(np.float64))
        if np.any(np.isinf(acc)) or np.any(np.isnan(acc)):
            raise DomainError("arithmetic overflow in reduce")
    return APLArray(cell_shape, acc.reshape(cell_shape))


def _scan_first(
    func: Callable[[APLArray, APLArray], APLArray],
    omega: APLArray,
    glyph: str | None = None,
) -> APLArray:
    """Scan along the first axis (⍀)."""
    _reject_chars_for_op(omega, glyph, "scan")
    if len(omega.shape) <= 1:
        return _scan(func, omega, glyph)
    op = _SCALAR_OPS.get(glyph) if glyph is not None else None
    if op is None:
        raise DomainError(f"Unknown function for scan: {glyph}")
    first = omega.shape[0]
    cell_shape = omega.shape[1:]
    cell_size = 1
    for s in cell_shape:
        cell_size *= s
    flat = omega.data.flatten() if is_numeric_array(omega.data) else omega.data

    def _do_scan(data: Any) -> Any:
        result = np.zeros(len(data), dtype=data.dtype)
        result[:cell_size] = data[:cell_size]
        acc = np.array(data[:cell_size], dtype=data.dtype)
        for i in range(1, first):
            cell = data[i * cell_size : (i + 1) * cell_size]
            for j in range(cell_size):
                acc[j] = op(acc[j], cell[j])
            result[i * cell_size : (i + 1) * cell_size] = acc
        return result

    try:
        with np.errstate(over="raise", invalid="raise"):
            result = _do_scan(flat)
    except FloatingPointError:
        with np.errstate(over="ignore", invalid="ignore"):
            result = _do_scan(flat.astype(np.float64))
        if np.any(np.isinf(result)) or np.any(np.isnan(result)):
            raise DomainError("arithmetic overflow in scan")
    return APLArray(list(omega.shape), result.reshape(omega.shape))


_OPERATOR_DISPATCH: dict[str, Any] = {
    "/": _reduce,
    "⌿": _reduce_first,
    "\\": _scan,
    "⍀": _scan_first,
}


class DerivedFunctionBinding:
    """A derived function: an operator applied to a function operand."""

    def apply(self, operator: str, function: object, operand: APLArray) -> APLArray:
        """Apply the derived function (operator + function) to an operand."""
        func, glyph = self._resolve_function(function)
        op_fn = _OPERATOR_DISPATCH.get(operator)
        if op_fn is None:
            raise DomainError(f"Unknown operator: {operator}")
        return op_fn(func, operand, glyph)

    def _resolve_function(self, function: object) -> tuple[Any, str | None]:
        """Resolve a function node to (dyadic callable, glyph or None)."""
        if isinstance(function, FunctionRef):
            return DyadicFunctionBinding.resolve(function.glyph), function.glyph
        raise DomainError("Operators require primitive function operands")
