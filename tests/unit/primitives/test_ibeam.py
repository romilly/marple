"""I-beam tests — new engine.

⌶ is a monadic operator whose left operand is an integer selecting a
built-in service: (A⌶)Y applies service A to Y.
"""

import pytest

from marple.ports.array import APLArray, S
from marple.engine import Interpreter
from marple.errors import DomainError


class TestIBeamBasic:
    def test_upper_via_ibeam(self) -> None:
        result = Interpreter(io=1).run("(100⌶) 'hello'")
        assert result.as_str() == "HELLO"

    def test_lower_via_ibeam(self) -> None:
        result = Interpreter(io=1).run("(101⌶) 'HELLO'")
        assert result.as_str() == "hello"

    def test_trim_via_ibeam(self) -> None:
        result = Interpreter(io=1).run("(102⌶) '  hi  '")
        assert result.as_str() == "hi"

    def test_ibeam_assigned(self) -> None:
        i = Interpreter(io=1)
        i.run("up←100⌶")
        result = i.run("up 'world'")
        assert result.as_str() == "WORLD"


class TestIBeamErrors:
    def test_unknown_code_raises(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("(9999⌶) 5")
