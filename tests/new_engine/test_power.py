"""Power operator (⍣) tests — new engine."""

import math

import pytest

from marple.arraymodel import APLArray, S
from marple.engine import Interpreter
from marple.errors import DomainError


class TestPowerInteger:
    def test_zero_applications(self) -> None:
        i = Interpreter(io=1)
        i.run("f←{⍵+1}")
        assert i.run("(f⍣0) 10") == S(10)

    def test_one_application(self) -> None:
        i = Interpreter(io=1)
        i.run("f←{⍵+1}")
        assert i.run("(f⍣1) 10") == S(11)

    def test_three_applications(self) -> None:
        i = Interpreter(io=1)
        i.run("f←{⍵+1}")
        assert i.run("(f⍣3) 10") == S(13)

    def test_negative_operand_error(self) -> None:
        i = Interpreter(io=1)
        i.run("f←{⍵+1}")
        with pytest.raises(DomainError):
            i.run("(f⍣¯1) 10")

    def test_with_left_arg(self) -> None:
        i = Interpreter(io=1)
        i.run("add←{⍺+⍵}")
        assert i.run("1(add⍣4) 10") == S(14)

    def test_power_of_two(self) -> None:
        i = Interpreter(io=1)
        i.run("dbl←{⍵×2}")
        assert i.run("(dbl⍣10) 1") == S(1024)


class TestPowerConvergence:
    def test_fixed_point_match(self) -> None:
        i = Interpreter(io=1)
        i.run("phi←{1+÷⍵}")
        result = i.run("(phi⍣≡) 1")
        assert abs(result.data[0] - (1 + math.sqrt(5)) / 2) < 1e-10

    def test_sqrt_newton(self) -> None:
        i = Interpreter(io=1)
        i.run("sqr←{0.5×⍵+⍺÷⍵}")
        result = i.run("2(sqr⍣≡) 1")
        assert abs(result.data[0] - math.sqrt(2)) < 1e-10

    def test_identity_converges_immediately(self) -> None:
        i = Interpreter(io=1)
        assert i.run("({⍵}⍣≡) 42") == S(42)

    def test_custom_convergence_function(self) -> None:
        i = Interpreter(io=1)
        i.run("close←{1e¯10>|⍺-⍵}")
        i.run("sqr←{0.5×⍵+⍺÷⍵}")
        result = i.run("2(sqr⍣close) 1")
        assert abs(result.data[0] - math.sqrt(2)) < 1e-10


class TestPowerStructural:
    def test_reverse_twice_is_identity(self) -> None:
        assert Interpreter(io=1).run("(⌽⍣2) 1 2 3") == APLArray([3], [1, 2, 3])

    def test_reverse_three_times(self) -> None:
        assert Interpreter(io=1).run("(⌽⍣3) 1 2 3") == APLArray([3], [3, 2, 1])
