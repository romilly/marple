"""Shared formatting for MARPLE display and ⍕."""

try:
    from typing import Any
except ImportError:
    pass

from marple.numpy_array import APLArray


def format_num(x: Any, pp: int = 10) -> str:
    """Format a number for display, using pp significant digits for floats."""
    if hasattr(x, "item"):
        x = x.item()  # type: ignore[union-attr]
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


def _is_char_array(arr: APLArray) -> bool:
    return len(arr.data) > 0 and all(isinstance(x, str) for x in arr.data)


def _rjust(s: str, width: int) -> str:
    if len(s) >= width:
        return s
    return " " * (width - len(s)) + s


def _format_matrix(result: APLArray, pp: int) -> str:
    """Format a rank-2 array as right-justified columns."""
    rows, cols = result.shape
    if _is_char_array(result):
        lines = []
        for r in range(rows):
            row_data = result.data[r * cols:(r + 1) * cols]
            lines.append("".join(str(x) for x in row_data))
        return "\n".join(lines)
    flat = result.data.flatten() if hasattr(result.data, 'flatten') else result.data
    strs = [format_num(flat[r * cols + c], pp) for r in range(rows) for c in range(cols)]
    col_widths = []
    for c in range(cols):
        w = max(len(strs[r * cols + c]) for r in range(rows))
        col_widths.append(w)
    lines = []
    for r in range(rows):
        parts = []
        for c in range(cols):
            parts.append(_rjust(strs[r * cols + c], col_widths[c]))
        lines.append(" ".join(parts))
    return "\n".join(lines)


def format_result(result: APLArray, env: Any = None) -> str:
    """Format an APLArray for display."""
    pp = 10
    if env is not None:
        pp_val = env.get("⎕PP")
        if pp_val is not None:
            pp = int(pp_val.data[0])
    if result.is_scalar():
        return format_num(result.data.flat[0], pp)
    if _is_char_array(result):
        if len(result.shape) == 1:
            return "".join(str(x) for x in result.data)
        if len(result.shape) == 2:
            return _format_matrix(result, pp)
    flat = result.data.flatten() if hasattr(result.data, 'flatten') else result.data
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
            slice_arr = APLArray([result.shape[-2], result.shape[-1]], slice_data.reshape(result.shape[-2], result.shape[-1]))
            slices.append(_format_matrix(slice_arr, pp))
        return "\n\n".join(slices)
    return repr(result)
