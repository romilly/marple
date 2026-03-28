"""Monadic primitive function dispatch for MARPLE."""

from __future__ import annotations

from typing import TYPE_CHECKING

from marple.arraymodel import APLArray, S

if TYPE_CHECKING:
    from marple.environment import Environment
from marple.errors import DomainError
from marple.functions import (
    negate,
    reciprocal,
    ceiling,
    floor,
    exponential,
    natural_log,
    absolute_value,
    logical_not,
    pi_times,
)
from marple.structural import (
    ravel,
    reverse,
    shape,
    transpose,
    matrix_inverse,
)


class MonadicFunctionBinding:
    """Dispatches and applies monadic primitive functions."""

    _SIMPLE: dict[str, object] = {
        "+": lambda omega: omega,
        "-": negate,
        "×": lambda omega: S((-1 if omega.data[0] < 0 else 1 if omega.data[0] > 0 else 0)),
        "÷": reciprocal,
        "⌈": ceiling,
        "⌊": floor,
        "*": exponential,
        "⍟": natural_log,
        "|": absolute_value,
        "~": logical_not,
        "⍴": shape,
        ",": ravel,
        "⌽": reverse,
        "⍉": transpose,
        "⌹": matrix_inverse,
        "○": pi_times,
    }

    _ENV_DEPENDENT: dict[str, str] = {
        "⍳": "_iota",
        "≢": "_tally",
    }

    def __init__(self, env: Environment) -> None:
        self._env = env

    def apply(self, glyph: str, operand: APLArray) -> APLArray:
        """Apply a monadic primitive function to an operand."""
        method_name = self._ENV_DEPENDENT.get(glyph)
        if method_name is not None:
            return getattr(self, method_name)(operand)
        func = self._SIMPLE.get(glyph)
        if func is not None:
            return func(operand)  # type: ignore[operator]
        raise DomainError(f"Unknown monadic function: {glyph}")

    def _iota(self, operand: APLArray) -> APLArray:
        io = self._env.io
        n = int(operand.data[0])
        return APLArray([n], list(range(io, n + io)))

    def _tally(self, operand: APLArray) -> APLArray:
        return S(1) if operand.is_scalar() else S(operand.shape[0])
