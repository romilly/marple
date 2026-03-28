"""Dfn tests — new engine."""

from marple.arraymodel import APLArray, S
from marple.engine import Interpreter


class TestBasicDfns:
    def test_identity(self) -> None:
        assert Interpreter(io=1).run("{⍵}5") == S(5)

    def test_double(self) -> None:
        assert Interpreter(io=1).run("{⍵+⍵}3") == S(6)

    def test_negate_dfn(self) -> None:
        assert Interpreter(io=1).run("{-⍵}5") == S(-5)

    def test_dfn_with_vector(self) -> None:
        assert Interpreter(io=1).run("{⍵+1}1 2 3") == APLArray([3], [2, 3, 4])


class TestNamedDfns:
    def test_named_dfn(self) -> None:
        i = Interpreter(io=1)
        i.run("double←{⍵+⍵}")
        assert i.run("double 3") == S(6)

    def test_named_dfn_with_vector(self) -> None:
        i = Interpreter(io=1)
        i.run("inc←{⍵+1}")
        assert i.run("inc 1 2 3") == APLArray([3], [2, 3, 4])


class TestDyadicDfns:
    def test_dyadic_dfn(self) -> None:
        assert Interpreter(io=1).run("3{⍺+⍵}4") == S(7)

    def test_named_dyadic(self) -> None:
        i = Interpreter(io=1)
        i.run("avg←{(⍺+⍵)÷2}")
        assert i.run("3 avg 5") == S(4.0)

    def test_named_dyadic_with_variable(self) -> None:
        i = Interpreter(io=1)
        i.run("add←{⍺+⍵}")
        i.run("x←10")
        assert i.run("x add 5") == S(15)

    def test_named_dyadic_with_parens(self) -> None:
        i = Interpreter(io=1)
        i.run("add←{⍺+⍵}")
        assert i.run("(2+3) add 5") == S(10)


class TestGuards:
    def test_single_guard(self) -> None:
        assert Interpreter(io=1).run("{⍵=0:42⋄⍵}0") == S(42)

    def test_guard_falls_through(self) -> None:
        assert Interpreter(io=1).run("{⍵=0:42⋄⍵}5") == S(5)

    def test_multiple_guards(self) -> None:
        i = Interpreter(io=1)
        i.run("sign←{⍵>0:1⋄⍵<0:¯1⋄0}")
        assert i.run("sign 5") == S(1)
        assert i.run("sign ¯3") == S(-1)
        assert i.run("sign 0") == S(0)


class TestRecursion:
    def test_factorial(self) -> None:
        i = Interpreter(io=1)
        i.run("fact←{⍵≤1:1⋄⍵×∇ ⍵-1}")
        assert i.run("fact 5") == S(120)

    def test_fibonacci(self) -> None:
        i = Interpreter(io=1)
        i.run("fib←{⍵=0:0⋄⍵=1:1⋄(∇ ⍵-1)+∇ ⍵-2}")
        assert i.run("fib 6") == S(8)


class TestDefaultAlpha:
    def test_default_alpha_monadic(self) -> None:
        i = Interpreter(io=1)
        i.run("pad←{⍺←0⋄⍺,⍵}")
        assert i.run("pad 1 2 3") == APLArray([4], [0, 1, 2, 3])

    def test_default_alpha_overridden(self) -> None:
        i = Interpreter(io=1)
        i.run("pad←{⍺←0⋄⍺,⍵}")
        assert i.run("9 pad 1 2 3") == APLArray([4], [9, 1, 2, 3])


class TestMultiStatement:
    def test_diamond_separated(self) -> None:
        i = Interpreter(io=1)
        i.run("sign←{⍵>0:1 ⋄ ⍵<0:¯1 ⋄ 0}")
        assert i.run("sign 5") == S(1)
        assert i.run("sign ¯3") == S(-1)
        assert i.run("sign 0") == S(0)

    def test_newline_separated(self) -> None:
        i = Interpreter(io=1)
        i.run("abs←{⍵<0:-⍵\n⍵}")
        assert i.run("abs ¯7") == S(7)
        assert i.run("abs 3") == S(3)


class TestNestedCalls:
    def test_nested_dfn_calls(self) -> None:
        i = Interpreter(io=1)
        i.run("double←{⍵+⍵}")
        i.run("quad←{double double ⍵}")
        assert i.run("quad 3") == S(12)


class TestDopApplication:
    def test_monadic_dop(self) -> None:
        i = Interpreter(io=1)
        i.run("twice←{⍺⍺ ⍺⍺ ⍵}")
        assert i.run("(-)twice 5") == S(5)

    def test_dop_with_dfn_operand(self) -> None:
        i = Interpreter(io=1)
        i.run("twice←{⍺⍺ ⍺⍺ ⍵}")
        i.run("double←{⍵+⍵}")
        assert i.run("(double) twice 3") == S(12)

    def test_dyadic_dop(self) -> None:
        i = Interpreter(io=1)
        i.run("swap←{⍵⍵ ⍺⍺ ⍵}")
        assert i.run("2(+swap -)5") == S(-5)
