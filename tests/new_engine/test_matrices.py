"""Matrix operation tests — new engine."""

from marple.arraymodel import APLArray, S
from marple.engine import Interpreter


class TestMatrixCreation:
    def test_reshape_to_matrix(self) -> None:
        result = Interpreter(io=1).run("2 3⍴⍳6")
        assert result.shape == [2, 3]
        assert list(result.data) == [1, 2, 3, 4, 5, 6]

    def test_reshape_scalar(self) -> None:
        result = Interpreter(io=1).run("3 3⍴0")
        assert result.shape == [3, 3]
        assert all(v == 0 for v in result.data)


class TestMatrixArithmetic:
    def test_matrix_plus_scalar(self) -> None:
        result = Interpreter(io=1).run("10+2 3⍴⍳6")
        assert result.shape == [2, 3]
        assert list(result.data) == [11, 12, 13, 14, 15, 16]

    def test_matrix_plus_matrix(self) -> None:
        i = Interpreter(io=1)
        i.run("A←2 2⍴1 2 3 4")
        i.run("B←2 2⍴10 20 30 40")
        result = i.run("A+B")
        assert list(result.data) == [11, 22, 33, 44]


class TestMatrixOps:
    def test_transpose(self) -> None:
        result = Interpreter(io=1).run("⍉2 3⍴⍳6")
        assert result.shape == [3, 2]

    def test_ravel(self) -> None:
        result = Interpreter(io=1).run(",2 3⍴⍳6")
        assert result.shape == [6]

    def test_matrix_inverse(self) -> None:
        result = Interpreter(io=1).run("⌹2 2⍴1 0 0 1")
        assert result.shape == [2, 2]

    def test_matrix_multiply(self) -> None:
        result = Interpreter(io=1).run("(2 2⍴1 2 3 4)+.×(2 2⍴5 6 7 8)")
        assert result == APLArray([2, 2], [19, 22, 43, 50])
