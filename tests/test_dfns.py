from marple.arraymodel import APLArray, S
from marple.interpreter import interpret, default_env


class TestBasicDfns:
    def test_identity(self) -> None:
        # {⍵}5 → 5
        assert interpret("{⍵}5") == S(5)

    def test_double(self) -> None:
        # {⍵+⍵}3 → 6
        assert interpret("{⍵+⍵}3") == S(6)

    def test_negate_dfn(self) -> None:
        # {-⍵}5 → ¯5
        assert interpret("{-⍵}5") == S(-5)

    def test_dfn_with_vector(self) -> None:
        # {⍵+1}1 2 3 → 2 3 4
        assert interpret("{⍵+1}1 2 3") == APLArray([3], [2, 3, 4])


class TestNamedDfns:
    def test_named_dfn(self) -> None:
        env = default_env()
        interpret("double←{⍵+⍵}", env)
        assert interpret("double 3", env) == S(6)

    def test_named_dfn_with_vector(self) -> None:
        env = default_env()
        interpret("inc←{⍵+1}", env)
        assert interpret("inc 1 2 3", env) == APLArray([3], [2, 3, 4])


class TestDyadicDfns:
    def test_dyadic_dfn(self) -> None:
        # 3{⍺+⍵}4 → 7
        assert interpret("3{⍺+⍵}4") == S(7)

    def test_named_dyadic(self) -> None:
        env = default_env()
        interpret("avg←{(⍺+⍵)÷2}", env)
        assert interpret("3 avg 5", env) == S(4.0)

    def test_named_dyadic_with_variable_left_arg(self) -> None:
        env = default_env()
        interpret("add←{⍺+⍵}", env)
        interpret("x←10", env)
        assert interpret("x add 5", env) == S(15)

    def test_named_dyadic_with_parenthesized_left_arg(self) -> None:
        env = default_env()
        interpret("add←{⍺+⍵}", env)
        assert interpret("(2+3) add 5", env) == S(10)


class TestGuards:
    def test_single_guard(self) -> None:
        # {⍵=0 : 42 ⋄ ⍵}0 → 42
        assert interpret("{⍵=0:42⋄⍵}0") == S(42)

    def test_guard_falls_through(self) -> None:
        # {⍵=0 : 42 ⋄ ⍵}5 → 5
        assert interpret("{⍵=0:42⋄⍵}5") == S(5)

    def test_multiple_guards(self) -> None:
        env = default_env()
        interpret("sign←{⍵>0:1⋄⍵<0:¯1⋄0}", env)
        assert interpret("sign 5", env) == S(1)
        assert interpret("sign ¯3", env) == S(-1)
        assert interpret("sign 0", env) == S(0)


class TestRecursion:
    def test_factorial(self) -> None:
        env = default_env()
        interpret("fact←{⍵≤1:1⋄⍵×∇ ⍵-1}", env)
        assert interpret("fact 5", env) == S(120)

    def test_fibonacci(self) -> None:
        env = default_env()
        interpret("fib←{⍵=0:0⋄⍵=1:1⋄(∇ ⍵-1)+∇ ⍵-2}", env)
        assert interpret("fib 6", env) == S(8)


class TestDefaultAlpha:
    def test_default_alpha_monadic(self) -> None:
        env = default_env()
        interpret("pad←{⍺←0⋄⍺,⍵}", env)
        assert interpret("pad 1 2 3", env) == APLArray([4], [0, 1, 2, 3])

    def test_default_alpha_overridden(self) -> None:
        env = default_env()
        interpret("pad←{⍺←0⋄⍺,⍵}", env)
        assert interpret("9 pad 1 2 3", env) == APLArray([4], [9, 1, 2, 3])


class TestMultiStatementDfns:
    def test_diamond_separated(self) -> None:
        env = default_env()
        interpret("sign←{⍵>0:1 ⋄ ⍵<0:¯1 ⋄ 0}", env)
        assert interpret("sign 5", env) == S(1)
        assert interpret("sign ¯3", env) == S(-1)
        assert interpret("sign 0", env) == S(0)

    def test_newline_separated(self) -> None:
        env = default_env()
        # Newlines converted to diamonds by the REPL/script runner,
        # but interpret() handles diamonds directly
        interpret("abs←{⍵<0:-⍵\n⍵}", env)
        assert interpret("abs ¯7", env) == S(7)
        assert interpret("abs 3", env) == S(3)

    def test_multi_guard_with_assignment(self) -> None:
        env = default_env()
        interpret("classify←{r←'zero' ⋄ ⍵>0:r←'positive' ⋄ ⍵<0:r←'negative' ⋄ r}", env)
        result = interpret("classify 5", env)
        assert "".join(str(c) for c in result.data) == "positive"

    def test_cr_multi_statement(self) -> None:
        env = default_env()
        interpret("sign←{⍵>0:1 ⋄ ⍵<0:¯1 ⋄ 0}", env)
        result = interpret("⎕CR 'sign'", env)
        text = "".join(str(c) for c in result.data)
        assert "⋄" in text
        assert "sign←{" in text

    def test_fx_multi_statement(self) -> None:
        env = default_env()
        interpret("⎕FX 'clamp←{⍵>100:100 ⋄ ⍵<0:0 ⋄ ⍵}'", env)
        assert interpret("clamp 150", env) == S(100)
        assert interpret("clamp ¯5", env) == S(0)
        assert interpret("clamp 50", env) == S(50)

    def test_cr_fx_round_trip_multi(self) -> None:
        env = default_env()
        interpret("sign←{⍵>0:1 ⋄ ⍵<0:¯1 ⋄ 0}", env)
        src = interpret("⎕CR 'sign'", env)
        text = "".join(str(c) for c in src.data)
        new_text = text.replace("sign", "sgn", 1)
        interpret("⎕FX '" + new_text + "'", env)
        assert interpret("sgn 5", env) == S(1)
        assert interpret("sgn ¯3", env) == S(-1)


class TestDopApplication:
    """Tests for direct operator (dop) application."""

    # ── Monadic dop with function operand ──

    def test_simple_dop_with_dfn_operand(self) -> None:
        env = default_env()
        interpret("twice←{⍺⍺ ⍺⍺ ⍵}", env)
        interpret("double←{⍵+⍵}", env)
        assert interpret("(double) twice 3", env) == S(12)

    def test_dop_with_negate(self) -> None:
        env = default_env()
        interpret("twice←{⍺⍺ ⍺⍺ ⍵}", env)
        # Negate twice: -(-5) = 5
        assert interpret("(-) twice 5", env) == S(5)

    def test_dop_with_reciprocal(self) -> None:
        env = default_env()
        interpret("twice←{⍺⍺ ⍺⍺ ⍵}", env)
        # Reciprocal twice: ÷(÷4) = 4
        assert interpret("(÷) twice 4", env) == S(4)

    def test_dop_with_iota(self) -> None:
        env = default_env()
        interpret("apply←{⍺⍺ ⍵}", env)
        result = interpret("(⍳) apply 5", env)
        assert result == APLArray([5], [1, 2, 3, 4, 5])

    # ── Monadic dop with array operand ──

    def test_dop_with_array_operand(self) -> None:
        env = default_env()
        interpret("addop←{⍺⍺+⍵}", env)
        assert interpret("(10) addop 5", env) == S(15)

    def test_dop_array_operand_vector(self) -> None:
        env = default_env()
        interpret("scale←{⍺⍺×⍵}", env)
        result = interpret("(2) scale 1 2 3", env)
        assert list(result.data) == [2, 4, 6]

    # ── Multi-statement dop ──

    def test_multi_statement_dop(self) -> None:
        env = default_env()
        interpret("apply_twice←{t←⍺⍺ ⍵ ⋄ ⍺⍺ t}", env)
        interpret("double←{⍵+⍵}", env)
        assert interpret("(double) apply_twice 3", env) == S(12)

    def test_dop_with_guard(self) -> None:
        env = default_env()
        interpret("safe←{⍵=0:0 ⋄ ⍺⍺ ⍵}", env)
        assert interpret("(÷) safe 4", env) == S(0.25)
        assert interpret("(÷) safe 0", env) == S(0)

    # ── Dop producing derived function used dyadically ──

    # ── Dop composing with other functions ──

    def test_dop_compose(self) -> None:
        env = default_env()
        interpret("apply←{⍺⍺ ⍵}", env)
        interpret("sum←{+/⍵}", env)
        assert interpret("(sum) apply ⍳10", env) == S(55)

    # ── ⎕NC and ⎕CR for dops ──

    def test_nc_dop(self) -> None:
        env = default_env()
        interpret("twice←{⍺⍺ ⍺⍺ ⍵}", env)
        assert interpret("⎕NC 'twice'", env) == S(4)

    def test_cr_dop(self) -> None:
        env = default_env()
        interpret("twice←{⍺⍺ ⍺⍺ ⍵}", env)
        result = interpret("⎕CR 'twice'", env)
        text = "".join(str(c) for c in result.data)
        assert "⍺⍺" in text

    def test_fx_dop(self) -> None:
        env = default_env()
        interpret("⎕FX 'twice←{⍺⍺ ⍺⍺ ⍵}'", env)
        assert interpret("⎕NC 'twice'", env) == S(4)

    # ── Error cases ──

    def test_alpha_alpha_outside_dop(self) -> None:
        import pytest
        from marple.errors import ValueError_
        with pytest.raises(ValueError_):
            interpret("{⍺⍺+⍵} 5")  # dfn used as dfn, but body has ⍺⍺
