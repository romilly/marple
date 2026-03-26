from marple.arraymodel import APLArray, S
from marple.interpreter import interpret


class TestReduce:
    def test_sum(self) -> None:
        # +/1 2 3 4 → 10
        assert interpret("+/1 2 3 4") == S(10)

    def test_product(self) -> None:
        # ×/1 2 3 4 → 24
        assert interpret("×/1 2 3 4") == S(24)

    def test_right_to_left(self) -> None:
        # -/1 2 3 → 1-(2-3) → 2
        assert interpret("-/1 2 3") == S(2)

    def test_maximum_reduce(self) -> None:
        # ⌈/3 1 4 1 5 → 5
        assert interpret("⌈/3 1 4 1 5") == S(5)

    def test_single_element(self) -> None:
        # +/5 → 5
        assert interpret("+/5") == S(5)

    def test_reduce_matrix_rows(self) -> None:
        # +/2 3⍴1 2 3 4 5 6 → 6 15 (sum each row)
        assert interpret("+/2 3⍴1 2 3 4 5 6") == APLArray([2], [6, 15])

    def test_reduce_large_sum(self) -> None:
        # +/⍳10000 → 50005000
        assert interpret("+/⍳10000") == S(50005000)

    def test_reduce_subtract_right_to_left(self) -> None:
        # -/1 2 3 4 → 1-(2-(3-4)) → 1-(2-(-1)) → 1-3 → ¯2
        assert interpret("-/1 2 3 4") == S(-2)


class TestScan:
    def test_running_sum(self) -> None:
        # +\1 2 3 → 1 3 6
        result = interpret(r"+\1 2 3")
        assert result == APLArray([3], [1, 3, 6])

    def test_running_product(self) -> None:
        # ×\1 2 3 4 → 1 2 6 24
        result = interpret(r"×\1 2 3 4")
        assert result == APLArray([4], [1, 2, 6, 24])

    def test_running_max(self) -> None:
        # ⌈\3 1 4 1 5 → 3 3 4 4 5
        result = interpret(r"⌈\3 1 4 1 5")
        assert result == APLArray([5], [3, 3, 4, 4, 5])


class TestFirstAxisReduce:
    def test_vector(self) -> None:
        # +⌿1 2 3 → same as +/1 2 3 for vectors
        assert interpret("+⌿1 2 3") == S(6)

    def test_matrix_sum_columns(self) -> None:
        # +⌿2 3⍴1 2 3 4 5 6 → 5 7 9 (sum down columns)
        assert interpret("+⌿2 3⍴1 2 3 4 5 6") == APLArray([3], [5, 7, 9])

    def test_matrix_max_columns(self) -> None:
        # ⌈⌿2 3⍴3 1 4 1 5 9 → 3 5 9
        assert interpret("⌈⌿2 3⍴3 1 4 1 5 9") == APLArray([3], [3, 5, 9])

    def test_rank3(self) -> None:
        # +⌿2 2 3⍴⍳12 → reduces along first axis
        # Layer 0: 1 2 3 / 4 5 6
        # Layer 1: 7 8 9 / 10 11 12
        # Sum: 8 10 12 / 14 16 18 → shape [2, 3]
        from marple.interpreter import default_env
        env = default_env()
        interpret("A←2 2 3⍴⍳12", env)
        result = interpret("+⌿A", env)
        assert result.shape == [2, 3]
        assert list(result.data) == [8, 10, 12, 14, 16, 18]


class TestFirstAxisScan:
    def test_vector(self) -> None:
        # +⍀1 2 3 → same as +\1 2 3 for vectors
        result = interpret("+⍀1 2 3")
        assert result == APLArray([3], [1, 3, 6])

    def test_matrix_scan_columns(self) -> None:
        # +⍀2 3⍴1 2 3 4 5 6 → running sum down columns
        # Row 0: 1 2 3
        # Row 1: 1+4 2+5 3+6 → 5 7 9
        result = interpret("+⍀2 3⍴1 2 3 4 5 6")
        assert result.shape == [2, 3]
        assert list(result.data) == [1, 2, 3, 5, 7, 9]

    def test_rank3(self) -> None:
        # +⍀2 2 3⍴⍳12 → running sum along first axis, shape preserved
        from marple.interpreter import default_env
        env = default_env()
        interpret("A←2 2 3⍴⍳12", env)
        result = interpret("+⍀A", env)
        assert result.shape == [2, 2, 3]
        # Layer 0 unchanged: 1 2 3 4 5 6
        # Layer 1 accumulated: 1+7 2+8 3+9 4+10 5+11 6+12 → 8 10 12 14 16 18
        assert list(result.data) == [1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 16, 18]


class TestFirstAxisReplicate:
    def test_compress_rows(self) -> None:
        # 1 0⌿2 3⍴1 2 3 4 5 6 → first row only
        from marple.interpreter import default_env
        env = default_env()
        interpret("M←2 3⍴1 2 3 4 5 6", env)
        result = interpret("1 0⌿M", env)
        assert result.shape == [1, 3]
        assert list(result.data) == [1, 2, 3]

    def test_replicate_rows(self) -> None:
        # 2 1⌿2 3⍴1 2 3 4 5 6 → first row twice, second once
        from marple.interpreter import default_env
        env = default_env()
        interpret("M←2 3⍴1 2 3 4 5 6", env)
        result = interpret("2 1⌿M", env)
        assert result.shape == [3, 3]
        assert list(result.data) == [1, 2, 3, 1, 2, 3, 4, 5, 6]

    def test_vector_same_as_slash(self) -> None:
        # 1 0 1⌿10 20 30 → same as 1 0 1/10 20 30
        result = interpret("1 0 1⌿10 20 30")
        assert list(result.data) == [10, 30]
