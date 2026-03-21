import math

from marple.arraymodel import APLArray, S
from marple.interpreter import interpret


class TestPowerAndLog:
    def test_exponential(self) -> None:
        # monadic * is e^x
        result = interpret("*1")
        assert result == S(math.e)

    def test_power(self) -> None:
        assert interpret("2*3") == S(8)

    def test_natural_log(self) -> None:
        result = interpret("⍟1")
        assert result == S(0.0)

    def test_log_base(self) -> None:
        assert interpret("10⍟100") == S(2.0)


class TestAbsoluteAndResidue:
    def test_absolute_value(self) -> None:
        assert interpret("|¯5") == S(5)

    def test_residue(self) -> None:
        assert interpret("3|7") == S(1)


class TestComparison:
    def test_less_than(self) -> None:
        assert interpret("3<5") == S(1)

    def test_less_than_false(self) -> None:
        assert interpret("5<3") == S(0)

    def test_less_equal(self) -> None:
        assert interpret("3≤3") == S(1)

    def test_equal(self) -> None:
        assert interpret("3=3") == S(1)

    def test_greater_equal(self) -> None:
        assert interpret("5≥3") == S(1)

    def test_greater_than(self) -> None:
        assert interpret("5>3") == S(1)

    def test_not_equal(self) -> None:
        assert interpret("3≠5") == S(1)

    def test_comparison_on_vectors(self) -> None:
        assert interpret("1 2 3<2 2 2") == APLArray([3], [1, 0, 0])


class TestCircular:
    def test_pi_times(self) -> None:
        # ○1 → π
        import math
        result = interpret("○1")
        assert abs(result.data[0] - math.pi) < 1e-10

    def test_pi_times_two(self) -> None:
        import math
        result = interpret("○2")
        assert abs(result.data[0] - 2 * math.pi) < 1e-10


class TestBoolean:
    def test_and(self) -> None:
        assert interpret("1∧1") == S(1)

    def test_and_false(self) -> None:
        assert interpret("1∧0") == S(0)

    def test_or(self) -> None:
        assert interpret("0∨1") == S(1)

    def test_not(self) -> None:
        assert interpret("~1") == S(0)

    def test_not_zero(self) -> None:
        assert interpret("~0") == S(1)
