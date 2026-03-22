from marple.arraymodel import APLArray, S
from marple.interpreter import interpret
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
        # Single colon in dfn guard should still be GUARD
        tokens = Tokenizer("x:42").tokenize()
        assert tokens[0] == Token(TokenType.ID, "x")
        assert tokens[1] == Token(TokenType.GUARD, ":")

    def test_qualified_in_expression(self) -> None:
        tokens = Tokenizer("$::str::upper 'hello'").tokenize()
        assert tokens[0] == Token(TokenType.QUALIFIED_NAME, "$::str::upper")
        assert tokens[1] == Token(TokenType.STRING, "hello")


class TestNamespaceExecution:
    def test_system_str_upper(self) -> None:
        result = interpret("$::str::upper 'hello'")
        assert result == APLArray([5], list("HELLO"))

    def test_system_str_lower(self) -> None:
        result = interpret("$::str::lower 'HELLO'")
        assert result == APLArray([5], list("hello"))

    def test_system_str_trim(self) -> None:
        result = interpret("$::str::trim '  hi  '")
        assert result == APLArray([2], list("hi"))


class TestImport:
    def test_import_function(self) -> None:
        env: dict[str, object] = {}
        interpret("#import $::str::upper", env)
        result = interpret("upper 'hello'", env)
        assert result == APLArray([5], list("HELLO"))

    def test_import_with_alias(self) -> None:
        env: dict[str, object] = {}
        interpret("#import $::str::upper as up", env)
        result = interpret("up 'hello'", env)
        assert result == APLArray([5], list("HELLO"))
