"""Namespace and import tests — new engine."""

from marple.arraymodel import APLArray, S
from marple.engine import Interpreter


class TestNamespaceExecution:
    def test_system_str_upper(self) -> None:
        result = Interpreter(io=1).run("$::str::upper 'hello'")
        assert "".join(str(c) for c in result.data) == "HELLO"

    def test_system_str_lower(self) -> None:
        result = Interpreter(io=1).run("$::str::lower 'HELLO'")
        assert "".join(str(c) for c in result.data) == "hello"


class TestImport:
    def test_import_function(self) -> None:
        i = Interpreter(io=1)
        i.run("#import $::str::upper")
        result = i.run("upper 'hello'")
        assert "".join(str(c) for c in result.data) == "HELLO"

    def test_import_with_alias(self) -> None:
        i = Interpreter(io=1)
        i.run("#import $::str::upper as up")
        result = i.run("up 'hello'")
        assert "".join(str(c) for c in result.data) == "HELLO"
