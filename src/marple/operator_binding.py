"""Operator bindings (reduce, scan) for MARPLE."""

from typing import Any, Callable

from marple.backend_functions import NDArray

from marple.numpy_array import APLArray, S
from marple.numpy_aplarray import NumpyAPLArray
from marple.backend_functions import (
    _DOWNCAST_CT, ignoring_numeric_errstate, is_char_array, is_int_dtype,
    is_numeric_array, maybe_downcast,
)
from marple.dyadic_functions import DyadicFunctionBinding
from marple.errors import DomainError
from marple.get_numpy import np


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
    # Dyalog's identity for empty ⌈/⌊ is ±float64.max (not ±inf).
    # Literal avoids a module-load call to np.finfo(np.float64), which
    # fails on ulab (no np.finfo, no float64). On CPython this is
    # exactly `np.finfo(np.float64).max`; on narrower-float MicroPython
    # builds the literal may coerce to ±inf, which is an acceptable
    # Pico-side fallback until a backend hook replaces it in Phase 6b.
    "⌈": -1.7976931348623157e308,
    "⌊": 1.7976931348623157e308,
    "∧": 1,
    "∨": 0,
    "=": 1,
    "≠": 0,
    "<": 0,
    "≤": 1,
    ">": 0,
    "≥": 1,
}


def _reduce_row(op: Callable[[Any, Any], Any], data: NDArray, start: int, length: int) -> Any:
    """Right-to-left reduce of a row, using numpy indexing.

    Upcasts integer data to float64 before the operation to prevent
    silent overflow wrapping. Checks for inf/nan after the operation
    and raises DomainError if the result cannot be represented.
    """
    row = data[start : start + length]
    if is_numeric_array(row) and is_int_dtype(row):
        row = row.astype(np.float64)
    with ignoring_numeric_errstate():
        acc = row[-1]
        for i in range(len(row) - 2, -1, -1):
            acc = op(row[i], acc)
    if hasattr(acc, 'item') and (np.isinf(acc) or np.isnan(acc)):
        raise DomainError("arithmetic overflow in reduce")
    return acc


def _reduce(
    func: Callable[[APLArray, APLArray], APLArray],
    omega: APLArray,
    glyph: str | None,
    axis: int,
) -> APLArray:
    """Reduce along `axis` (0-based).

    Moves `axis` to last position and reuses last-axis row-wise fold.
    """
    _reject_chars_for_op(omega, glyph, "reduce")
    shape = list(omega.shape)
    rank = len(shape)
    if rank == 0:
        # Reducing a scalar returns it unchanged.
        return omega
    if axis < 0 or axis >= rank:
        raise DomainError(f"Axis out of range for rank-{rank} array")
    op = _SCALAR_OPS.get(glyph) if glyph is not None else None
    if op is None:
        raise DomainError(f"Unknown function for reduce: {glyph}")

    n = shape[axis]
    result_shape = shape[:axis] + shape[axis + 1:]

    # Empty reduce: identity-filled result.
    if n == 0:
        identity = _IDENTITY_ELEMENTS.get(glyph) if glyph is not None else None
        if identity is None:
            raise DomainError("Cannot reduce empty array")
        if not result_shape:
            return S(identity)
        return NumpyAPLArray(result_shape, np.full(result_shape, identity, dtype=np.float64))

    # Move target axis to last position; reduce along rows of length n.
    moved = np.moveaxis(omega.data, axis, rank - 1)
    flat = moved.flatten() if is_numeric_array(moved) else moved
    if is_numeric_array(flat) and is_int_dtype(flat):
        flat = flat.astype(np.float64)

    if rank == 1:
        result_val = _reduce_row(op, flat, 0, n)
        if hasattr(result_val, 'item'):
            result_val = maybe_downcast(np.array([result_val]), _DOWNCAST_CT)[0]
        return S(result_val)

    rows = flat.reshape(-1, n)
    result = np.zeros(len(rows), dtype=np.float64)
    for r, row in enumerate(rows):
        result[r] = _reduce_row(op, row, 0, n)
    result = maybe_downcast(result.reshape(result_shape), _DOWNCAST_CT)
    return NumpyAPLArray(result_shape, result)


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


def _scan_row_accumulate(ufunc: np.ufunc, data: NDArray, row_len: int) -> NDArray:
    """Apply ufunc.accumulate to each row of length row_len in flat data."""
    rows = data.reshape(-1, row_len)
    with ignoring_numeric_errstate():
        result = ufunc.accumulate(rows, axis=1)
    return result.flatten()


def _scan_row_general(op: Callable[[Any, Any], Any], data: NDArray, row_len: int) -> NDArray:
    """O(n²) right-to-left reduce per prefix, row by row."""
    rows = data.reshape(-1, row_len)
    result = np.zeros_like(rows)
    with ignoring_numeric_errstate():
        for r, row in enumerate(rows):
            result[r, 0] = row[0]
            for k in range(1, row_len):
                acc = row[k]
                for j in range(k - 1, -1, -1):
                    acc = op(row[j], acc)
                result[r, k] = acc
    return result.flatten()


def _scan(
    func: Callable[[APLArray, APLArray], APLArray],
    omega: APLArray,
    glyph: str | None,
    axis: int,
) -> APLArray:
    """Scan along `axis` (0-based).

    Moves `axis` to last position, runs last-axis row-scan, moves back.
    """
    _reject_chars_for_op(omega, glyph, "scan")
    shape = list(omega.shape)
    rank = len(shape)
    if rank == 0:
        return omega
    if axis < 0 or axis >= rank:
        raise DomainError(f"Axis out of range for rank-{rank} array")

    n = shape[axis]
    if n == 0:
        return NumpyAPLArray(shape, omega.data)

    moved = np.moveaxis(omega.data, axis, rank - 1)
    moved_shape = list(moved.shape)
    flat = moved.flatten() if is_numeric_array(moved) else moved
    if is_numeric_array(flat) and is_int_dtype(flat):
        flat = flat.astype(np.float64)

    if glyph is not None:
        ufunc = _ACCUMULATE_UFUNCS.get(glyph)
        if ufunc is not None:
            scanned = _scan_row_accumulate(ufunc, flat, n)
        else:
            op = _SCALAR_OPS.get(glyph)
            if op is not None:
                scanned = _scan_row_general(op, flat, n)
            else:
                raise DomainError(f"Unknown function for scan: {glyph}")
    else:
        raise DomainError(f"Unknown function for scan: {glyph}")

    if hasattr(scanned, "dtype") and "float" in str(scanned.dtype):
        if np.any(np.isinf(scanned)) or np.any(np.isnan(scanned)):
            raise DomainError("arithmetic overflow in scan")
        scanned = maybe_downcast(scanned, _DOWNCAST_CT)

    scanned_arr = scanned.reshape(moved_shape)
    final = np.moveaxis(scanned_arr, rank - 1, axis)
    return NumpyAPLArray(shape, final.reshape(shape))


# Default axis (0-based, relative to the argument's rank) per operator glyph.
# Subtract from rank to get last-axis; 0 means first axis.
_DEFAULT_LAST_AXIS = {"/", "\\"}
_DEFAULT_FIRST_AXIS = {"⌿", "⍀"}


def _default_axis(operator: str, rank: int) -> int:
    if operator in _DEFAULT_LAST_AXIS:
        return rank - 1
    if operator in _DEFAULT_FIRST_AXIS:
        return 0
    raise DomainError(f"Unknown operator: {operator}")
