"""Matrix operation tests — new engine."""

from marple.numpy_array import APLArray, S
from marple.engine import Interpreter


class TestMatrixCreation:
    def test_shape_of_matrix(self) -> None:
        result = Interpreter(io=1).run("⍴2 3⍴⍳6")
        assert result == APLArray.array([2], [2, 3])



class TestMatrixArithmetic:
    def test_matrix_plus_scalar(self) -> None:
        result = Interpreter(io=1).run("10+2 3⍴⍳6")
        assert result == APLArray.array([2, 3], [[11, 12, 13], [14, 15, 16]])

    def test_negate_matrix(self) -> None:
        result = Interpreter(io=1).run("-2 2⍴1 2 3 4")
        assert result == APLArray.array([2, 2], [[-1, -2], [-3, -4]])

    def test_matrix_plus_matrix(self) -> None:
        i = Interpreter(io=1)
        i.run("A←2 2⍴1 2 3 4")
        i.run("B←2 2⍴10 20 30 40")
        result = i.run("A+B")
        assert result == APLArray.array([2, 2], [[11, 22], [33, 44]])


class TestMatrixOps:
    def test_transpose(self) -> None:
        result = Interpreter(io=1).run("⍉2 3⍴⍳6")
        assert result.shape == [3, 2]

    def test_ravel(self) -> None:
        result = Interpreter(io=1).run(",2 3⍴⍳6")
        assert result == APLArray.array([6], [1, 2, 3, 4, 5, 6])

    def test_transpose_vector(self) -> None:
        result = Interpreter(io=1).run("⍉1 2 3")
        assert result == APLArray.array([3], [1, 2, 3])

    def test_matrix_inverse(self) -> None:
        result = Interpreter(io=1).run("⌹2 2⍴1 0 0 1")
        assert result.shape == [2, 2]

    def test_matrix_multiply(self) -> None:
        result = Interpreter(io=1).run("(2 2⍴1 2 3 4)+.×(2 2⍴5 6 7 8)")
        assert result == APLArray.array([2, 2], [[19, 22], [43, 50]])


class TestGrade:
    def test_grade_up(self) -> None:
        result = Interpreter(io=1).run("⍋3 1 4 1 5")
        assert result == APLArray.array([5], [2, 4, 1, 3, 5])

    def test_grade_down(self) -> None:
        result = Interpreter(io=1).run("⍒3 1 4 1 5")
        assert result == APLArray.array([5], [5, 3, 1, 2, 4])


class TestEncodeDecode:
    def test_encode(self) -> None:
        result = Interpreter(io=1).run("2 2 2⊤7")
        assert result == APLArray.array([3], [1, 1, 1])

    def test_decode(self) -> None:
        result = Interpreter(io=1).run("2⊥1 1 1")
        assert result == S(7)

    def test_decode_mixed_base(self) -> None:
        result = Interpreter(io=1).run("24 60 60⊥1 2 3")
        assert result == S(3723)
