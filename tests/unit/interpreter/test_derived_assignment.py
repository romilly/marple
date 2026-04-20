"""Tests for assigning derived and primitive function values to
variables.

This exercises a code path that was broken until this file landed:
`ctx.assign()` used to call `self.evaluate(value_node)` on the
raw parser output, which required a `Node` instance. Raw glyph
strings (`+`) and `BoundOperator` instances (`⍴∘⍴`, `+/⍤1`) are
not `Node` subclasses, so `f←+` and friends raised
`DOMAIN ERROR: Unknown AST node`.
"""

import pytest

from marple.engine import Interpreter
from marple.ports.array import APLArray, S


class TestAssignBeside:
    """Canonical case from the Dyalog Beside docs: RANK←⍴∘⍴."""

    def test_rank_idiom(self) -> None:
        i = Interpreter(io=1)
        i.run("RANK←⍴∘⍴")
        assert i.run("RANK 'abc'") == APLArray.array([1], [1])
        assert i.run("RANK 2 3⍴⍳6") == APLArray.array([1], [2])
        assert i.run("RANK 2 3 4⍴⍳24") == APLArray.array([1], [3])

    def test_sum_of_iota(self) -> None:
        """Triangular number via SUMIOTA←+/∘⍳."""
        i = Interpreter(io=1)
        i.run("SUMIOTA←+/∘⍳")
        assert i.run("SUMIOTA 10") == S(55)
        assert i.run("SUMIOTA 100") == S(5050)

    def test_beside_dyadic(self) -> None:
        """Dyadic application of a stored beside-derived function."""
        i = Interpreter(io=1)
        i.run("PREPEND←,∘⍳")
        result = i.run("0 PREPEND 5")
        assert result == APLArray.array([6], [0, 1, 2, 3, 4, 5])


class TestAssignPrimitiveFunction:
    """`f←+` and similar: primitive verbs as function values."""

    def test_primitive_as_dyadic(self) -> None:
        i = Interpreter(io=1)
        i.run("f←+")
        assert i.run("2 f 3") == S(5)

    def test_primitive_as_monadic(self) -> None:
        i = Interpreter(io=1)
        i.run("f←-")
        assert i.run("f 5") == S(-5)

    def test_primitive_with_reduce(self) -> None:
        """Stored primitive can be used as an operator operand."""
        i = Interpreter(io=1)
        i.run("f←+")
        assert i.run("f/⍳5") == S(15)


class TestAssignRankDerived:
    """`SUM←+/⍤1` and similar: rank-derived functions."""

    def test_row_sums(self) -> None:
        i = Interpreter(io=1)
        i.run("SUM←+/⍤1")
        result = i.run("SUM 2 3⍴⍳6")
        assert result == APLArray.array([2], [6, 15])

    def test_row_sums_rank3(self) -> None:
        i = Interpreter(io=1)
        i.run("SUM←+/⍤1")
        result = i.run("SUM 2 3 4⍴⍳24")
        # For each of 6 rows of 4 elements: sum of that row
        assert result.shape == [2, 3]


class TestAssignCommute:
    """`dup←+⍨` and similar: commute-derived functions."""

    def test_commute_monadic(self) -> None:
        """`+⍨ ω ≡ ω + ω` — double the value."""
        i = Interpreter(io=1)
        i.run("dup←+⍨")
        assert i.run("dup 5") == S(10)
        assert i.run("dup 3 4 5") == APLArray.array([3], [6, 8, 10])

    def test_commute_dyadic(self) -> None:
        """`α -⍨ ω ≡ ω - α` — swapped subtraction."""
        i = Interpreter(io=1)
        i.run("revsub←-⍨")
        assert i.run("3 revsub 10") == S(7)  # 10 - 3 = 7


class TestAssignPower:
    """`twice←{⍵+1}⍣2` and similar: power-derived functions."""

    def test_power_with_dfn(self) -> None:
        i = Interpreter(io=1)
        i.run("incr←{⍵+1}")
        i.run("thrice←incr⍣3")
        assert i.run("thrice 10") == S(13)


class TestAssignClassGuard:
    """Regression guard: reassigning noun ↔ function should ClassError."""

    def test_function_to_noun_raises(self) -> None:
        from marple.errors import ClassError
        i = Interpreter(io=1)
        i.run("x←5")
        with pytest.raises(ClassError):
            i.run("x←+")

    def test_noun_to_function_raises(self) -> None:
        from marple.errors import ClassError
        i = Interpreter(io=1)
        i.run("f←+")
        with pytest.raises(ClassError):
            i.run("f←5")
