"""Dyadic primitive function dispatch for MARPLE."""

from typing import Any

from marple.arraymodel import APLArray
from marple.errors import DomainError
from marple.functions import (
    add,
    subtract,
    multiply,
    divide,
    maximum,
    minimum,
    power,
    logarithm,
    residue,
    logical_and,
    logical_or,
    circular,
)
from marple.structural import (
    catenate,
    drop,
    encode,
    decode,
    expand,
    replicate,
    replicate_first,
    reshape,
    rotate,
    take,
    matrix_divide,
)


class DyadicFunctionBinding:
    """Dispatches and applies dyadic primitive functions."""

    _SIMPLE: dict[str, object] = {
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

    def __init__(self, env: dict[str, Any]) -> None:
        self._env = env

    def apply(self, glyph: str, left: APLArray, right: APLArray) -> APLArray:
        """Apply a dyadic primitive function to left and right arguments."""
        func = self._SIMPLE.get(glyph)
        if func is not None:
            return func(left, right)  # type: ignore[operator]
        raise DomainError(f"Unknown dyadic function: {glyph}")
