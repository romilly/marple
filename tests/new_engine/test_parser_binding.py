"""Parser binding precedence tests — new engine."""

from marple.arraymodel import APLArray, S
from marple.engine import Interpreter


class TestReduceWithDfnOperand:
    def test_dfn_reduce(self) -> None:
        assert Interpreter(io=1).run("{⍺+⍵}/⍳5") == S(15)

    def test_dfn_scan(self) -> None:
        assert Interpreter(io=1).run("{⍺+⍵}\\1 2 3") == APLArray([3], [1, 3, 6])


class TestConjunctionBindsPrecedence:
    def test_rank_binds_before_subtract(self) -> None:
        i = Interpreter(io=1)
        i.run("a←5")
        result = i.run(",⍤0 -a")
        assert result == APLArray([1], [-5])
