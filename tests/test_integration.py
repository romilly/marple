from marple.arraymodel import APLArray, S
from marple.interpreter import interpret


class TestSpecExamples:
    def test_right_to_left_evaluation(self) -> None:
        # From the spec: 1 ÷ 2 ⌊ 3 × 4 - 5
        # = 1 ÷ (2 ⌊ (3 × (4 - 5)))
        # = 1 ÷ (2 ⌊ (3 × ¯1))
        # = 1 ÷ (2 ⌊ ¯3)
        # = 1 ÷ ¯3
        result = interpret("1÷2⌊3×4-5")
        assert result == S(1 / -3)

    def test_parens_override(self) -> None:
        # (2+3)×4 = 20
        assert interpret("(2+3)×4") == S(20)


class TestVectorArithmetic:
    def test_vector_plus_vector(self) -> None:
        assert interpret("1 2+3 4") == APLArray([2], [4, 6])

    def test_scalar_times_vector(self) -> None:
        assert interpret("2×1 2 3") == APLArray([3], [2, 4, 6])

    def test_negate_vector(self) -> None:
        assert interpret("-1 2 3") == APLArray([3], [-1, -2, -3])


class TestVariables:
    def test_use_variable_in_expression(self) -> None:
        env: dict[str, APLArray] = {}
        interpret("x←10", env)
        interpret("y←20", env)
        assert interpret("x+y", env) == S(30)

    def test_reassignment(self) -> None:
        env: dict[str, APLArray] = {}
        interpret("x←5", env)
        interpret("x←x+1", env)
        assert interpret("x", env) == S(6)
