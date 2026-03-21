from marple.arraymodel import APLArray, S
from marple.interpreter import interpret


class TestCharacterDisplay:
    def test_char_vector_no_spaces(self) -> None:
        from marple.repl import format_result
        result = interpret("'HELLO'")
        assert format_result(result) == "HELLO"

    def test_char_matrix_no_spaces(self) -> None:
        from marple.repl import format_result
        result = interpret("2 3⍴'CATDOG'")
        assert format_result(result) == "CAT\nDOG"

    def test_numeric_vector_with_spaces(self) -> None:
        from marple.repl import format_result
        result = interpret("1 2 3")
        assert format_result(result) == "1 2 3"
