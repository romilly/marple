"""End-to-end expression evaluation via the Interpreter — eval order, vector arithmetic, variables."""

from marple.numpy_array import APLArray, S
from marple.engine import Interpreter


class TestSpecExamples:
    def test_right_to_left_evaluation(self) -> None:
        result = Interpreter(io=1).run("1÷2⌊3×4-5")
        assert result == S(1 / -3)

    def test_parens_override(self) -> None:
        assert Interpreter(io=1).run("(2+3)×4") == S(20)


class TestVectorArithmetic:
    def test_vector_plus_vector(self) -> None:
        assert Interpreter(io=1).run("1 2+3 4") == APLArray.array([2], [4, 6])

    def test_scalar_times_vector(self) -> None:
        assert Interpreter(io=1).run("2×1 2 3") == APLArray.array([3], [2, 4, 6])

    def test_negate_vector(self) -> None:
        assert Interpreter(io=1).run("-1 2 3") == APLArray.array([3], [-1, -2, -3])


class TestVariables:
    def test_use_variable_in_expression(self) -> None:
        i = Interpreter(io=1)
        i.run("x←10")
        i.run("y←20")
        assert i.run("x+y") == S(30)

    def test_reassignment(self) -> None:
        i = Interpreter(io=1)
        i.run("x←5")
        i.run("x←x+1")
        assert i.run("x") == S(6)
