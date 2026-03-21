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
