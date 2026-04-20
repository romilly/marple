"""Inner and outer product tests — new engine."""

import pytest

from marple.ports.array import APLArray, S
from marple.engine import Interpreter
from marple.errors import DomainError, LengthError


class TestInnerProduct:
    def test_dot_product(self) -> None:
        assert Interpreter(io=1).run("1 2 3+.×4 5 6") == S(32)

    def test_matrix_multiply(self) -> None:
        i = Interpreter(io=1)
        i.run("A←2 2⍴1 2 3 4")
        i.run("B←2 2⍴5 6 7 8")
        result = i.run("A+.×B")
        assert result == APLArray.array([2, 2], [[19, 22], [43, 50]])

    def test_matrix_multiply_float(self) -> None:
        i = Interpreter(io=1)
        i.run("A←2 3⍴1.5 2.5 3.5 4.5 5.5 6.5")
        i.run("B←3 2⍴0.1 0.2 0.3 0.4 0.5 0.6")
        result = i.run("A+.×B")
        assert result.shape == [2, 2]

    def test_matrix_multiply_non_square(self) -> None:
        i = Interpreter(io=1)
        i.run("A←2 3⍴⍳6")
        i.run("B←3 2⍴⍳6")
        result = i.run("A+.×B")
        assert result == APLArray.array([2, 2], [[22, 28], [49, 64]])

    def test_matrix_vector_inner(self) -> None:
        i = Interpreter(io=1)
        i.run("M←2 3⍴⍳6")
        result = i.run("M+.×1 2 3")
        assert result.shape == [2]
        assert list(result.data) == [14, 32]

    def test_vector_matrix_inner(self) -> None:
        i = Interpreter(io=1)
        i.run("M←2 3⍴⍳6")
        result = i.run("1 2+.×M")
        assert result.shape == [3]
        assert list(result.data) == [9, 12, 15]

    def test_length_error(self) -> None:
        with pytest.raises(LengthError):
            Interpreter(io=1).run("2 3+.×3 4 5")

    def test_rank3_matrix_inner(self) -> None:
        """(2 2 3) +.× (3 2) → (2 2 2)"""
        i = Interpreter(io=1)
        i.run("A←2 2 3⍴⍳12")
        i.run("B←3 2⍴1 2 3 4 5 6")
        result = i.run("A+.×B")
        assert result == APLArray.array([2, 2, 2],
            [[[22, 28], [49, 64]], [[76, 100], [103, 136]]])


    def test_inner_product_int_upcasts_to_float(self) -> None:
        """Repeated +.× on int matrices must upcast to float64 so int64
        wraparound doesn't produce a silently-wrong answer. 4 iterations
        push element magnitudes past int64 range but stay well inside
        float64 range — the result should be finite and positive.
        """
        i = Interpreter(io=1)
        i.run("⎕RL←42")
        i.run("y ← ?10 10⍴100")
        result = i.run("({⍵+.×⍵}⍣4) y")
        import math
        for v in result.data.flat:
            assert v > 0 and not math.isinf(float(v)), f"Bad value: {v}"

    def test_inner_product_float_overflow_raises(self) -> None:
        """10 iterations push element magnitudes past float64's ~1.8e308
        ceiling. That is genuine overflow and must raise DomainError
        rather than silently returning ∞ (which the old
        `v > 0` assertion masked).
        """
        i = Interpreter(io=1)
        i.run("⎕RL←42")
        i.run("y ← ?10 10⍴100")
        with pytest.raises(DomainError):
            i.run("({⍵+.×⍵}⍣10) y")


class TestOuterProduct:
    def test_multiplication_table(self) -> None:
        result = Interpreter(io=1).run("(⍳3)∘.×⍳4")
        assert result == APLArray.array([3, 4],
            [[1, 2, 3, 4], [2, 4, 6, 8], [3, 6, 9, 12]])

    def test_outer_addition(self) -> None:
        result = Interpreter(io=1).run("1 2 3∘.+10 20")
        assert result == APLArray.array([3, 2], [[11, 21], [12, 22], [13, 23]])

    def test_outer_product_no_int_overflow(self) -> None:
        """∘.× on large int vectors must not wrap around."""
        i = Interpreter(io=1)
        # 1e9 * 1e9 = 1e18 which overflows int64 (max ~9.2e18)
        # 3e9 * 3e9 = 9e18 which is right at the edge
        # 1e10 * 1e10 = 1e20 which clearly overflows
        result = i.run("(1e10 2e10)∘.×(3e10 4e10)")
        for v in result.data.flat:
            assert v > 0, f"Overflow detected: {v}"

    def test_outer_product_float_overflow_raises(self) -> None:
        """∘.× where element products exceed float64 max must raise
        DomainError (rather than silently returning ∞)."""
        with pytest.raises(DomainError):
            Interpreter(io=1).run("(2⍴1e200)∘.×2⍴1e200")

    def test_outer_equality(self) -> None:
        result = Interpreter(io=1).run("1 2 3∘.=1 3")
        assert result == APLArray.array([3, 2], [[1, 0], [0, 0], [0, 1]])


class TestInnerProductAssignment:
    """f←+.× produces a stored function applicable later."""

    def test_assign_and_apply_dot_product(self) -> None:
        i = Interpreter(io=1)
        i.run("f←+.×")
        assert i.run("1 2 3 f 4 5 6") == S(32)

    def test_assign_and_matrix_multiply(self) -> None:
        i = Interpreter(io=1)
        i.run("dot←+.×")
        i.run("A←2 2⍴1 2 3 4")
        i.run("B←2 2⍴5 6 7 8")
        result = i.run("A dot B")
        assert result == APLArray.array([2, 2], [[19, 22], [43, 50]])


class TestOuterProductAssignment:
    """f←∘.× produces a stored function applicable later."""

    def test_assign_and_apply_outer_multiply(self) -> None:
        i = Interpreter(io=1)
        i.run("f←∘.×")
        result = i.run("1 2 3 f 4 5 6")
        assert result == APLArray.array([3, 3], [[4, 5, 6], [8, 10, 12], [12, 15, 18]])

    def test_assign_and_apply_outer_equality(self) -> None:
        i = Interpreter(io=1)
        i.run("eq←∘.=")
        result = i.run("1 2 3 eq 1 3")
        assert result == APLArray.array([3, 2], [[1, 0], [0, 0], [0, 1]])
