"""Test that APL's right-to-left evaluation order is correct.

In APL, the right argument of a dyadic function is always
evaluated before the left argument.
"""
from marple.arraymodel import APLArray, S
from marple.interpreter import interpret, default_env


class TestDyadicEvalOrder:
    def test_outer_product_with_assignment(self) -> None:
        # z∘.×z←⍳5 should assign z then use it on both sides
        env = default_env()
        result = interpret("z∘.×z←⍳5", env)
        assert result.shape == [5, 5]
        assert result.data[0] == 1   # 1×1
        assert result.data[4] == 5   # 1×5
        assert result.data[24] == 25 # 5×5

    def test_inner_product_with_assignment(self) -> None:
        env = default_env()
        result = interpret("v+.×v←⍳3", env)
        # v←1 2 3, then v+.×v = 1+4+9 = 14
        assert result == S(14)

    def test_dyadic_func_with_assignment(self) -> None:
        env = default_env()
        result = interpret("x+x←5", env)
        assert result == S(10)

    def test_dyadic_dfn_with_assignment(self) -> None:
        env = default_env()
        result = interpret("x{⍺+⍵}x←3", env)
        assert result == S(6)
