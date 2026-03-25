from marple.arraymodel import APLArray, S
from marple.interpreter import interpret, default_env


class TestInnerProduct:
    def test_dot_product(self) -> None:
        # 1 2 3+.×4 5 6 → (1×4)+(2×5)+(3×6) → 32
        assert interpret("1 2 3+.×4 5 6") == S(32)

    def test_matrix_multiply(self) -> None:
        # (2 2⍴1 2 3 4)+.×(2 2⍴5 6 7 8) → 2×2 matrix
        # [1 2] × [5 6] = [1×5+2×7  1×6+2×8] = [19 22]
        # [3 4]   [7 8]   [3×5+4×7  3×6+4×8]   [43 50]
        env = default_env()
        interpret("A←2 2⍴1 2 3 4", env)
        interpret("B←2 2⍴5 6 7 8", env)
        result = interpret("A+.×B", env)
        assert result == APLArray([2, 2], [19, 22, 43, 50])


    def test_matrix_multiply_float(self) -> None:
        # Float matrices must not crash or return scalar
        env = default_env()
        interpret("A←2 3⍴1.5 2.5 3.5 4.5 5.5 6.5", env)
        interpret("B←3 2⍴0.1 0.2 0.3 0.4 0.5 0.6", env)
        result = interpret("A+.×B", env)
        assert result.shape == [2, 2]

    def test_matrix_multiply_non_square(self) -> None:
        # (2 3⍴⍳6)+.×(3 2⍴⍳6) → 2×2 matrix
        # [1 2 3] × [1 2] = [1×1+2×3+3×5  1×2+2×4+3×6] = [22 28]
        # [4 5 6]   [3 4]   [4×1+5×3+6×5  4×2+5×4+6×6]   [49 64]
        #           [5 6]
        env = default_env()
        interpret("A←2 3⍴⍳6", env)
        interpret("B←3 2⍴⍳6", env)
        result = interpret("A+.×B", env)
        assert result.shape == [2, 2]
        assert list(result.data) == [22, 28, 49, 64]

    def test_matrix_vector_inner(self) -> None:
        # (2 3⍴⍳6)+.×1 2 3 → vector of length 2
        env = default_env()
        interpret("M←2 3⍴⍳6", env)
        result = interpret("M+.×1 2 3", env)
        assert result.shape == [2]
        assert list(result.data) == [14, 32]

    def test_vector_matrix_inner(self) -> None:
        # 1 2+.×(2 3⍴⍳6) → vector of length 3
        env = default_env()
        interpret("M←2 3⍴⍳6", env)
        result = interpret("1 2+.×M", env)
        assert result.shape == [3]
        assert list(result.data) == [9, 12, 15]

    def test_length_error(self) -> None:
        # 2 3+.×3 4 5 → length error (2 vs 3)
        import pytest
        from marple.errors import LengthError
        with pytest.raises(LengthError):
            interpret("2 3+.×3 4 5")


class TestOuterProduct:
    def test_multiplication_table(self) -> None:
        # (⍳3)∘.×(⍳4) → 3×4 multiplication table
        result = interpret("(⍳3)∘.×⍳4")
        assert result == APLArray([3, 4], [
            1, 2, 3, 4,
            2, 4, 6, 8,
            3, 6, 9, 12,
        ])

    def test_outer_addition(self) -> None:
        # 1 2 3∘.+10 20 → 2D addition table
        result = interpret("1 2 3∘.+10 20")
        assert result == APLArray([3, 2], [11, 21, 12, 22, 13, 23])

    def test_outer_equality(self) -> None:
        # 1 2 3∘.=1 3 → Boolean table
        result = interpret("1 2 3∘.=1 3")
        assert result == APLArray([3, 2], [1, 0, 0, 0, 0, 1])
