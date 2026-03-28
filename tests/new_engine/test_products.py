"""Inner and outer product tests — new engine."""

import pytest

from marple.arraymodel import APLArray, S
from marple.engine import Interpreter
from marple.errors import LengthError


class TestInnerProduct:
    def test_dot_product(self) -> None:
        assert Interpreter(io=1).run("1 2 3+.×4 5 6") == S(32)

    def test_matrix_multiply(self) -> None:
        i = Interpreter(io=1)
        i.run("A←2 2⍴1 2 3 4")
        i.run("B←2 2⍴5 6 7 8")
        result = i.run("A+.×B")
        assert result == APLArray([2, 2], [19, 22, 43, 50])

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
        assert result.shape == [2, 2]
        assert list(result.data) == [22, 28, 49, 64]

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


class TestOuterProduct:
    def test_multiplication_table(self) -> None:
        result = Interpreter(io=1).run("(⍳3)∘.×⍳4")
        assert result == APLArray([3, 4], [
            1, 2, 3, 4, 2, 4, 6, 8, 3, 6, 9, 12])

    def test_outer_addition(self) -> None:
        result = Interpreter(io=1).run("1 2 3∘.+10 20")
        assert result == APLArray([3, 2], [11, 21, 12, 22, 13, 23])

    def test_outer_equality(self) -> None:
        result = Interpreter(io=1).run("1 2 3∘.=1 3")
        assert result == APLArray([3, 2], [1, 0, 0, 0, 0, 1])
