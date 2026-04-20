"""Dfn tests — new engine."""

import pytest

from marple.ports.array import APLArray, S
from marple.engine import Interpreter
from marple.errors import SyntaxError_


class TestBasicDfns:
    def test_identity(self) -> None:
        assert Interpreter(io=1).run("{⍵}5") == S(5)

    def test_double(self) -> None:
        assert Interpreter(io=1).run("{⍵+⍵}3") == S(6)

    def test_negate_dfn(self) -> None:
        assert Interpreter(io=1).run("{-⍵}5") == S(-5)

    def test_dfn_with_vector(self) -> None:
        assert Interpreter(io=1).run("{⍵+1}1 2 3") == APLArray.array([3], [2, 3, 4])


class TestNamedDfns:
    def test_named_dfn(self) -> None:
        i = Interpreter(io=1)
        i.run("double←{⍵+⍵}")
        assert i.run("double 3") == S(6)

    def test_named_dfn_with_vector(self) -> None:
        i = Interpreter(io=1)
        i.run("inc←{⍵+1}")
        assert i.run("inc 1 2 3") == APLArray.array([3], [2, 3, 4])


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
        assert i.run("pad 1 2 3") == APLArray.array([4], [0, 1, 2, 3])

    def test_default_alpha_overridden(self) -> None:
        i = Interpreter(io=1)
        i.run("pad←{⍺←0⋄⍺,⍵}")
        assert i.run("9 pad 1 2 3") == APLArray.array([4], [9, 1, 2, 3])


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


class TestMultiGuard:
    def test_multi_guard_with_assignment(self) -> None:
        from marple.backend_functions import chars_to_str
        i = Interpreter(io=1)
        i.run("classify←{r←'zero' ⋄ ⍵>0:r←'positive' ⋄ ⍵<0:r←'negative' ⋄ r}")
        result = i.run("classify 5")
        assert chars_to_str(result.data) == "positive"


class TestCRandFX:
    def test_cr_multi_statement(self) -> None:
        from marple.backend_functions import chars_to_str
        i = Interpreter(io=1)
        i.run("sign←{⍵>0:1 ⋄ ⍵<0:¯1 ⋄ 0}")
        result = i.run("⎕CR 'sign'")
        text = chars_to_str(result.data)
        assert "⋄" in text
        assert "sign←{" in text

    def test_fx_multi_statement(self) -> None:
        i = Interpreter(io=1)
        i.run("⎕FX 'clamp←{⍵>100:100 ⋄ ⍵<0:0 ⋄ ⍵}'")
        assert i.run("clamp 150") == S(100)
        assert i.run("clamp ¯5") == S(0)
        assert i.run("clamp 50") == S(50)

    def test_fx_matrix_two_rows(self) -> None:
        # Matrix-form ⎕FX takes a 2D char matrix (one line per row).
        # Bug pre-fix: operand.data[r*cols:(r+1)*cols] sliced ROWS of
        # the 2D uint32 ndarray instead of flat elements, so the
        # extracted "lines" were either both rows concatenated or empty,
        # causing parse failures or wrong definitions.
        i = Interpreter(io=1)
        # 2 rows of 11 cols, both 'add←{⍵+1}  ' (cycled by reshape).
        # After rstrip: 'add←{⍵+1}' on each row, joined as a duplicate
        # assignment which is legal (second wins).
        i.run("⎕FX 2 11⍴'add←{⍵+1}  '")
        assert i.run("add 5") == S(6)

    def test_cr_fx_round_trip_multi(self) -> None:
        from marple.backend_functions import chars_to_str
        i = Interpreter(io=1)
        i.run("sign←{⍵>0:1 ⋄ ⍵<0:¯1 ⋄ 0}")
        src = i.run("⎕CR 'sign'")
        text = chars_to_str(src.data)
        new_text = text.replace("sign", "sgn", 1)
        i.run("⎕FX '" + new_text + "'")
        assert i.run("sgn 5") == S(1)
        assert i.run("sgn ¯3") == S(-1)


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

    def test_dop_with_negate(self) -> None:
        i = Interpreter(io=1)
        i.run("twice←{⍺⍺ ⍺⍺ ⍵}")
        assert i.run("(-) twice 5") == S(5)

    def test_dop_with_reciprocal(self) -> None:
        i = Interpreter(io=1)
        i.run("twice←{⍺⍺ ⍺⍺ ⍵}")
        assert i.run("(÷) twice 4") == S(4)

    def test_dop_with_iota(self) -> None:
        i = Interpreter(io=1)
        i.run("apply←{⍺⍺ ⍵}")
        result = i.run("(⍳) apply 5")
        assert result == APLArray.array([5], [1, 2, 3, 4, 5])

    def test_dop_with_array_operand(self) -> None:
        i = Interpreter(io=1)
        i.run("addop←{⍺⍺+⍵}")
        assert i.run("(10) addop 5") == S(15)

    def test_dop_array_operand_vector(self) -> None:
        i = Interpreter(io=1)
        i.run("scale←{⍺⍺×⍵}")
        result = i.run("(2) scale 1 2 3")
        assert list(result.data) == [2, 4, 6]

    def test_multi_statement_dop(self) -> None:
        i = Interpreter(io=1)
        i.run("apply_twice←{t←⍺⍺ ⍵ ⋄ ⍺⍺ t}")
        i.run("double←{⍵+⍵}")
        assert i.run("(double) apply_twice 3") == S(12)

    def test_dop_with_guard(self) -> None:
        i = Interpreter(io=1)
        i.run("safe←{⍵=0:0 ⋄ ⍺⍺ ⍵}")
        assert i.run("(÷) safe 4") == S(0.25)
        assert i.run("(÷) safe 0") == S(0)

    def test_dop_with_reduce(self) -> None:
        i = Interpreter(io=1)
        i.run("redop←{⍺⍺/⍵}")
        assert i.run("(+) redop ⍳10") == S(55)

    def test_dop_with_scan(self) -> None:
        i = Interpreter(io=1)
        i.run("scanop←{⍺⍺\\⍵}")
        result = i.run("(+) scanop 1 2 3")
        assert list(result.data) == [1, 3, 6]

    def test_dop_compose(self) -> None:
        i = Interpreter(io=1)
        i.run("apply←{⍺⍺ ⍵}")
        i.run("sum←{+/⍵}")
        assert i.run("(sum) apply ⍳10") == S(55)

    def test_nc_dop(self) -> None:
        i = Interpreter(io=1)
        i.run("twice←{⍺⍺ ⍺⍺ ⍵}")
        assert i.run("⎕NC 'twice'") == S(4)

    def test_cr_dop(self) -> None:
        from marple.backend_functions import chars_to_str
        i = Interpreter(io=1)
        i.run("twice←{⍺⍺ ⍺⍺ ⍵}")
        result = i.run("⎕CR 'twice'")
        text = chars_to_str(result.data)
        assert "⍺⍺" in text

    def test_fx_dop(self) -> None:
        i = Interpreter(io=1)
        i.run("⎕FX 'twice←{⍺⍺ ⍺⍺ ⍵}'")
        assert i.run("⎕NC 'twice'") == S(4)

    def test_dyadic_dop(self) -> None:
        i = Interpreter(io=1)
        i.run("swap←{⍵⍵ ⍺⍺ ⍵}")
        assert i.run("2(+swap -)5") == S(-5)

    def test_dyadic_dop_two_functions(self) -> None:
        i = Interpreter(io=1)
        i.run("compose←{⍵⍵ ⍺⍺ ⍵}")
        i.run("double←{⍵+⍵}")
        i.run("neg←{-⍵}")
        assert i.run("double compose neg 3") == S(-6)

    def test_dyadic_dop_with_primitives(self) -> None:
        i = Interpreter(io=1)
        i.run("compose←{⍵⍵ ⍺⍺ ⍵}")
        assert i.run("(-) compose (÷) 4") == S(-0.25)

    def test_dyadic_dop_array_operands(self) -> None:
        i = Interpreter(io=1)
        i.run("between←{⍺⍺+⍵⍵×⍵}")
        assert i.run("(10) between (3) 5") == S(25)

    def test_operator_with_parens(self) -> None:
        i = Interpreter(io=1)
        i.run("twice←{⍺⍺ ⍺⍺ ⍵}")
        i.run("double←{⍵+⍵}")
        assert i.run("((double) twice 5)-3") == S(17)

    def test_alpha_alpha_outside_dop(self) -> None:
        with pytest.raises(SyntaxError_):
            Interpreter(io=1).run("{⍺⍺+⍵} 5")
