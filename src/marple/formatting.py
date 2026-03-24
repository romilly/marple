"""Shared numeric formatting for MARPLE display and ⍕."""

try:
    from typing import Any
except ImportError:
    pass


def format_num(x: Any, pp: int = 10) -> str:
    """Format a number for display, using pp significant digits for floats."""
    # Convert numpy scalars to Python types
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
    return str(x)
