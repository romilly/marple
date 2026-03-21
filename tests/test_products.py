from marple.arraymodel import APLArray, S
from marple.interpreter import interpret


class TestInnerProduct:
    def test_dot_product(self) -> None:
        # 1 2 3+.×4 5 6 → (1×4)+(2×5)+(3×6) → 32
        assert interpret("1 2 3+.×4 5 6") == S(32)

    def test_matrix_multiply(self) -> None:
        # (2 2⍴1 2 3 4)+.×(2 2⍴5 6 7 8) → 2×2 matrix
        # [1 2] × [5 6] = [1×5+2×7  1×6+2×8] = [19 22]
        # [3 4]   [7 8]   [3×5+4×7  3×6+4×8]   [43 50]
        env: dict[str, APLArray] = {}
        interpret("A←2 2⍴1 2 3 4", env)
        interpret("B←2 2⍴5 6 7 8", env)
        result = interpret("A+.×B", env)
        assert result == APLArray([2, 2], [19, 22, 43, 50])


    def test_length_error(self) -> None:
        # 2 3+.×3 4 5 → length error (2 vs 3)
        import pytest
        with pytest.raises(ValueError, match="length"):
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
