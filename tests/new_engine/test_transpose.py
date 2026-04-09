"""Transpose (⍉, monadic) tests — generalisation to arbitrary rank.

Per the ISO/Dyalog spec for monadic ⍉:

    R ← ⍉Y
    Y may be any array. R has shape ⌽⍴Y, with the order of axes
    reversed.

So scalar/vector transpose is identity, matrix transpose swaps the
two axes, rank-3 reverses (a,b,c)→(c,b,a), and so on.

Crucially, Y "may be any array" — chars are allowed (unlike decode
and encode, which require simple numeric arrays).

Each test's docstring shows the exact APL expression so it can be
verified against Dyalog directly.
"""

from marple.engine import Interpreter
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
