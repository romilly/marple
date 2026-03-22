from marple.arraymodel import APLArray, S
from marple.interpreter import interpret


class TestVectorIndexing:
    def test_single_element(self) -> None:
        env: dict[str, APLArray] = {}
        interpret("v←10 20 30 40 50", env)
        assert interpret("v[3]", env) == S(30)

    def test_multiple_elements(self) -> None:
        env: dict[str, APLArray] = {}
        interpret("v←10 20 30 40 50", env)
        assert interpret("v[1 3 5]", env) == APLArray([3], [10, 30, 50])


class TestMatrixIndexing:
    def test_single_element(self) -> None:
        env: dict[str, APLArray] = {}
        interpret("M←2 3⍴⍳6", env)
        # M[2;3] → 6
        assert interpret("M[2;3]", env) == S(6)

    def test_entire_row(self) -> None:
        env: dict[str, APLArray] = {}
        interpret("M←2 3⍴⍳6", env)
        # M[1;] → 1 2 3
        assert interpret("M[1;]", env) == APLArray([3], [1, 2, 3])

    def test_entire_column(self) -> None:
        env: dict[str, APLArray] = {}
        interpret("M←2 3⍴⍳6", env)
        # M[;2] → 2 5
        assert interpret("M[;2]", env) == APLArray([2], [2, 5])


class TestSystemVariables:
    def test_default_index_origin(self) -> None:
        # Default ⎕IO is 1
        assert interpret("⎕IO") == S(1)

    def test_index_origin_zero(self) -> None:
        env: dict[str, APLArray] = {}
        interpret("⎕IO←0", env)
        # ⍳3 with origin 0 → 0 1 2
        assert interpret("⍳3", env) == APLArray([3], [0, 1, 2])

    def test_indexing_with_origin_zero(self) -> None:
        env: dict[str, APLArray] = {}
        interpret("⎕IO←0", env)
        interpret("v←10 20 30", env)
        assert interpret("v[0]", env) == S(10)

    def test_grade_up_with_origin_zero(self) -> None:
        env: dict[str, APLArray] = {}
        interpret("⎕IO←0", env)
        # ⍋3 1 4 → 0-based indices
        assert interpret("⍋3 1 4", env) == APLArray([3], [1, 0, 2])

    def test_grade_down_with_origin_zero(self) -> None:
        env: dict[str, APLArray] = {}
        interpret("⎕IO←0", env)
        assert interpret("⍒3 1 4", env) == APLArray([3], [2, 0, 1])

    def test_index_of_with_origin_zero(self) -> None:
        env: dict[str, APLArray] = {}
        interpret("⎕IO←0", env)
        # 10 20 30⍳20 → 1 (0-based)
        assert interpret("10 20 30⍳20", env) == S(1)

    def test_index_of_not_found_with_origin_zero(self) -> None:
        env: dict[str, APLArray] = {}
        interpret("⎕IO←0", env)
        # 10 20 30⍳99 → 3 (one beyond last 0-based index)
        assert interpret("10 20 30⍳99", env) == S(3)
