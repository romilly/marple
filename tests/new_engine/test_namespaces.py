"""Namespace and import tests — new engine."""

from marple.numpy_array import APLArray, S
from marple.engine import Interpreter
from marple.tokenizer import Token, TokenType, Tokenizer


class TestQualifiedNameTokenization:
    def test_simple_qualified(self) -> None:
        tokens = Tokenizer("utils::trim").tokenize()
        assert tokens[0] == Token(TokenType.QUALIFIED_NAME, "utils::trim")

    def test_triple_qualified(self) -> None:
        tokens = Tokenizer("math::stats::mean").tokenize()
        assert tokens[0] == Token(TokenType.QUALIFIED_NAME, "math::stats::mean")

    def test_system_workspace(self) -> None:
        tokens = Tokenizer("$::io::nread").tokenize()
        assert tokens[0] == Token(TokenType.QUALIFIED_NAME, "$::io::nread")

    def test_guard_not_affected(self) -> None:
        tokens = Tokenizer("x:42").tokenize()
        assert tokens[0] == Token(TokenType.ID, "x")
        assert tokens[1] == Token(TokenType.GUARD, ":")

    def test_qualified_in_expression(self) -> None:
        tokens = Tokenizer("$::str::upper 'hello'").tokenize()
        assert tokens[0] == Token(TokenType.QUALIFIED_NAME, "$::str::upper")
        assert tokens[1] == Token(TokenType.STRING, "hello")


class TestNamespaceExecution:
    def test_system_str_upper(self) -> None:
        from marple.backend_functions import chars_to_str
        result = Interpreter(io=1).run("$::str::upper 'hello'")
        assert chars_to_str(result.data) == "HELLO"

    def test_system_str_lower(self) -> None:
        from marple.backend_functions import chars_to_str
        result = Interpreter(io=1).run("$::str::lower 'HELLO'")
        assert chars_to_str(result.data) == "hello"

    def test_system_str_trim(self) -> None:
        from marple.backend_functions import chars_to_str
        result = Interpreter(io=1).run("$::str::trim '  hi  '")
        assert result.shape == [2]
        assert chars_to_str(result.data) == "hi"


class TestImport:
    def test_import_function(self) -> None:
        from marple.backend_functions import chars_to_str
        i = Interpreter(io=1)
        i.run("#import $::str::upper")
        result = i.run("upper 'hello'")
        assert chars_to_str(result.data) == "HELLO"

    def test_import_with_alias(self) -> None:
        from marple.backend_functions import chars_to_str
        i = Interpreter(io=1)
        i.run("#import $::str::upper as up")
        result = i.run("up 'hello'")
        assert chars_to_str(result.data) == "HELLO"
