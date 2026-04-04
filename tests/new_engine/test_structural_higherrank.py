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


class TestCharacterData:
    def test_take_char_with_space_fill(self) -> None:
        """5↑'abc' pads with spaces."""
        result = Interpreter(io=1).run("5↑'abc'")
        assert result.shape == [5]
        assert list(result.data) == list("abc  ")

    def test_rotate_char_vector(self) -> None:
        result = Interpreter(io=1).run("1⌽'hello'")
        assert list(result.data) == list("elloh")

    def test_rotate_char_matrix(self) -> None:
        result = Interpreter(io=1).run("1⌽2 3⍴'ABCDEF'")
        assert result.shape == [2, 3]
        assert list(result.data) == list("BCAEFD")

    def test_reverse_char_matrix(self) -> None:
        result = Interpreter(io=1).run("⌽2 3⍴'ABCDEF'")
        assert result.shape == [2, 3]
        assert list(result.data) == list("CBAFED")

    def test_rotate_first_char_matrix(self) -> None:
        result = Interpreter(io=1).run("1⊖2 3⍴'ABCDEF'")
        assert result.shape == [2, 3]
        assert list(result.data) == list("DEFABC")
