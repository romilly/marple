"""Transpose (⍉) tests — monadic and dyadic.

Monadic ⍉Y per the ISO/Dyalog spec:
    R has shape ⌽⍴Y, with the order of axes reversed.

Dyadic X⍉Y per the spec:
    X is a simple scalar/vector whose elements are valid axis
    indices for Y. The Ith element of X gives the new position
    for the Ith axis of Y. If X repositions multiple axes of Y
    to the same axis, the elements used are those whose indices
    on the relevant axes of Y are equal (diagonal extraction).
    ⎕IO is an implicit argument.

Both forms accept Y of any type (chars allowed, unlike encode
and decode which require simple numeric arrays).
"""

import pytest

from marple.engine import Interpreter
from marple.errors import LengthError, RankError
from marple.numpy_array import APLArray, S


class TestTransposeMonadic:
    """Monadic ⍉ — reverse axis order; shape becomes ⌽⍴Y."""

    # ------------------------------------------------------------------
    # Identity cases: rank 0 and rank 1
    # ------------------------------------------------------------------

    def test_transpose_scalar(self) -> None:
        # ⍉7 → 7
        # ⍴⍉Y = ⌽⍴Y = ⌽⍳0 = ⍳0 = empty → result shape [].
        assert Interpreter(io=1).run("⍉7") == S(7)

    def test_transpose_vector(self) -> None:
        # ⍉1 2 3 → 1 2 3
        # A vector has shape [n]; reversed it is still [n].
        result = Interpreter(io=1).run("⍉1 2 3")
        assert result == APLArray.array([3], [1, 2, 3])

    def test_transpose_char_vector(self) -> None:
        # ⍉'abc' → 'abc'   (vector identity, regardless of type)
        result = Interpreter(io=1).run("⍉'abc'")
        assert result == Interpreter(io=1).run("'abc'")

    # ------------------------------------------------------------------
    # Rank 2 (matrices)
    # ------------------------------------------------------------------

    def test_transpose_matrix(self) -> None:
        # ⍉2 3⍴⍳6  →  3 2 ⍴ 1 4 2 5 3 6
        # The spec example:
        #   M = 1 2 3 / 4 5 6
        #   ⍉M = 1 4 / 2 5 / 3 6
        result = Interpreter(io=1).run("⍉2 3⍴⍳6")
        assert result == APLArray.array(
            [3, 2],
            [[1, 4],
             [2, 5],
             [3, 6]],
        )

    def test_transpose_matrix_non_square(self) -> None:
        # ⍉3 5⍴⍳15 → shape [5, 3]
        i = Interpreter(io=1)
        i.run("M←3 5⍴⍳15")
        result = i.run("⍉M")
        assert result.shape == [5, 3]
        # Verify the (0,0) and (4,2) corners are the right elements:
        # row r col c of ⍉M = M[c, r], so ⍉M[0,0] = M[0,0] = 1,
        # and ⍉M[4,2] = M[2,4] = 15.
        assert result == APLArray.array(
            [5, 3],
            [[1, 6, 11],
             [2, 7, 12],
             [3, 8, 13],
             [4, 9, 14],
             [5, 10, 15]],
        )

    def test_transpose_char_matrix(self) -> None:
        # ⍉2 3⍴'abcdef' →
        #   M = a b c
        #       d e f
        #   ⍉M = a d
        #        b e
        #        c f
        i = Interpreter(io=1)
        i.run("M←2 3⍴'abcdef'")
        result = i.run("⍉M")
        # Compare via the equivalent string-built matrix.
        expected = i.run("3 2⍴'adbecf'")
        assert result == expected

    def test_transpose_float_matrix(self) -> None:
        # Float matrix transpose preserves the float dtype.
        result = Interpreter(io=1).run("⍉2 2⍴1.5 2.5 3.5 4.5")
        assert result == APLArray.array(
            [2, 2],
            [[1.5, 3.5],
             [2.5, 4.5]],
        )
        import numpy as np
        assert np.issubdtype(result.data.dtype, np.floating)

    # ------------------------------------------------------------------
    # Rank 3 — the spec's cube example
    # ------------------------------------------------------------------

    def test_transpose_rank3_cube_shape(self) -> None:
        # cube has shape 2 3 4; ⍉cube has shape 4 3 2.
        result = Interpreter(io=1).run("⍴⍉2 3 4⍴⍳24")
        assert result == APLArray.array([3], [4, 3, 2])

    def test_transpose_rank3_cube_values(self) -> None:
        # The full cube example from the spec:
        #   cube = 2 3 4 ⍴ ⍳24
        # ⍉cube has shape (4,3,2). Element [i,j,k] of ⍉cube equals
        # element [k,j,i] of cube.
        i = Interpreter(io=1)
        i.run("cube←2 3 4⍴⍳24")
        result = i.run("⍉cube")
        # Build the expected from the spec's display:
        #   ⍉cube[0,:,:] = 1 13 / 5 17 / 9 21
        #   ⍉cube[1,:,:] = 2 14 / 6 18 / 10 22
        #   ⍉cube[2,:,:] = 3 15 / 7 19 / 11 23
        #   ⍉cube[3,:,:] = 4 16 / 8 20 / 12 24
        assert result == APLArray.array(
            [4, 3, 2],
            [
                [[1, 13], [5, 17], [9, 21]],
                [[2, 14], [6, 18], [10, 22]],
                [[3, 15], [7, 19], [11, 23]],
                [[4, 16], [8, 20], [12, 24]],
            ],
        )

    # ------------------------------------------------------------------
    # Higher rank — generalised
    # ------------------------------------------------------------------

    def test_transpose_rank4_shape(self) -> None:
        # ⍴⍉2 3 4 5⍴⍳120 → 5 4 3 2
        result = Interpreter(io=1).run("⍴⍉2 3 4 5⍴⍳120")
        assert result == APLArray.array([4], [5, 4, 3, 2])

    # ------------------------------------------------------------------
    # Empty arrays
    # ------------------------------------------------------------------

    def test_transpose_empty_vector(self) -> None:
        # ⍉⍳0 → ⍳0  (empty vector, identity)
        result = Interpreter(io=1).run("⍉⍳0")
        assert result.shape == [0]

    def test_transpose_empty_matrix_zero_rows(self) -> None:
        # ⍉0 3⍴0 → shape 3 0 (empty matrix with axes swapped)
        result = Interpreter(io=1).run("⍉0 3⍴0")
        assert result.shape == [3, 0]

    def test_transpose_empty_matrix_zero_cols(self) -> None:
        # ⍉3 0⍴0 → shape 0 3
        result = Interpreter(io=1).run("⍉3 0⍴0")
        assert result.shape == [0, 3]

    # ------------------------------------------------------------------
    # Involution: ⍉⍉Y = Y for any Y
    # ------------------------------------------------------------------

    def test_transpose_involution_vector(self) -> None:
        # ⍉⍉1 2 3 4 → 1 2 3 4
        result = Interpreter(io=1).run("⍉⍉1 2 3 4")
        assert result == APLArray.array([4], [1, 2, 3, 4])

    def test_transpose_involution_matrix(self) -> None:
        # ⍉⍉2 3⍴⍳6 → 2 3⍴⍳6
        i = Interpreter(io=1)
        original = i.run("2 3⍴⍳6")
        twice = i.run("⍉⍉2 3⍴⍳6")
        assert twice == original

    def test_transpose_involution_rank3(self) -> None:
        # ⍉⍉2 3 4⍴⍳24 → 2 3 4⍴⍳24
        i = Interpreter(io=1)
        original = i.run("2 3 4⍴⍳24")
        twice = i.run("⍉⍉2 3 4⍴⍳24")
        assert twice == original


class TestTransposeDyadic:
    """Dyadic ⍉ — axis permutation, with diagonal extraction when
    X has repeated values.

    ⎕IO is an implicit argument: in IO=1, axis indices in X are
    1-based; in IO=0, they are 0-based.
    """

    # ------------------------------------------------------------------
    # Spec examples (taken directly from the Dyalog ⍉ documentation)
    # ------------------------------------------------------------------

    def test_dyadic_spec_2_1_3_swaps_first_two_axes(self) -> None:
        # 2 1 3⍉(2 3 4⍴⍳24) — the first spec example.
        # X says: axis 1 of Y → result position 2;
        #         axis 2 of Y → result position 1;
        #         axis 3 of Y → result position 3.
        # So result[i,j,k] = Y[j,i,k]. Result shape (3,2,4).
        i = Interpreter(io=1)
        i.run("A←2 3 4⍴⍳24")
        result = i.run("2 1 3⍉A")
        assert result == APLArray.array(
            [3, 2, 4],
            [
                [[ 1,  2,  3,  4], [13, 14, 15, 16]],
                [[ 5,  6,  7,  8], [17, 18, 19, 20]],
                [[ 9, 10, 11, 12], [21, 22, 23, 24]],
            ],
        )

    def test_dyadic_spec_diagonal_3d(self) -> None:
        # 1 1 1⍉A — all three axes of A go to the single result axis.
        # Diagonal: result[i] = A[i,i,i]. Length min(2,3,4) = 2.
        # Values: A[0,0,0] = 1 (1-indexed), A[1,1,1] = 18.
        i = Interpreter(io=1)
        i.run("A←2 3 4⍴⍳24")
        result = i.run("1 1 1⍉A")
        assert result == APLArray.array([2], [1, 18])

    def test_dyadic_spec_partial_diagonal(self) -> None:
        # 1 1 2⍉A — axes 1 and 2 collapse to result axis 1; axis 3
        # becomes result axis 2. result[i,j] = A[i,i,j].
        # Result shape (min(2,3), 4) = (2,4).
        i = Interpreter(io=1)
        i.run("A←2 3 4⍴⍳24")
        result = i.run("1 1 2⍉A")
        assert result == APLArray.array(
            [2, 4],
            [[ 1,  2,  3,  4],
             [17, 18, 19, 20]],
        )

    # ------------------------------------------------------------------
    # Identity and equivalence with monadic ⍉
    # ------------------------------------------------------------------

    def test_dyadic_identity_matrix(self) -> None:
        # 1 2⍉M is identity (axis 1 stays at 1, axis 2 stays at 2).
        i = Interpreter(io=1)
        original = i.run("2 3⍴⍳6")
        result = i.run("1 2⍉2 3⍴⍳6")
        assert result == original

    def test_dyadic_swap_matrix_equals_monadic(self) -> None:
        # 2 1⍉M is the same as ⍉M.
        i = Interpreter(io=1)
        monadic = i.run("⍉2 3⍴⍳6")
        dyadic = i.run("2 1⍉2 3⍴⍳6")
        assert dyadic == monadic

    def test_dyadic_full_reverse_equals_monadic_rank3(self) -> None:
        # 3 2 1⍉A reverses all three axes — same as ⍉A.
        i = Interpreter(io=1)
        i.run("A←2 3 4⍴⍳24")
        monadic = i.run("⍉A")
        dyadic = i.run("3 2 1⍉A")
        assert dyadic == monadic

    def test_dyadic_vector_identity(self) -> None:
        # 1⍉V is identity (rank 1, single axis stays at position 1).
        # X is the scalar 1, treated as a 1-element vector for this rule.
        result = Interpreter(io=1).run("1⍉1 2 3 4")
        assert result == APLArray.array([4], [1, 2, 3, 4])

    def test_dyadic_rank4_full_reverse(self) -> None:
        # 4 3 2 1⍉Y reverses all four axes. Equivalent to ⍉Y.
        i = Interpreter(io=1)
        i.run("Y←2 3 4 5⍴⍳120")
        monadic = i.run("⍉Y")
        dyadic = i.run("4 3 2 1⍉Y")
        assert dyadic == monadic

    # ------------------------------------------------------------------
    # Diagonal extraction (matrix cases)
    # ------------------------------------------------------------------

    def test_dyadic_matrix_main_diagonal_square(self) -> None:
        # 1 1⍉(2 2⍴1 2 3 4) → 1 4 (the main diagonal).
        result = Interpreter(io=1).run("1 1⍉2 2⍴1 2 3 4")
        assert result == APLArray.array([2], [1, 4])

    def test_dyadic_matrix_main_diagonal_non_square(self) -> None:
        # 1 1⍉(2 3⍴⍳6) → 1 5
        # The (2,3) matrix:    1 2 3
        #                      4 5 6
        # Diagonal length min(2,3)=2; elements at (0,0) and (1,1).
        result = Interpreter(io=1).run("1 1⍉2 3⍴⍳6")
        assert result == APLArray.array([2], [1, 5])

    # ------------------------------------------------------------------
    # Type and dtype
    # ------------------------------------------------------------------

    def test_dyadic_char_matrix_works(self) -> None:
        # 2 1⍉(2 3⍴'abcdef') — chars allowed, just like monadic ⍉.
        i = Interpreter(io=1)
        original_transposed = i.run("⍉2 3⍴'abcdef'")
        dyadic = i.run("2 1⍉2 3⍴'abcdef'")
        assert dyadic == original_transposed

    def test_dyadic_float_dtype_preserved(self) -> None:
        # 2 1⍉(float matrix) preserves the float dtype.
        result = Interpreter(io=1).run("2 1⍉2 2⍴1.5 2.5 3.5 4.5")
        assert result == APLArray.array(
            [2, 2],
            [[1.5, 3.5],
             [2.5, 4.5]],
        )
        import numpy as np
        assert np.issubdtype(result.data.dtype, np.floating)

    # ------------------------------------------------------------------
    # ⎕IO sensitivity
    # ------------------------------------------------------------------

    def test_dyadic_io0_swap_matrix(self) -> None:
        # In ⎕IO=0, valid axis indices for a matrix are 0 and 1.
        # 1 0⍉M swaps the axes (= ⍉M).
        i = Interpreter(io=0)
        monadic = i.run("⍉2 3⍴⍳6")
        dyadic = i.run("1 0⍉2 3⍴⍳6")
        assert dyadic == monadic

    def test_dyadic_io0_diagonal(self) -> None:
        # In ⎕IO=0, 0 0⍉M is the diagonal.
        i = Interpreter(io=0)
        result = i.run("0 0⍉2 2⍴1 2 3 4")
        assert result == APLArray.array([2], [1, 4])

    # ------------------------------------------------------------------
    # Error cases
    # ------------------------------------------------------------------

    def test_dyadic_length_mismatch_raises(self) -> None:
        # X length must equal rank(Y). Y is rank 2, X has length 3.
        with pytest.raises(LengthError):
            Interpreter(io=1).run("1 2 3⍉2 3⍴⍳6")

    def test_dyadic_scalar_x_scalar_y_raises_length(self) -> None:
        # 0⍉1 in ⎕IO=0: scalar X has length 1, scalar Y has rank 0;
        # the lengths don't match. Verified against Dyalog as
        # LENGTH ERROR.
        with pytest.raises(LengthError):
            Interpreter(io=0).run("0⍉1")

    def test_dyadic_scalar_x_matrix_y_raises_length(self) -> None:
        # 2⍉(2 3⍴⍳6) — scalar X (length 1) against rank-2 Y. Lengths
        # don't match. Verified against Dyalog as LENGTH ERROR.
        with pytest.raises(LengthError):
            Interpreter(io=1).run("2⍉2 3⍴⍳6")

    def test_dyadic_invalid_axis_raises(self) -> None:
        # X contains an axis index outside [⎕IO, ⎕IO+rank(Y)-1].
        # In IO=1 with rank 2, valid indices are 1 and 2; 3 is invalid.
        # Verified against Dyalog as RANK ERROR.
        with pytest.raises(RankError):
            Interpreter(io=1).run("1 3⍉2 3⍴⍳6")

    def test_dyadic_missing_axis_raises(self) -> None:
        # All integers in [⎕IO, ⌈/X] must appear in X. For X = 1 3 1
        # the max is 3 but 2 is missing.
        # Verified against Dyalog as RANK ERROR.
        with pytest.raises(RankError):
            Interpreter(io=1).run("1 3 1⍉2 3 4⍴⍳24")
