"""Dyadic primitive function dispatch for MARPLE."""


from typing import Any

from marple.arraymodel import APLArray, S

#if TYPE_CHECKING:
from marple.environment import Environment

from marple.errors import DomainError, LengthError
from marple.functions import (
    add,
    binomial,
    divide,
    subtract,
    multiply,
    maximum,
    minimum,
    power,
    logarithm,
    residue,
    logical_and,
    logical_or,
    circular,
    less_than,
    less_equal,
    equal,
    greater_equal,
    greater_than,
    not_equal,
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
        "∧": logical_and,  # wrapper — will become GCD when fixed
        "∨": logical_or,   # wrapper — will become LCM when fixed
        "⍴": lambda a, o: a.reshape(o),
        ",": lambda a, o: a.catenate(o),
        "↑": lambda a, o: a.take(o),
        "↓": lambda a, o: a.drop(o),
        "⌽": lambda a, o: a.rotate(o),
        "⊖": lambda a, o: a.rotate_first(o),
        "⊤": lambda a, o: a.encode(o),
        "⊥": lambda a, o: a.decode(o),
        "/": lambda a, o: a.replicate(o),
        "⌿": lambda a, o: a.replicate_first(o),
        "\\": lambda a, o: a.expand(o),
        "⌹": lambda a, o: a.matrix_divide(o),
        "○": circular,
        "!": binomial,
        "≡": lambda a, o: a.match(o),
        "≢": lambda a, o: a.not_match(o),
    }

    _ENV_DEPENDENT: dict[str, str] = {
        "<": "_less_than",
        "≤": "_less_equal",
        "=": "_equal",
        "≥": "_greater_equal",
        ">": "_greater_than",
        "≠": "_not_equal",
        "⍳": "_index_of",
        "∈": "_membership",
        "⌷": "_from",
        "⍕": "_format",
        "?": "_deal",
    }

    def __init__(self, env: Environment) -> None:
        self._env = env

    def apply(self, glyph: str, left: APLArray, right: APLArray) -> APLArray:
        """Apply a dyadic primitive function to left and right arguments."""
        method_name = self._ENV_DEPENDENT.get(glyph)
        if method_name is not None:
            return getattr(self, method_name)(left, right)
        func = self._SIMPLE.get(glyph)
        if func is not None:
            return func(left, right)  # type: ignore[operator]
        raise DomainError(f"Unknown dyadic function: {glyph}")

    def _less_than(self, left: APLArray, right: APLArray) -> APLArray:
        return left.less_than(right, self._env.ct)

    def _less_equal(self, left: APLArray, right: APLArray) -> APLArray:
        return left.less_equal(right, self._env.ct)

    def _equal(self, left: APLArray, right: APLArray) -> APLArray:
        return left.equal(right, self._env.ct)

    def _greater_equal(self, left: APLArray, right: APLArray) -> APLArray:
        return left.greater_equal(right, self._env.ct)

    def _greater_than(self, left: APLArray, right: APLArray) -> APLArray:
        return left.greater_than(right, self._env.ct)

    def _not_equal(self, left: APLArray, right: APLArray) -> APLArray:
        return left.not_equal(right, self._env.ct)

    def _index_of(self, left: APLArray, right: APLArray) -> APLArray:
        return left.index_of(right, self._env.io, self._env.ct)

    def _membership(self, left: APLArray, right: APLArray) -> APLArray:
        return left.membership(right, self._env.ct)

    def _from(self, left: APLArray, right: APLArray) -> APLArray:
        return left.from_array(right, self._env.io)

    def _format(self, left: APLArray, right: APLArray) -> APLArray:
        return left.dyadic_format(right)

    def _deal(self, left: APLArray, right: APLArray) -> APLArray:
        return left.deal(right, io=self._env.io)

    # Comparison functions for operator use (reduce/scan)
    # ct defaults to 0, so they work with 2 args
    _OPERATOR_COMPARISONS: dict[str, object] = {
        "<": less_than,
        "≤": less_equal,
        "=": equal,
        "≥": greater_equal,
        ">": greater_than,
        "≠": not_equal,
    }

    @classmethod
    def resolve(cls, glyph: str) -> object:
        """Return the callable for a glyph, for use by operators."""
        func = cls._SIMPLE.get(glyph)
        if func is not None:
            return func
        func = cls._OPERATOR_COMPARISONS.get(glyph)
        if func is not None:
            return func
        raise DomainError(f"Unknown function for operator: {glyph}")

    def resolve_with_env(self, glyph: str) -> object:
        """Return a callable for a glyph, including env-dependent functions."""
        method_name = self._ENV_DEPENDENT.get(glyph)
        if method_name is not None:
            method = getattr(self, method_name)
            return lambda a, o, _m=method: _m(a, o)
        func = self._SIMPLE.get(glyph)
        if func is not None:
            return func
        raise DomainError(f"Unknown function for operator: {glyph}")
