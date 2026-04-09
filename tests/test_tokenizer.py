from marple.tokenizer import Token, TokenType, Tokenizer


class TestTokenizerNumbers:
    def test_single_integer(self) -> None:
        tokens = Tokenizer("5").tokenize()
        assert tokens[0] == Token(TokenType.NUMBER, 5)

    def test_multi_digit_integer(self) -> None:
        tokens = Tokenizer("42").tokenize()
        assert tokens[0] == Token(TokenType.NUMBER, 42)

    def test_float(self) -> None:
        tokens = Tokenizer("3.14").tokenize()
        assert tokens[0] == Token(TokenType.NUMBER, 3.14)

    def test_negative_number_with_high_minus(self) -> None:
        tokens = Tokenizer("¯3").tokenize()
        assert tokens[0] == Token(TokenType.NUMBER, -3)

    def test_negative_float(self) -> None:
        tokens = Tokenizer("¯2.5").tokenize()
        assert tokens[0] == Token(TokenType.NUMBER, -2.5)

    def test_scientific_with_high_minus_exponent(self) -> None:
        tokens = Tokenizer("1E¯14").tokenize()
        assert tokens[0] == Token(TokenType.NUMBER, 1e-14)

    def test_scientific_uppercase_positive(self) -> None:
        tokens = Tokenizer("2.5E3").tokenize()
        assert tokens[0] == Token(TokenType.NUMBER, 2500.0)

    def test_scientific_negative_mantissa_and_exponent(self) -> None:
        tokens = Tokenizer("¯1.5E¯3").tokenize()
        assert tokens[0] == Token(TokenType.NUMBER, -1.5e-3)


class TestTokenizerFunctions:
    def test_plus(self) -> None:
        tokens = Tokenizer("+").tokenize()
        assert tokens[0] == Token(TokenType.FUNCTION, "+")

    def test_minus(self) -> None:
        tokens = Tokenizer("-").tokenize()
        assert tokens[0] == Token(TokenType.FUNCTION, "-")

    def test_times(self) -> None:
        tokens = Tokenizer("×").tokenize()
        assert tokens[0] == Token(TokenType.FUNCTION, "×")

    def test_divide(self) -> None:
        tokens = Tokenizer("÷").tokenize()
        assert tokens[0] == Token(TokenType.FUNCTION, "÷")

    def test_ceiling(self) -> None:
        tokens = Tokenizer("⌈").tokenize()
        assert tokens[0] == Token(TokenType.FUNCTION, "⌈")

    def test_floor(self) -> None:
        tokens = Tokenizer("⌊").tokenize()
        assert tokens[0] == Token(TokenType.FUNCTION, "⌊")


class TestTokenizerDelimiters:
    def test_lparen(self) -> None:
        tokens = Tokenizer("(").tokenize()
        assert tokens[0] == Token(TokenType.LPAREN, "(")

    def test_rparen(self) -> None:
        tokens = Tokenizer(")").tokenize()
        assert tokens[0] == Token(TokenType.RPAREN, ")")

    def test_assign(self) -> None:
        tokens = Tokenizer("←").tokenize()
        assert tokens[0] == Token(TokenType.ASSIGN, "←")


class TestTokenizerIdentifiers:
    def test_simple_id(self) -> None:
        tokens = Tokenizer("x").tokenize()
        assert tokens[0] == Token(TokenType.ID, "x")

    def test_multi_char_id(self) -> None:
        tokens = Tokenizer("mean").tokenize()
        assert tokens[0] == Token(TokenType.ID, "mean")


class TestTokenizerExpressions:
    def test_simple_addition(self) -> None:
        tokens = Tokenizer("3+4").tokenize()
        assert tokens == [
            Token(TokenType.NUMBER, 3),
            Token(TokenType.FUNCTION, "+"),
            Token(TokenType.NUMBER, 4),
            Token(TokenType.EOF, None),
        ]

    def test_strand_notation(self) -> None:
        tokens = Tokenizer("1 2 3").tokenize()
        assert tokens == [
            Token(TokenType.NUMBER, 1),
            Token(TokenType.NUMBER, 2),
            Token(TokenType.NUMBER, 3),
            Token(TokenType.EOF, None),
        ]

    def test_expression_with_spaces(self) -> None:
        tokens = Tokenizer("3 + 4").tokenize()
        assert tokens == [
            Token(TokenType.NUMBER, 3),
            Token(TokenType.FUNCTION, "+"),
            Token(TokenType.NUMBER, 4),
            Token(TokenType.EOF, None),
        ]

    def test_assignment(self) -> None:
        tokens = Tokenizer("x ← 5").tokenize()
        assert tokens == [
            Token(TokenType.ID, "x"),
            Token(TokenType.ASSIGN, "←"),
            Token(TokenType.NUMBER, 5),
            Token(TokenType.EOF, None),
        ]

    def test_comment_ignored(self) -> None:
        tokens = Tokenizer("3 + 4 ⍝ add them").tokenize()
        assert tokens == [
            Token(TokenType.NUMBER, 3),
            Token(TokenType.FUNCTION, "+"),
            Token(TokenType.NUMBER, 4),
            Token(TokenType.EOF, None),
        ]

    def test_ends_with_eof(self) -> None:
        tokens = Tokenizer("5").tokenize()
        assert tokens[-1] == Token(TokenType.EOF, None)


class TestTokenizerUnknownChars:
    """The tokenizer must reject unknown characters with a clear
    error rather than silently dropping them. Two prior bugs (zilde
    ⍬ and commute ⍨) were both consequences of the silent fall-through
    in the tokenize loop — the parser saw an incomplete token stream
    and produced confusing downstream errors."""

    def test_unknown_char_raises(self) -> None:
        # § is a printable character not in any APL glyph set, not
        # alphanumeric, not whitespace.
        import pytest
        from marple.errors import SyntaxError_
        with pytest.raises(SyntaxError_):
            Tokenizer("1 § 2").tokenize()

    def test_tab_is_skipped(self) -> None:
        # Standard whitespace (tab, CR) should still be silently
        # skipped — only NON-whitespace unknown characters error.
        tokens = Tokenizer("1\t+\t2").tokenize()
        assert tokens == [
            Token(TokenType.NUMBER, 1),
            Token(TokenType.FUNCTION, "+"),
            Token(TokenType.NUMBER, 2),
            Token(TokenType.EOF, None),
        ]

    def test_carriage_return_is_skipped(self) -> None:
        tokens = Tokenizer("1\r+\r2").tokenize()
        assert tokens == [
            Token(TokenType.NUMBER, 1),
            Token(TokenType.FUNCTION, "+"),
            Token(TokenType.NUMBER, 2),
            Token(TokenType.EOF, None),
        ]
