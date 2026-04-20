"""Rank operator tests — new engine."""

import pytest

from marple.ports.array import APLArray, S
from marple.engine import Interpreter
from marple.errors import LengthError


class TestRankMonadic:
    def test_reverse_rows(self) -> None:
        i = Interpreter(io=1)
        i.run("M←3 4⍴⍳12")
        result = i.run("(⌽⍤1) M")
        assert result == APLArray.array([3, 4], [[4, 3, 2, 1], [8, 7, 6, 5], [12, 11, 10, 9]])

    def test_sum_rows(self) -> None:
        i = Interpreter(io=1)
        i.run("M←3 4⍴⍳12")
        result = i.run("(+/⍤1) M")
        assert result == APLArray.array([3], [10, 26, 42])

    def test_scan_rows(self) -> None:
        i = Interpreter(io=1)
        i.run("M←2 3⍴⍳6")
        result = i.run("(+\\⍤1) M")
        assert result == APLArray.array([2, 3], [[1, 3, 6], [4, 9, 15]])

    def test_rank0_identity(self) -> None:
        result = Interpreter(io=1).run("(⌽⍤0) 1 2 3")
        assert result == APLArray.array([3], [1, 2, 3])

    def test_full_rank(self) -> None:
        i = Interpreter(io=1)
        i.run("M←2 3⍴⍳6")
        result = i.run("(⌽⍤2) M")
        assert result == APLArray.array([2, 3], [[3, 2, 1], [6, 5, 4]])

    def test_negative_rank(self) -> None:
        i = Interpreter(io=1)
        i.run("A←2 3 4⍴⍳24")
        result = i.run("(⌽⍤¯1) A")
        expected = i.run("(⌽⍤2) A")
        assert result == expected


class TestRankDfn:
    def test_dfn_with_rank(self) -> None:
        i = Interpreter(io=1)
        i.run("M←3 4⍴⍳12")
        result = i.run("({⍵+100}⍤1) M")
        assert result == APLArray.array([3, 4], [[101, 102, 103, 104], [105, 106, 107, 108], [109, 110, 111, 112]])

    def test_named_dfn_with_rank(self) -> None:
        i = Interpreter(io=1)
        i.run("M←3 4⍴⍳12")
        i.run("myrev←{⌽⍵}")
        result = i.run("(myrev⍤1) M")
        assert result == APLArray.array([3, 4], [[4, 3, 2, 1], [8, 7, 6, 5], [12, 11, 10, 9]])


class TestRankDyadic:
    def test_add_vector_to_rows(self) -> None:
        i = Interpreter(io=1)
        i.run("M←3 4⍴⍳12")
        result = i.run("10 20 30 40 (+⍤1) M")
        assert result == APLArray.array([3, 4], [[11, 22, 33, 44], [15, 26, 37, 48], [19, 30, 41, 52]])

    def test_scalar_per_row(self) -> None:
        i = Interpreter(io=1)
        i.run("M←3 4⍴⍳12")
        result = i.run("100 200 300 (+⍤0 1) M")
        assert result == APLArray.array([3, 4], [[101, 102, 103, 104], [205, 206, 207, 208], [309, 310, 311, 312]])

    def test_frame_mismatch_error(self) -> None:
        i = Interpreter(io=1)
        i.run("M←3 4⍴⍳12")
        with pytest.raises(LengthError):
            i.run("1 2 (+⍤0 1) M")


class TestRank3D:
    def test_sum_rows_3d(self) -> None:
        i = Interpreter(io=1)
        i.run("A←2 3 4⍴⍳24")
        result = i.run("(+/⍤1) A")
        assert result == APLArray.array([2, 3], [[10, 26, 42], [58, 74, 90]])
