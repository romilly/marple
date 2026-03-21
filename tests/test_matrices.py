from marple.arraymodel import APLArray, S
from marple.interpreter import interpret


class TestMatrixCreation:
    def test_reshape_to_matrix(self) -> None:
        # 2 3⍴⍳6 → 2×3 matrix
        result = interpret("2 3⍴⍳6")
        assert result == APLArray([2, 3], [1, 2, 3, 4, 5, 6])

    def test_shape_of_matrix(self) -> None:
        result = interpret("⍴2 3⍴⍳6")
        assert result == APLArray([2], [2, 3])

    def test_ravel_matrix(self) -> None:
        result = interpret(",2 3⍴⍳6")
        assert result == APLArray([6], [1, 2, 3, 4, 5, 6])


class TestMatrixArithmetic:
    def test_scalar_plus_matrix(self) -> None:
        result = interpret("10+2 3⍴⍳6")
        assert result == APLArray([2, 3], [11, 12, 13, 14, 15, 16])

    def test_negate_matrix(self) -> None:
        result = interpret("-2 2⍴1 2 3 4")
        assert result == APLArray([2, 2], [-1, -2, -3, -4])


class TestTranspose:
    def test_transpose_matrix(self) -> None:
        # ⍉2 3⍴⍳6 → 3×2 matrix
        # 1 2 3    1 4
        # 4 5 6 →  2 5
        #          3 6
        result = interpret("⍉2 3⍴⍳6")
        assert result == APLArray([3, 2], [1, 4, 2, 5, 3, 6])

    def test_transpose_vector(self) -> None:
        # ⍉ of a vector is identity
        result = interpret("⍉1 2 3")
        assert result == APLArray([3], [1, 2, 3])


class TestGrade:
    def test_grade_up(self) -> None:
        # ⍋3 1 4 1 5 → 2 4 1 3 5 (indices that would sort ascending)
        result = interpret("⍋3 1 4 1 5")
        assert result == APLArray([5], [2, 4, 1, 3, 5])

    def test_grade_down(self) -> None:
        # ⍒3 1 4 1 5 → 5 3 1 2 4 (indices that would sort descending)
        result = interpret("⍒3 1 4 1 5")
        assert result == APLArray([5], [5, 3, 1, 2, 4])


class TestEncodeDecode:
    def test_encode(self) -> None:
        # 2 2 2⊤7 → 1 1 1 (binary representation of 7)
        result = interpret("2 2 2⊤7")
        assert result == APLArray([3], [1, 1, 1])

    def test_decode(self) -> None:
        # 2⊥1 1 1 → 7 (evaluate as base-2)
        result = interpret("2⊥1 1 1")
        assert result == S(7)

    def test_decode_mixed_base(self) -> None:
        # 24 60 60⊥1 2 3 → 3723 (1 hour, 2 minutes, 3 seconds)
        result = interpret("24 60 60⊥1 2 3")
        assert result == S(3723)
