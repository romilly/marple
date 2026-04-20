"""Right-to-left evaluation order tests — new engine."""

from marple.ports.array import APLArray, S
from marple.engine import Interpreter


class TestDyadicEvalOrder:
    def test_outer_product_with_assignment(self) -> None:
        i = Interpreter(io=1)
        result = i.run("z∘.×z←⍳5")
        assert result.shape == [5, 5]
        assert result.data[0, 0] == 1
        assert result.data[4, 4] == 25

    def test_inner_product_with_assignment(self) -> None:
        i = Interpreter(io=1)
        result = i.run("v+.×v←⍳3")
        assert result == S(14)

    def test_dyadic_func_with_assignment(self) -> None:
        i = Interpreter(io=1)
        result = i.run("x+x←5")
        assert result == S(10)

    def test_dyadic_dfn_with_assignment(self) -> None:
        i = Interpreter(io=1)
        result = i.run("x{⍺+⍵}x←3")
        assert result == S(6)
