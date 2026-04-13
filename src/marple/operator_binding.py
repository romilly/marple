"""Operator bindings (reduce, scan) for MARPLE."""

from typing import Any, Callable

import numpy.typing as npt

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


def _reduce_row(op: Callable[[Any, Any], Any], data: npt.NDArray[Any], start: int, length: int) -> Any:
    """Right-to-left reduce of a row, using numpy indexing.

    Upcasts integer data to float64 before the operation to prevent
    silent overflow wrapping. Checks for inf/nan after the operation
    and raises DomainError if the result cannot be represented.
    """
    row = data[start : start + length]
    if is_numeric_array(row) and "int" in str(row.dtype):
        row = row.astype(np.float64)
    with np.errstate(over="ignore", invalid="ignore"):
        acc = row[-1]
        for i in range(len(row) - 2, -1, -1):
            acc = op(row[i], acc)
    if hasattr(acc, 'item') and (np.isinf(acc) or np.isnan(acc)):
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
        result_val = _reduce_row(op, flat, 0, n)
        if hasattr(result_val, 'item'):
            result_val = maybe_downcast(np.array([result_val]), _DOWNCAST_CT)[0]
        return S(result_val)
    last = omega.shape[-1]
    new_shape = omega.shape[:-1]
    n_rows = n // last
    result = np.zeros(n_rows, dtype=np.float64)
    for i in range(n_rows):
        result[i] = _reduce_row(op, flat, i * last, last)
    result = maybe_downcast(result.reshape(new_shape), _DOWNCAST_CT)
    return APLArray(new_shape, result)


_ACCUMULATE_UFUNCS: dict[str, np.ufunc] = {}
if hasattr(np, 'add') and hasattr(np.add, 'accumulate'):
    _ACCUMULATE_UFUNCS = {
        "+": np.add,
        "×": np.multiply,
        "⌈": np.maximum,
        "⌊": np.minimum,
    }

_SCALAR_OPS: dict[str, Callable[[Any, Any], Any]] = {
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


def _scan_row_accumulate(ufunc: np.ufunc, data: npt.NDArray[Any], row_len: int) -> npt.NDArray[Any]:
    """Apply ufunc.accumulate to each row of length row_len in flat data."""
    n = len(data)
    result = np.empty(n, dtype=data.dtype)
    with np.errstate(over="ignore", invalid="ignore"):
        for i in range(0, n, row_len):
            result[i:i + row_len] = ufunc.accumulate(data[i:i + row_len])
    return result


def _scan_row_general(op: Callable[[Any, Any], Any], data: npt.NDArray[Any], row_len: int) -> npt.NDArray[Any]:
    """O(n²) right-to-left reduce per prefix, row by row."""
    n = len(data)
    result = np.zeros(n, dtype=data.dtype)
    with np.errstate(over="ignore", invalid="ignore"):
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

    # Upcast integer data to float64 to prevent silent overflow wrapping.
    scan_data = flat
    if is_numeric_array(flat) and "int" in str(flat.dtype):
        scan_data = flat.astype(np.float64)

    if glyph is not None:
        ufunc = _ACCUMULATE_UFUNCS.get(glyph)
        if ufunc is not None:
            result = _scan_row_accumulate(ufunc, scan_data, row_len)
        else:
            op = _SCALAR_OPS.get(glyph)
            if op is not None:
                result = _scan_row_general(op, scan_data, row_len)
            else:
                raise DomainError(f"Unknown function for scan: {glyph}")
    else:
        raise DomainError(f"Unknown function for scan: {glyph}")

    if hasattr(result, "dtype") and "float" in str(result.dtype):
        if np.any(np.isinf(result)) or np.any(np.isnan(result)):
            raise DomainError("arithmetic overflow in scan")
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

    reduce_data = flat
    if is_numeric_array(flat) and "int" in str(flat.dtype):
        reduce_data = flat.astype(np.float64)

    acc = np.array(reduce_data[:cell_size], dtype=reduce_data.dtype)
    with np.errstate(over="ignore", invalid="ignore"):
        for i in range(1, first):
            cell = reduce_data[i * cell_size : (i + 1) * cell_size]
            for j in range(cell_size):
                acc[j] = op(acc[j], cell[j])

    if hasattr(acc, "dtype") and "float" in str(acc.dtype):
        if np.any(np.isinf(acc)) or np.any(np.isnan(acc)):
            raise DomainError("arithmetic overflow in reduce")
        acc = maybe_downcast(acc, _DOWNCAST_CT)
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
    scan_data = flat
    if is_numeric_array(flat) and "int" in str(flat.dtype):
        scan_data = flat.astype(np.float64)

    result = np.zeros(len(scan_data), dtype=scan_data.dtype)
    result[:cell_size] = scan_data[:cell_size]
    acc = np.array(scan_data[:cell_size], dtype=scan_data.dtype)
    with np.errstate(over="ignore", invalid="ignore"):
        for i in range(1, first):
            cell = scan_data[i * cell_size : (i + 1) * cell_size]
            for j in range(cell_size):
                acc[j] = op(acc[j], cell[j])
            result[i * cell_size : (i + 1) * cell_size] = acc

    if hasattr(result, "dtype") and "float" in str(result.dtype):
        if np.any(np.isinf(result)) or np.any(np.isnan(result)):
            raise DomainError("arithmetic overflow in scan")
        result = maybe_downcast(result, _DOWNCAST_CT)
    return APLArray(list(omega.shape), result.reshape(omega.shape))


_OPERATOR_DISPATCH: dict[str, Callable[..., APLArray]] = {
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
