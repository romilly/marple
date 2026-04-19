"""First-axis rotate/reverse (⊖) and matrix rotate/reverse (⌽) tests."""

from marple.numpy_array import APLArray, S
from marple.engine import Interpreter


class TestMonadicReverseMatrix:
    def test_reverse_matrix_reverses_rows(self) -> None:
        """⌽ on matrix reverses along last axis (each row)."""
        result = Interpreter(io=1).run("⌽2 3⍴1 2 3 4 5 6")
        assert result == APLArray.array([2, 3], [[3, 2, 1], [6, 5, 4]])

    def test_reverse_vector_unchanged(self) -> None:
        result = Interpreter(io=1).run("⌽1 2 3")
        assert result == APLArray.array([3], [3, 2, 1])


class TestDyadicRotateMatrix:
    def test_rotate_matrix_rotates_each_row(self) -> None:
        """1⌽M rotates each row left by 1."""
        result = Interpreter(io=1).run("1⌽2 3⍴1 2 3 4 5 6")
        assert result == APLArray.array([2, 3], [[2, 3, 1], [5, 6, 4]])

    def test_rotate_matrix_negative(self) -> None:
        result = Interpreter(io=1).run("¯1⌽2 3⍴1 2 3 4 5 6")
        assert result == APLArray.array([2, 3], [[3, 1, 2], [6, 4, 5]])

    def test_rotate_vector_unchanged(self) -> None:
        result = Interpreter(io=1).run("1⌽1 2 3 4 5")
        assert result == APLArray.array([5], [2, 3, 4, 5, 1])


class TestMonadicReverseFirst:
    def test_reverse_first_axis(self) -> None:
        """⊖ on matrix reverses row order."""
        result = Interpreter(io=1).run("⊖2 3⍴1 2 3 4 5 6")
        assert result == APLArray.array([2, 3], [[4, 5, 6], [1, 2, 3]])

    def test_reverse_first_vector(self) -> None:
        """⊖ on vector is same as ⌽."""
        result = Interpreter(io=1).run("⊖1 2 3")
        assert result == APLArray.array([3], [3, 2, 1])


class TestDyadicRotateFirst:
    def test_rotate_first_axis(self) -> None:
        """1⊖M shifts rows up by 1."""
        result = Interpreter(io=1).run("1⊖2 3⍴1 2 3 4 5 6")
        assert result == APLArray.array([2, 3], [[4, 5, 6], [1, 2, 3]])

    def test_rotate_first_axis_negative(self) -> None:
        """¯1⊖M shifts rows down by 1."""
        result = Interpreter(io=1).run("¯1⊖3 3⍴⍳9")
        assert result == APLArray.array([3, 3], [[7, 8, 9], [1, 2, 3], [4, 5, 6]])

    def test_rotate_first_vector(self) -> None:
        """⊖ on vector is same as ⌽."""
        result = Interpreter(io=1).run("1⊖1 2 3 4 5")
        assert result == APLArray.array([5], [2, 3, 4, 5, 1])
