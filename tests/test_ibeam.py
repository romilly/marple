import os
import tempfile

import pytest

from marple.arraymodel import APLArray, S
from marple.interpreter import interpret, default_env


class TestIBeamBasic:
    def test_monadic_ibeam(self) -> None:
        result = interpret("(⌶'marple.stdlib.str_impl.upper') 'hello'")
        assert result == APLArray([5], list("HELLO"))

    def test_monadic_ibeam_trim(self) -> None:
        result = interpret("(⌶'marple.stdlib.str_impl.trim') '  hi  '")
        assert result == APLArray([2], list("hi"))

    def test_monadic_ibeam_lower(self) -> None:
        result = interpret("(⌶'marple.stdlib.str_impl.lower') 'HELLO'")
        assert result == APLArray([5], list("hello"))

    def test_ibeam_assigned(self) -> None:
        env = default_env()
        interpret("up←⌶'marple.stdlib.str_impl.upper'", env)
        result = interpret("up 'world'", env)
        assert result == APLArray([5], list("WORLD"))


class TestIBeamIO:
    def test_nread(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("hello world")
            path = f.name
        try:
            result = interpret(f"(⌶'marple.stdlib.io_impl.nread') '{path}'")
            assert result == APLArray([11], list("hello world"))
        finally:
            os.unlink(path)

    def test_dyadic_nwrite(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            path = f.name
        try:
            interpret(f"'test data' (⌶'marple.stdlib.io_impl.nwrite') '{path}'")
            with open(path) as f:
                assert f.read() == "test data"
        finally:
            os.unlink(path)


class TestIBeamErrors:
    def test_bad_module(self) -> None:
        with pytest.raises(Exception, match="DOMAIN ERROR"):
            interpret("(⌶'nonexistent.module.func') 5")

    def test_bad_function(self) -> None:
        with pytest.raises(Exception, match="DOMAIN ERROR"):
            interpret("(⌶'marple.stdlib.str_impl.nonexistent') 'hi'")
