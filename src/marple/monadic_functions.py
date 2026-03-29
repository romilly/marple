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
    factorial,
    natural_log,
    absolute_value,
    logical_not,
    pi_times,
)
import random as _random

from marple.structural import (
    grade_down,
    grade_up,
    ravel,
    reverse,
    reverse_first,
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
        "⊖": reverse_first,
        "⍉": transpose,
        "⌹": matrix_inverse,
        "○": pi_times,
        "!": factorial,
    }

    _ENV_DEPENDENT: dict[str, str] = {
        "⍳": "_iota",
        "≢": "_tally",
        "⍋": "_grade_up",
        "⍒": "_grade_down",
        "?": "_roll",
        "⍕": "_format",
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

    def _grade_up(self, operand: APLArray) -> APLArray:
        return grade_up(operand, self._env.io)

    def _grade_down(self, operand: APLArray) -> APLArray:
        return grade_down(operand, self._env.io)

    def _roll(self, operand: APLArray) -> APLArray:
        """Monadic ?: roll. ?N → random int ⎕IO..N, ?0 → random float [0,1)."""
        io = self._env.io
        def roll_one(v: object) -> object:
            n = int(v)  # type: ignore[arg-type]
            return _random.random() if n == 0 else _random.randint(io, n - 1 + io)
        if operand.is_scalar():
            return S(roll_one(operand.data[0]))
        return APLArray(list(operand.shape), [roll_one(v) for v in operand.data])

    def _format(self, operand: APLArray) -> APLArray:
        from marple.formatting import format_num
        if operand.is_scalar():
            s = format_num(operand.data[0])
        else:
            parts = [format_num(val) for val in operand.data]
            s = " ".join(parts)
        return APLArray([len(s)], list(s))
