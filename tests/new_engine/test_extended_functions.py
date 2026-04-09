"""Extended function tests — new engine."""

import math

from marple.numpy_array import APLArray, S
from marple.engine import Interpreter


class TestPowerAndLog:
    def test_exponential(self) -> None:
        assert Interpreter(io=1).run("*1") == S(math.e)

    def test_power(self) -> None:
        assert Interpreter(io=1).run("2*3") == S(8)

    def test_natural_log(self) -> None:
        assert Interpreter(io=1).run("⍟1") == S(0.0)

    def test_log_base(self) -> None:
        assert Interpreter(io=1).run("10⍟100") == S(2.0)


class TestAbsoluteAndResidue:
    def test_absolute_value(self) -> None:
        assert Interpreter(io=1).run("|¯5") == S(5)

    def test_residue(self) -> None:
        assert Interpreter(io=1).run("3|7") == S(1)


class TestComparison:
    def test_less_than(self) -> None:
        assert Interpreter(io=1).run("3<5") == S(1)

    def test_less_than_false(self) -> None:
        assert Interpreter(io=1).run("5<3") == S(0)

    def test_less_equal(self) -> None:
        assert Interpreter(io=1).run("3≤3") == S(1)

    def test_equal(self) -> None:
        assert Interpreter(io=1).run("3=3") == S(1)

    def test_greater_equal(self) -> None:
        assert Interpreter(io=1).run("5≥3") == S(1)

    def test_greater_than(self) -> None:
        assert Interpreter(io=1).run("5>3") == S(1)

    def test_not_equal(self) -> None:
        assert Interpreter(io=1).run("3≠5") == S(1)

    def test_comparison_on_vectors(self) -> None:
        assert Interpreter(io=1).run("1 2 3<2 2 2") == APLArray.array([3], [1, 0, 0])


class TestCircular:
    def test_pi_times(self) -> None:
        result = Interpreter(io=1).run("○1")
        assert abs(result.data.item() - math.pi) < 1e-10

    def test_sin(self) -> None:
        result = Interpreter(io=1).run("1○○0.5")
        assert abs(result.data[0] - 1.0) < 1e-10

    def test_cos(self) -> None:
        result = Interpreter(io=1).run("2○○1")
        assert abs(result.data[0] - (-1.0)) < 1e-10

    def test_arcsin(self) -> None:
        result = Interpreter(io=1).run("¯1○1")
        assert abs(result.data[0] - math.pi / 2) < 1e-10

    def test_pi_times_two(self) -> None:
        result = Interpreter(io=1).run("○2")
        assert abs(result.data.item() - 2 * math.pi) < 1e-10

    def test_tan(self) -> None:
        result = Interpreter(io=1).run("3○0")  # tan(0) = 0
        assert abs(result.data[0]) < 1e-10

    def test_sqrt_via_circle(self) -> None:
        # 0○x → sqrt(1-x²)
        result = Interpreter(io=1).run("0○0.6")  # sqrt(1 - 0.36) = sqrt(0.64) = 0.8
        assert abs(result.data[0] - 0.8) < 1e-10

    def test_sinh(self) -> None:
        result = Interpreter(io=1).run("5○1")
        assert abs(result.data[0] - math.sinh(1)) < 1e-10


class TestBoolean:
    def test_and(self) -> None:
        assert Interpreter(io=1).run("1∧1") == S(1)

    def test_and_false(self) -> None:
        assert Interpreter(io=1).run("1∧0") == S(0)

    def test_or(self) -> None:
        assert Interpreter(io=1).run("0∨1") == S(1)

    def test_not(self) -> None:
        assert Interpreter(io=1).run("~1") == S(0)

    def test_not_zero(self) -> None:
        assert Interpreter(io=1).run("~0") == S(1)
