"""I-beam tests — new engine.

⌶ is a monadic operator whose left operand is an integer selecting a
built-in service: (A⌶)Y applies service A to Y.
"""

import pytest

from marple.backend_functions import chars_to_str
from marple.numpy_array import APLArray, S
from marple.engine import Interpreter
from marple.errors import DomainError


class TestIBeamBasic:
    def test_upper_via_ibeam(self) -> None:
        result = Interpreter(io=1).run("(100⌶) 'hello'")
        assert chars_to_str(result.data) == "HELLO"

    def test_lower_via_ibeam(self) -> None:
        result = Interpreter(io=1).run("(101⌶) 'HELLO'")
        assert chars_to_str(result.data) == "hello"

    def test_trim_via_ibeam(self) -> None:
        result = Interpreter(io=1).run("(102⌶) '  hi  '")
        assert chars_to_str(result.data) == "hi"

    def test_ibeam_assigned(self) -> None:
        i = Interpreter(io=1)
        i.run("up←100⌶")
        result = i.run("up 'world'")
        assert chars_to_str(result.data) == "WORLD"


class TestIBeamErrors:
    def test_unknown_code_raises(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("(9999⌶) 5")
