from __future__ import annotations

from dataclasses import dataclass

from marple.tokenizer import Token, TokenType, Tokenizer


# AST nodes

@dataclass(frozen=True)
class Num:
    value: int | float


@dataclass(frozen=True)
class Str:
    value: str


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
class RankDerived:
    """Unapplied rank-derived function: f⍤k"""
    function: object  # str (glyph), ReduceOp, ScanOp, Dfn, or Var
    rank_spec: object  # AST node (Num or Vector)


@dataclass(frozen=True)
class ReduceOp:
    """Unapplied reduce: f/ as a function value"""
    function: str


@dataclass(frozen=True)
class ScanOp:
    """Unapplied scan: f\\ as a function value"""
    function: str


@dataclass(frozen=True)
class IBeamDerived:
    """I-beam derived function: ⌶'module.function'"""
    path: str


@dataclass(frozen=True)
class InnerProduct:
    left_fn: str
    right_fn: str
    left: object  # AST node
    right: object  # AST node


@dataclass(frozen=True)
class OuterProduct:
    function: str
    left: object  # AST node
    right: object  # AST node


@dataclass(frozen=True)
class SysVar:
    name: str


@dataclass(frozen=True)
class Index:
    array: object  # AST node
    indices: list[object | None]  # None means "all along this axis"


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
        if token.type == TokenType.STRING:
            self._eat(TokenType.STRING)
            assert isinstance(token.value, str)
            return Str(token.value)
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
        if token.type == TokenType.SYSVAR:
            self._eat(TokenType.SYSVAR)
            assert isinstance(token.value, str)
            return SysVar(token.value)
        if token.type == TokenType.LBRACE:
            return self._parse_dfn()
        raise SyntaxError(f"Unexpected token: {token}")

    def _parse_atom_with_index(self) -> object:
        """Parse an atom, then check for bracket indexing."""
        atom = self._parse_atom()
        if self._current().type == TokenType.LBRACKET:
            return self._parse_bracket_index(atom)
        return atom

    def _parse_bracket_index(self, array: object) -> Index:
        """Parse [idx] or [row;col] bracket indexing."""
        self._eat(TokenType.LBRACKET)
        indices: list[object | None] = []
        # First index (may be empty for [;col])
        if self._current().type == TokenType.SEMICOLON:
            indices.append(None)
        elif self._current().type == TokenType.RBRACKET:
            indices.append(None)
        else:
            indices.append(self._parse_statement())
        # Additional indices separated by ;
        while self._current().type == TokenType.SEMICOLON:
            self._eat(TokenType.SEMICOLON)
            if self._current().type in (TokenType.SEMICOLON, TokenType.RBRACKET):
                indices.append(None)
            else:
                indices.append(self._parse_statement())
        self._eat(TokenType.RBRACKET)
        return Index(array, indices)

    def _is_array_start(self) -> bool:
        return self._current().type in (
            TokenType.NUMBER, TokenType.LPAREN, TokenType.ID,
            TokenType.OMEGA, TokenType.ALPHA, TokenType.NABLA,
            TokenType.LBRACE, TokenType.STRING,
        )

    def _parse_array(self) -> object:
        """Parse one or more adjacent numeric atoms as a vector,
        or a single non-numeric atom."""
        first = self._parse_atom_with_index()
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
        # Check for assignment: ID ← or ⎕SYSVAR ←
        if (
            self._current().type in (TokenType.ID, TokenType.SYSVAR)
            and self._peek() is not None
            and self._peek().type == TokenType.ASSIGN  # type: ignore[union-attr]
        ):
            name_token = self._eat(self._current().type)
            self._eat(TokenType.ASSIGN)
            value = self._parse_statement()
            assert isinstance(name_token.value, str)
            return Assignment(name_token.value, value)

        # Check for i-beam operator: ⌶'path'
        if (
            self._current().type == TokenType.OPERATOR
            and self._current().value == "⌶"
        ):
            self._eat(TokenType.OPERATOR)
            path_token = self._eat(TokenType.STRING)
            assert isinstance(path_token.value, str)
            return IBeamDerived(path_token.value)

        # Check for primitive function (possibly followed by operator)
        if self._current().type == TokenType.FUNCTION:
            func_glyph, op_glyph = self._parse_function_expr()
            if op_glyph == "⍤":
                # Rank operator: f⍤k
                rank_spec = self._parse_array()
                return RankDerived(func_glyph, rank_spec)
            if op_glyph in ("/", "\\"):
                # Check if followed by ⍤ (e.g., +/⍤1)
                if (
                    self._current().type == TokenType.OPERATOR
                    and self._current().value == "⍤"
                ):
                    self._eat(TokenType.OPERATOR)
                    rank_spec = self._parse_array()
                    inner = ReduceOp(func_glyph) if op_glyph == "/" else ScanOp(func_glyph)
                    return RankDerived(inner, rank_spec)
                operand = self._parse_statement()
                return DerivedFunc(op_glyph, func_glyph, operand)
            if op_glyph is not None:
                operand = self._parse_statement()
                return DerivedFunc(op_glyph, func_glyph, operand)
            operand = self._parse_statement()
            return MonadicFunc(func_glyph, operand)

        # Parse left argument (array — may include dfn, ⍵, ⍺, ∇)
        left = self._parse_array()

        # Check for dyadic primitive function or inner/outer product
        if self._current().type == TokenType.FUNCTION:
            func_glyph, op_glyph = self._parse_function_expr()
            if op_glyph == ".":
                # Inner product: left f.g right
                right_fn_token = self._eat(TokenType.FUNCTION)
                assert isinstance(right_fn_token.value, str)
                right = self._parse_statement()
                return InnerProduct(func_glyph, right_fn_token.value, left, right)
            if op_glyph is not None:
                operand = self._parse_statement()
                return DerivedFunc(op_glyph, func_glyph, operand)
            right = self._parse_statement()
            return DyadicFunc(func_glyph, left, right)

        # Check for dyadic operator as function: left / right or left \ right
        if (
            self._current().type == TokenType.OPERATOR
            and self._current().value in ("/", "\\")
        ):
            op_token = self._eat(TokenType.OPERATOR)
            assert isinstance(op_token.value, str)
            right = self._parse_statement()
            return DyadicFunc(op_token.value, left, right)

        # Check for outer product: left ∘.f right
        if (
            self._current().type == TokenType.OPERATOR
            and self._current().value == "∘"
        ):
            self._eat(TokenType.OPERATOR)  # ∘
            self._eat(TokenType.OPERATOR)  # .
            func_token = self._eat(TokenType.FUNCTION)
            assert isinstance(func_token.value, str)
            right = self._parse_statement()
            return OuterProduct(func_token.value, left, right)

        # Check for ⍤ after Dfn or Var: {dfn}⍤k or name⍤k
        if (
            isinstance(left, (Dfn, Var))
            and self._current().type == TokenType.OPERATOR
            and self._current().value == "⍤"
        ):
            self._eat(TokenType.OPERATOR)
            rank_spec = self._parse_array()
            left = RankDerived(left, rank_spec)

        # Check for dfn/var in dyadic position: left {body} right  or  left name right
        if self._current().type == TokenType.LBRACE:
            dfn = self._parse_dfn()
            right = self._parse_statement()
            return DyadicDfnCall(dfn, left, right)

        # Check for parenthesized function in dyadic position: left (f⍤k) right
        if self._current().type == TokenType.LPAREN:
            saved_pos = self._pos
            self._eat(TokenType.LPAREN)
            inner = self._parse_statement()
            if self._current().type == TokenType.RPAREN:
                self._eat(TokenType.RPAREN)
                if isinstance(inner, (RankDerived, IBeamDerived)) and self._is_array_start():
                    right = self._parse_statement()
                    return DyadicDfnCall(inner, left, right)
            self._pos = saved_pos

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

        # Check if left is a dfn/var/rank-derived being applied as a monadic function
        if isinstance(left, (Dfn, Var, Nabla, RankDerived, IBeamDerived)) and self._is_array_start():
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
