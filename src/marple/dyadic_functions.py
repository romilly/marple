"""Dyadic primitive function dispatch for MARPLE."""


from typing import Any

from marple.arraymodel import APLArray, S

#if TYPE_CHECKING:
from marple.environment import Environment
import random as _random

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
from marple.structural import (
    catenate,
    drop,
    encode,
    decode,
    expand,
    from_array,
    index_of,
    membership,
    replicate,
    replicate_first,
    reshape,
    rotate,
    rotate_first,
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
        "⊖": rotate_first,
        "⊤": encode,
        "⊥": decode,
        "/": replicate,
        "⌿": replicate_first,
        "\\": expand,
        "⌹": matrix_divide,
        "○": circular,
        "!": binomial,
        "≡": lambda a, o: S(1 if a == o else 0),
        "≢": lambda a, o: S(0 if a == o else 1),
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
        return less_than(left, right, self._env.ct)

    def _less_equal(self, left: APLArray, right: APLArray) -> APLArray:
        return less_equal(left, right, self._env.ct)

    def _equal(self, left: APLArray, right: APLArray) -> APLArray:
        return equal(left, right, self._env.ct)

    def _greater_equal(self, left: APLArray, right: APLArray) -> APLArray:
        return greater_equal(left, right, self._env.ct)

    def _greater_than(self, left: APLArray, right: APLArray) -> APLArray:
        return greater_than(left, right, self._env.ct)

    def _not_equal(self, left: APLArray, right: APLArray) -> APLArray:
        return not_equal(left, right, self._env.ct)

    def _index_of(self, left: APLArray, right: APLArray) -> APLArray:
        return index_of(left, right, self._env.io, self._env.ct)

    def _membership(self, left: APLArray, right: APLArray) -> APLArray:
        return membership(left, right, self._env.ct)

    def _from(self, left: APLArray, right: APLArray) -> APLArray:
        return from_array(left, right, self._env.io)

    def _format(self, left: APLArray, right: APLArray) -> APLArray:
        if left.is_scalar():
            width = int(left.data[0])
            precision = None
        else:
            width = int(left.data[0])
            precision = int(left.data[1]) if len(left.data) > 1 else None
        values = right.data if not right.is_scalar() else [right.data[0]]
        result_chars: list[str] = []
        for v in values:
            if precision is not None:
                formatted = f"{float(v):.{precision}f}"
            else:
                formatted = str(v)
            padded = " " * max(0, width - len(formatted)) + formatted
            result_chars.extend(list(padded))
        return APLArray.array([len(result_chars)], result_chars)

    def _deal(self, left: APLArray, right: APLArray) -> APLArray:
        io = self._env.io
        n = int(left.data[0])
        m = int(right.data[0])
        if n > m:
            raise LengthError(f"Deal: cannot choose {n} from {m}")
        result = _random.sample(range(io, m + io), n)
        return APLArray.array([n], result)

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
