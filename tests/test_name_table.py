import pytest

from marple.arraymodel import APLArray, S
from marple.errors import ClassError
from marple.interpreter import interpret, default_env


class TestNameTableFundamentals:
    def test_array_assignment(self) -> None:
        env = default_env()
        interpret("x←5", env)
        assert env["__name_table__"]["x"] == 2  # ARRAY

    def test_function_assignment(self) -> None:
        env = default_env()
        interpret("f←{⍵+1}", env)
        assert env["__name_table__"]["f"] == 3  # FUNCTION

    def test_reassign_array_ok(self) -> None:
        env = default_env()
        interpret("x←5", env)
        interpret("x←10", env)
        assert interpret("x", env) == S(10)

    def test_reassign_function_ok(self) -> None:
        env = default_env()
        interpret("f←{⍵+1}", env)
        interpret("f←{⍵×2}", env)
        assert interpret("f 5", env) == S(10)

    def test_class_change_error(self) -> None:
        env = default_env()
        interpret("f←{⍵+1}", env)
        with pytest.raises(ClassError):
            interpret("f←42", env)

    def test_class_change_error_array_to_function(self) -> None:
        env = default_env()
        interpret("x←42", env)
        with pytest.raises(ClassError):
            interpret("x←{⍵+1}", env)


class TestFunctionCallsWithoutParens:
    def test_named_fn_with_iota(self) -> None:
        env = default_env()
        interpret("double←{⍵+⍵}", env)
        result = interpret("double ⍳5", env)
        assert result == APLArray([5], [2, 4, 6, 8, 10])

    def test_named_fn_with_scalar(self) -> None:
        env = default_env()
        interpret("double←{⍵+⍵}", env)
        assert interpret("double 5", env) == S(10)

    def test_named_fn_with_negate(self) -> None:
        env = default_env()
        interpret("f←{⍵+1}", env)
        assert interpret("f -3", env) == S(-2)

    def test_named_fn_with_reverse(self) -> None:
        env = default_env()
        interpret("f←{⍵+1}", env)
        result = interpret("f ⌽⍳5", env)
        assert result == APLArray([5], [6, 5, 4, 3, 2])


class TestArrayNamesInDyadicContext:
    def test_array_dyadic_iota(self) -> None:
        env = default_env()
        interpret("data←10 20 30", env)
        assert interpret("data⍳20", env) == S(2)

    def test_array_dyadic_add(self) -> None:
        env = default_env()
        interpret("x←5", env)
        assert interpret("x+3", env) == S(8)

    def test_array_dyadic_rotate(self) -> None:
        env = default_env()
        interpret("v←1 2 3", env)
        result = interpret("2⌽v", env)
        assert result == APLArray([3], [3, 1, 2])


class TestFunctionsInsideDfns:
    def test_call_outer_fn_in_dfn(self) -> None:
        env = default_env()
        interpret("double←{⍵+⍵}", env)
        assert interpret("{double ⍵} 5", env) == S(10)

    def test_call_outer_fn_with_iota_in_dfn(self) -> None:
        env = default_env()
        interpret("double←{⍵+⍵}", env)
        result = interpret("{double ⍳⍵} 5", env)
        assert result == APLArray([5], [2, 4, 6, 8, 10])

    def test_nested_fn_calls(self) -> None:
        env = default_env()
        interpret("f←{⍵×2}", env)
        interpret("g←{f ⍵+1}", env)
        assert interpret("g 3", env) == S(8)


class TestDfnsWithDiamonds:
    def test_local_variable(self) -> None:
        env = default_env()
        interpret("f←{x←⍵+1⋄x×2}", env)
        assert interpret("f 5", env) == S(12)

    def test_multiple_locals(self) -> None:
        env = default_env()
        interpret("f←{a←⍵⋄b←a+1⋄a×b}", env)
        assert interpret("f 3", env) == S(12)

    def test_guard_with_diamond(self) -> None:
        env = default_env()
        interpret("f←{⍵>0:⍵⋄-⍵}", env)
        assert interpret("f ¯5", env) == S(5)


class TestFunctionsDefinedInDfns:
    def test_define_and_call_monadic_in_dfn(self) -> None:
        env = default_env()
        result = interpret("{g←{⍵+10}⋄g ⍵} 5", env)
        assert result == S(15)

    def test_define_and_call_dyadic_in_dfn(self) -> None:
        env = default_env()
        result = interpret("{add←{⍺+⍵}⋄3 add 4} 0", env)
        assert result == S(7)


class TestWithProducts:
    def test_fn_applied_to_inner_product(self) -> None:
        env = default_env()
        interpret("f←{⍵+1}", env)
        assert interpret("f 1 2 3+.×4 5 6", env) == S(33)

    def test_fn_applied_to_outer_product(self) -> None:
        env = default_env()
        interpret("double←{⍵+⍵}", env)
        result = interpret("double (⍳3)∘.×⍳3", env)
        assert result == APLArray([3, 3], [2, 4, 6, 4, 8, 12, 6, 12, 18])


class TestWithRankOperator:
    def test_named_fn_with_rank(self) -> None:
        env = default_env()
        interpret("double←{⍵+⍵}", env)
        result = interpret("(double⍤1) 2 3⍴⍳6", env)
        assert result == APLArray([2, 3], [2, 4, 6, 8, 10, 12])

    def test_sort_with_rank(self) -> None:
        env = default_env()
        interpret("sort←{⍵[⍋⍵]}", env)
        interpret("M←3 4⍴12 1 8 3 5 9 2 7 11 4 6 10", env)
        result = interpret("(sort⍤1) M", env)
        # Each row sorted: 1 3 8 12 | 2 5 7 9 | 4 6 10 11
        assert result == APLArray([3, 4], [1, 3, 8, 12, 2, 5, 7, 9, 4, 6, 10, 11])


class TestImportClassification:
    def test_imported_fn_no_parens(self) -> None:
        env = default_env()
        interpret("#import $::str::upper", env)
        result = interpret("upper 'hello'", env)
        assert result == APLArray([5], list("HELLO"))

    def test_imported_fn_with_alias_no_parens(self) -> None:
        env = default_env()
        interpret("#import $::str::upper as up", env)
        result = interpret("up 'hello'", env)
        assert result == APLArray([5], list("HELLO"))


class TestErrorCases:
    def test_undefined_name(self) -> None:
        from marple.errors import ValueError_
        env = default_env()
        with pytest.raises(ValueError_):
            interpret("nosuchvar", env)
