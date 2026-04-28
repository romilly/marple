"""Operator bindings (reduce, scan) for MARPLE."""

from typing import Any, Callable

from marple.backend_functions import NDArray
from marple.adapters.numpy_array_builder import BUILDER

from marple.ports.array import APLArray, S, ignoring_numeric_errstate, is_numeric_array, np_reshape, is_int_dtype, maybe_upcast
from marple.backend_functions import (
    _DOWNCAST_CT, 
    maybe_downcast,
    numeric_upcast_dtype,
)
from marple.dyadic_functions import DyadicFunctionBinding
from marple.errors import DomainError
import numpy as np


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
    if glyph in _ARITHMETIC_GLYPHS_REJECTING_CHARS and omega.is_char():
        raise DomainError(f"{glyph} {op_name} is not defined on character data")


# Glyph-keyed maps for reduce/scan

# Dyalog's identity for empty ⌈/⌊ is ±float64.max. Detect at module load
# which path we're on: CPython/numpy has np.finfo and gives the exact
# Dyalog value; ulab has no np.finfo and no float64, so fall back to the
# widest float its available `np.float` type supports (float32 max).
if hasattr(np, "finfo"):
    _FLOAT_MAX: float = float(np.finfo(np.float64).max)
else:
    _FLOAT_MAX = 3.4028235e38  # ulab: float32 max


_IDENTITY_ELEMENTS: dict[str, int | float] = {
    "+": 0,
    "-": 0,
    "×": 1,
    "÷": 1,
    "⌈": -_FLOAT_MAX,
    "⌊": _FLOAT_MAX,
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
        # TODO: np reference below must go
        return BUILDER.apl_array(result_shape,
                             np.full(result_shape, identity, dtype=numeric_upcast_dtype()))

    # Move target axis to last position; reduce along rows of length n.
    moved = _move_axis(omega.data, axis, rank - 1, rank)
    flat = moved.flatten() if is_numeric_array(moved) else moved
    flat = maybe_upcast(flat)

    if rank == 1:
        result_val = _reduce_row(op, flat, 0, n)
        if hasattr(result_val, 'item'):
            result_val = maybe_downcast(np.array([result_val]), _DOWNCAST_CT)[0]
        return S(result_val)

    rows = np_reshape(flat, -1, n)
    result = np.zeros(len(rows), dtype=numeric_upcast_dtype())
    for r, row in enumerate(rows):
        result[r] = _reduce_row(op, row, 0, n)
    result = maybe_downcast(np_reshape(result, result_shape), _DOWNCAST_CT)
    return BUILDER.apl_array(result_shape, result)


def _move_axis(data: NDArray, src: int, dst: int, rank: int) -> NDArray:
    """Move axis `src` of `data` to position `dst`.

    Uses `np.moveaxis` if the active backend exposes it. Falls back to
    `data.T` for the one non-trivial case that a bare full-reverse
    transpose solves correctly: rank 2 with a single axis swap. Higher
    ranks need an axis-permutation primitive that ulab doesn't expose
    (`.transpose()` takes no args on ulab, only full reverse), so those
    raise a clear DomainError — the limit is not the rank cap itself
    but the missing primitive, so a future ulab build that adds
    `np.moveaxis` will just work.
    """
    if src == dst:
        return data
    if hasattr(np, "moveaxis"):
        return np.moveaxis(data, src, dst)
    if rank == 2 and {src, dst} == {0, 1}:
        return data.T
    raise DomainError(
        "axis move {}→{} of rank-{} array needs np.moveaxis; not "
        "available on this backend".format(src, dst, rank))


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
    rows = np_reshape(data, -1, row_len)
    with ignoring_numeric_errstate():
        result = ufunc.accumulate(rows, axis=1)
    return result.flatten()


def _scan_row_general(op: Callable[[Any, Any], Any], data: NDArray, row_len: int) -> NDArray:
    """O(n²) right-to-left reduce per prefix, row by row."""
    rows = np_reshape(data, -1, row_len)
    # np.zeros_like is missing on ulab; spell out shape+dtype via zeros.
    result = np.zeros(rows.shape, dtype=numeric_upcast_dtype())
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
        return omega

    moved = _move_axis(omega.data, axis, rank - 1, rank)
    moved_shape = list(moved.shape)
    flat = moved.flatten() if is_numeric_array(moved) else moved
    flat = maybe_upcast(flat)

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

    scanned_arr = np_reshape(scanned, moved_shape)
    final = _move_axis(scanned_arr, rank - 1, axis, rank)
    return BUILDER.apl_array(shape, np_reshape(final, shape))


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
