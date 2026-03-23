import pytest

from marple.arraymodel import APLArray, S
from marple.errors import LengthError
from marple.interpreter import interpret, default_env


class TestRankMonadic:
    def test_reverse_rows(self) -> None:
        env = default_env()
        interpret("M←3 4⍴⍳12", env)
        result = interpret("(⌽⍤1) M", env)
        assert result == APLArray([3, 4], [4, 3, 2, 1, 8, 7, 6, 5, 12, 11, 10, 9])

    def test_sum_rows(self) -> None:
        env = default_env()
        interpret("M←3 4⍴⍳12", env)
        result = interpret("(+/⍤1) M", env)
        assert result == APLArray([3], [10, 26, 42])

    def test_scan_rows(self) -> None:
        env = default_env()
        interpret("M←2 3⍴⍳6", env)
        result = interpret(r"(+\⍤1) M", env)
        assert result == APLArray([2, 3], [1, 3, 6, 4, 9, 15])

    def test_rank0_identity(self) -> None:
        # Reversing scalars is identity
        result = interpret("(⌽⍤0) 1 2 3")
        assert result == APLArray([3], [1, 2, 3])

    def test_full_rank(self) -> None:
        env = default_env()
        interpret("M←2 3⍴⍳6", env)
        # ⌽⍤2 applies ⌽ to the whole matrix as a single cell
        # Our ⌽ reverses flat data: 1 2 3 4 5 6 → 6 5 4 3 2 1
        result = interpret("(⌽⍤2) M", env)
        assert result == APLArray([2, 3], [6, 5, 4, 3, 2, 1])

    def test_negative_rank(self) -> None:
        env = default_env()
        interpret("A←2 3 4⍴⍳24", env)
        # ⌽⍤¯1 on rank 3 → rank 2 cells (matrices), reverse each matrix
        result = interpret("(⌽⍤¯1) A", env)
        # Same as (⌽⍤2) A — reverses rows within each 3×4 matrix
        expected = interpret("(⌽⍤2) A", env)
        assert result == expected


class TestRankDfn:
    def test_dfn_with_rank(self) -> None:
        env = default_env()
        interpret("M←3 4⍴⍳12", env)
        result = interpret("({⍵+100}⍤1) M", env)
        assert result == APLArray([3, 4], [101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112])

    def test_named_dfn_with_rank(self) -> None:
        env = default_env()
        interpret("M←3 4⍴⍳12", env)
        interpret("myrev←{⌽⍵}", env)
        result = interpret("(myrev⍤1) M", env)
        assert result == APLArray([3, 4], [4, 3, 2, 1, 8, 7, 6, 5, 12, 11, 10, 9])


class TestRankDyadic:
    def test_add_vector_to_rows(self) -> None:
        env = default_env()
        interpret("M←3 4⍴⍳12", env)
        # Vector + each row (scalar extension at frame level)
        result = interpret("10 20 30 40 (+⍤1) M", env)
        assert result == APLArray([3, 4], [11, 22, 33, 44, 15, 26, 37, 48, 19, 30, 41, 52])

    def test_scalar_per_row(self) -> None:
        env = default_env()
        interpret("M←3 4⍴⍳12", env)
        # 100 200 300 added as scalars to each row
        result = interpret("100 200 300 (+⍤0 1) M", env)
        assert result == APLArray([3, 4], [101, 102, 103, 104, 205, 206, 207, 208, 309, 310, 311, 312])

    def test_frame_mismatch_error(self) -> None:
        env = default_env()
        interpret("M←3 4⍴⍳12", env)
        with pytest.raises(LengthError):
            interpret("1 2 (+⍤0 1) M", env)


class TestRank3D:
    def test_sum_rows_3d(self) -> None:
        env = default_env()
        interpret("A←2 3 4⍴⍳24", env)
        result = interpret("(+/⍤1) A", env)
        # 6 vectors summed → 6 scalars, frame 2 3
        assert result == APLArray([2, 3], [10, 26, 42, 58, 74, 90])
