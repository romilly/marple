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
class DerivedFunc:
    operator: str
    function: str
    operand: object  # AST node


@dataclass(frozen=True)
class Omega:
    pass


@dataclass(frozen=True)
class Alpha:
    pass


@dataclass(frozen=True)
class Nabla:
    pass


@dataclass(frozen=True)
class Guard:
    condition: object  # AST node
    body: object  # AST node


@dataclass(frozen=True)
class AlphaDefault:
    default: object  # AST node


@dataclass(frozen=True)
class Dfn:
    body: list[object]  # list of statements (may include Guards and AlphaDefault)


@dataclass(frozen=True)
class MonadicDfnCall:
    dfn: object  # Dfn or Var
    operand: object  # AST node


@dataclass(frozen=True)
class DyadicDfnCall:
    dfn: object  # Dfn or Var
    left: object  # AST node
    right: object  # AST node


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

    def _parse_dfn(self) -> Dfn:
        """Parse a dfn: { statement (⋄ statement)* }"""
        self._eat(TokenType.LBRACE)
        statements: list[object] = []
        while self._current().type != TokenType.RBRACE:
            stmt = self._parse_dfn_statement()
            statements.append(stmt)
            if self._current().type == TokenType.DIAMOND:
                self._eat(TokenType.DIAMOND)
        self._eat(TokenType.RBRACE)
        return Dfn(statements)

    def _parse_dfn_statement(self) -> object:
        """Parse a statement inside a dfn, handling guards and ⍺← default."""
        # Check for ⍺← default
        if (
            self._current().type == TokenType.ALPHA
            and self._peek() is not None
            and self._peek().type == TokenType.ASSIGN  # type: ignore[union-attr]
        ):
            self._eat(TokenType.ALPHA)
            self._eat(TokenType.ASSIGN)
            default = self._parse_statement()
            return AlphaDefault(default)

        stmt = self._parse_statement()
        # Check for guard: expr : expr
        if self._current().type == TokenType.GUARD:
            self._eat(TokenType.GUARD)
            body = self._parse_statement()
            return Guard(stmt, body)
        return stmt

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
        if token.type == TokenType.OMEGA:
            self._eat(TokenType.OMEGA)
            return Omega()
        if token.type == TokenType.ALPHA:
            self._eat(TokenType.ALPHA)
            return Alpha()
        if token.type == TokenType.NABLA:
            self._eat(TokenType.NABLA)
            return Nabla()
        if token.type == TokenType.LBRACE:
            return self._parse_dfn()
        raise SyntaxError(f"Unexpected token: {token}")

    def _is_array_start(self) -> bool:
        return self._current().type in (
            TokenType.NUMBER, TokenType.LPAREN, TokenType.ID,
            TokenType.OMEGA, TokenType.ALPHA, TokenType.NABLA,
            TokenType.LBRACE,
        )

    def _parse_array(self) -> object:
        """Parse one or more adjacent numeric atoms as a vector,
        or a single non-numeric atom."""
        first = self._parse_atom()
        if not isinstance(first, Num):
            return first
        elements: list[Num] = [first]
        while self._current().type == TokenType.NUMBER:
            token = self._eat(TokenType.NUMBER)
            assert isinstance(token.value, (int, float))
            elements.append(Num(token.value))
        if len(elements) == 1:
            return elements[0]
        return Vector(elements)

    def _parse_function_expr(self) -> tuple[str, str | None]:
        """Parse a function glyph, possibly followed by an operator.
        Returns (function_glyph, operator_glyph_or_None)."""
        func_token = self._eat(TokenType.FUNCTION)
        assert isinstance(func_token.value, str)
        if self._current().type == TokenType.OPERATOR:
            op_token = self._eat(TokenType.OPERATOR)
            assert isinstance(op_token.value, str)
            return func_token.value, op_token.value
        return func_token.value, None

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

        # Check for primitive function (possibly followed by operator)
        if self._current().type == TokenType.FUNCTION:
            func_glyph, op_glyph = self._parse_function_expr()
            if op_glyph is not None:
                operand = self._parse_statement()
                return DerivedFunc(op_glyph, func_glyph, operand)
            operand = self._parse_statement()
            return MonadicFunc(func_glyph, operand)

        # Parse left argument (array — may include dfn, ⍵, ⍺, ∇)
        left = self._parse_array()

        # Check for dyadic primitive function
        if self._current().type == TokenType.FUNCTION:
            func_glyph, op_glyph = self._parse_function_expr()
            if op_glyph is not None:
                operand = self._parse_statement()
                return DerivedFunc(op_glyph, func_glyph, operand)
            right = self._parse_statement()
            return DyadicFunc(func_glyph, left, right)

        # Check for dfn/var in dyadic position: left {body} right  or  left name right
        if self._current().type == TokenType.LBRACE:
            dfn = self._parse_dfn()
            right = self._parse_statement()
            return DyadicDfnCall(dfn, left, right)

        if (
            self._current().type == TokenType.ID
            and isinstance(left, (Num, Vector))
        ):
            # Could be: left name right (dyadic named dfn call)
            # But only if the name is followed by an array
            saved_pos = self._pos
            name_token = self._eat(TokenType.ID)
            assert isinstance(name_token.value, str)
            if self._is_array_start():
                right = self._parse_statement()
                return DyadicDfnCall(Var(name_token.value), left, right)
            # Not a dyadic call — backtrack
            self._pos = saved_pos

        # Check if left is a dfn/var being applied as a monadic function
        if isinstance(left, (Dfn, Var, Nabla)) and self._is_array_start():
            right = self._parse_statement()
            return MonadicDfnCall(left, right)

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
