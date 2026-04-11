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
    """Original rank tests."""

    def test_monadic_rank(self) -> None:
        result = Interpreter(io=1).run("(+/⍤1) 3 4⍴⍳12")
        assert result == APLArray.array([3], [10, 26, 42])

    def test_dyadic_rank(self) -> None:
        result = Interpreter(io=1).run("10(+⍤0 1)1 2 3")
        assert result == APLArray.array([3], [11, 12, 13])


class TestRankMonadicReduceAtRank:
    """Monadic rank: +/ applied at various cell ranks on rank-3 array."""

    def test_row_sums_rank1(self) -> None:
        """+/⍤1 on 2 3 4 array: sum each row → shape 2 3."""
        i = Interpreter(io=1)
        i.run("A←2 3 4⍴⍳24")
        result = i.run("(+/⍤1)A")
        # Rows: 1+2+3+4=10, 5+6+7+8=26, 9+10+11+12=42,
        #       13+14+15+16=58, 17+18+19+20=74, 21+22+23+24=90
        assert result == APLArray.array([2, 3], [[10, 26, 42], [58, 74, 90]])

    def test_column_sums_rank2(self) -> None:
        """+/⍤2 on 2 3 4 array: reduce each layer along last axis → shape 2 3."""
        i = Interpreter(io=1)
        i.run("A←2 3 4⍴⍳24")
        result = i.run("(+/⍤2)A")
        # +/ on a matrix reduces along last axis (rows), giving column-count results
        # Layer 0: rows [1 2 3 4],[5 6 7 8],[9 10 11 12] → sums 10,26,42
        # Layer 1: rows [13..16],[17..20],[21..24] → sums 58,74,90
        assert result == APLArray.array([2, 3], [[10, 26, 42], [58, 74, 90]])

    def test_reduce_first_rank2(self) -> None:
        """+⌿⍤2 on 2 3 4 array: reduce each layer along first axis → shape 2 4."""
        i = Interpreter(io=1)
        i.run("A←2 3 4⍴⍳24")
        result = i.run("(+⌿⍤2)A")
        # Layer 0: col sums of 3×4 matrix → [1+5+9, 2+6+10, 3+7+11, 4+8+12] = [15,18,21,24]
        # Layer 1: [13+17+21, 14+18+22, 15+19+23, 16+20+24] = [51,54,57,60]
        assert result == APLArray.array([2, 4], [[15, 18, 21, 24], [51, 54, 57, 60]])

    def test_product_rank1(self) -> None:
        """×/⍤1 on a matrix: product of each row."""
        result = Interpreter(io=1).run("(×/⍤1) 2 3⍴1 2 3 4 5 6")
        assert result == APLArray.array([2], [6, 120])

    def test_max_reduce_rank1(self) -> None:
        """⌈/⍤1 on a matrix: max of each row."""
        result = Interpreter(io=1).run("(⌈/⍤1) 2 3⍴3 1 4 1 5 9")
        assert result == APLArray.array([2], [4, 9])

    def test_min_reduce_rank1(self) -> None:
        """⌊/⍤1 on a matrix: min of each row."""
        result = Interpreter(io=1).run("(⌊/⍤1) 2 3⍴3 1 4 1 5 9")
        assert result == APLArray.array([2], [1, 1])


class TestRankMonadicStructural:
    """Monadic rank with structural functions."""

    def test_reverse_each_row(self) -> None:
        """⌽⍤1 on a matrix: reverse each row independently."""
        result = Interpreter(io=1).run("(⌽⍤1) 3 4⍴⍳12")
        assert result == APLArray.array([3, 4],
            [[4, 3, 2, 1], [8, 7, 6, 5], [12, 11, 10, 9]])

    def test_reverse_each_row_rank3(self) -> None:
        """⌽⍤1 on a rank-3 array."""
        i = Interpreter(io=1)
        i.run("A←2 2 3⍴⍳12")
        result = i.run("(⌽⍤1)A")
        assert result == APLArray.array([2, 2, 3],
            [[[3, 2, 1], [6, 5, 4]], [[9, 8, 7], [12, 11, 10]]])

    def test_reverse_first_each_layer(self) -> None:
        """⊖⍤2 on 2 3 4 array: reverse rows within each 3×4 layer."""
        i = Interpreter(io=1)
        i.run("A←2 3 4⍴⍳24")
        result = i.run("(⊖⍤2)A")
        assert result == APLArray.array([2, 3, 4],
            [[[9, 10, 11, 12], [5, 6, 7, 8], [1, 2, 3, 4]],
             [[21, 22, 23, 24], [17, 18, 19, 20], [13, 14, 15, 16]]])

    def test_iota_rank0_on_vector(self) -> None:
        """⍳⍤0 on a vector: generate ⍳ for each element → matrix (uniform results)."""
        result = Interpreter(io=1).run("(⍳⍤0) 3 3 3")
        # Each element is 3, so ⍳3 = 1 2 3 for each → shape 3 3
        assert result == APLArray.array([3, 3], [[1, 2, 3], [1, 2, 3], [1, 2, 3]])


class TestRankNegativeRank:
    """Negative rank specifications (complementary rank)."""

    def test_neg1_on_matrix(self) -> None:
        """⍤¯1 on a rank-2 array → 1-cells (rows). Same as ⍤1."""
        result = Interpreter(io=1).run("(+/⍤¯1) 3 4⍴⍳12")
        assert result == APLArray.array([3], [10, 26, 42])

    def test_neg1_on_rank3(self) -> None:
        """⍤¯1 on a rank-3 array → 2-cells (matrices)."""
        i = Interpreter(io=1)
        i.run("A←2 3 4⍴⍳24")
        result = i.run("(+⌿⍤¯1)A")
        # +⌿ on each 3×4 matrix: column sums
        assert result == APLArray.array([2, 4], [[15, 18, 21, 24], [51, 54, 57, 60]])

    def test_neg1_on_vector(self) -> None:
        """⍤¯1 on a rank-1 array → 0-cells (scalars). +/ on a scalar is identity."""
        result = Interpreter(io=1).run("(+/⍤¯1) 1 2 3")
        assert result == APLArray.array([3], [1, 2, 3])

    def test_neg2_on_rank3(self) -> None:
        """⍤¯2 on a rank-3 array → 1-cells (rows). Same as ⍤1."""
        i = Interpreter(io=1)
        i.run("A←2 3 4⍴⍳24")
        result = i.run("(+/⍤¯2)A")
        assert result == APLArray.array([2, 3], [[10, 26, 42], [58, 74, 90]])

    def test_reverse_neg1_matrix(self) -> None:
        """⌽⍤¯1 on a matrix: ¯1 → rank 1 → reverse each row."""
        result = Interpreter(io=1).run("(⌽⍤¯1) 2 3⍴1 2 3 4 5 6")
        assert result == APLArray.array([2, 3], [[3, 2, 1], [6, 5, 4]])


class TestRankClamping:
    """Rank values that exceed argument rank are clamped."""

    def test_rank_exceeds_argument_matrix(self) -> None:
        """⍤99 on a matrix: clamped to rank 2, whole array is one cell."""
        result = Interpreter(io=1).run("(+/⍤99) 3 4⍴⍳12")
        # +/ on the whole matrix reduces last axis (rows) → shape 3
        assert result == APLArray.array([3], [10, 26, 42])

    def test_rank_exceeds_argument_vector(self) -> None:
        """⍤99 on a vector: clamped to rank 1, whole vector is one cell."""
        result = Interpreter(io=1).run("(+/⍤99) 1 2 3 4 5")
        assert result == S(15)

    def test_rank_exceeds_is_identity_wrapper(self) -> None:
        """f⍤99 should produce same result as plain f."""
        i = Interpreter(io=1)
        i.run("M←3 4⍴⍳12")
        direct = i.run("⌽M")
        via_rank = i.run("(⌽⍤99)M")
        assert via_rank == direct

    def test_rank0_on_scalar(self) -> None:
        """⍤0 on a scalar: scalar is a single 0-cell."""
        result = Interpreter(io=1).run("(+/⍤0) 42")
        assert result == S(42)

    def test_negative_rank_clamped_to_zero(self) -> None:
        """⍤¯5 on a matrix (rank 2): 2+(-5)=¯3, clamped to 0."""
        result = Interpreter(io=1).run("(+/⍤¯5) 3 3⍴⍳9")
        # +/ on each scalar is identity → original matrix unchanged
        assert result == APLArray.array([3, 3],
            [[1, 2, 3], [4, 5, 6], [7, 8, 9]])


class TestRankDyadicBasic:
    """Dyadic rank: basic arithmetic with various operand forms."""

    def test_scalar_plus_each_row(self) -> None:
        """Scalar added to each row via ⍤0 1."""
        result = Interpreter(io=1).run("10(+⍤0 1)3 3⍴⍳9")
        # 10 + each row: frame agreement — left frame empty (one 0-cell),
        # right frame [3] (three 1-cells). Scalar extension.
        assert result == APLArray.array([3, 3],
            [[11, 12, 13], [14, 15, 16], [17, 18, 19]])

    def test_vector_paired_with_rows(self) -> None:
        """Each element of left vector paired with corresponding row via ⍤0 1."""
        result = Interpreter(io=1).run("100 200 300(+⍤0 1)3 4⍴⍳12")
        assert result == APLArray.array([3, 4],
            [[101, 102, 103, 104],
             [205, 206, 207, 208],
             [309, 310, 311, 312]])

    def test_vector_plus_each_row_rank1_1(self) -> None:
        """Vector added to each row via ⍤1 1 — scalar extension of left frame."""
        result = Interpreter(io=1).run("10 20 30 40(+⍤1 1)3 4⍴⍳12")
        # Left: single 1-cell [10 20 30 40], frame empty
        # Right: three 1-cells, frame [3]
        # Scalar extension: left vector added to each row
        assert result == APLArray.array([3, 4],
            [[11, 22, 33, 44], [15, 26, 37, 48], [19, 30, 41, 52]])

    def test_subtract_scalar_from_rows(self) -> None:
        """Subtract each scalar from corresponding row."""
        result = Interpreter(io=1).run("10 20 30(-⍤0 1)3 4⍴⍳12")
        assert result == APLArray.array([3, 4],
            [[10-1, 10-2, 10-3, 10-4],
             [20-5, 20-6, 20-7, 20-8],
             [30-9, 30-10, 30-11, 30-12]])

    def test_multiply_scalar_times_rows(self) -> None:
        """Multiply: scalar × each row."""
        result = Interpreter(io=1).run("2 3(×⍤0 1)2 3⍴1 2 3 4 5 6")
        assert result == APLArray.array([2, 3], [[2, 4, 6], [12, 15, 18]])

    def test_dyadic_rank0_is_elementwise(self) -> None:
        """⍤0 on both sides: element-wise, same as plain scalar function."""
        i = Interpreter(io=1)
        i.run("M←3 4⍴⍳12")
        i.run("N←3 4⍴10×⍳12")
        direct = i.run("M+N")
        via_rank = i.run("M(+⍤0)N")
        assert via_rank == direct

    def test_matrix_plus_matrix_rank1(self) -> None:
        """Two matrices with matching frames, added row by row."""
        i = Interpreter(io=1)
        result = i.run("(3 4⍴⍳12)(+⍤1)(3 4⍴100×⍳12)")
        assert result == APLArray.array([3, 4],
            [[101, 202, 303, 404],
             [505, 606, 707, 808],
             [909, 1010, 1111, 1212]])


class TestRankDyadicScalarExtension:
    """Dyadic rank: frame scalar extension (one frame empty)."""

    def test_single_scalar_added_to_all_elements(self) -> None:
        """42 (+⍤0) matrix: left is one 0-cell, right has 3×4 frame of 0-cells."""
        result = Interpreter(io=1).run("42(+⍤0)3 4⍴⍳12")
        assert result == APLArray.array([3, 4],
            [[43, 44, 45, 46], [47, 48, 49, 50], [51, 52, 53, 54]])

    def test_single_row_added_to_each_row(self) -> None:
        """One vector (frame empty) + each row of matrix (frame [3])."""
        result = Interpreter(io=1).run("10 20 30(+⍤1)3 3⍴⍳9")
        assert result == APLArray.array([3, 3],
            [[11, 22, 33], [14, 25, 36], [17, 28, 39]])

    def test_scalar_times_each_layer(self) -> None:
        """Scalar × each layer of a rank-3 array via ⍤0 2."""
        i = Interpreter(io=1)
        i.run("A←2 2 3⍴⍳12")
        result = i.run("10 20(×⍤0 2)A")
        # Left frame [2], right frame [2] — matched
        # 10 × first layer, 20 × second layer
        assert result == APLArray.array([2, 2, 3],
            [[[10, 20, 30], [40, 50, 60]], [[140, 160, 180], [200, 220, 240]]])


class TestRankOperandExtension:
    """Right operand extension rules: scalar→3, 2-vec→3."""

    def test_single_value_extends_to_triple(self) -> None:
        """⍤1 extends to ⍤1 1 1: monadic rank=1, dyadic left=1, right=1."""
        # Monadic use: +/⍤1 same as +/⍤1 1 1
        result = Interpreter(io=1).run("(+/⍤1) 3 4⍴⍳12")
        assert result == APLArray.array([3], [10, 26, 42])

    def test_two_value_extension_monadic_uses_second(self) -> None:
        """⍤2 1 extends to ⍤1 2 1: monadic rank is the SECOND value (right rank).

        This is the backward-cyclic rule b c → c b c.
        When used monadically, ⍤2 1 uses rank 1, not rank 2.
        """
        # Monadic: rank is 1 (the second/last element), so +/ reduces each row
        result = Interpreter(io=1).run("(+/⍤2 1) 3 4⍴⍳12")
        assert result == APLArray.array([3], [10, 26, 42])

    def test_two_value_extension_dyadic(self) -> None:
        """⍤0 1 extends to ⍤1 0 1: dyadic left rank=0, right rank=1."""
        result = Interpreter(io=1).run("100 200 300(+⍤0 1)3 4⍴⍳12")
        assert result == APLArray.array([3, 4],
            [[101, 102, 103, 104],
             [205, 206, 207, 208],
             [309, 310, 311, 312]])

    def test_three_value_explicit(self) -> None:
        """⍤5 0 1: monadic rank=5 (clamped), dyadic left=0, right=1."""
        result = Interpreter(io=1).run("100 200 300(+⍤5 0 1)3 4⍴⍳12")
        assert result == APLArray.array([3, 4],
            [[101, 102, 103, 104],
             [205, 206, 207, 208],
             [309, 310, 311, 312]])


class TestRankOnScalars:
    """Rank applied to scalar arguments."""

    def test_monadic_scalar_rank0(self) -> None:
        """f⍤0 on scalar: the scalar is the single 0-cell."""
        result = Interpreter(io=1).run("(+/⍤0) 7")
        assert result == S(7)

    def test_monadic_scalar_rank99(self) -> None:
        """f⍤99 on scalar: clamped to 0, same as above."""
        result = Interpreter(io=1).run("(+/⍤99) 7")
        assert result == S(7)

    def test_dyadic_scalar_scalar_rank0(self) -> None:
        """Scalar + scalar at ⍤0: just addition."""
        result = Interpreter(io=1).run("3(+⍤0)4")
        assert result == S(7)

    def test_dyadic_scalar_vector_rank0_1(self) -> None:
        """Scalar + vector at ⍤0 1: scalar is one 0-cell, vector is one 1-cell."""
        result = Interpreter(io=1).run("10(+⍤0 1)1 2 3")
        assert result == APLArray.array([3], [11, 12, 13])

    def test_dyadic_scalar_matrix_rank0(self) -> None:
        """Scalar + matrix at ⍤0: scalar paired with each element."""
        result = Interpreter(io=1).run("100(+⍤0)2 3⍴⍳6")
        assert result == APLArray.array([2, 3],
            [[101, 102, 103], [104, 105, 106]])


class TestRankEquivalences:
    """Key invariants: rank equivalences that must hold."""

    def test_rank_full_equals_direct(self) -> None:
        """f⍤(rank Y) ≡ f — specifying full rank is a no-op wrapper."""
        i = Interpreter(io=1)
        i.run("M←3 4⍴⍳12")
        direct = i.run("+⌿M")
        via_rank = i.run("(+⌿⍤2)M")
        assert via_rank == direct

    def test_reduce_rows_via_rank(self) -> None:
        """+/⍤¯1 reduces each major cell (row) of a matrix."""
        i = Interpreter(io=1)
        i.run("M←3 4⍴⍳12")
        via_rank = i.run("(+/⍤¯1)M")
        # +/⍤¯1 reduces each row: [1+2+3+4, 5+6+7+8, 9+10+11+12] = [10,26,42]
        assert via_rank == APLArray.array([3], [10, 26, 42])

    def test_reduce_rows_rank3_via_rank(self) -> None:
        """+/⍤¯1 reduces each row of each matrix in a rank-3 array."""
        i = Interpreter(io=1)
        i.run("A←2 3 4⍴⍳24")
        via_rank = i.run("(+/⍤¯1)A")
        assert via_rank == APLArray.array([2, 3], [[10, 26, 42], [58, 74, 90]])

    def test_scalar_function_rank0_is_noop(self) -> None:
        """For scalar functions, f⍤0 ≡ f — both are element-wise."""
        i = Interpreter(io=1)
        i.run("M←3 4⍴⍳12")
        i.run("N←3 4⍴10×⍳12")
        direct = i.run("M+N")
        via_rank = i.run("M(+⍤0)N")
        assert via_rank == direct

    def test_dyadic_scalar_rank0_is_noop(self) -> None:
        """Scalar dyadic at ⍤0: same as direct application."""
        i = Interpreter(io=1)
        i.run("M←2 3⍴⍳6")
        direct = i.run("10×M")
        via_rank = i.run("10(×⍤0)M")
        assert via_rank == direct


class TestRankHigherRankArrays:
    """Rank on rank-3 and rank-4 arrays."""

    def test_rank1_on_rank3(self) -> None:
        """Row sums on a 2×3×4 array → shape 2×3."""
        i = Interpreter(io=1)
        i.run("A←2 3 4⍴⍳24")
        result = i.run("(+/⍤1)A")
        assert result == APLArray.array([2, 3], [[10, 26, 42], [58, 74, 90]])

    def test_rank2_on_rank3(self) -> None:
        """Column sums on each layer of 2×3×4 → shape 2×4."""
        i = Interpreter(io=1)
        i.run("A←2 3 4⍴⍳24")
        result = i.run("(+⌿⍤2)A")
        assert result == APLArray.array([2, 4], [[15, 18, 21, 24], [51, 54, 57, 60]])

    def test_reverse_rank1_on_rank3(self) -> None:
        """Reverse each row in a rank-3 array."""
        i = Interpreter(io=1)
        i.run("A←2 2 3⍴⍳12")
        result = i.run("(⌽⍤1)A")
        assert result == APLArray.array([2, 2, 3],
            [[[3, 2, 1], [6, 5, 4]], [[9, 8, 7], [12, 11, 10]]])

    def test_rank1_on_rank4(self) -> None:
        """Row sums on a rank-4 array."""
        i = Interpreter(io=1)
        i.run("A←2 2 2 3⍴⍳24")
        result = i.run("(+/⍤1)A")
        # Each row of length 3 is summed. Frame is 2×2×2.
        assert result == APLArray.array([2, 2, 2],
            [[[6, 15], [24, 33]], [[42, 51], [60, 69]]])

    def test_dyadic_rank_on_rank3(self) -> None:
        """Add vector to each layer of rank-3 array via ⍤0 2."""
        i = Interpreter(io=1)
        i.run("A←2 2 3⍴1 2 3 4 5 6 7 8 9 10 11 12")
        result = i.run("100 200(+⍤0 2)A")
        assert result == APLArray.array([2, 2, 3],
            [[[101, 102, 103], [104, 105, 106]],
             [[207, 208, 209], [210, 211, 212]]])


class TestRankWithRotate:
    """Rank with dyadic rotate (⌽)."""

    def test_rotate_each_row(self) -> None:
        """Scalar ⌽ at rank 1: rotate each row by the same amount."""
        result = Interpreter(io=1).run("2(⌽⍤1)3 4⍴⍳12")
        assert result == APLArray.array([3, 4],
            [[3, 4, 1, 2], [7, 8, 5, 6], [11, 12, 9, 10]])

    def test_different_rotations_per_row(self) -> None:
        """Different rotation amounts paired with corresponding rows via ⍤0 1."""
        result = Interpreter(io=1).run("0 1 2(⌽⍤0 1)3 4⍴⍳12")
        assert result == APLArray.array([3, 4],
            [[1, 2, 3, 4], [6, 7, 8, 5], [11, 12, 9, 10]])


class TestRankWithReplicate:
    """Rank with replicate/compress."""

    def test_compress_each_row(self) -> None:
        """Boolean mask applied to each row via /⍤1."""
        result = Interpreter(io=1).run("1 0 1 0((/⍤1)⍤1)3 4⍴⍳12")
        # Select elements at positions 1 and 3 from each row
        assert result == APLArray.array([3, 2], [[1, 3], [5, 7], [9, 11]])

    def test_compress_at_rank_one_paren(self) -> None:
        """(/⍤1) works as a function — compress applied at rank 1."""
        result = Interpreter(io=1).run("1 0 1(/⍤1)3 3⍴⍳9")
        assert result == APLArray.array([3, 2], [[1, 3], [4, 6], [7, 9]])

    def test_replicate_first_at_rank_two(self) -> None:
        """⌿ as a function operand at rank 2 — select rows."""
        result = Interpreter(io=1).run("1 0 1(⌿⍤2)3 3⍴⍳9")
        assert result == APLArray.array([2, 3], [[1, 2, 3], [7, 8, 9]])

    def test_expand_at_rank_one(self) -> None:
        """\\ as a function operand at rank 1 — expand each row."""
        result = Interpreter(io=1).run("1 0 1(\\⍤1)2 2⍴⍳4")
        # Each row [a b] becomes [a 0 b]
        assert result.shape == [2, 3]
        assert list(result.data[0]) == [1, 0, 2]
        assert list(result.data[1]) == [3, 0, 4]

    def test_plus_reduce_still_binds_first(self) -> None:
        """`+/⍤1` must still parse as (plus-reduce)-at-rank-1, NOT
        as plus followed by (slash-at-rank-1). Case 4 (adverb
        binding with operand) should fire before the new Case 4.5
        gets a chance.
        """
        result = Interpreter(io=1).run("(+/⍤1) 2 3⍴⍳6")
        assert result == APLArray.array([2], [6, 15])

    def test_nested_rank_with_plus_reduce(self) -> None:
        """`((+/⍤1)⍤1) matrix` — nested rank operators. Previously
        failed with "Operators require primitive function operands"
        because apply_func_monadic did not handle nested rank."""
        result = Interpreter(io=1).run("((+/⍤1)⍤1) 2 3⍴⍳6")
        assert result == APLArray.array([2], [6, 15])


class TestRankShapePreservation:
    """Result shape is frame , result-cell-shape."""

    def test_shape_of_row_sums(self) -> None:
        """Shape of +/⍤1 on 3×4 matrix: frame [3], result cell shape [] → [3]."""
        result = Interpreter(io=1).run("(+/⍤1) 3 4⍴⍳12")
        assert list(result.shape) == [3]

    def test_shape_of_row_sums_rank3(self) -> None:
        """Shape of +/⍤1 on 2×3×4: frame [2,3], result cell shape [] → [2,3]."""
        i = Interpreter(io=1)
        i.run("A←2 3 4⍴⍳24")
        result = i.run("(+/⍤1)A")
        assert list(result.shape) == [2, 3]

    def test_shape_of_column_sums(self) -> None:
        """Shape of +⌿⍤2 on 2×3×4: frame [2], result cell shape [4] → [2,4]."""
        i = Interpreter(io=1)
        i.run("A←2 3 4⍴⍳24")
        result = i.run("(+⌿⍤2)A")
        assert list(result.shape) == [2, 4]

    def test_shape_reverse_rank1_preserves(self) -> None:
        """⌽⍤1 preserves shape: each row reversed, shape unchanged."""
        i = Interpreter(io=1)
        i.run("A←2 3 4⍴⍳24")
        result = i.run("(⌽⍤1)A")
        assert list(result.shape) == [2, 3, 4]

    def test_shape_dyadic_rank(self) -> None:
        """Shape of 100 200 300(+⍤0 1)3 4⍴⍳12: frame [3], cell shape [4] → [3,4]."""
        result = Interpreter(io=1).run("100 200 300(+⍤0 1)3 4⍴⍳12")
        assert list(result.shape) == [3, 4]


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
