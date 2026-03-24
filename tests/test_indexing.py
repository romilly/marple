from marple.arraymodel import APLArray, S
from marple.interpreter import interpret, default_env


class TestVectorIndexing:
    def test_single_element(self) -> None:
        env = default_env()
        interpret("v←10 20 30 40 50", env)
        assert interpret("v[3]", env) == S(30)

    def test_multiple_elements(self) -> None:
        env = default_env()
        interpret("v←10 20 30 40 50", env)
        assert interpret("v[1 3 5]", env) == APLArray([3], [10, 30, 50])


class TestIndexingPreservesShape:
    """Indexing A[I] must preserve the shape of I."""

    def test_scalar_index(self) -> None:
        env = default_env()
        interpret("v←10 20 30", env)
        result = interpret("v[2]", env)
        assert result.shape == []

    def test_vector_index(self) -> None:
        env = default_env()
        interpret("v←10 20 30 40 50", env)
        result = interpret("v[2 4]", env)
        assert result.shape == [2]

    def test_matrix_index(self) -> None:
        env = default_env()
        interpret("v←10 20 30 40 50", env)
        result = interpret("v[2 3⍴1 2 3 4 5 1]", env)
        assert result.shape == [2, 3]
        assert list(result.data) == [10, 20, 30, 40, 50, 10]

    def test_rank3_index(self) -> None:
        env = default_env()
        interpret("v←10 20 30 40", env)
        result = interpret("v[2 2 2⍴1 2 3 4 1 2 3 4]", env)
        assert result.shape == [2, 2, 2]
        assert list(result.data) == [10, 20, 30, 40, 10, 20, 30, 40]

    def test_rank4_index(self) -> None:
        env = default_env()
        interpret("v←10 20 30", env)
        result = interpret("v[2 1 3 1⍴1 2 3 1 2 3]", env)
        assert result.shape == [2, 1, 3, 1]

    def test_outer_product_index(self) -> None:
        """The original bug report: ' *'[1+r∘.=s]"""
        env = default_env()
        interpret("r←1 2 3", env)
        interpret("s←1 2 3", env)
        result = interpret("' *'[1+r∘.=s]", env)
        assert result.shape == [3, 3]

    def test_string_index_with_matrix(self) -> None:
        env = default_env()
        result = interpret("'abcde'[2 3⍴1 2 3 4 5 1]", env)
        assert result.shape == [2, 3]
        assert result.data == ['a', 'b', 'c', 'd', 'e', 'a']


class TestMatrixIndexing:
    def test_single_element(self) -> None:
        env = default_env()
        interpret("M←2 3⍴⍳6", env)
        # M[2;3] → 6
        assert interpret("M[2;3]", env) == S(6)

    def test_entire_row(self) -> None:
        env = default_env()
        interpret("M←2 3⍴⍳6", env)
        # M[1;] → 1 2 3
        assert interpret("M[1;]", env) == APLArray([3], [1, 2, 3])

    def test_entire_column(self) -> None:
        env = default_env()
        interpret("M←2 3⍴⍳6", env)
        # M[;2] → 2 5
        assert interpret("M[;2]", env) == APLArray([2], [2, 5])


class TestSystemVariables:
    def test_default_index_origin(self) -> None:
        # Default ⎕IO is 1
        assert interpret("⎕IO") == S(1)

    def test_index_origin_zero(self) -> None:
        env = default_env()
        interpret("⎕IO←0", env)
        # ⍳3 with origin 0 → 0 1 2
        assert interpret("⍳3", env) == APLArray([3], [0, 1, 2])

    def test_indexing_with_origin_zero(self) -> None:
        env = default_env()
        interpret("⎕IO←0", env)
        interpret("v←10 20 30", env)
        assert interpret("v[0]", env) == S(10)

    def test_grade_up_with_origin_zero(self) -> None:
        env = default_env()
        interpret("⎕IO←0", env)
        # ⍋3 1 4 → 0-based indices
        assert interpret("⍋3 1 4", env) == APLArray([3], [1, 0, 2])

    def test_grade_down_with_origin_zero(self) -> None:
        env = default_env()
        interpret("⎕IO←0", env)
        assert interpret("⍒3 1 4", env) == APLArray([3], [2, 0, 1])

    def test_index_of_with_origin_zero(self) -> None:
        env = default_env()
        interpret("⎕IO←0", env)
        # 10 20 30⍳20 → 1 (0-based)
        assert interpret("10 20 30⍳20", env) == S(1)

    def test_index_of_not_found_with_origin_zero(self) -> None:
        env = default_env()
        interpret("⎕IO←0", env)
        # 10 20 30⍳99 → 3 (one beyond last 0-based index)
        assert interpret("10 20 30⍳99", env) == S(3)
