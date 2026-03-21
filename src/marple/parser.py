from __future__ import annotations

from dataclasses import dataclass

from marple.tokenizer import Token, TokenType, Tokenizer


# AST nodes

@dataclass(frozen=True)
class Num:
    value: int | float


@dataclass(frozen=True)
class Vector:
    elements: list[Num]


@dataclass(frozen=True)
class MonadicFunc:
    function: str
    operand: object  # AST node


@dataclass(frozen=True)
class DyadicFunc:
    function: str
    left: object  # AST node
    right: object  # AST node


@dataclass(frozen=True)
class Assignment:
    name: str
    value: object  # AST node


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class Program:
    statements: list[object]


class Parser:
    """Right-to-left recursive descent parser for APL expressions.

    APL evaluation is right-to-left with long right scope and short left scope.
    The parser processes tokens left-to-right but builds the AST respecting
    APL's right-to-left semantics.
    """

    def __init__(self, tokens: list[Token]) -> None:
        self._tokens = tokens
        self._pos = 0

    def _current(self) -> Token:
        return self._tokens[self._pos]

    def _peek(self) -> Token | None:
        if self._pos + 1 < len(self._tokens):
            return self._tokens[self._pos + 1]
        return None

    def _eat(self, token_type: TokenType) -> Token:
        token = self._current()
        if token.type != token_type:
            raise SyntaxError(f"Expected {token_type}, got {token.type}")
        self._pos += 1
        return token

    def _parse_atom(self) -> object:
        token = self._current()
        if token.type == TokenType.LPAREN:
            self._eat(TokenType.LPAREN)
            result = self._parse_statement()
            self._eat(TokenType.RPAREN)
            return result
        if token.type == TokenType.NUMBER:
            self._eat(TokenType.NUMBER)
            assert isinstance(token.value, (int, float))
            return Num(token.value)
        if token.type == TokenType.ID:
            self._eat(TokenType.ID)
            assert isinstance(token.value, str)
            return Var(token.value)
        raise SyntaxError(f"Unexpected token: {token}")

    def _parse_array(self) -> object:
        """Parse one or more adjacent atoms (strand notation)."""
        first = self._parse_atom()
        elements = [first]
        while self._current().type in (TokenType.NUMBER, TokenType.LPAREN, TokenType.ID):
            elements.append(self._parse_atom())
        if len(elements) == 1:
            return elements[0]
        # Strand notation produces a vector
        nums = []
        for el in elements:
            if not isinstance(el, Num):
                raise SyntaxError("Strand notation only supports numeric literals")
            nums.append(el)
        return Vector(nums)

    def _parse_statement(self) -> object:
        """Parse a statement: assignment or expression."""
        # Check for assignment: ID ←
        if (
            self._current().type == TokenType.ID
            and self._peek() is not None
            and self._peek().type == TokenType.ASSIGN  # type: ignore[union-attr]
        ):
            name_token = self._eat(TokenType.ID)
            self._eat(TokenType.ASSIGN)
            value = self._parse_statement()
            assert isinstance(name_token.value, str)
            return Assignment(name_token.value, value)

        # Check for monadic function (function at start of expression)
        if self._current().type == TokenType.FUNCTION:
            func_token = self._eat(TokenType.FUNCTION)
            operand = self._parse_statement()
            assert isinstance(func_token.value, str)
            return MonadicFunc(func_token.value, operand)

        # Parse left argument (array)
        left = self._parse_array()

        # Check for dyadic function
        if self._current().type == TokenType.FUNCTION:
            func_token = self._eat(TokenType.FUNCTION)
            right = self._parse_statement()
            assert isinstance(func_token.value, str)
            return DyadicFunc(func_token.value, left, right)

        return left

    def parse(self) -> object:
        statements = [self._parse_statement()]
        while self._current().type == TokenType.DIAMOND:
            self._eat(TokenType.DIAMOND)
            statements.append(self._parse_statement())
        if self._current().type != TokenType.EOF:
            raise SyntaxError(f"Unexpected token after expression: {self._current()}")
        if len(statements) == 1:
            return statements[0]
        return Program(statements)


def parse(source: str) -> object:
    tokens = Tokenizer(source).tokenize()
    return Parser(tokens).parse()
