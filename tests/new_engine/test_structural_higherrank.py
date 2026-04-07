"""Structural functions on higher-rank and character arrays."""

from marple.numpy_array import APLArray, S
from marple.engine import Interpreter


class TestTakeMultiAxis:
    def test_take_two_axes(self) -> None:
        """2 3↑4 5⍴⍳20 takes 2 rows and 3 columns."""
        result = Interpreter(io=0).run("2 3↑4 5⍴⍳20")
        assert result.shape == [2, 3]
        assert list(result.data) == [0, 1, 2, 5, 6, 7]

    def test_take_with_padding(self) -> None:
        """6 3↑4 5⍴⍳20 pads extra rows with zeros."""
        result = Interpreter(io=0).run("6 3↑4 5⍴⍳20")
        assert result.shape == [6, 3]
        # 4 real rows × 3 cols = 12 data, then 2 padded rows × 3 cols = 6 zeros
        assert list(result.data[12:]) == [0, 0, 0, 0, 0, 0]

    def test_take_negative_both(self) -> None:
        """¯2 ¯3↑4 5⍴⍳20 takes last 2 rows, last 3 cols."""
        result = Interpreter(io=0).run("¯2 ¯3↑4 5⍴⍳20")
        assert result.shape == [2, 3]
        assert list(result.data) == [12, 13, 14, 17, 18, 19]

    def test_scalar_left_on_matrix(self) -> None:
        """3↑4 5⍴⍳20 takes first 3 rows, all columns."""
        result = Interpreter(io=0).run("3↑4 5⍴⍳20")
        assert result.shape == [3, 5]


class TestDropMultiAxis:
    def test_drop_two_axes(self) -> None:
        """1 2↓4 5⍴⍳20 drops 1 row and 2 columns."""
        result = Interpreter(io=0).run("1 2↓4 5⍴⍳20")
        assert result.shape == [3, 3]
        assert list(result.data) == [7, 8, 9, 12, 13, 14, 17, 18, 19]

    def test_scalar_left_on_matrix(self) -> None:
        """1↓4 5⍴⍳20 drops first row, keeps all columns."""
        result = Interpreter(io=0).run("1↓4 5⍴⍳20")
        assert result.shape == [3, 5]


def _flat_chars(arr: APLArray) -> str:
    """Render a character array of any rank as a string.

    chars_to_str iterates data.flat internally, so it handles 1D and
    2D (and higher) uint32 char arrays uniformly without an explicit
    flatten at the call site.
    """
    from marple.backend_functions import chars_to_str
    return chars_to_str(arr.data)


class TestCharacterData:
    def test_take_char_with_space_fill(self) -> None:
        """5↑'abc' pads with spaces."""
        result = Interpreter(io=1).run("5↑'abc'")
        assert result.shape == [5]
        assert _flat_chars(result) == "abc  "

    def test_rotate_char_vector(self) -> None:
        result = Interpreter(io=1).run("1⌽'hello'")
        assert _flat_chars(result) == "elloh"

    def test_rotate_char_matrix(self) -> None:
        result = Interpreter(io=1).run("1⌽2 3⍴'ABCDEF'")
        assert result.shape == [2, 3]
        assert _flat_chars(result) == "BCAEFD"

    def test_reverse_char_matrix(self) -> None:
        result = Interpreter(io=1).run("⌽2 3⍴'ABCDEF'")
        assert result.shape == [2, 3]
        assert _flat_chars(result) == "CBAFED"

    def test_rotate_first_char_matrix(self) -> None:
        result = Interpreter(io=1).run("1⊖2 3⍴'ABCDEF'")
        assert result.shape == [2, 3]
        assert _flat_chars(result) == "DEFABC"

    def test_reshape_char(self) -> None:
        result = Interpreter(io=1).run("3⍴'AB'")
        assert result.shape == [3]
        assert _flat_chars(result) == "ABA"

    def test_reshape_char_matrix(self) -> None:
        result = Interpreter(io=1).run("2 3⍴'ABCD'")
        assert result.shape == [2, 3]
        assert _flat_chars(result) == "ABCDAB"

    def test_ravel_char_matrix(self) -> None:
        result = Interpreter(io=1).run(",2 3⍴'ABCDEF'")
        assert result.shape == [6]
        assert _flat_chars(result) == "ABCDEF"

    def test_reverse_char_vector(self) -> None:
        result = Interpreter(io=1).run("⌽'hello'")
        assert result.shape == [5]
        assert _flat_chars(result) == "olleh"

    def test_transpose_char_matrix(self) -> None:
        result = Interpreter(io=1).run("⍉2 3⍴'ABCDEF'")
        assert result.shape == [3, 2]
        assert _flat_chars(result) == "ADBECF"

    def test_catenate_char(self) -> None:
        result = Interpreter(io=1).run("'hello','world'")
        assert result.shape == [10]
        assert _flat_chars(result) == "helloworld"

    def test_catenate_char_scalar(self) -> None:
        i = Interpreter(io=1)
        result = i.run("'hello','-'")
        assert result.shape == [6]
        assert _flat_chars(result) == "hello-"

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
