"""Shared formatting for MARPLE display and ⍕."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from marple.adapters.numpy_array_builder import BUILDER

from marple.ports.array import APLArray


if TYPE_CHECKING:
    from marple.environment import Environment


def format_num(x: Any, pp: int = 10) -> str:
    """Format a number for display, using pp significant digits for floats."""
    if isinstance(x, bool):
        return str(int(x))
    if isinstance(x, float):
        if x == int(x) and abs(x) < 1e15:
            n = int(x)
            return "¯" + str(abs(n)) if n < 0 else str(n)
        s = f"{x:.{pp}g}"
        if s.startswith("-"):
            s = "¯" + s[1:]
        return s
    if isinstance(x, int) and x < 0:
        return "¯" + str(abs(x))
    try:
        from decimal import Decimal
        if isinstance(x, Decimal):
            s = str(x)
            if s.startswith("-"):
                return "¯" + s[1:]
            return s
    except ImportError:
        pass
    return str(x)


def _rjust(s: str, width: int) -> str:
    if len(s) >= width:
        return s
    return " " * (width - len(s)) + s


def _format_matrix(result: APLArray, pp: int) -> str:
    """Format a rank-2 array as right-justified columns."""
    rows, cols = result.shape
    if result.is_char():
        return "\n".join(result.slice_axis(0, r).as_str() for r in range(rows))
    nested = result.to_list()
    strs = [[format_num(nested[r][c], pp) for c in range(cols)]
            for r in range(rows)]
    col_widths = [max(len(strs[r][c]) for r in range(rows)) for c in range(cols)]
    lines = [" ".join(_rjust(strs[r][c], col_widths[c]) for c in range(cols))
             for r in range(rows)]
    return "\n".join(lines)


def format_result(result: APLArray, env: 'Environment | None' = None) -> str:
    """Format an APLArray for display."""
    pp = 10
    if env is not None:
        pp_val = env.get("⎕PP")
        if isinstance(pp_val, APLArray):
            pp = int(pp_val.scalar_value())
    if result.is_scalar():
        raw = result.scalar_value()
        if result.is_char():
            return chr(int(raw))
        return format_num(raw, pp)
    if result.is_char():
        if len(result.shape) == 1:
            return result.as_str()
        if len(result.shape) == 2:
            return _format_matrix(result, pp)
    flat = result.data.flatten()
    if len(result.shape) == 1:
        return " ".join(format_num(x, pp) for x in flat)
    if len(result.shape) == 2:
        return _format_matrix(result, pp)
    if len(result.shape) >= 3:
        slice_size = result.shape[-2] * result.shape[-1]
        num_slices = len(flat) // slice_size
        slices = []
        for s in range(num_slices):
            start = s * slice_size
            slice_data = flat[start:start + slice_size]
            slice_shape = [result.shape[-2], result.shape[-1]]
            slice_arr = BUILDER.apl_array(slice_shape, slice_data.reshape(slice_shape))
            slices.append(_format_matrix(slice_arr, pp))
        return "\n\n".join(slices)
    return repr(result)
