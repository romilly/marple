"""Operator tests — new engine."""

from marple.numpy_array import APLArray, S
from marple.engine import Interpreter


class TestReduce:
    def test_sum(self) -> None:
        assert Interpreter(io=1).run("+/⍳5") == S(15)

    def test_product(self) -> None:
        assert Interpreter(io=1).run("×/⍳5") == S(120)

    def test_right_to_left(self) -> None:
        assert Interpreter(io=1).run("-/1 2 3") == S(2)

    def test_max_reduce(self) -> None:
        assert Interpreter(io=1).run("⌈/3 1 4 1 5") == S(5)

    def test_single_element(self) -> None:
        assert Interpreter(io=1).run("+/5") == S(5)

    def test_reduce_matrix_rows(self) -> None:
        result = Interpreter(io=1).run("+/2 3⍴⍳6")
        assert result == APLArray.array([2], [6, 15])

    def test_reduce_large_sum(self) -> None:
        assert Interpreter(io=1).run("+/⍳10000") == S(50005000)

    def test_reduce_subtract_right_to_left(self) -> None:
        assert Interpreter(io=1).run("-/1 2 3 4") == S(-2)


class TestReduceFirst:
    def test_reduce_first_axis(self) -> None:
        result = Interpreter(io=1).run("+⌿2 3⍴⍳6")
        assert result == APLArray.array([3], [5, 7, 9])

    def test_matrix_sum_columns(self) -> None:
        assert Interpreter(io=1).run("+⌿2 3⍴1 2 3 4 5 6") == APLArray.array([3], [5, 7, 9])

    def test_matrix_max_columns(self) -> None:
        assert Interpreter(io=1).run("⌈⌿2 3⍴3 1 4 1 5 9") == APLArray.array([3], [3, 5, 9])

    def test_reduce_first_rank3(self) -> None:
        i = Interpreter(io=1)
        i.run("A←2 2 3⍴⍳12")
        result = i.run("+⌿A")
        assert result.shape == [2, 3]
        assert list(result.data) == [8, 10, 12, 14, 16, 18]

    def test_vector_same_as_reduce(self) -> None:
        assert Interpreter(io=1).run("+⌿1 2 3") == S(6)


class TestScan:
    def test_running_sum(self) -> None:
        assert Interpreter(io=1).run("+\\⍳5") == APLArray.array([5], [1, 3, 6, 10, 15])

    def test_running_product(self) -> None:
        assert Interpreter(io=1).run("×\\⍳5") == APLArray.array([5], [1, 2, 6, 24, 120])

    def test_running_max(self) -> None:
        result = Interpreter(io=1).run("⌈\\3 1 4 1 5")
        assert result == APLArray.array([5], [3, 3, 4, 4, 5])


class TestInnerProduct:
    def test_dot_product(self) -> None:
        assert Interpreter(io=1).run("1 2 3+.×4 5 6") == S(32)

    def test_matrix_multiply(self) -> None:
        result = Interpreter(io=1).run("(2 2⍴1 2 3 4)+.×(2 2⍴5 6 7 8)")
        assert result == APLArray.array([2, 2], [19, 22, 43, 50])

    def test_non_square(self) -> None:
        i = Interpreter(io=1)
        i.run("A←2 3⍴⍳6")
        i.run("B←3 2⍴⍳6")
        result = i.run("A+.×B")
        assert result.shape == [2, 2]
        assert list(result.data) == [22, 28, 49, 64]

    def test_matrix_vector(self) -> None:
        i = Interpreter(io=1)
        i.run("M←2 3⍴⍳6")
        result = i.run("M+.×1 2 3")
        assert result.shape == [2]
        assert list(result.data) == [14, 32]

    def test_vector_matrix(self) -> None:
        i = Interpreter(io=1)
        i.run("M←2 3⍴⍳6")
        result = i.run("1 2+.×M")
        assert result.shape == [3]
        assert list(result.data) == [9, 12, 15]


class TestOuterProduct:
    def test_multiplication_table(self) -> None:
        result = Interpreter(io=1).run("(⍳3)∘.×⍳4")
        assert result == APLArray.array([3, 4], [
            1, 2, 3, 4, 2, 4, 6, 8, 3, 6, 9, 12])

    def test_outer_addition(self) -> None:
        result = Interpreter(io=1).run("1 2 3∘.+10 20")
        assert result == APLArray.array([3, 2], [11, 21, 12, 22, 13, 23])

    def test_outer_equality(self) -> None:
        result = Interpreter(io=1).run("1 2 3∘.=1 3")
        assert result == APLArray.array([3, 2], [1, 0, 0, 0, 0, 1])


class TestRank:
    def test_monadic_rank(self) -> None:
        result = Interpreter(io=1).run("(+/⍤1) 3 4⍴⍳12")
        assert result == APLArray.array([3], [10, 26, 42])

    def test_dyadic_rank(self) -> None:
        result = Interpreter(io=1).run("10(+⍤0 1)1 2 3")
        assert result == APLArray.array([3], [11, 12, 13])


class TestScanFirst:
    def test_scan_first_vector(self) -> None:
        result = Interpreter(io=1).run("+⍀1 2 3")
        assert result == APLArray.array([3], [1, 3, 6])

    def test_scan_first_matrix_columns(self) -> None:
        result = Interpreter(io=1).run("+⍀2 3⍴1 2 3 4 5 6")
        assert result.shape == [2, 3]
        assert list(result.data) == [1, 2, 3, 5, 7, 9]

    def test_scan_first_rank3(self) -> None:
        i = Interpreter(io=1)
        i.run("A←2 2 3⍴⍳12")
        result = i.run("+⍀A")
        assert result.shape == [2, 2, 3]
        assert list(result.data) == [1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 16, 18]


class TestReplicateFirst:
    def test_compress_rows(self) -> None:
        i = Interpreter(io=1)
        i.run("M←2 3⍴1 2 3 4 5 6")
        result = i.run("1 0⌿M")
        assert result.shape == [1, 3]
        assert list(result.data) == [1, 2, 3]

    def test_replicate_rows(self) -> None:
        i = Interpreter(io=1)
        i.run("M←2 3⍴1 2 3 4 5 6")
        result = i.run("2 1⌿M")
        assert result.shape == [3, 3]
        assert list(result.data) == [1, 2, 3, 1, 2, 3, 4, 5, 6]

    def test_vector_same_as_slash(self) -> None:
        result = Interpreter(io=1).run("1 0 1⌿10 20 30")
        assert list(result.data) == [10, 30]
