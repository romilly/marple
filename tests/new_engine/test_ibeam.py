"""I-beam (Python integration) tests — new engine."""

import pytest

from marple.backend_functions import chars_to_str
from marple.numpy_array import APLArray, S
from marple.engine import Interpreter


class TestIBeamBasic:
    def test_monadic_ibeam(self) -> None:
        result = Interpreter(io=1).run("(⌶'marple.stdlib.str_impl.upper') 'hello'")
        assert chars_to_str(result.data) == "HELLO"

    def test_monadic_ibeam_trim(self) -> None:
        result = Interpreter(io=1).run("(⌶'marple.stdlib.str_impl.trim') '  hi  '")
        assert chars_to_str(result.data) == "hi"

    def test_monadic_ibeam_lower(self) -> None:
        result = Interpreter(io=1).run("(⌶'marple.stdlib.str_impl.lower') 'HELLO'")
        assert chars_to_str(result.data) == "hello"

    def test_ibeam_assigned(self) -> None:
        i = Interpreter(io=1)
        i.run("up←⌶'marple.stdlib.str_impl.upper'")
        result = i.run("up 'world'")
        assert chars_to_str(result.data) == "WORLD"


class TestIBeamErrors:
    def test_bad_module(self) -> None:
        with pytest.raises(Exception, match="DOMAIN ERROR"):
            Interpreter(io=1).run("(⌶'nonexistent.module.func') 5")

    def test_bad_function(self) -> None:
        with pytest.raises(Exception, match="DOMAIN ERROR"):
            Interpreter(io=1).run("(⌶'marple.stdlib.str_impl.nonexistent') 'hi'")
