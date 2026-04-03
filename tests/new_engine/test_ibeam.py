"""I-beam (Python integration) tests — new engine."""

import pytest

from marple.arraymodel import APLArray, S
from marple.engine import Interpreter


class TestIBeamBasic:
    def test_monadic_ibeam(self) -> None:
        result = Interpreter(io=1).run("(⌶'marple.stdlib.str_impl.upper') 'hello'")
        assert result == APLArray.array([5], list("HELLO"))

    def test_monadic_ibeam_trim(self) -> None:
        result = Interpreter(io=1).run("(⌶'marple.stdlib.str_impl.trim') '  hi  '")
        assert result == APLArray.array([2], list("hi"))

    def test_monadic_ibeam_lower(self) -> None:
        result = Interpreter(io=1).run("(⌶'marple.stdlib.str_impl.lower') 'HELLO'")
        assert result == APLArray.array([5], list("hello"))

    def test_ibeam_assigned(self) -> None:
        i = Interpreter(io=1)
        i.run("up←⌶'marple.stdlib.str_impl.upper'")
        result = i.run("up 'world'")
        assert result == APLArray.array([5], list("WORLD"))


class TestIBeamErrors:
    def test_bad_module(self) -> None:
        with pytest.raises(Exception, match="DOMAIN ERROR"):
            Interpreter(io=1).run("(⌶'nonexistent.module.func') 5")

    def test_bad_function(self) -> None:
        with pytest.raises(Exception, match="DOMAIN ERROR"):
            Interpreter(io=1).run("(⌶'marple.stdlib.str_impl.nonexistent') 'hi'")
