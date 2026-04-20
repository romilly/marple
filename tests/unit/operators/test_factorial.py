"""Factorial (!) and binomial coefficient tests."""

from marple.ports.array import APLArray, S
from marple.engine import Interpreter


class TestMonadicFactorial:
    def test_factorial_zero(self) -> None:
        assert Interpreter(io=1).run("!0") == S(1)

    def test_factorial_one(self) -> None:
        assert Interpreter(io=1).run("!1") == S(1)

    def test_factorial_five(self) -> None:
        assert Interpreter(io=1).run("!5") == S(120)

    def test_factorial_ten(self) -> None:
        assert Interpreter(io=1).run("!10") == S(3628800)

    def test_factorial_pervades(self) -> None:
        assert Interpreter(io=1).run("!0 1 2 3 4") == APLArray.array([5], [1, 1, 2, 6, 24])


class TestDyadicBinomial:
    def test_binomial_basic(self) -> None:
        assert Interpreter(io=1).run("2!5") == S(10)

    def test_binomial_zero(self) -> None:
        assert Interpreter(io=1).run("0!5") == S(1)

    def test_binomial_equal(self) -> None:
        assert Interpreter(io=1).run("5!5") == S(1)

    def test_binomial_choose_one(self) -> None:
        assert Interpreter(io=1).run("1!7") == S(7)

    def test_binomial_pervades(self) -> None:
        assert Interpreter(io=1).run("2!3 4 5") == APLArray.array([3], [3, 6, 10])
