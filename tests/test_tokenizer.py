"""Tokenizer unit tests.

Note: value-producing tokens are AST nodes (Num, Str, Var,
PrimitiveFunction, …) — the tokenizer emits them directly so
there is no parallel token hierarchy to translate through.
Marker tokens (parens, delimiters, EOF) and the OperatorToken
remain as `Token` subclasses in tokenizer.py.
"""

from marple.nodes import (
    Num,
    PrimitiveFunction,
    Str,
    Var,
)
from marple.tokenizer import (
    AssignToken,
    EofToken,
    LParenToken,
    RParenToken,
    Tokenizer,
)


class TestTokenizerNumbers:
    def test_single_integer(self) -> None:
        tokens = Tokenizer("5").tokenize()
        assert tokens[0] == Num(5)

    def test_multi_digit_integer(self) -> None:
        tokens = Tokenizer("42").tokenize()
        assert tokens[0] == Num(42)

    def test_float(self) -> None:
        tokens = Tokenizer("3.14").tokenize()
        assert tokens[0] == Num(3.14)

    def test_negative_number_with_high_minus(self) -> None:
        tokens = Tokenizer("¯3").tokenize()
        assert tokens[0] == Num(-3)

    def test_negative_float(self) -> None:
        tokens = Tokenizer("¯2.5").tokenize()
        assert tokens[0] == Num(-2.5)

    def test_scientific_with_high_minus_exponent(self) -> None:
        tokens = Tokenizer("1E¯14").tokenize()
        assert tokens[0] == Num(1e-14)

    def test_scientific_uppercase_positive(self) -> None:
        tokens = Tokenizer("2.5E3").tokenize()
        assert tokens[0] == Num(2500.0)

    def test_scientific_negative_mantissa_and_exponent(self) -> None:
        tokens = Tokenizer("¯1.5E¯3").tokenize()
        assert tokens[0] == Num(-1.5e-3)


class TestTokenizerFunctions:
    def test_plus(self) -> None:
        tokens = Tokenizer("+").tokenize()
        assert tokens[0] == PrimitiveFunction("+")

    def test_minus(self) -> None:
        tokens = Tokenizer("-").tokenize()
        assert tokens[0] == PrimitiveFunction("-")

    def test_times(self) -> None:
        tokens = Tokenizer("×").tokenize()
        assert tokens[0] == PrimitiveFunction("×")

    def test_divide(self) -> None:
        tokens = Tokenizer("÷").tokenize()
        assert tokens[0] == PrimitiveFunction("÷")

    def test_ceiling(self) -> None:
        tokens = Tokenizer("⌈").tokenize()
        assert tokens[0] == PrimitiveFunction("⌈")

    def test_floor(self) -> None:
        tokens = Tokenizer("⌊").tokenize()
        assert tokens[0] == PrimitiveFunction("⌊")


class TestTokenizerDelimiters:
    def test_lparen(self) -> None:
        tokens = Tokenizer("(").tokenize()
        assert tokens[0] == LParenToken()

    def test_rparen(self) -> None:
        tokens = Tokenizer(")").tokenize()
        assert tokens[0] == RParenToken()

    def test_assign(self) -> None:
        tokens = Tokenizer("←").tokenize()
        assert tokens[0] == AssignToken()


class TestTokenizerIdentifiers:
    def test_simple_id(self) -> None:
        tokens = Tokenizer("x").tokenize()
        assert tokens[0] == Var("x")

    def test_multi_char_id(self) -> None:
        tokens = Tokenizer("mean").tokenize()
        assert tokens[0] == Var("mean")


class TestTokenizerExpressions:
    def test_simple_addition(self) -> None:
        tokens = Tokenizer("3+4").tokenize()
        assert tokens == [
            Num(3),
            PrimitiveFunction("+"),
            Num(4),
            EofToken(),
        ]

    def test_strand_notation(self) -> None:
        tokens = Tokenizer("1 2 3").tokenize()
        assert tokens == [
            Num(1),
            Num(2),
            Num(3),
            EofToken(),
        ]

    def test_expression_with_spaces(self) -> None:
        tokens = Tokenizer("3 + 4").tokenize()
        assert tokens == [
            Num(3),
            PrimitiveFunction("+"),
            Num(4),
            EofToken(),
        ]

    def test_assignment(self) -> None:
        tokens = Tokenizer("x ← 5").tokenize()
        assert tokens == [
            Var("x"),
            AssignToken(),
            Num(5),
            EofToken(),
        ]

    def test_comment_ignored(self) -> None:
        tokens = Tokenizer("3 + 4 ⍝ add them").tokenize()
        assert tokens == [
            Num(3),
            PrimitiveFunction("+"),
            Num(4),
            EofToken(),
        ]

    def test_ends_with_eof(self) -> None:
        tokens = Tokenizer("5").tokenize()
        assert tokens[-1] == EofToken()


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

    def test_high_minus_without_digit_raises(self) -> None:
        """`¯` must be followed by a digit; `¯a` or bare `¯` is a
        syntax error rather than an internal AssertionError from
        _read_number."""
        import pytest
        from marple.errors import SyntaxError_
        with pytest.raises(SyntaxError_):
            Tokenizer("¯a").tokenize()
        with pytest.raises(SyntaxError_):
            Tokenizer("¯").tokenize()

    def test_tab_is_skipped(self) -> None:
        # Standard whitespace (tab, CR) should still be silently
        # skipped — only NON-whitespace unknown characters error.
        tokens = Tokenizer("1\t+\t2").tokenize()
        assert tokens == [
            Num(1),
            PrimitiveFunction("+"),
            Num(2),
            EofToken(),
        ]

    def test_carriage_return_is_skipped(self) -> None:
        tokens = Tokenizer("1\r+\r2").tokenize()
        assert tokens == [
            Num(1),
            PrimitiveFunction("+"),
            Num(2),
            EofToken(),
        ]
