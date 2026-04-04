"""From (⌷) tests — new engine."""

import pytest

from marple.numpy_array import APLArray, S
from marple.engine import Interpreter


class TestFromVector:
    def test_scalar_index(self) -> None:
        assert Interpreter(io=1).run("3⌷10 20 30 40 50") == S(30)

    def test_vector_index(self) -> None:
        assert Interpreter(io=1).run("1 3 5⌷10 20 30 40 50") == APLArray.array([3], [10, 30, 50])

    def test_repeated_indices(self) -> None:
        assert Interpreter(io=1).run("3 3 1⌷10 20 30 40 50") == APLArray.array([3], [30, 30, 10])


class TestFromMatrix:
    def test_select_row(self) -> None:
        i = Interpreter(io=1)
        i.run("M←3 4⍴⍳12")
        assert i.run("2⌷M") == APLArray.array([4], [5, 6, 7, 8])

    def test_select_rows(self) -> None:
        i = Interpreter(io=1)
        i.run("M←3 4⍴⍳12")
        assert i.run("1 3⌷M") == APLArray.array([2, 4], [1, 2, 3, 4, 9, 10, 11, 12])


class TestFromIndexOrigin:
    def test_respects_io_zero(self) -> None:
        i = Interpreter(io=0)
        assert i.run("0⌷10 20 30") == S(10)

    def test_index_error(self) -> None:
        with pytest.raises(Exception):
            Interpreter(io=1).run("6⌷10 20 30 40 50")


class TestFromWithRank:
    def test_column_select(self) -> None:
        i = Interpreter(io=1)
        i.run("M←3 4⍴⍳12")
        result = i.run("3(⌷⍤0 1)M")
        assert result == APLArray.array([3], [3, 7, 11])

    def test_multi_column_select(self) -> None:
        i = Interpreter(io=1)
        i.run("M←3 4⍴⍳12")
        result = i.run("1 3(⌷⍤1)M")
        assert result == APLArray.array([3, 2], [1, 3, 5, 7, 9, 11])
