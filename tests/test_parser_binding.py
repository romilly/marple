"""Tests for correct operator binding precedence (Iverson's algorithm).

These tests verify that operators bind tighter than functions,
following the rules in Iverson's Dictionary of APL.
"""
from marple.arraymodel import APLArray, S
from marple.interpreter import interpret, default_env


class TestReduceWithDfnOperand:
    """Dfn followed by / should be reduce, not replicate."""

    def test_dfn_reduce(self) -> None:
        # {⍺+⍵}/⍳5 → reduce with add: 1+2+3+4+5 = 15
        assert interpret("{⍺+⍵}/⍳5") == S(15)

    def test_dfn_scan(self) -> None:
        # {⍵+⍵}\1 2 3 → scan with double: 2 8 24... no.
        # Actually scan with {⍵+⍵}: scan applies fn dyadically,
        # so {⍺+⍵}\1 2 3 would be better. Let's use identity:
        # {⍺+⍵}\1 2 3 → 1 3 6
        assert interpret("{⍺+⍵}\\1 2 3") == APLArray([3], [1, 3, 6])


class TestConjunctionBindsPrecedence:
    """Conjunction (⍤) should grab its right operand before - can."""

    def test_rank_binds_before_subtract(self) -> None:
        env = default_env()
        interpret("a←5", env)
        # ,⍤0 applied to -a: ravel each scalar of (-5)
        # The key: ⍤ grabs 0 before - can claim it
        result = interpret(",⍤0 -a", env)
        # ,⍤0 on scalar ¯5 → 1-element vector [¯5]
        assert result == APLArray([1], [-5])
