"""Take, drop, and catenate on higher-rank arrays (first axis)."""

from marple.arraymodel import APLArray, S
from marple.engine import Interpreter


class TestTakeMatrix:
    def test_take_rows(self) -> None:
        """3↑4 5⍴⍳20 takes first 3 rows."""
        result = Interpreter(io=0).run("3↑4 5⍴⍳20")
        assert result.shape == [3, 5]
        assert list(result.data) == list(range(15))

    def test_take_negative_rows(self) -> None:
        """¯2↑4 5⍴⍳20 takes last 2 rows."""
        result = Interpreter(io=0).run("¯2↑4 5⍴⍳20")
        assert result.shape == [2, 5]
        assert list(result.data) == list(range(10, 20))

    def test_take_more_than_available(self) -> None:
        """6↑4 5⍴⍳20 pads with zeros."""
        result = Interpreter(io=0).run("6↑4 5⍴⍳20")
        assert result.shape == [6, 5]
        # First 20 elements are 0..19, last 10 are 0 (fill)
        assert list(result.data[:20]) == list(range(20))
        assert list(result.data[20:]) == [0] * 10

    def test_take_vector_unchanged(self) -> None:
        """Take on vectors still works as before."""
        result = Interpreter(io=1).run("3↑1 2 3 4 5")
        assert result == APLArray.array([3], [1, 2, 3])


class TestDropMatrix:
    def test_drop_rows(self) -> None:
        """1↓4 5⍴⍳20 drops first row."""
        result = Interpreter(io=0).run("1↓4 5⍴⍳20")
        assert result.shape == [3, 5]
        assert list(result.data) == list(range(5, 20))

    def test_drop_negative_rows(self) -> None:
        """¯1↓4 5⍴⍳20 drops last row."""
        result = Interpreter(io=0).run("¯1↓4 5⍴⍳20")
        assert result.shape == [3, 5]
        assert list(result.data) == list(range(15))

    def test_drop_vector_unchanged(self) -> None:
        """Drop on vectors still works as before."""
        result = Interpreter(io=1).run("2↓1 2 3 4 5")
        assert result == APLArray.array([3], [3, 4, 5])


class TestCatenateMatrix:
    def test_catenate_matrices(self) -> None:
        """M,M joins along last axis (columns)."""
        result = Interpreter(io=0).run("(3 2⍴⍳6),(3 2⍴10+⍳6)")
        assert result.shape == [3, 4]
        assert list(result.data) == [0, 1, 10, 11, 2, 3, 12, 13, 4, 5, 14, 15]

    def test_catenate_vectors_unchanged(self) -> None:
        result = Interpreter(io=1).run("1 2 3,4 5")
        assert result == APLArray.array([5], [1, 2, 3, 4, 5])
