"""Rotate/reverse tests for rank-3 arrays."""

from marple.ports.array import APLArray, S
from marple.engine import Interpreter


class TestReverseRank3:
    def test_reverse_last_axis(self) -> None:
        """⌽ on 2×2×3 reverses each innermost vector."""
        i = Interpreter(io=1)
        i.run("A←2 2 3⍴⍳12")
        result = i.run("⌽A")
        # Layer 0: 1 2 3 / 4 5 6 → 3 2 1 / 6 5 4
        # Layer 1: 7 8 9 / 10 11 12 → 9 8 7 / 12 11 10
        assert result == APLArray.array([2, 2, 3],
            [[[3, 2, 1], [6, 5, 4]], [[9, 8, 7], [12, 11, 10]]])

    def test_reverse_first_axis(self) -> None:
        """⊖ on 2×2×3 reverses along first axis (swaps layers)."""
        i = Interpreter(io=1)
        i.run("A←2 2 3⍴⍳12")
        result = i.run("⊖A")
        assert result == APLArray.array([2, 2, 3],
            [[[7, 8, 9], [10, 11, 12]], [[1, 2, 3], [4, 5, 6]]])


class TestRotateRank3:
    def test_rotate_last_axis(self) -> None:
        """1⌽ on 2×2×3 rotates each innermost vector."""
        i = Interpreter(io=1)
        i.run("A←2 2 3⍴⍳12")
        result = i.run("1⌽A")
        assert result == APLArray.array([2, 2, 3],
            [[[2, 3, 1], [5, 6, 4]], [[8, 9, 7], [11, 12, 10]]])

    def test_rotate_first_axis(self) -> None:
        """1⊖ on 2×2×3 rotates along first axis (shifts layers)."""
        i = Interpreter(io=1)
        i.run("A←2 2 3⍴⍳12")
        result = i.run("1⊖A")
        assert result == APLArray.array([2, 2, 3],
            [[[7, 8, 9], [10, 11, 12]], [[1, 2, 3], [4, 5, 6]]])
