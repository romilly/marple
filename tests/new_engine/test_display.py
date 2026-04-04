"""Display formatting tests — new engine."""

from marple.engine import Interpreter
from marple.formatting import format_result


class TestQuadPPDisplay:
    def test_pp_affects_format_result(self) -> None:
        i = Interpreter(io=1)
        i.run("⎕PP←17")
        result = i.run("0.1+0.2")
        text = format_result(result, i.env)
        assert "0.3000000000000000" in text

    def test_default_pp_rounds(self) -> None:
        i = Interpreter(io=1)
        result = i.run("0.1+0.2")
        text = format_result(result, i.env)
        assert text == "0.3"


class TestCharacterDisplay:
    def test_char_vector_no_spaces(self) -> None:
        result = Interpreter(io=1).run("'HELLO'")
        assert format_result(result) == "HELLO"

    def test_char_matrix_no_spaces(self) -> None:
        result = Interpreter(io=1).run("2 3⍴'CATDOG'")
        assert format_result(result) == "CAT\nDOG"

    def test_numeric_vector_with_spaces(self) -> None:
        result = Interpreter(io=1).run("1 2 3")
        assert format_result(result) == "1 2 3"


class TestNumericMatrixDisplay:
    def test_columns_right_aligned(self) -> None:
        result = Interpreter(io=1).run("2 3∘.÷6 9 2")
        lines = format_result(result).split("\n")
        assert len(lines) == 2
        assert len(lines[0]) == len(lines[1])

    def test_integer_matrix_aligned(self) -> None:
        result = Interpreter(io=1).run("2 3⍴1 20 300 4 50 600")
        lines = format_result(result).split("\n")
        assert lines[0] == "1 20 300"
        assert lines[1] == "4 50 600"

    def test_float_matrix_truncated(self) -> None:
        result = Interpreter(io=1).run("÷ 2 3⍴⍳5")
        lines = format_result(result).split("\n")
        assert len(lines[0]) < 30
        assert "0.3333333333" in lines[0]
        assert "0.33333333333" not in lines[0]

    def test_float_whole_number_no_decimal(self) -> None:
        result = Interpreter(io=1).run("÷1")
        assert format_result(result) == "1"
