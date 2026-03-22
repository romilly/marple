from __future__ import annotations

from typing import Any

from marple.arraymodel import APLArray, S
from marple.errors import APLError

_env: dict[str, Any] | None = None
_last_error: int = 0


def set_env(env: dict[str, Any]) -> None:
    global _env, _last_error
    _env = env
    if "__error_init__" not in env:
        _last_error = 0
        env["__error_init__"] = True


def ea(left: APLArray, right: APLArray) -> APLArray:
    """Execute Alternate: try right expression, on error evaluate left instead."""
    global _last_error
    from marple.interpreter import interpret

    if _env is None:
        raise RuntimeError("No environment set for ea")

    right_str = "".join(str(c) for c in right.data)
    try:
        return interpret(right_str, _env)
    except APLError as e:
        _last_error = e.code
        left_str = "".join(str(c) for c in left.data)
        return interpret(left_str, _env)


def en(right: APLArray) -> APLArray:
    """Error Number: return the code of the most recent error, or 0."""
    return S(_last_error)
