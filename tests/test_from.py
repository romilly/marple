from marple.arraymodel import APLArray, S
from marple.interpreter import interpret, default_env
import pytest


class TestFromVector:
    def test_scalar_index(self) -> None:
        # 3⌷10 20 30 40 50 → 30
        assert interpret("3⌷10 20 30 40 50") == S(30)

    def test_vector_index(self) -> None:
        # 1 3 5⌷10 20 30 40 50 → 10 30 50
        assert interpret("1 3 5⌷10 20 30 40 50") == APLArray([3], [10, 30, 50])

    def test_repeated_indices(self) -> None:
        # 3 3 1⌷10 20 30 40 50 → 30 30 10
        assert interpret("3 3 1⌷10 20 30 40 50") == APLArray([3], [30, 30, 10])


class TestFromMatrix:
    def test_select_row(self) -> None:
        env = default_env()
        interpret("M←3 4⍴⍳12", env)
        # 2⌷M → 5 6 7 8
        assert interpret("2⌷M", env) == APLArray([4], [5, 6, 7, 8])

    def test_select_rows(self) -> None:
        env = default_env()
        interpret("M←3 4⍴⍳12", env)
        # 1 3⌷M → 2×4 matrix
        assert interpret("1 3⌷M", env) == APLArray([2, 4], [1, 2, 3, 4, 9, 10, 11, 12])


class TestFromIndexOrigin:
    def test_respects_io_zero(self) -> None:
        env = default_env()
        interpret("⎕IO←0", env)
        assert interpret("0⌷10 20 30", env) == S(10)

    def test_index_error(self) -> None:
        with pytest.raises(Exception):
            interpret("6⌷10 20 30 40 50")


class TestFromWithRank:
    def test_column_select(self) -> None:
        env = default_env()
        interpret("M←3 4⍴⍳12", env)
        # 3(⌷⍤0 1)M → column 3: 3 7 11
        result = interpret("3(⌷⍤0 1)M", env)
        assert result == APLArray([3], [3, 7, 11])

    def test_multi_column_select(self) -> None:
        env = default_env()
        interpret("M←3 4⍴⍳12", env)
        # 1 3(⌷⍤1)M → columns 1 and 3: 3×2 matrix
        result = interpret("1 3(⌷⍤1)M", env)
        assert result == APLArray([3, 2], [1, 3, 5, 7, 9, 11])
