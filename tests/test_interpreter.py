from marple.arraymodel import APLArray, S
from marple.interpreter import interpret


class TestInterpreterScalars:
    def test_single_number(self) -> None:
        assert interpret("5") == S(5)

    def test_negative_number(self) -> None:
        assert interpret("¯3") == S(-3)

    def test_float(self) -> None:
        assert interpret("3.14") == S(3.14)


class TestInterpreterMonadic:
    def test_negate(self) -> None:
        assert interpret("-5") == S(-5)

    def test_reciprocal(self) -> None:
        assert interpret("÷4") == S(0.25)

    def test_ceiling(self) -> None:
        assert interpret("⌈2.3") == S(3)

    def test_floor(self) -> None:
        assert interpret("⌊2.7") == S(2)


class TestInterpreterDyadic:
    def test_add(self) -> None:
        assert interpret("3+4") == S(7)

    def test_subtract(self) -> None:
        assert interpret("5-3") == S(2)

    def test_multiply(self) -> None:
        assert interpret("3×4") == S(12)

    def test_divide(self) -> None:
        assert interpret("10÷4") == S(2.5)

    def test_maximum(self) -> None:
        assert interpret("3⌈5") == S(5)

    def test_minimum(self) -> None:
        assert interpret("3⌊5") == S(3)


class TestInterpreterRightToLeft:
    def test_long_right_scope(self) -> None:
        # 1+2×3 → 1+(2×3) → 7
        assert interpret("1+2×3") == S(7)

    def test_chained_operations(self) -> None:
        # 2×3+4 → 2×(3+4) → 14
        assert interpret("2×3+4") == S(14)


class TestInterpreterParens:
    def test_parens_override(self) -> None:
        # (1+2)×3 → 9
        assert interpret("(1+2)×3") == S(9)


class TestInterpreterVectors:
    def test_vector_literal(self) -> None:
        assert interpret("1 2 3") == APLArray([3], [1, 2, 3])

    def test_vector_addition(self) -> None:
        assert interpret("1 2 3+4 5 6") == APLArray([3], [5, 7, 9])

    def test_scalar_plus_vector(self) -> None:
        assert interpret("10+1 2 3") == APLArray([3], [11, 12, 13])

    def test_negate_vector(self) -> None:
        assert interpret("-1 2 3") == APLArray([3], [-1, -2, -3])


class TestInterpreterAssignment:
    def test_assign_and_use(self) -> None:
        env: dict[str, APLArray] = {}
        interpret("x←5", env)
        assert interpret("x+3", env) == S(8)

    def test_assign_returns_value(self) -> None:
        assert interpret("x←5") == S(5)


class TestInterpreterComments:
    def test_comment_ignored(self) -> None:
        assert interpret("3+4 ⍝ add them") == S(7)
