"""Tests for the Beside (∘) operator — function composition.

    (f∘g) ω  ≡  f (g ω)                 (monadic form)
    α (f∘g) ω ≡  α f (g ω)              (dyadic form)

`g` is always applied monadically; `f`'s valence follows the
valence of the derived function.
"""

import pytest

from marple.engine import Interpreter
from marple.numpy_array import APLArray, S


class TestBesideMonadic:
    """`(f∘g) ω  ≡  f (g ω)`."""

    def test_shape_of_shape(self) -> None:
        """`⍴∘⍴ ω` — the (1-element vector) rank via shape-of-shape.
        `⍴` always returns a vector, so `⍴⍴ω` returns a 1-element
        vector containing the rank of ω.

        The usual APL idiom is `RANK ← ⍴∘⍴` then `RANK ω`, but
        storing derived functions in variables is a pre-existing
        bug in MARPLE — test the composition directly instead.
        """
        i = Interpreter(io=1)
        # `⍴'abc'` = ,3 (shape [1]); `⍴,3` = ,1 (shape [1])
        assert i.run("⍴∘⍴ 'abc'") == APLArray.array([1], [1])
        # `⍴2 3⍴⍳6` = 2 3 (shape [2]); `⍴2 3` = ,2 (shape [1])
        assert i.run("⍴∘⍴ 2 3⍴⍳6") == APLArray.array([1], [2])
        # `⍴2 3 4⍴⍳24` = 2 3 4 (shape [3]); `⍴2 3 4` = ,3 (shape [1])
        assert i.run("⍴∘⍴ 2 3 4⍴⍳24") == APLArray.array([1], [3])

    def test_sum_of_iota(self) -> None:
        """`+/∘⍳ N` — sum of 1..N."""
        result = Interpreter(io=1).run("+/∘⍳ 100")
        assert result == S(5050)

    def test_neg_of_abs(self) -> None:
        """`-∘| ω` — negate the absolute value."""
        result = Interpreter(io=1).run("-∘| ¯3 4 ¯5")
        assert result == APLArray.array([3], [-3, -4, -5])

    def test_reverse_of_iota(self) -> None:
        """`⌽∘⍳ N` — descending sequence."""
        result = Interpreter(io=1).run("⌽∘⍳ 5")
        assert result == APLArray.array([5], [5, 4, 3, 2, 1])


class TestBesideDyadic:
    """`α (f∘g) ω  ≡  α f (g ω)`."""

    def test_plus_of_reciprocal(self) -> None:
        """`X +∘÷ Y` ≡ `X + ÷Y`. `1 +∘÷ 1` = `1 + ÷1` = 2."""
        result = Interpreter(io=1).run("1 +∘÷ 1")
        assert result == S(2)

    def test_prepend_iota(self) -> None:
        """`0 ,∘⍳ N` ≡ `0 , ⍳N` — prepend zero to 1..N."""
        result = Interpreter(io=1).run("0 ,∘⍳ 5")
        assert result == APLArray.array([6], [0, 1, 2, 3, 4, 5])

    def test_dyadic_with_reverse(self) -> None:
        """`X -∘⌽ Y` ≡ `X - ⌽Y`."""
        result = Interpreter(io=1).run("1 2 3 -∘⌽ 10 20 30")
        # X − ⌽Y = 1 2 3 − 30 20 10 = ¯29 ¯18 ¯7
        assert result == APLArray.array([3], [-29, -18, -7])


class TestBesideWithUserFunctions:
    """Beside must work with user-defined dfns on either side."""

    def test_dfn_as_g(self) -> None:
        i = Interpreter(io=1)
        i.run("double←{2×⍵}")
        result = i.run("+/∘double 1 2 3 4")
        # double → 2 4 6 8; +/ → 20
        assert result == S(20)

    def test_dfn_as_f(self) -> None:
        i = Interpreter(io=1)
        i.run("sumpair←{⍺+⍵}")
        # α sumpair∘⌽ ω = α + ⌽ω
        result = i.run("1 2 3 sumpair∘⌽ 10 20 30")
        assert result == APLArray.array([3], [31, 22, 13])


class TestBesideCombinations:
    """Beside nested with other operators already supported."""

    def test_beside_inside_rank(self) -> None:
        """`(+/∘⍳)⍤0` applied to each scalar — "triangular number".
        Exercises the executor's nested-operator dispatch for
        `BoundOperator('∘', ...)` inside a rank-derived function.
        """
        result = Interpreter(io=1).run("((+/∘⍳)⍤0) 1 2 3 4 5")
        # For each n: +/⍳n = 1+2+...+n = n(n+1)/2
        assert result == APLArray.array([5], [1, 3, 6, 10, 15])


class TestBesideValueBind:
    """Dyalog ∘ overloads on operand kind:

      f∘B  →  (f∘B) ω ≡ ω f B   (right-bind)
      A∘g  →  (A∘g) ω ≡ A g ω   (left-bind)

    Bind consumes the dyadic valence; dyadic application of a
    bound form raises SYNTAX ERROR (matches Dyalog).
    Both operands as values (e.g. `2∘3`) is also a SYNTAX ERROR.
    """

    def test_right_bind_scalar(self) -> None:
        """`(+∘1) 5 ≡ 5 + 1 = 6`."""
        assert Interpreter(io=1).run("(+∘1) 5") == S(6)

    def test_right_bind_vector_omega(self) -> None:
        """`(+∘1) 1 2 3 ≡ 1 2 3 + 1`."""
        assert Interpreter(io=1).run("(+∘1) 1 2 3") == APLArray.array([3], [2, 3, 4])

    def test_left_bind_scalar(self) -> None:
        """`(10∘-) 3 ≡ 10 - 3 = 7`."""
        assert Interpreter(io=1).run("(10∘-) 3") == S(7)

    def test_left_bind_with_plus(self) -> None:
        """`(1∘+) 5 ≡ 1 + 5 = 6`."""
        assert Interpreter(io=1).run("(1∘+) 5") == S(6)

    def test_right_bind_stored(self) -> None:
        """`f ← +∘1` then `f 5` round-trips through env."""
        i = Interpreter(io=1)
        i.run("f←+∘1")
        assert i.run("f 5") == S(6)

    def test_left_bind_stored(self) -> None:
        """`g ← 10∘-` then `g 3` round-trips through env."""
        i = Interpreter(io=1)
        i.run("g←10∘-")
        assert i.run("g 3") == S(7)

    def test_dyadic_application_of_bound_form_is_syntax_error(self) -> None:
        """Bind consumes the dyadic valence; `5 (+∘1) 3` is invalid."""
        from marple.errors import SyntaxError_
        with pytest.raises(SyntaxError_):
            Interpreter(io=1).run("5 (+∘1) 3")

    # Note: `2∘3` (both operands values) is also a syntax error in
    # Dyalog, but marple's parser fails earlier with an AssertionError
    # before reaching `BesideConjunction.derive_dyadic`. That's a
    # pre-existing parser gap (independent of value-bind support);
    # not covered here.
