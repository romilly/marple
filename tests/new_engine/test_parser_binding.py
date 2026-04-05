"""Parser binding precedence tests — new engine."""

import pytest

from marple.numpy_array import APLArray, S
from marple.engine import Interpreter
from marple.errors import DomainError


class TestReduceWithDfnOperand:
    def test_dfn_reduce_raises_domain_error(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("{⍺+⍵}/⍳5")

    def test_dfn_scan_raises_domain_error(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("{⍺+⍵}\\1 2 3")


class TestConjunctionBindsPrecedence:
    def test_rank_binds_before_subtract(self) -> None:
        i = Interpreter(io=1)
        i.run("a←5")
        result = i.run(",⍤0 -a")
        assert result == APLArray.array([1], [-5])
