import pytest

from marple.errors import SyntaxError_
from marple.parser import (
    Assignment,
    DyadicFunc,
    MonadicFunc,
    Num,
    Vector,
    parse,
)


class TestParserNumbers:
    def test_single_integer(self) -> None:
        assert parse("5") == Num(5)

    def test_negative_number(self) -> None:
        assert parse("¯3") == Num(-3)

    def test_float(self) -> None:
        assert parse("3.14") == Num(3.14)


class TestParserVectors:
    def test_strand_notation(self) -> None:
        assert parse("1 2 3") == Vector([Num(1), Num(2), Num(3)])


class TestParserMonadicFunctions:
    def test_negate(self) -> None:
        assert parse("-5") == MonadicFunc("-", Num(5))

    def test_negate_vector(self) -> None:
        assert parse("-1 2 3") == MonadicFunc("-", Vector([Num(1), Num(2), Num(3)]))


class TestParserDyadicFunctions:
    def test_addition(self) -> None:
        assert parse("3+4") == DyadicFunc("+", Num(3), Num(4))

    def test_right_to_left(self) -> None:
        # 1+2×3 should parse as 1+(2×3)
        assert parse("1+2×3") == DyadicFunc("+", Num(1), DyadicFunc("×", Num(2), Num(3)))

    def test_subtraction(self) -> None:
        assert parse("5-3") == DyadicFunc("-", Num(5), Num(3))


class TestParserParentheses:
    def test_parens_override_scope(self) -> None:
        # (1+2)×3 should parse as (1+2)×3
        assert parse("(1+2)×3") == DyadicFunc(
            "×", DyadicFunc("+", Num(1), Num(2)), Num(3)
        )


class TestParserUnbalancedBraces:
    def test_unbalanced_open_brace_raises_error(self) -> None:
        with pytest.raises(SyntaxError_, match="Unmatched"):
            parse("double←{")


class TestParserAssignment:
    def test_simple_assignment(self) -> None:
        assert parse("x←5") == Assignment("x", Num(5))

    def test_assignment_with_expression(self) -> None:
        assert parse("x←3+4") == Assignment("x", DyadicFunc("+", Num(3), Num(4)))
