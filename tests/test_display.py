from marple.arraymodel import APLArray, S
from marple.interpreter import interpret, default_env
from marple.repl import format_result


class TestQuadPPDisplay:
    def test_pp_affects_format_result(self) -> None:
        env = default_env()
        interpret("⎕PP←17", env)
        result = interpret("0.1+0.2", env)
        text = format_result(result, env)
        # With 17 digits, the float imprecision is visible
        assert "0.3000000000000000" in text

    def test_default_pp_rounds(self) -> None:
        result = interpret("0.1+0.2")
        text = format_result(result)
        assert text == "0.3"


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


class TestNumericMatrixDisplay:
    def test_columns_right_aligned(self) -> None:
        from marple.repl import format_result
        # 2 3 ∘.÷ 6 9 2 produces a matrix where columns have varying widths
        result = interpret("2 3∘.÷6 9 2")
        lines = format_result(result).split("\n")
        # Each column should be right-aligned
        # Column widths should match the widest element in each column
        assert len(lines) == 2
        # All lines should be the same length (right-padded)
        assert len(lines[0]) == len(lines[1])

    def test_integer_matrix_aligned(self) -> None:
        from marple.repl import format_result
        result = interpret("2 3⍴1 20 300 4 50 600")
        lines = format_result(result).split("\n")
        assert lines[0] == "1 20 300"
        assert lines[1] == "4 50 600"

    def test_float_matrix_truncated(self) -> None:
        from marple.repl import format_result
        result = interpret("÷ 2 3⍴⍳5")
        lines = format_result(result).split("\n")
        # Should not have 16-digit floats
        assert len(lines[0]) < 30
        # 0.3333333333 (10 sig digits) not 0.3333333333333333
        assert "0.3333333333" in lines[0]
        assert "0.33333333333" not in lines[0]

    def test_float_whole_number_no_decimal(self) -> None:
        from marple.repl import format_result
        result = interpret("÷1")
        assert format_result(result) == "1"
