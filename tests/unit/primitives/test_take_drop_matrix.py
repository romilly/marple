"""Take, drop, and catenate on higher-rank arrays (first axis)."""

from marple.ports.array import APLArray, S
from marple.engine import Interpreter


class TestTakeMatrix:
    def test_take_rows(self) -> None:
        """3↑4 5⍴⍳20 takes first 3 rows."""
        result = Interpreter(io=0).run("3↑4 5⍴⍳20")
        assert result == APLArray.array([3, 5],
            [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9], [10, 11, 12, 13, 14]])

    def test_take_negative_rows(self) -> None:
        """¯2↑4 5⍴⍳20 takes last 2 rows."""
        result = Interpreter(io=0).run("¯2↑4 5⍴⍳20")
        assert result == APLArray.array([2, 5],
            [[10, 11, 12, 13, 14], [15, 16, 17, 18, 19]])

    def test_take_more_than_available(self) -> None:
        """6↑4 5⍴⍳20 pads with zeros."""
        result = Interpreter(io=0).run("6↑4 5⍴⍳20")
        assert result == APLArray.array([6, 5], [
            [0, 1, 2, 3, 4],
            [5, 6, 7, 8, 9],
            [10, 11, 12, 13, 14],
            [15, 16, 17, 18, 19],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ])

    def test_take_vector_unchanged(self) -> None:
        """Take on vectors still works as before."""
        result = Interpreter(io=1).run("3↑1 2 3 4 5")
        assert result == APLArray.array([3], [1, 2, 3])


class TestDropMatrix:
    def test_drop_rows(self) -> None:
        """1↓4 5⍴⍳20 drops first row."""
        result = Interpreter(io=0).run("1↓4 5⍴⍳20")
        assert result == APLArray.array([3, 5],
            [[5, 6, 7, 8, 9], [10, 11, 12, 13, 14], [15, 16, 17, 18, 19]])

    def test_drop_negative_rows(self) -> None:
        """¯1↓4 5⍴⍳20 drops last row."""
        result = Interpreter(io=0).run("¯1↓4 5⍴⍳20")
        assert result == APLArray.array([3, 5],
            [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9], [10, 11, 12, 13, 14]])

    def test_drop_vector_unchanged(self) -> None:
        """Drop on vectors still works as before."""
        result = Interpreter(io=1).run("2↓1 2 3 4 5")
        assert result == APLArray.array([3], [3, 4, 5])


class TestCatenateMatrix:
    def test_catenate_matrices(self) -> None:
        """M,M joins along last axis (columns)."""
        result = Interpreter(io=0).run("(3 2⍴⍳6),(3 2⍴10+⍳6)")
        assert result == APLArray.array([3, 4],
            [[0, 1, 10, 11], [2, 3, 12, 13], [4, 5, 14, 15]])

    def test_catenate_vectors_unchanged(self) -> None:
        result = Interpreter(io=1).run("1 2 3,4 5")
        assert result == APLArray.array([5], [1, 2, 3, 4, 5])
