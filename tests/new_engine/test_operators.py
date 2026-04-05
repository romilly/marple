"""Operator tests — new engine."""

import pytest

from marple.numpy_array import APLArray, S
from marple.engine import Interpreter
from marple.errors import DomainError


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
        assert result == APLArray.array([2, 3], [[8, 10, 12], [14, 16, 18]])

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

    def test_scan_matrix(self) -> None:
        result = Interpreter(io=1).run("+\\2 3⍴1 2 3 4 5 6")
        assert result == APLArray.array([2, 3], [[1, 3, 6], [4, 9, 15]])

    def test_scan_rank3(self) -> None:
        result = Interpreter(io=1).run("+\\2 2 3⍴⍳12")
        assert result == APLArray.array([2, 2, 3],
            [[[1, 3, 6], [4, 9, 15]], [[7, 15, 24], [10, 21, 33]]])

    def test_scan_rank4(self) -> None:
        result = Interpreter(io=1).run("+\\2 2 2 3⍴⍳24")
        assert result == APLArray.array([2, 2, 2, 3],
            [[[[1, 3, 6], [4, 9, 15]], [[7, 15, 24], [10, 21, 33]]],
             [[[13, 27, 42], [16, 33, 51]], [[19, 39, 60], [22, 45, 69]]]])

    def test_subtract_scan_vector(self) -> None:
        """APL scan is right-to-left reduce per prefix."""
        result = Interpreter(io=1).run("-\\1 2 3 4")
        assert result == APLArray.array([4], [1, -1, 2, -2])

    def test_subtract_scan_matrix(self) -> None:
        result = Interpreter(io=1).run("-\\2 3⍴1 2 3 4 5 6")
        assert result == APLArray.array([2, 3], [[1, -1, 2], [4, -1, 5]])

    def test_subtract_scan_rank3(self) -> None:
        result = Interpreter(io=1).run("-\\2 2 3⍴⍳12")
        assert result == APLArray.array([2, 2, 3],
            [[[1, -1, 2], [4, -1, 5]], [[7, -1, 8], [10, -1, 11]]])

    def test_subtract_scan_rank4(self) -> None:
        result = Interpreter(io=1).run("-\\2 2 2 3⍴⍳24")
        assert result == APLArray.array([2, 2, 2, 3],
            [[[[1, -1, 2], [4, -1, 5]], [[7, -1, 8], [10, -1, 11]]],
             [[[13, -1, 14], [16, -1, 17]], [[19, -1, 20], [22, -1, 23]]]])


class TestDfnWithOperator:
    def test_dfn_with_reduce_raises_domain_error(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("{⍺+⍵}/1 2 3")

    def test_dfn_with_scan_raises_domain_error(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("{⍺+⍵}\\1 2 3")


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
        assert result == APLArray.array([2, 3], [[1, 2, 3], [5, 7, 9]])

    def test_scan_first_rank3(self) -> None:
        i = Interpreter(io=1)
        i.run("A←2 2 3⍴⍳12")
        result = i.run("+⍀A")
        assert result == APLArray.array([2, 2, 3],
            [[[1, 2, 3], [4, 5, 6]], [[8, 10, 12], [14, 16, 18]]])


class TestReplicateFirst:
    def test_compress_rows(self) -> None:
        i = Interpreter(io=1)
        i.run("M←2 3⍴1 2 3 4 5 6")
        result = i.run("1 0⌿M")
        assert result == APLArray.array([1, 3], [[1, 2, 3]])

    def test_replicate_rows(self) -> None:
        i = Interpreter(io=1)
        i.run("M←2 3⍴1 2 3 4 5 6")
        result = i.run("2 1⌿M")
        assert result == APLArray.array([3, 3], [[1, 2, 3], [1, 2, 3], [4, 5, 6]])

    def test_vector_same_as_slash(self) -> None:
        result = Interpreter(io=1).run("1 0 1⌿10 20 30")
        assert list(result.data) == [10, 30]
