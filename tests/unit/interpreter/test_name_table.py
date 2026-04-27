"""Name table tests — new engine."""

import pytest

#from marple.ports.array import APLArray, S
from marple.engine import Interpreter
from marple.errors import ClassError, ValueError_
from marple.adapters.numpy_array_builder import BUILDER
S = BUILDER.S


class TestNameTableFundamentals:
    def test_array_nc(self) -> None:
        i = Interpreter(io=1)
        i.run("x←5")
        assert i.run("⎕NC 'x'") == S(2)

    def test_function_nc(self) -> None:
        i = Interpreter(io=1)
        i.run("f←{⍵+1}")
        assert i.run("⎕NC 'f'") == S(3)

    def test_reassign_array_ok(self) -> None:
        i = Interpreter(io=1)
        i.run("x←5")
        i.run("x←10")
        assert i.run("x") == S(10)

    def test_reassign_function_ok(self) -> None:
        i = Interpreter(io=1)
        i.run("f←{⍵+1}")
        i.run("f←{⍵×2}")
        assert i.run("f 5") == S(10)

    def test_class_change_error(self) -> None:
        i = Interpreter(io=1)
        i.run("f←{⍵+1}")
        with pytest.raises(ClassError):
            i.run("f←42")

    def test_class_change_error_array_to_function(self) -> None:
        i = Interpreter(io=1)
        i.run("x←42")
        with pytest.raises(ClassError):
            i.run("x←{⍵+1}")


class TestFunctionCalls:
    def test_named_fn_with_iota(self) -> None:
        i = Interpreter(io=1)
        i.run("double←{⍵+⍵}")
        assert i.run("double ⍳5") == BUILDER.apl_array([5], [2, 4, 6, 8, 10])

    def test_named_fn_with_scalar(self) -> None:
        i = Interpreter(io=1)
        i.run("double←{⍵+⍵}")
        assert i.run("double 5") == S(10)

    def test_named_fn_with_negate(self) -> None:
        i = Interpreter(io=1)
        i.run("f←{⍵+1}")
        assert i.run("f -3") == S(-2)

    def test_named_fn_with_reverse(self) -> None:
        i = Interpreter(io=1)
        i.run("f←{⍵+1}")
        assert i.run("f ⌽⍳5") == BUILDER.apl_array([5], [6, 5, 4, 3, 2])


class TestArraysInDyadicContext:
    def test_array_dyadic_iota(self) -> None:
        i = Interpreter(io=1)
        i.run("data←10 20 30")
        assert i.run("data⍳20") == S(2)

    def test_array_dyadic_add(self) -> None:
        i = Interpreter(io=1)
        i.run("x←5")
        assert i.run("x+3") == S(8)

    def test_array_dyadic_rotate(self) -> None:
        i = Interpreter(io=1)
        i.run("v←1 2 3")
        assert i.run("2⌽v") == BUILDER.apl_array([3], [3, 1, 2])


class TestFunctionsInsideDfns:
    def test_call_outer_fn(self) -> None:
        i = Interpreter(io=1)
        i.run("double←{⍵+⍵}")
        assert i.run("{double ⍵} 5") == S(10)

    def test_call_outer_fn_with_iota(self) -> None:
        i = Interpreter(io=1)
        i.run("double←{⍵+⍵}")
        assert i.run("{double ⍳⍵} 5") == BUILDER.apl_array([5], [2, 4, 6, 8, 10])

    def test_nested_fn_calls(self) -> None:
        i = Interpreter(io=1)
        i.run("f←{⍵×2}")
        i.run("g←{f ⍵+1}")
        assert i.run("g 3") == S(8)


class TestDfnsWithDiamonds:
    def test_local_variable(self) -> None:
        i = Interpreter(io=1)
        i.run("f←{x←⍵+1⋄x×2}")
        assert i.run("f 5") == S(12)

    def test_multiple_locals(self) -> None:
        i = Interpreter(io=1)
        i.run("f←{a←⍵⋄b←a+1⋄a×b}")
        assert i.run("f 3") == S(12)

    def test_guard_with_diamond(self) -> None:
        i = Interpreter(io=1)
        i.run("f←{⍵>0:⍵⋄-⍵}")
        assert i.run("f ¯5") == S(5)


class TestFunctionsDefinedInDfns:
    def test_define_and_call_monadic(self) -> None:
        assert Interpreter(io=1).run("{g←{⍵+10}⋄g ⍵} 5") == S(15)

    def test_define_and_call_dyadic(self) -> None:
        assert Interpreter(io=1).run("{add←{⍺+⍵}⋄3 add 4} 0") == S(7)


class TestWithProducts:
    def test_fn_applied_to_inner_product(self) -> None:
        i = Interpreter(io=1)
        i.run("f←{⍵+1}")
        assert i.run("f 1 2 3+.×4 5 6") == S(33)

    def test_fn_applied_to_outer_product(self) -> None:
        i = Interpreter(io=1)
        i.run("double←{⍵+⍵}")
        result = i.run("double (⍳3)∘.×⍳3")
        assert result == BUILDER.apl_array([3, 3], [[2, 4, 6], [4, 8, 12], [6, 12, 18]])


class TestWithRank:
    def test_named_fn_with_rank(self) -> None:
        i = Interpreter(io=1)
        i.run("double←{⍵+⍵}")
        result = i.run("(double⍤1) 2 3⍴⍳6")
        assert result == BUILDER.apl_array([2, 3], [[2, 4, 6], [8, 10, 12]])

    def test_sort_with_rank(self) -> None:
        i = Interpreter(io=1)
        i.run("sort←{⍵[⍋⍵]}")
        i.run("M←3 4⍴12 1 8 3 5 9 2 7 11 4 6 10")
        result = i.run("(sort⍤1) M")
        assert result == BUILDER.apl_array([3, 4], [[1, 3, 8, 12], [2, 5, 7, 9], [4, 6, 10, 11]])


class TestImport:
    def test_imported_fn_no_parens(self) -> None:
        i = Interpreter(io=1)
        i.run("#import $::str::upper")
        assert i.run("upper 'hello'").as_str() == "HELLO"

    def test_imported_fn_with_alias(self) -> None:
        i = Interpreter(io=1)
        i.run("#import $::str::upper as up")
        assert i.run("up 'hello'").as_str() == "HELLO"


class TestErrorCases:
    def test_undefined_name(self) -> None:
        with pytest.raises(ValueError_):
            Interpreter(io=1).run("nosuchvar")
