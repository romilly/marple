from marple.errors import SyntaxError_
from marple.tokenizer import Token, TokenType, Tokenizer


# AST nodes

class Num:
    def __init__(self, value: int | float) -> None:
        self.value = value
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Num):
            return NotImplemented
        return self.value == other.value


class Str:
    def __init__(self, value: str) -> None:
        self.value = value
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Str):
            return NotImplemented
        return self.value == other.value


class Vector:
    def __init__(self, elements: list[Num]) -> None:
        self.elements = elements
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector):
            return NotImplemented
        return self.elements == other.elements


class MonadicFunc:
    def __init__(self, function: str, operand: object) -> None:
        self.function = function
        self.operand = operand
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MonadicFunc):
            return NotImplemented
        return self.function == other.function and self.operand == other.operand


class DyadicFunc:
    def __init__(self, function: str, left: object, right: object) -> None:
        self.function = function
        self.left = left
        self.right = right
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DyadicFunc):
            return NotImplemented
        return self.function == other.function and self.left == other.left and self.right == other.right


class Assignment:
    def __init__(self, name: str, value: object) -> None:
        self.name = name
        self.value = value
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Assignment):
            return NotImplemented
        return self.name == other.name and self.value == other.value


class Var:
    def __init__(self, name: str) -> None:
        self.name = name
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Var):
            return NotImplemented
        return self.name == other.name


class QualifiedVar:
    def __init__(self, parts: list[str]) -> None:
        self.parts = parts
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, QualifiedVar):
            return NotImplemented
        return self.parts == other.parts


class DerivedFunc:
    def __init__(self, operator: str, function: str, operand: object) -> None:
        self.operator = operator
        self.function = function
        self.operand = operand
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DerivedFunc):
            return NotImplemented
        return self.operator == other.operator and self.function == other.function and self.operand == other.operand


class MonadicDopCall:
    """User-defined operator applied monadically: (operand op) argument"""
    def __init__(self, op_name: object, operand: object, argument: object) -> None:
        self.op_name = op_name    # the operator (Var)
        self.operand = operand    # ⍺⍺ (the left function/array)
        self.argument = argument  # ⍵ (the right argument)
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MonadicDopCall):
            return NotImplemented
        return self.op_name == other.op_name and self.operand == other.operand and self.argument == other.argument


class DyadicDopCall:
    """User-defined operator applied dyadically: left (operand op) right"""
    def __init__(self, op_name: object, operand: object, left: object, right: object) -> None:
        self.op_name = op_name
        self.operand = operand
        self.left = left
        self.right = right
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DyadicDopCall):
            return NotImplemented
        return self.op_name == other.op_name and self.operand == other.operand and self.left == other.left and self.right == other.right


class RankDerived:
    """Unapplied rank-derived function: f⍤k"""
    def __init__(self, function: object, rank_spec: object) -> None:
        self.function = function
        self.rank_spec = rank_spec
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RankDerived):
            return NotImplemented
        return self.function == other.function and self.rank_spec == other.rank_spec


class ReduceOp:
    """Unapplied reduce: f/ as a function value"""
    def __init__(self, function: str) -> None:
        self.function = function
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ReduceOp):
            return NotImplemented
        return self.function == other.function


class ScanOp:
    """Unapplied scan: f\\ as a function value"""
    def __init__(self, function: str) -> None:
        self.function = function
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ScanOp):
            return NotImplemented
        return self.function == other.function


class IBeamDerived:
    """I-beam derived function: ⌶'module.function'"""
    def __init__(self, path: str) -> None:
        self.path = path
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, IBeamDerived):
            return NotImplemented
        return self.path == other.path


class InnerProduct:
    def __init__(self, left_fn: str, right_fn: str, left: object, right: object) -> None:
        self.left_fn = left_fn
        self.right_fn = right_fn
        self.left = left
        self.right = right
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, InnerProduct):
            return NotImplemented
        return self.left_fn == other.left_fn and self.right_fn == other.right_fn and self.left == other.left and self.right == other.right


class OuterProduct:
    def __init__(self, function: str, left: object, right: object) -> None:
        self.function = function
        self.left = left
        self.right = right
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, OuterProduct):
            return NotImplemented
        return self.function == other.function and self.left == other.left and self.right == other.right


class SysVar:
    def __init__(self, name: str) -> None:
        self.name = name
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SysVar):
            return NotImplemented
        return self.name == other.name


class Index:
    def __init__(self, array: object, indices: list[object | None]) -> None:
        self.array = array
        self.indices = indices
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Index):
            return NotImplemented
        return self.array == other.array and self.indices == other.indices


class Omega:
    pass


class Alpha:
    pass


class FunctionRef:
    """A reference to a primitive function glyph, used as a dop operand."""
    def __init__(self, glyph: str) -> None:
        self.glyph = glyph
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FunctionRef):
            return NotImplemented
        return self.glyph == other.glyph


class AlphaAlpha:
    """⍺⍺ — left operand reference in a dop."""
    pass


class OmegaOmega:
    """⍵⍵ — right operand reference in a dop."""
    pass


class Nabla:
    pass


class Guard:
    def __init__(self, condition: object, body: object) -> None:
        self.condition = condition
        self.body = body
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Guard):
            return NotImplemented
        return self.condition == other.condition and self.body == other.body


class AlphaDefault:
    def __init__(self, default: object) -> None:
        self.default = default
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AlphaDefault):
            return NotImplemented
        return self.default == other.default


class Dfn:
    def __init__(self, body: list[object]) -> None:
        self.body = body
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Dfn):
            return NotImplemented
        return self.body == other.body


class MonadicDfnCall:
    def __init__(self, dfn: object, operand: object) -> None:
        self.dfn = dfn
        self.operand = operand
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MonadicDfnCall):
            return NotImplemented
        return self.dfn == other.dfn and self.operand == other.operand


class DyadicDfnCall:
    def __init__(self, dfn: object, left: object, right: object) -> None:
        self.dfn = dfn
        self.left = left
        self.right = right
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DyadicDfnCall):
            return NotImplemented
        return self.dfn == other.dfn and self.left == other.left and self.right == other.right


class Program:
    def __init__(self, statements: list[object]) -> None:
        self.statements = statements
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Program):
            return NotImplemented
        return self.statements == other.statements


class Parser:
    """Right-to-left recursive descent parser for APL expressions.

    APL evaluation is right-to-left with long right scope and short left scope.
    The parser processes tokens left-to-right but builds the AST respecting
    APL's right-to-left semantics.
    """

    def __init__(self, tokens: list[Token], name_table: dict[str, int] | None = None,
                 operator_arity: dict[str, int] | None = None) -> None:
        self._tokens = tokens
        self._pos = 0
        self._name_table = name_table or {}
        self._operator_arity = operator_arity or {}

    def _is_function_name(self, name: str) -> bool:
        """Check if a name is classified as a function in the name table."""
        return self._name_table.get(name) == 3  # NC_FUNCTION

    def _is_operator_name(self, name: str) -> bool:
        """Check if a name is classified as an operator in the name table."""
        return self._name_table.get(name) == 4  # NC_OPERATOR

    def _current(self) -> Token:
        return self._tokens[self._pos]

    def _peek(self) -> Token | None:
        if self._pos + 1 < len(self._tokens):
            return self._tokens[self._pos + 1]
        return None

    def _eat(self, token_type: TokenType) -> Token:
        token = self._current()
        if token.type != token_type:
            raise SyntaxError_(f"Expected {token_type}, got {token.type}")
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
            # Check for bare function glyph as operand: (-)  (+)  (⍳)  etc.
            if (
                self._current().type == TokenType.FUNCTION
                and self._pos + 1 < len(self._tokens)
                and self._tokens[self._pos + 1].type == TokenType.RPAREN
            ):
                fn_token = self._eat(TokenType.FUNCTION)
                self._eat(TokenType.RPAREN)
                assert isinstance(fn_token.value, str)
                return FunctionRef(fn_token.value)
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
        if token.type == TokenType.QUALIFIED_NAME:
            self._eat(TokenType.QUALIFIED_NAME)
            assert isinstance(token.value, str)
            return QualifiedVar(token.value.split("::"))
        if token.type == TokenType.OMEGA:
            self._eat(TokenType.OMEGA)
            return Omega()
        if token.type == TokenType.ALPHA:
            self._eat(TokenType.ALPHA)
            return Alpha()
        if token.type == TokenType.ALPHA_ALPHA:
            self._eat(TokenType.ALPHA_ALPHA)
            return AlphaAlpha()
        if token.type == TokenType.OMEGA_OMEGA:
            self._eat(TokenType.OMEGA_OMEGA)
            return OmegaOmega()
        if token.type == TokenType.NABLA:
            self._eat(TokenType.NABLA)
            return Nabla()
        if token.type == TokenType.SYSVAR:
            self._eat(TokenType.SYSVAR)
            assert isinstance(token.value, str)
            return SysVar(token.value)
        if token.type == TokenType.LBRACE:
            return self._parse_dfn()
        raise SyntaxError_(f"Unexpected token: {token}")

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
            TokenType.OMEGA, TokenType.ALPHA, TokenType.ALPHA_ALPHA,
            TokenType.OMEGA_OMEGA, TokenType.NABLA,
            TokenType.LBRACE, TokenType.STRING, TokenType.QUALIFIED_NAME,
            TokenType.SYSVAR,
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
            if op_glyph in ("/", "\\", "⌿", "⍀"):
                # Check if followed by ⍤ (e.g., +/⍤1)
                if (
                    self._current().type == TokenType.OPERATOR
                    and self._current().value == "⍤"
                ):
                    self._eat(TokenType.OPERATOR)
                    rank_spec = self._parse_array()
                    inner = ReduceOp(func_glyph) if op_glyph in ("/", "⌿") else ScanOp(func_glyph)
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

        # Check for user-defined operator: left op_name [right_operand] argument
        if (
            self._current().type == TokenType.ID
            and self._is_operator_name(self._current().value)
        ):
            op_token = self._eat(TokenType.ID)
            assert isinstance(op_token.value, str)
            op_var = Var(op_token.value)
            arity = self._operator_arity.get(op_token.value, 1)
            if arity == 2:
                # Dyadic operator (conjunction): left op right_operand argument
                # Right operand is a single atom (Iverson: immediate next token)
                right_operand = self._parse_atom_with_index()
                argument = self._parse_statement()
                return DyadicDopCall(op_var, left, right_operand, argument)
            else:
                # Monadic operator (adverb): left op argument
                argument = self._parse_statement()
                return MonadicDopCall(op_var, left, argument)

        # If left is a known function name, it has long right scope
        _fn_name = None
        if isinstance(left, Var):
            _fn_name = left.name
        elif isinstance(left, SysVar):
            _fn_name = left.name
        if (
            _fn_name is not None
            and self._is_function_name(_fn_name)
            and (self._is_array_start()
                 or self._current().type == TokenType.FUNCTION
                 or self._current().type == TokenType.SYSVAR
                 or (self._current().type == TokenType.OPERATOR
                     and self._current().value == "⌶"))
        ):
            right = self._parse_statement()
            return MonadicDfnCall(left, right)

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

        # ⍺⍺/ or ⍺⍺\ → reduce/scan with operand function (not replicate/expand)
        if (
            isinstance(left, (AlphaAlpha, OmegaOmega))
            and self._current().type == TokenType.OPERATOR
            and self._current().value in ("/", "\\", "⌿", "⍀")
        ):
            op_token = self._eat(TokenType.OPERATOR)
            assert isinstance(op_token.value, str)
            operand = self._parse_statement()
            return DerivedFunc(op_token.value, left, operand)

        # Check for dyadic operator as function: left / right, left \ right, etc.
        if (
            self._current().type == TokenType.OPERATOR
            and self._current().value in ("/", "\\", "⌿", "⍀")
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
            self._current().type in (TokenType.ID, TokenType.SYSVAR)
            and not isinstance(left, (Dfn, Nabla))
        ):
            # Could be: left name right (dyadic named dfn/sys call)
            # But only if the name is followed by an array
            saved_pos = self._pos
            tok_type = self._current().type
            name_token = self._eat(tok_type)
            assert isinstance(name_token.value, str)
            if self._is_array_start() or self._current().type == TokenType.FUNCTION:
                right = self._parse_statement()
                node_fn = Var(name_token.value) if tok_type == TokenType.ID else SysVar(name_token.value)
                return DyadicDfnCall(node_fn, left, right)
            # Not a dyadic call — backtrack
            self._pos = saved_pos

        # Check if left is a dfn/var/rank-derived being applied as a monadic function
        if isinstance(left, (Dfn, Var, QualifiedVar, Nabla, AlphaAlpha, OmegaOmega, RankDerived, IBeamDerived)) and self._is_array_start():
            right = self._parse_statement()
            return MonadicDfnCall(left, right)

        return left

    def parse(self) -> object:
        # Empty input (e.g. comment-only line) → return Num(0) as no-op
        if self._current().type == TokenType.EOF:
            return Num(0)
        statements = [self._parse_statement()]
        while self._current().type == TokenType.DIAMOND:
            self._eat(TokenType.DIAMOND)
            statements.append(self._parse_statement())
        if self._current().type != TokenType.EOF:
            raise SyntaxError_(f"Unexpected token after expression: {self._current()}")
        if len(statements) == 1:
            return statements[0]
        return Program(statements)


def parse(source: str, name_table: dict[str, int] | None = None,
          operator_arity: dict[str, int] | None = None) -> object:
    tokens = Tokenizer(source).tokenize()
    return Parser(tokens, name_table, operator_arity).parse()
