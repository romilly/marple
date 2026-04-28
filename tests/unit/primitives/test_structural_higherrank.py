"""Structural functions on higher-rank and character arrays."""

from marple.ports.array import APLArray, S, str_to_char_array
from marple.engine import Interpreter
from marple.adapters.numpy_array_builder import BUILDER


class TestTakeMultiAxis:
    def test_take_two_axes(self) -> None:
        """2 3↑4 5⍴⍳20 takes 2 rows and 3 columns."""
        result = Interpreter(io=0).run("2 3↑4 5⍴⍳20")
        assert result == BUILDER.apl_array([2, 3], [[0, 1, 2], [5, 6, 7]])

    def test_take_with_padding(self) -> None:
        """6 3↑4 5⍴⍳20 pads extra rows with zeros."""
        result = Interpreter(io=0).run("6 3↑4 5⍴⍳20")
        assert result == BUILDER.apl_array([6, 3], [
            [0, 1, 2],
            [5, 6, 7],
            [10, 11, 12],
            [15, 16, 17],
            [0, 0, 0],
            [0, 0, 0],
        ])

    def test_take_negative_both(self) -> None:
        """¯2 ¯3↑4 5⍴⍳20 takes last 2 rows, last 3 cols."""
        result = Interpreter(io=0).run("¯2 ¯3↑4 5⍴⍳20")
        assert result == BUILDER.apl_array([2, 3], [[12, 13, 14], [17, 18, 19]])

    def test_scalar_left_on_matrix(self) -> None:
        """3↑4 5⍴⍳20 takes first 3 rows, all columns."""
        result = Interpreter(io=0).run("3↑4 5⍴⍳20")
        assert result.shape == [3, 5]


class TestDropMultiAxis:
    def test_drop_two_axes(self) -> None:
        """1 2↓4 5⍴⍳20 drops 1 row and 2 columns."""
        result = Interpreter(io=0).run("1 2↓4 5⍴⍳20")
        assert result == BUILDER.apl_array([3, 3],
            [[7, 8, 9], [12, 13, 14], [17, 18, 19]])

    def test_scalar_left_on_matrix(self) -> None:
        """1↓4 5⍴⍳20 drops first row, keeps all columns."""
        result = Interpreter(io=0).run("1↓4 5⍴⍳20")
        assert result.shape == [3, 5]


class TestCharacterData:
    def test_take_char_with_space_fill(self) -> None:
        """5↑'abc' pads with spaces."""
        result = Interpreter(io=1).run("5↑'abc'")
        assert result == BUILDER.apl_array([5], str_to_char_array("abc  "))

    def test_take_char_exact(self) -> None:
        result = Interpreter(io=1).run("3↑'abcde'")
        assert result == BUILDER.apl_array([3], str_to_char_array("abc"))

    def test_take_char_negative(self) -> None:
        # ¯3↑'abcde' takes the last 3
        result = Interpreter(io=1).run("¯3↑'abcde'")
        assert result == BUILDER.apl_array([3], str_to_char_array("cde"))

    def test_take_char_negative_with_fill(self) -> None:
        # ¯5↑'abc' takes 5 from the right; fill prepends
        result = Interpreter(io=1).run("¯5↑'abc'")
        assert result == BUILDER.apl_array([5], str_to_char_array("  abc"))

    def test_take_char_zero(self) -> None:
        result = Interpreter(io=1).run("0↑'abc'")
        assert result == BUILDER.apl_array([0], str_to_char_array(""))

    def test_take_from_empty_char(self) -> None:
        # Take from an empty char vector — fills with spaces.
        result = Interpreter(io=1).run("3↑''")
        assert result == BUILDER.apl_array([3], str_to_char_array("   "))

    def test_take_first_row_of_char_matrix(self) -> None:
        # 1↑2 3⍴'ABCDEF' takes first major cell (row); result is 1×3 matrix
        result = Interpreter(io=1).run("1↑2 3⍴'ABCDEF'")
        assert result == BUILDER.apl_array([1, 3], str_to_char_array("ABC").reshape(1, 3))

    def test_take_negative_row_of_char_matrix(self) -> None:
        result = Interpreter(io=1).run("¯1↑2 3⍴'ABCDEF'")
        assert result == BUILDER.apl_array([1, 3], str_to_char_array("DEF").reshape(1, 3))

    def test_take_two_axes_char_matrix(self) -> None:
        # 1 2↑ takes the first row, first 2 cols
        result = Interpreter(io=1).run("1 2↑2 3⍴'ABCDEF'")
        assert result == BUILDER.apl_array([1, 2], str_to_char_array("AB").reshape(1, 2))

    def test_drop_char_vector(self) -> None:
        result = Interpreter(io=1).run("2↓'abcde'")
        assert result == BUILDER.apl_array([3], str_to_char_array("cde"))

    def test_drop_char_negative(self) -> None:
        result = Interpreter(io=1).run("¯2↓'abcde'")
        assert result == BUILDER.apl_array([3], str_to_char_array("abc"))

    def test_drop_char_zero(self) -> None:
        result = Interpreter(io=1).run("0↓'abc'")
        assert result == BUILDER.apl_array([3], str_to_char_array("abc"))

    def test_drop_too_many_chars(self) -> None:
        # Dropping more than length gives empty char vector
        result = Interpreter(io=1).run("5↓'abc'")
        assert result == BUILDER.apl_array([0], str_to_char_array(""))

    def test_drop_first_row_of_char_matrix(self) -> None:
        # 1↓ drops the first row, leaving a 1×3 matrix
        result = Interpreter(io=1).run("1↓2 3⍴'ABCDEF'")
        assert result == BUILDER.apl_array([1, 3], str_to_char_array("DEF").reshape(1, 3))

    def test_rotate_char_vector(self) -> None:
        result = Interpreter(io=1).run("1⌽'hello'")
        assert result == BUILDER.apl_array([5], str_to_char_array("elloh"))

    def test_rotate_char_matrix(self) -> None:
        result = Interpreter(io=1).run("1⌽2 3⍴'ABCDEF'")
        assert result == BUILDER.apl_array([2, 3], str_to_char_array("BCAEFD").reshape(2, 3))

    def test_reverse_char_matrix(self) -> None:
        result = Interpreter(io=1).run("⌽2 3⍴'ABCDEF'")
        assert result == BUILDER.apl_array([2, 3], str_to_char_array("CBAFED").reshape(2, 3))

    def test_rotate_first_char_matrix(self) -> None:
        result = Interpreter(io=1).run("1⊖2 3⍴'ABCDEF'")
        assert result == BUILDER.apl_array([2, 3], str_to_char_array("DEFABC").reshape(2, 3))

    def test_reshape_char(self) -> None:
        result = Interpreter(io=1).run("3⍴'AB'")
        assert result == BUILDER.apl_array([3], str_to_char_array("ABA"))

    def test_reshape_char_matrix(self) -> None:
        result = Interpreter(io=1).run("2 3⍴'ABCD'")
        assert result == BUILDER.apl_array([2, 3], str_to_char_array("ABCDAB").reshape(2, 3))

    def test_reshape_char_scalar_to_vector(self) -> None:
        # Reshape a scalar char to a vector — should fill all positions.
        result = Interpreter(io=1).run("5⍴'X'")
        assert result == BUILDER.apl_array([5], str_to_char_array("XXXXX"))

    def test_reshape_empty_char_to_vector(self) -> None:
        # Reshape an empty char vector to a non-empty target — APL fills
        # with the prototype element, which for chars is space.
        result = Interpreter(io=1).run("5⍴''")
        assert result == BUILDER.apl_array([5], str_to_char_array("     "))

    def test_reshape_char_to_empty(self) -> None:
        # 0⍴'AB' produces an empty char vector, not an empty numeric one.
        result = Interpreter(io=1).run("0⍴'AB'")
        assert result == BUILDER.apl_array([0], str_to_char_array(""))

    def test_reshape_empty_char_to_empty(self) -> None:
        # 0⍴'' is the degenerate case — empty source, empty target.
        result = Interpreter(io=1).run("0⍴''")
        assert result == BUILDER.apl_array([0], str_to_char_array(""))

    def test_reshape_char_to_rank3(self) -> None:
        # Reshape into a rank-3 char array.
        result = Interpreter(io=1).run("2 2 3⍴'ABCDEFGHIJKL'")
        assert result == BUILDER.apl_array([2, 2, 3], str_to_char_array("ABCDEFGHIJKL").reshape(2, 2, 3))

    def test_reshape_char_matrix_to_different_shape(self) -> None:
        # Take a 2x3 char matrix and reshape it to 3x2.
        result = Interpreter(io=1).run("3 2⍴2 3⍴'ABCDEF'")
        assert result == BUILDER.apl_array([3, 2], str_to_char_array("ABCDEF").reshape(3, 2))

    def test_reshape_char_cycles_when_target_larger(self) -> None:
        # Reshape larger than source cycles the source data.
        result = Interpreter(io=1).run("7⍴'AB'")
        assert result == BUILDER.apl_array([7], str_to_char_array("ABABABA"))

    def test_ravel_char_matrix(self) -> None:
        result = Interpreter(io=1).run(",2 3⍴'ABCDEF'")
        assert result == BUILDER.apl_array([6], str_to_char_array("ABCDEF"))

    def test_reverse_char_vector(self) -> None:
        result = Interpreter(io=1).run("⌽'hello'")
        assert result == BUILDER.apl_array([5], str_to_char_array("olleh"))

    def test_transpose_char_matrix(self) -> None:
        result = Interpreter(io=1).run("⍉2 3⍴'ABCDEF'")
        assert result == BUILDER.apl_array([3, 2], str_to_char_array("ADBECF").reshape(3, 2))

    def test_catenate_char(self) -> None:
        result = Interpreter(io=1).run("'hello','world'")
        assert result == BUILDER.apl_array([10], str_to_char_array("helloworld"))

    def test_catenate_char_scalar(self) -> None:
        result = Interpreter(io=1).run("'hello','-'")
        assert result == BUILDER.apl_array([6], str_to_char_array("hello-"))

    def test_comparison_char_equal(self) -> None:
        assert Interpreter(io=1).run("'A'='A'") == S(1)

    def test_comparison_char_not_equal(self) -> None:
        assert Interpreter(io=1).run("'A'='B'") == S(0)

    def test_comparison_char_less(self) -> None:
        assert Interpreter(io=1).run("'A'<'B'") == S(1)

    def test_comparison_char_vector_equal(self) -> None:
        result = Interpreter(io=1).run("'abc'='aXc'")
        assert result.shape == [3]

    def test_comparison_char_ne(self) -> None:
        assert Interpreter(io=1).run("'A'≠'B'") == S(1)
        assert Interpreter(io=1).run("'A'≠'A'") == S(0)
