from __future__ import annotations

from typing import Any

from marple.arraymodel import APLArray, S
from marple.interpreter import _DfnClosure, interpret


def _format_value(value: object) -> str | None:
    """Convert an APLArray value to APL source text."""
    if isinstance(value, _DfnClosure):
        return None  # handled separately via source tracking
    if not isinstance(value, APLArray):
        return None
    if value.is_scalar():
        v = value.data[0]
        if isinstance(v, str):
            return f"'{v}'"
        if isinstance(v, (int, float)) and v < 0:
            return f"¯{abs(v)}"
        return str(v)
    # Check if character data
    is_char = len(value.data) > 0 and all(isinstance(x, str) for x in value.data)
    if is_char:
        char_str = "".join(str(x) for x in value.data)
        quoted = f"'{char_str}'"
        if len(value.shape) == 1:
            return quoted
        shape_str = " ".join(str(s) for s in value.shape)
        return f"{shape_str}⍴{quoted}"
    # Numeric data
    def _fmt_num(x: object) -> str:
        if isinstance(x, (int, float)) and x < 0:
            return f"¯{abs(x)}"
        return str(x)

    data_str = " ".join(_fmt_num(x) for x in value.data)
    if len(value.shape) == 1:
        return data_str
    shape_str = " ".join(str(s) for s in value.shape)
    return f"{shape_str}⍴{data_str}"


def save_workspace(env: dict[str, Any], path: str) -> None:
    """Save workspace to a file of APL assignment statements."""
    lines: list[str] = []
    # Save system variables first
    for name in sorted(env):
        if name.startswith("⎕"):
            value = env[name]
            if isinstance(value, APLArray):
                formatted = _format_value(value)
                if formatted is not None:
                    lines.append(f"{name}←{formatted}")
    # Save user definitions
    sources: dict[str, str] = env.get("__sources__", {})
    for name in sorted(env):
        if name.startswith("⎕") or name.startswith("__"):
            continue
        if name in ("⍵", "⍺", "∇"):
            continue
        value = env[name]
        if isinstance(value, _DfnClosure) and name in sources:
            lines.append(sources[name])
        elif isinstance(value, APLArray):
            formatted = _format_value(value)
            if formatted is not None:
                lines.append(f"{name}←{formatted}")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def load_workspace(env: dict[str, Any], path: str) -> None:
    """Load workspace by executing each line as APL."""
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                interpret(line, env)
