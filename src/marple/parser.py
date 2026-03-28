from abc import ABC, abstractmethod

from marple.arraymodel import APLArray, S
from marple.errors import SyntaxError_, DomainError, ValueError_
from marple.tokenizer import Token, TokenType, Tokenizer


# ── Category constants for Iverson's stack-based parser ──

CAT_END = 0    # End marker (⋄, EOF)
CAT_NOUN = 1   # Noun (array/data)
CAT_VERB = 2   # Verb (function)
CAT_ADV = 3    # Adverb (monadic operator: /, \, ⌿, ⍀, ∘.)
CAT_CONJ = 4   # Conjunction (dyadic operator: ⍤, ., ⌶)
CAT_ASGN = 5   # Assignment (←)
CAT_LP = 6     # Left paren
CAT_RP = 7     # Right paren
CAT_EMPTY = 8  # Padding for window positions

# Context sets for case matching
_CTX_MONAD = frozenset({CAT_END, CAT_ADV, CAT_VERB, CAT_ASGN, CAT_LP})
_CTX_DYAD = frozenset({CAT_END, CAT_NOUN, CAT_ADV, CAT_VERB, CAT_ASGN, CAT_LP})

# System functions (classified as verbs) vs system variables (nouns)
_SYS_FUNCTIONS = frozenset({
    "⎕CR", "⎕FX", "⎕NC", "⎕EX", "⎕SIGNAL", "⎕EA",
    "⎕UCS", "⎕DR", "⎕NREAD", "⎕NWRITE", "⎕NEXISTS", "⎕NDELETE",
    "⎕DL", "⎕FMT", "⎕VFI", "⎕JSON", "⎕NL", "⎕CSV",
})


def _ast_contains(node: object, target_type: type) -> bool:
    """Check if any node in an AST subtree is of target_type."""
    if isinstance(node, target_type):
        return True
    if hasattr(node, '__dict__'):
        for val in node.__dict__.values():
            if isinstance(val, list):
                if any(_ast_contains(item, target_type) for item in val):
                    return True
            elif hasattr(val, '__dict__') and not isinstance(val, type):
                if _ast_contains(val, target_type):
                    return True
    return False


# AST nodes

class Node(ABC):
    """Abstract base for all AST nodes that can be evaluated."""
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__dict__ == other.__dict__
    @abstractmethod
    def execute(self, ctx: object) -> object: ...


class Num(Node):
    def __init__(self, value: int | float) -> None:
        self.value = value
    def execute(self, ctx: object) -> APLArray:
        value = self.value
        if isinstance(value, float) and ctx.env.fr == 1287:  # type: ignore[union-attr]
            from decimal import Decimal
            value = Decimal(str(self.value))
        return S(value)


class Str(Node):
    def __init__(self, value: str) -> None:
        self.value = value
    def execute(self, ctx: object) -> APLArray:
        return APLArray([len(self.value)], list(self.value))


class Vector(Node):
    def __init__(self, elements: list[Num]) -> None:
        self.elements = elements
    def execute(self, ctx: object) -> APLArray:
        values = [el.value for el in self.elements]
        return APLArray([len(values)], list(values))


class MonadicFunc(Node):
    def __init__(self, function: str, operand: object) -> None:
        self.function = function
        self.operand = operand
    def execute(self, ctx: object) -> APLArray:
        operand = ctx.evaluate(self.operand)  # type: ignore[union-attr]
        return ctx.dispatch_monadic(self.function, operand)  # type: ignore[union-attr]


class DyadicFunc(Node):
    def __init__(self, function: str, left: object, right: object) -> None:
        self.function = function
        self.left = left
        self.right = right
    def execute(self, ctx: object) -> APLArray:
        right = ctx.evaluate(self.right)  # type: ignore[union-attr]
        left = ctx.evaluate(self.left)  # type: ignore[union-attr]
        return ctx.dispatch_dyadic(self.function, left, right)  # type: ignore[union-attr]


class Assignment(Node):
    def __init__(self, name: str, value: object) -> None:
        self.name = name
        self.value = value
    def execute(self, ctx: object) -> APLArray:
        return ctx.assign(self.name, self.value)  # type: ignore[union-attr]


class Var(Node):
    def __init__(self, name: str) -> None:
        self.name = name
    def execute(self, ctx: object) -> APLArray:
        if self.name not in ctx.env:  # type: ignore[union-attr]
            raise ValueError_(f"Undefined variable: {self.name}")
        return ctx.env[self.name]  # type: ignore[union-attr]


class QualifiedVar:
    def __init__(self, parts: list[str]) -> None:
        self.parts = parts
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, QualifiedVar):
            return NotImplemented
        return self.parts == other.parts


class DerivedFunc(Node):
    def __init__(self, operator: str, function: str, operand: object) -> None:
        self.operator = operator
        self.function = function
        self.operand = operand
    def execute(self, ctx: object) -> APLArray:
        operand = ctx.evaluate(self.operand)  # type: ignore[union-attr]
        return ctx.apply_derived(self.operator, self.function, operand)  # type: ignore[union-attr]


class MonadicDopCall(Node):
    """User-defined operator applied: (operand op) argument
    or: left (operand op) right (when derived verb is used dyadically)"""
    def __init__(self, op_name: object, operand: object, argument: object,
                 alpha: object = None) -> None:
        self.op_name = op_name    # the operator (Var)
        self.operand = operand    # ⍺⍺ (the left function/array)
        self.argument = argument  # ⍵ (the right argument)
        self.alpha = alpha        # ⍺ (left arg when derived verb used dyadically)
    def execute(self, ctx: object) -> APLArray:
        from marple.dfn_binding import DfnBinding
        dop_val = ctx.evaluate(self.op_name)  # type: ignore[union-attr]
        if not isinstance(dop_val, DfnBinding):
            raise DomainError(f"Expected operator, got {type(dop_val)}")
        operand = ctx.evaluate(self.operand)  # type: ignore[union-attr]
        argument = ctx.evaluate(self.argument)  # type: ignore[union-attr]
        alpha = ctx.evaluate(self.alpha) if self.alpha is not None else None  # type: ignore[union-attr]
        return dop_val.apply(argument, alpha_alpha=operand, alpha=alpha)


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


class SysVar(Node):
    def __init__(self, name: str) -> None:
        self.name = name
    def execute(self, ctx: object) -> APLArray:
        return ctx.eval_sysvar(self.name)  # type: ignore[union-attr]


class Index:
    def __init__(self, array: object, indices: list[object | None]) -> None:
        self.array = array
        self.indices = indices
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Index):
            return NotImplemented
        return self.array == other.array and self.indices == other.indices


class Omega(Node):
    def execute(self, ctx: object) -> APLArray:
        if "⍵" not in ctx.env:  # type: ignore[union-attr]
            raise ValueError_("⍵ used outside of dfn")
        return ctx.env["⍵"]  # type: ignore[union-attr]


class Alpha(Node):
    def execute(self, ctx: object) -> APLArray:
        if "⍺" not in ctx.env:  # type: ignore[union-attr]
            raise ValueError_("⍺ used outside of dfn")
        return ctx.env["⍺"]  # type: ignore[union-attr]


class FunctionRef(Node):
    """A reference to a primitive function glyph, used as a dop operand."""
    def __init__(self, glyph: str) -> None:
        self.glyph = glyph
    def execute(self, ctx: object) -> object:
        return self


class AlphaAlpha(Node):
    """⍺⍺ — left operand reference in a dop."""
    def execute(self, ctx: object) -> object:
        if "⍺⍺" not in ctx.env:  # type: ignore[union-attr]
            raise ValueError_("⍺⍺ used outside of dop")
        return ctx.env["⍺⍺"]  # type: ignore[union-attr]


class OmegaOmega:
    """⍵⍵ — right operand reference in a dop."""
    pass


class BoundOperator:
    """Operator bound to operand(s), not yet applied to argument.

    Created during adverb/conjunction binding (cases 4/5) and resolved
    into final AST nodes during function application (cases 1/3).
    """
    def __init__(self, operator: object, left_operand: object, left_cat: int,
                 right_operand: object = None, right_cat: int = CAT_EMPTY) -> None:
        self.operator = operator           # str ("/","⍤",".",etc) or Var for user dop
        self.left_operand = left_operand   # ⍺⍺ operand node
        self.left_cat = left_cat           # category of left operand (NOUN or VERB)
        self.right_operand = right_operand # ⍵⍵ operand (conjunctions only)
        self.right_cat = right_cat         # category of right operand
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BoundOperator):
            return NotImplemented
        return (self.operator == other.operator and
                self.left_operand == other.left_operand and
                self.right_operand == other.right_operand)


class FmtArgs:
    """List of semicolon-separated arguments for ⎕FMT."""
    def __init__(self, args: list[object]) -> None:
        self.args = args
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FmtArgs):
            return NotImplemented
        return self.args == other.args


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


class Dfn(Node):
    def __init__(self, body: list[object]) -> None:
        self.body = body
    def execute(self, ctx: object) -> object:
        return ctx.create_binding(self)  # type: ignore[union-attr]


class MonadicDfnCall(Node):
    def __init__(self, dfn: object, operand: object) -> None:
        self.dfn = dfn
        self.operand = operand
    def execute(self, ctx: object) -> APLArray:
        from marple.dfn_binding import DfnBinding
        if isinstance(self.dfn, SysVar):
            return ctx.dispatch_sys_monadic(self.dfn.name, self.operand)  # type: ignore[union-attr]
        if isinstance(self.dfn, RankDerived):
            return ctx.apply_rank_monadic(self.dfn, self.operand)  # type: ignore[union-attr]
        dfn_val = ctx.evaluate(self.dfn)  # type: ignore[union-attr]
        operand = ctx.evaluate(self.operand)  # type: ignore[union-attr]
        if isinstance(dfn_val, DfnBinding):
            return dfn_val.apply(operand)
        if isinstance(dfn_val, FunctionRef):
            return ctx.dispatch_monadic(dfn_val.glyph, operand)  # type: ignore[union-attr]
        raise DomainError(f"Expected dfn, got {type(dfn_val)}")


class DyadicDfnCall(Node):
    def __init__(self, dfn: object, left: object, right: object) -> None:
        self.dfn = dfn
        self.left = left
        self.right = right
    def execute(self, ctx: object) -> APLArray:
        from marple.dfn_binding import DfnBinding
        dfn_val = ctx.evaluate(self.dfn)  # type: ignore[union-attr]
        right = ctx.evaluate(self.right)  # type: ignore[union-attr]
        left = ctx.evaluate(self.left)  # type: ignore[union-attr]
        if isinstance(dfn_val, DfnBinding):
            return dfn_val.apply(right, alpha=left)
        raise DomainError(f"Expected dfn, got {type(dfn_val)}")


class Program(Node):
    def __init__(self, statements: list[object]) -> None:
        self.statements = statements
    def execute(self, ctx: object) -> object:
        result: object = S(0)
        for stmt in self.statements:
            result = ctx.evaluate(stmt)  # type: ignore[union-attr]
        return result


class Parser:
    """Stack-based APL parser following Iverson's parsing algorithm.

    Uses a 4-position window on a stack with 9 pattern-matching rules
    to correctly handle operator binding precedence.
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

    # ── Token classification ──

    def _classify_operator(self, op: str) -> int:
        """Classify an operator token as adverb or conjunction."""
        if op in ("/", "\\", "⌿", "⍀", "∘."):
            return CAT_ADV
        if op in ("⍤", "⌶", ".", "∘"):
            return CAT_CONJ
        return CAT_ADV

    def _classify_name(self, name: str) -> int:
        """Classify a name using the name table."""
        if self._is_operator_name(name):
            arity = self._operator_arity.get(name, 1)
            return CAT_ADV if arity == 1 else CAT_CONJ
        if self._is_function_name(name):
            return CAT_VERB
        return CAT_NOUN

    def _classify_sysvar(self, name: str) -> int:
        """Classify a system variable/function."""
        if name in _SYS_FUNCTIONS:
            return CAT_VERB
        return CAT_NOUN

    def _classify_dfn(self, dfn: Dfn) -> int:
        """Classify a dfn as verb, adverb, or conjunction."""
        if _ast_contains(dfn, OmegaOmega):
            return CAT_CONJ
        if _ast_contains(dfn, AlphaAlpha):
            return CAT_ADV
        return CAT_VERB

    # ── Item building (token → classified items) ──

    def _build_items(self) -> list[tuple[int, object]]:
        """Build classified items from current position to expression end.

        Advances self._pos as tokens are consumed. Stops at statement
        boundaries (⋄, :, }, ], ;, EOF) at paren depth 0.
        """
        items: list[tuple[int, object]] = []
        paren_depth = 0
        stop_types = frozenset({
            TokenType.DIAMOND, TokenType.GUARD, TokenType.RBRACE,
            TokenType.RBRACKET, TokenType.SEMICOLON, TokenType.EOF,
            TokenType.LBRACKET,
        })

        while self._pos < len(self._tokens):
            tok = self._current()

            if paren_depth == 0 and tok.type in stop_types:
                break

            if tok.type == TokenType.LPAREN:
                items.append((CAT_LP, None))
                self._pos += 1
                paren_depth += 1

            elif tok.type == TokenType.RPAREN:
                paren_depth -= 1
                if paren_depth < 0:
                    break
                items.append((CAT_RP, None))
                self._pos += 1

            elif tok.type == TokenType.LBRACE:
                dfn = self._parse_dfn()
                cat = self._classify_dfn(dfn)
                items.append((cat, dfn))

            elif tok.type == TokenType.NUMBER:
                node = self._parse_array()
                items.append((CAT_NOUN, node))

            elif tok.type == TokenType.STRING:
                self._pos += 1
                assert isinstance(tok.value, str)
                items.append((CAT_NOUN, Str(tok.value)))

            elif tok.type == TokenType.FUNCTION:
                self._pos += 1
                assert isinstance(tok.value, str)
                items.append((CAT_VERB, tok.value))

            elif tok.type == TokenType.OPERATOR:
                assert isinstance(tok.value, str)
                op = tok.value
                self._pos += 1
                # Compound ∘.f → outer product (pre-bound verb)
                if (op == "∘" and self._pos < len(self._tokens)
                        and self._current().type == TokenType.OPERATOR
                        and self._current().value == "."):
                    self._pos += 1  # consume .
                    fn_tok = self._eat(TokenType.FUNCTION)
                    assert isinstance(fn_tok.value, str)
                    bound = BoundOperator("∘.", fn_tok.value, CAT_VERB)
                    items.append((CAT_VERB, bound))
                # I-beam ⌶'path' → IBeamDerived verb
                elif (op == "⌶" and self._pos < len(self._tokens)
                        and self._current().type == TokenType.STRING):
                    path_tok = self._eat(TokenType.STRING)
                    assert isinstance(path_tok.value, str)
                    items.append((CAT_VERB, IBeamDerived(path_tok.value)))
                else:
                    cat = self._classify_operator(op)
                    items.append((cat, op))

            elif tok.type == TokenType.ASSIGN:
                self._pos += 1
                items.append((CAT_ASGN, "←"))

            elif tok.type == TokenType.ID:
                assert isinstance(tok.value, str)
                name = tok.value
                self._pos += 1
                var_node = Var(name)
                if self._current().type == TokenType.LBRACKET:
                    node = self._parse_bracket_index(var_node)
                    items.append((CAT_NOUN, node))
                elif self._current().type == TokenType.ASSIGN:
                    items.append((CAT_NOUN, var_node))
                else:
                    cat = self._classify_name(name)
                    items.append((cat, var_node))

            elif tok.type == TokenType.SYSVAR:
                assert isinstance(tok.value, str)
                name = tok.value
                self._pos += 1
                sv_node = SysVar(name)
                if self._current().type == TokenType.LBRACKET:
                    node = self._parse_bracket_index(sv_node)
                    items.append((CAT_NOUN, node))
                elif self._current().type == TokenType.ASSIGN:
                    items.append((CAT_NOUN, sv_node))
                elif (name == "⎕FMT"
                      and self._current().type == TokenType.LPAREN):
                    # Special: ⎕FMT (val1;val2;...) — semicolon-separated args
                    items.append((CAT_VERB, sv_node))
                    fmt_args = self._parse_fmt_args()
                    items.append((CAT_NOUN, fmt_args))
                else:
                    cat = self._classify_sysvar(name)
                    items.append((cat, sv_node))

            elif tok.type == TokenType.OMEGA:
                self._pos += 1
                items.append((CAT_NOUN, Omega()))

            elif tok.type == TokenType.ALPHA:
                self._pos += 1
                items.append((CAT_NOUN, Alpha()))

            elif tok.type == TokenType.ALPHA_ALPHA:
                self._pos += 1
                items.append((CAT_NOUN, AlphaAlpha()))

            elif tok.type == TokenType.OMEGA_OMEGA:
                self._pos += 1
                items.append((CAT_NOUN, OmegaOmega()))

            elif tok.type == TokenType.NABLA:
                self._pos += 1
                items.append((CAT_VERB, Nabla()))

            elif tok.type == TokenType.QUALIFIED_NAME:
                assert isinstance(tok.value, str)
                self._pos += 1
                items.append((CAT_NOUN, QualifiedVar(tok.value.split("::"))))

            else:
                raise SyntaxError_(f"Unexpected token: {tok}")

        return items

    def _parse_fmt_args(self) -> FmtArgs:
        """Parse (val1;val2;...) for ⎕FMT. Similar to bracket indexing."""
        self._eat(TokenType.LPAREN)
        args: list[object] = []
        args.append(self._parse_statement())
        while self._current().type == TokenType.SEMICOLON:
            self._eat(TokenType.SEMICOLON)
            args.append(self._parse_statement())
        self._eat(TokenType.RPAREN)
        return FmtArgs(args)

    def _is_callable_noun(self, node: object) -> bool:
        """Check if a NOUN-classified node can act as a function.
        Returns True for: ⍺⍺, ⍵⍵, ∇, all Vars (may be dynamically-defined
        functions), QualifiedVars, system functions, Dfns."""
        if isinstance(node, (AlphaAlpha, OmegaOmega, Nabla, Dfn)):
            return True
        if isinstance(node, (Var, QualifiedVar)):
            return True
        if isinstance(node, SysVar) and node.name in _SYS_FUNCTIONS:
            return True
        return False

    # ── AST construction helpers ──

    def _make_monadic(self, verb_node: object, arg_node: object) -> object:
        """Create AST node for monadic verb application."""
        if isinstance(verb_node, str):
            return MonadicFunc(verb_node, arg_node)
        if isinstance(verb_node, BoundOperator):
            return self._apply_bound_monadic(verb_node, arg_node)
        if isinstance(verb_node, (Var, Dfn, QualifiedVar, Nabla,
                                  AlphaAlpha, OmegaOmega,
                                  RankDerived, IBeamDerived, FunctionRef)):
            return MonadicDfnCall(verb_node, arg_node)
        if isinstance(verb_node, SysVar):
            return MonadicDfnCall(verb_node, arg_node)
        raise SyntaxError_(f"Cannot apply as monadic function: {type(verb_node)}")

    def _make_dyadic(self, verb_node: object, left_node: object,
                     right_node: object) -> object:
        """Create AST node for dyadic verb application."""
        if isinstance(verb_node, str):
            return DyadicFunc(verb_node, left_node, right_node)
        if isinstance(verb_node, BoundOperator):
            return self._apply_bound_dyadic(verb_node, left_node, right_node)
        if isinstance(verb_node, (Var, Dfn, QualifiedVar, Nabla,
                                  AlphaAlpha, OmegaOmega,
                                  RankDerived, IBeamDerived, FunctionRef)):
            return DyadicDfnCall(verb_node, left_node, right_node)
        if isinstance(verb_node, SysVar):
            return DyadicDfnCall(verb_node, left_node, right_node)
        raise SyntaxError_(f"Cannot apply as dyadic function: {type(verb_node)}")

    def _apply_bound_monadic(self, bound: BoundOperator,
                             arg_node: object) -> object:
        """Apply a bound operator (derived verb) monadically."""
        op = bound.operator
        operand = bound.left_operand

        if isinstance(op, str) and op in ("/", "\\", "⌿", "⍀"):
            if (bound.left_cat == CAT_VERB
                    or isinstance(operand, (AlphaAlpha, OmegaOmega))):
                # fn/ → reduce/scan; ⍺⍺/ defers to runtime
                return DerivedFunc(op, operand, arg_node)
            else:
                # noun/ → replicate/expand (treated as dyadic function)
                return DyadicFunc(op, operand, arg_node)

        if isinstance(op, str) and op == "⍤":
            # Rank: fn⍤k applied monadically
            rank_node = RankDerived(operand, bound.right_operand)
            return MonadicDfnCall(rank_node, arg_node)

        if isinstance(op, str) and op == ".":
            # Inner product applied monadically — error
            raise SyntaxError_("Inner product requires two arguments")

        if isinstance(op, str) and op == "∘.":
            # Outer product applied monadically — error
            raise SyntaxError_("Outer product requires two arguments")

        if isinstance(op, str) and op == "⌶":
            # I-beam: ⌶'path' applied monadically
            ibeam = IBeamDerived(operand) if isinstance(operand, str) else operand
            return MonadicDfnCall(ibeam, arg_node)

        # User-defined operator
        if isinstance(op, Var):
            # Wrap primitive glyphs in FunctionRef for the interpreter
            op_operand = FunctionRef(operand) if isinstance(operand, str) else operand
            if bound.right_operand is not None:
                # Dyadic dop (conjunction): op(⍺⍺, ⍵⍵) applied to ⍵
                r_operand = bound.right_operand
                r_operand = FunctionRef(r_operand) if isinstance(r_operand, str) else r_operand
                return DyadicDopCall(op, op_operand, r_operand, arg_node)
            return MonadicDopCall(op, op_operand, arg_node)

        raise SyntaxError_(f"Unknown operator in bound form: {op}")

    def _apply_bound_dyadic(self, bound: BoundOperator,
                            left_node: object, right_node: object) -> object:
        """Apply a bound operator (derived verb) dyadically."""
        op = bound.operator
        operand = bound.left_operand

        if isinstance(op, str) and op == "⍤":
            rank_node = RankDerived(operand, bound.right_operand)
            return DyadicDfnCall(rank_node, left_node, right_node)

        if isinstance(op, str) and op == ".":
            # Inner product: left (f.g) right
            left_fn = operand
            right_fn = bound.right_operand
            return InnerProduct(left_fn, right_fn, left_node, right_node)

        if isinstance(op, str) and op == "∘.":
            # Outer product: left (∘.f) right
            return OuterProduct(operand, left_node, right_node)

        if isinstance(op, str) and op in ("/", "\\", "⌿", "⍀"):
            if (bound.left_cat == CAT_VERB
                    or isinstance(operand, (AlphaAlpha, OmegaOmega))):
                return DerivedFunc(op, operand, right_node)
            else:
                return DyadicFunc(op, operand, right_node)

        # User-defined operator applied dyadically
        if isinstance(op, Var):
            op_operand = FunctionRef(operand) if isinstance(operand, str) else operand
            if bound.right_operand is not None:
                r_operand = bound.right_operand
                r_operand = FunctionRef(r_operand) if isinstance(r_operand, str) else r_operand
                return DyadicDopCall(op, op_operand, r_operand, right_node)
            return MonadicDopCall(op, op_operand, right_node, alpha=left_node)

        raise SyntaxError_(f"Unknown operator in bound dyadic form: {op}")

    # ── Iverson's stack-based parsing algorithm ──

    def _stack_parse(self, items: list[tuple[int, object]]) -> object:
        """Run Iverson's 9-case stack-based parser on classified items.

        Items are processed right-to-left. The stack grows upward.
        stack[-1] = r0 (top/newest), stack[-2] = r1, etc.
        """
        stack: list[tuple[int, object]] = []
        # Items in left-to-right order; pop from right = read right-to-left
        # END marker at position 0 = popped last = leftmost sentinel
        input_q = [(CAT_END, None)] + items

        while True:
            n = len(stack)
            c0 = stack[-1][0] if n >= 1 else CAT_EMPTY
            c1 = stack[-2][0] if n >= 2 else CAT_EMPTY
            c2 = stack[-3][0] if n >= 3 else CAT_EMPTY
            c3 = stack[-4][0] if n >= 4 else CAT_EMPTY

            matched = False

            # Case 1: Monadic function — E/A/V/←/LP  V  N  —
            if (c0 in _CTX_MONAD
                    and c1 == CAT_VERB and c2 == CAT_NOUN):
                verb_node = stack[-2][1]
                arg_node = stack[-3][1]
                result = self._make_monadic(verb_node, arg_node)
                stack[-3:-1] = [(CAT_NOUN, result)]
                matched = True

            # Case 1.5: Callable noun as monadic function
            # Handles ⍺⍺, ⍵⍵, ∇, named functions, Vars applied monadically
            # Skip when deeper callable+noun exists (let case 3.6 handle it)
            elif (c0 in _CTX_MONAD
                    and c1 == CAT_NOUN and c2 == CAT_NOUN
                    and self._is_callable_noun(stack[-2][1])
                    and not (n >= 4 and c3 == CAT_NOUN
                             and self._is_callable_noun(stack[-3][1]))):
                verb_node = stack[-2][1]
                arg_node = stack[-3][1]
                result = self._make_monadic(verb_node, arg_node)
                stack[-3:-1] = [(CAT_NOUN, result)]
                matched = True

            # Case 2: Monadic fn (conjunction context) — C  N  V  N
            elif (c0 == CAT_CONJ and c1 == CAT_NOUN
                    and c2 == CAT_VERB and c3 == CAT_NOUN):
                verb_node = stack[-3][1]
                arg_node = stack[-4][1]
                result = self._make_monadic(verb_node, arg_node)
                stack[-4:-2] = [(CAT_NOUN, result)]
                matched = True

            # Case 3: Dyadic function — E/N/A/V/←/LP  N  V  N
            elif (c0 in _CTX_DYAD
                    and c1 == CAT_NOUN and c2 == CAT_VERB
                    and c3 == CAT_NOUN):
                left_node = stack[-2][1]
                verb_node = stack[-3][1]
                right_node = stack[-4][1]
                result = self._make_dyadic(verb_node, left_node, right_node)
                stack[-4:-1] = [(CAT_NOUN, result)]
                matched = True

            # Case 3.5: Dyadic callable noun — N(non-callable) N(callable) N
            # E.g. `3 add 4` where add is a dynamically-defined function
            elif (c0 in _CTX_DYAD
                    and c1 == CAT_NOUN and c2 == CAT_NOUN
                    and c3 == CAT_NOUN
                    and not self._is_callable_noun(stack[-2][1])
                    and self._is_callable_noun(stack[-3][1])):
                left_node = stack[-2][1]
                verb_node = stack[-3][1]
                right_node = stack[-4][1]
                result = self._make_dyadic(verb_node, left_node, right_node)
                stack[-4:-1] = [(CAT_NOUN, result)]
                matched = True

            # Case 3.6: Deep monadic chain — N(callable) N(callable) N
            # E.g. `⍺⍺ ⍺⍺ ⍵`: bind deeper pair first for right-to-left eval
            elif (c0 in _CTX_DYAD
                    and c2 == CAT_NOUN and c3 == CAT_NOUN
                    and self._is_callable_noun(stack[-3][1])):
                verb_node = stack[-3][1]
                arg_node = stack[-4][1]
                result = self._make_monadic(verb_node, arg_node)
                stack[-4:-2] = [(CAT_NOUN, result)]
                matched = True

            # Case 4: Adverb binding — E/N/A/V/←/LP  N/V  A  —
            elif (c0 in _CTX_DYAD
                    and c1 in (CAT_NOUN, CAT_VERB) and c2 == CAT_ADV):
                operand_node = stack[-2][1]
                operand_cat = stack[-2][0]
                adv_node = stack[-3][1]
                bound = BoundOperator(adv_node, operand_node, operand_cat)
                stack[-3:-1] = [(CAT_VERB, bound)]
                matched = True

            # Case 5: Conjunction binding — E/N/A/V/←/LP  N/V  C  N/V
            elif (c0 in _CTX_DYAD
                    and c1 in (CAT_NOUN, CAT_VERB) and c2 == CAT_CONJ
                    and c3 in (CAT_NOUN, CAT_VERB)):
                left_operand = stack[-2][1]
                left_cat = stack[-2][0]
                conj_node = stack[-3][1]
                right_operand = stack[-4][1]
                right_cat = stack[-4][0]
                bound = BoundOperator(conj_node, left_operand, left_cat,
                                      right_operand, right_cat)
                stack[-4:-1] = [(CAT_VERB, bound)]
                matched = True

            # Case 6: Assignment — N/name  ←  N/V/A/C  —
            elif (c0 in (CAT_NOUN,) and c1 == CAT_ASGN
                    and c2 in (CAT_NOUN, CAT_VERB, CAT_ADV, CAT_CONJ)):
                name_node = stack[-1][1]
                value_node = stack[-3][1]
                value_cat = stack[-3][0]
                if isinstance(name_node, (Var, SysVar)):
                    name_str = name_node.name
                else:
                    raise SyntaxError_(f"Invalid assignment target: {name_node}")
                result = Assignment(name_str, value_node)
                stack[-3:] = [(value_cat, result)]
                matched = True

            # Case 7: Parentheses — LP  N/A/C/V  RP  —
            elif (c0 == CAT_LP
                    and c1 in (CAT_NOUN, CAT_ADV, CAT_CONJ, CAT_VERB)
                    and c2 == CAT_RP):
                inner_cat = stack[-2][0]
                inner_node = stack[-2][1]
                stack[-3:] = [(inner_cat, inner_node)]
                matched = True

            if not matched:
                # Cases 8/9: Shift next item from input
                if input_q:
                    stack.append(input_q.pop())
                else:
                    break

        # Extract result — should be END + result on stack
        # Find the result (skip END markers)
        result_node = None
        for cat, node in stack:
            if cat != CAT_END and node is not None:
                result_node = node
        if result_node is None:
            return Num(0)
        return result_node

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
        """Parse a statement using Iverson's stack-based algorithm."""
        items = self._build_items()
        if not items:
            return Num(0)
        result = self._stack_parse(items)
        # Handle trailing bracket indexing: result[idx]
        if (self._pos < len(self._tokens)
                and self._current().type == TokenType.LBRACKET):
            result = self._parse_bracket_index(result)
        return result

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
