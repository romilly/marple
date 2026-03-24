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
