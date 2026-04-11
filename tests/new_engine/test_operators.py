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


class TestReduceOverflow:
    """`×/⍳10000` used to silently return 0 due to int64 wraparound.

    Follow Dyalog's "upcast when you must, downcast when you can" rule:
    stay in the integer path while the result fits, fall back to float64
    on integer overflow, and raise DomainError on float64 overflow to ∞.
    """

    def test_product_reduce_huge_raises_domain_error(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("×/⍳10000")


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


class TestCommute:
    """Commute operator (⍨).

    Per the standard semantics:
      - Monadic:  f⍨ ω  ≡  ω f ω    (apply f with ω on both sides)
      - Dyadic:   α f⍨ ω ≡  ω f α    (swap arguments)
    """

    # Monadic form: f⍨ ω → ω f ω
    def test_commute_monadic_plus(self) -> None:
        # +⍨ 5 → 5 + 5 = 10
        assert Interpreter(io=1).run("+⍨ 5") == S(10)

    def test_commute_monadic_times(self) -> None:
        # ×⍨ 4 → 4 × 4 = 16
        assert Interpreter(io=1).run("×⍨ 4") == S(16)

    def test_commute_monadic_minus_is_zero(self) -> None:
        # -⍨ 5 → 5 - 5 = 0
        assert Interpreter(io=1).run("-⍨ 5") == S(0)

    def test_commute_monadic_on_vector(self) -> None:
        # +⍨ 1 2 3 → 2 4 6 (elementwise doubling)
        result = Interpreter(io=1).run("+⍨ 1 2 3")
        assert result == APLArray.array([3], [2, 4, 6])

    # Dyadic form: α f⍨ ω → ω f α
    def test_commute_dyadic_minus_swaps(self) -> None:
        # 5 -⍨ 3 → 3 - 5 = ¯2 (NOT 5 - 3 = 2)
        assert Interpreter(io=1).run("5 -⍨ 3") == S(-2)

    def test_commute_dyadic_divide_swaps(self) -> None:
        # 2 ÷⍨ 10 → 10 ÷ 2 = 5
        assert Interpreter(io=1).run("2 ÷⍨ 10") == S(5)

    def test_commute_dyadic_with_vectors(self) -> None:
        # 1 2 3 ,⍨ 4 5 6 → (4 5 6),(1 2 3) → 4 5 6 1 2 3
        result = Interpreter(io=1).run("1 2 3 ,⍨ 4 5 6")
        assert result == APLArray.array([6], [4, 5, 6, 1, 2, 3])

    # Dfn operand
    def test_commute_with_dfn_monadic(self) -> None:
        # f←{⍺×⍵}  →  f⍨ 5 = 5×5 = 25
        i = Interpreter(io=1)
        i.run("f←{⍺×⍵}")
        assert i.run("f⍨ 5") == S(25)

    def test_commute_with_dfn_dyadic(self) -> None:
        # g←{⍺-⍵}  →  10 g⍨ 3  ≡  3 g 10  ≡  3 - 10 = ¯7
        i = Interpreter(io=1)
        i.run("g←{⍺-⍵}")
        assert i.run("10 g⍨ 3") == S(-7)

    # Single-evaluation guarantee — important for impure functions
    def test_commute_evaluates_omega_once(self) -> None:
        # If commute evaluated ⍵ twice, `+⍨ ?6` would be the sum of
        # two independent random rolls. Evaluating once means it
        # equals 2v for the single roll v. We can prove this by
        # seeding the RNG, running both forms, and comparing.
        i = Interpreter(io=1)
        i.run("⎕RL←42")
        commute_result = i.run("+⍨ ?6").data.item()
        i.run("⎕RL←42")
        single_roll = i.run("?6").data.item()
        assert commute_result == 2 * single_roll
