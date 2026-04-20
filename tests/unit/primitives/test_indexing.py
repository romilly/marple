"""Bracket indexing tests — new engine."""

from marple.ports.array import APLArray, S
from marple.engine import Interpreter


class TestVectorIndexing:
    def test_single_element(self) -> None:
        i = Interpreter(io=1)
        i.run("v←10 20 30 40 50")
        assert i.run("v[3]") == S(30)

    def test_multiple_elements(self) -> None:
        i = Interpreter(io=1)
        i.run("v←10 20 30 40 50")
        assert i.run("v[1 3 5]") == APLArray.array([3], [10, 30, 50])


class TestIndexingPreservesShape:
    def test_scalar_index(self) -> None:
        i = Interpreter(io=1)
        i.run("v←10 20 30")
        result = i.run("v[2]")
        assert result.shape == []

    def test_vector_index(self) -> None:
        i = Interpreter(io=1)
        i.run("v←10 20 30 40 50")
        result = i.run("v[2 4]")
        assert result.shape == [2]

    def test_matrix_index(self) -> None:
        i = Interpreter(io=1)
        i.run("v←10 20 30 40 50")
        result = i.run("v[2 3⍴1 2 3 4 5 1]")
        assert result == APLArray.array([2, 3], [[10, 20, 30], [40, 50, 10]])

    def test_rank3_index(self) -> None:
        i = Interpreter(io=1)
        i.run("v←10 20 30 40")
        result = i.run("v[2 2 2⍴1 2 3 4 1 2 3 4]")
        assert result == APLArray.array([2, 2, 2],
            [[[10, 20], [30, 40]], [[10, 20], [30, 40]]])

    def test_rank4_index(self) -> None:
        i = Interpreter(io=1)
        i.run("v←10 20 30")
        result = i.run("v[2 1 3 1⍴1 2 3 1 2 3]")
        assert result.shape == [2, 1, 3, 1]

    def test_outer_product_index(self) -> None:
        """The original bug report: ' *'[1+r∘.=s]"""
        i = Interpreter(io=1)
        i.run("r←1 2 3")
        i.run("s←1 2 3")
        result = i.run("' *'[1+r∘.=s]")
        assert result.shape == [3, 3]

    def test_string_index_with_matrix(self) -> None:
        from marple.backend_functions import chars_to_str
        result = Interpreter(io=1).run("'abcde'[2 3⍴1 2 3 4 5 1]")
        assert result.shape == [2, 3]
        assert chars_to_str(result.data) == "abcdea"


class TestStringBracketIndexWithFunction:
    """Bracket indexing on a string literal binds tighter than function application."""

    def test_shape_of_string_bracket_index(self) -> None:
        i = Interpreter(io=1)
        result = i.run("⍴' *'[1 2 1]")
        assert result == APLArray.array([1], [3])

    def test_shape_of_string_bracket_index_matrix(self) -> None:
        i = Interpreter(io=1)
        result = i.run("⍴' *'[2 2⍴1 2 1 2]")
        assert result == APLArray.array([2], [2, 2])


class TestNumericBracketIndexWithFunction:
    """Bracket indexing on a numeric vector binds tighter than function application."""

    def test_shape_of_numeric_bracket_index(self) -> None:
        i = Interpreter(io=1)
        i.run("v←10 20 30 40 50")
        result = i.run("⍴v[2 3]")
        assert result == APLArray.array([1], [2])

    def test_shape_of_paren_vector_bracket_index(self) -> None:
        """⍴(1 2 3 4 5)[2 3] should give 2, not error."""
        i = Interpreter(io=1)
        result = i.run("⍴(1 2 3 4 5)[2 3]")
        assert result == APLArray.array([1], [2])

    def test_shape_of_literal_vector_bracket_index(self) -> None:
        """⍴1 2 3 4 5[2 3] — bracket binds to the whole vector."""
        i = Interpreter(io=1)
        result = i.run("⍴1 2 3 4 5[2 3]")
        assert result == APLArray.array([1], [2])


class TestMatrixIndexing:
    def test_single_element(self) -> None:
        i = Interpreter(io=1)
        i.run("M←2 3⍴⍳6")
        assert i.run("M[2;3]") == S(6)

    def test_entire_row(self) -> None:
        i = Interpreter(io=1)
        i.run("M←2 3⍴⍳6")
        assert i.run("M[1;]") == APLArray.array([3], [1, 2, 3])

    def test_entire_column(self) -> None:
        i = Interpreter(io=1)
        i.run("M←2 3⍴⍳6")
        assert i.run("M[;2]") == APLArray.array([2], [2, 5])


class TestDefaultIndexOrigin:
    def test_default_index_origin(self) -> None:
        assert Interpreter(io=1).run("⎕IO") == S(1)

    def test_index_origin_zero(self) -> None:
        assert Interpreter(io=0).run("⍳3") == APLArray.array([3], [0, 1, 2])


class TestIndexOriginZero:
    def test_indexing_with_io0(self) -> None:
        i = Interpreter(io=0)
        i.run("v←10 20 30")
        assert i.run("v[0]") == S(10)

    def test_grade_up_with_io0(self) -> None:
        assert Interpreter(io=0).run("⍋3 1 4") == APLArray.array([3], [1, 0, 2])

    def test_index_of_with_io0(self) -> None:
        assert Interpreter(io=0).run("10 20 30⍳20") == S(1)

    def test_grade_down_with_io0(self) -> None:
        assert Interpreter(io=0).run("⍒3 1 4") == APLArray.array([3], [2, 0, 1])

    def test_index_of_not_found_with_io0(self) -> None:
        assert Interpreter(io=0).run("10 20 30⍳99") == S(3)
