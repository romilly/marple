from typing import Callable

from marple.errors import SyntaxError_
from marple.nodes import (  # noqa: F401 — re-exported for backward compatibility
    Alpha,
    AlphaAlpha,
    AlphaDefault,
    Assignment,
    BoundOperator,
    CAT_EMPTY,
    DerivedFunc,
    Dfn,
    DyadicDfnCall,
    DyadicDopCall,
    DyadicFunc,
    ExecutionContext,
    FmtArgs,
    FunctionRef,
    Guard,
    IBeamDerived,
    Index,
    InnerProduct,
    MonadicDfnCall,
    MonadicDopCall,
    MonadicFunc,
    Nabla,
    Node,
    Num,
    Omega,
    OmegaOmega,
    OuterProduct,
    Program,
    QualifiedVar,
    RankDerived,
    ReduceOp,
    ScanOp,
    Str,
    SysVar,
    Var,
    Vector,
)
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
# CAT_EMPTY imported from nodes

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

            # Parens need inline handling — they track paren_depth state
            if tok.type == TokenType.LPAREN:
                items.append((CAT_LP, None))
                self._pos += 1
                paren_depth += 1
                continue
            if tok.type == TokenType.RPAREN:
                paren_depth -= 1
                if paren_depth < 0:
                    break
                items.append((CAT_RP, None))
                self._pos += 1
                continue

            handler = self._ITEM_DISPATCH.get(tok.type)
            if handler is not None:
                handler(self, tok, items)
            else:
                raise SyntaxError_(f"Unexpected token: {tok}")

        return items

    def _item_lbrace(self, tok: Token, items: list[tuple[int, object]]) -> None:
        dfn = self._parse_dfn()
        cat = self._classify_dfn(dfn)
        items.append((cat, dfn))

    def _item_number(self, tok: Token, items: list[tuple[int, object]]) -> None:
        node = self._parse_array()
        items.append((CAT_NOUN, node))

    def _item_string(self, tok: Token, items: list[tuple[int, object]]) -> None:
        self._pos += 1
        assert isinstance(tok.value, str)
        items.append((CAT_NOUN, Str(tok.value)))

    def _item_function(self, tok: Token, items: list[tuple[int, object]]) -> None:
        self._pos += 1
        assert isinstance(tok.value, str)
        items.append((CAT_VERB, tok.value))

    def _item_operator(self, tok: Token, items: list[tuple[int, object]]) -> None:
        assert isinstance(tok.value, str)
        op = tok.value
        self._pos += 1
        if (op == "∘" and self._pos < len(self._tokens)
                and self._current().type == TokenType.OPERATOR
                and self._current().value == "."):
            self._pos += 1
            fn_tok = self._eat(TokenType.FUNCTION)
            assert isinstance(fn_tok.value, str)
            bound = BoundOperator("∘.", fn_tok.value, CAT_VERB)
            items.append((CAT_VERB, bound))
        elif (op == "⌶" and self._pos < len(self._tokens)
                and self._current().type == TokenType.STRING):
            path_tok = self._eat(TokenType.STRING)
            assert isinstance(path_tok.value, str)
            items.append((CAT_VERB, IBeamDerived(path_tok.value)))
        else:
            cat = self._classify_operator(op)
            items.append((cat, op))

    def _item_assign(self, tok: Token, items: list[tuple[int, object]]) -> None:
        self._pos += 1
        items.append((CAT_ASGN, "←"))

    def _item_id(self, tok: Token, items: list[tuple[int, object]]) -> None:
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

    def _item_sysvar(self, tok: Token, items: list[tuple[int, object]]) -> None:
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
            items.append((CAT_VERB, sv_node))
            fmt_args = self._parse_fmt_args()
            items.append((CAT_NOUN, fmt_args))
        else:
            cat = self._classify_sysvar(name)
            items.append((cat, sv_node))

    def _item_omega(self, tok: Token, items: list[tuple[int, object]]) -> None:
        self._pos += 1
        items.append((CAT_NOUN, Omega()))

    def _item_alpha(self, tok: Token, items: list[tuple[int, object]]) -> None:
        self._pos += 1
        items.append((CAT_NOUN, Alpha()))

    def _item_alpha_alpha(self, tok: Token, items: list[tuple[int, object]]) -> None:
        self._pos += 1
        items.append((CAT_NOUN, AlphaAlpha()))

    def _item_omega_omega(self, tok: Token, items: list[tuple[int, object]]) -> None:
        self._pos += 1
        items.append((CAT_NOUN, OmegaOmega()))

    def _item_nabla(self, tok: Token, items: list[tuple[int, object]]) -> None:
        self._pos += 1
        items.append((CAT_VERB, Nabla()))

    def _item_qualified_name(self, tok: Token, items: list[tuple[int, object]]) -> None:
        assert isinstance(tok.value, str)
        self._pos += 1
        items.append((CAT_NOUN, QualifiedVar(tok.value.split("::"))))

    _ITEM_DISPATCH: dict[str, Callable[['Parser', Token, list[tuple[int, object]]], None]] = {
        TokenType.LBRACE: _item_lbrace,
        TokenType.NUMBER: _item_number,
        TokenType.STRING: _item_string,
        TokenType.FUNCTION: _item_function,
        TokenType.OPERATOR: _item_operator,
        TokenType.ASSIGN: _item_assign,
        TokenType.ID: _item_id,
        TokenType.SYSVAR: _item_sysvar,
        TokenType.OMEGA: _item_omega,
        TokenType.ALPHA: _item_alpha,
        TokenType.ALPHA_ALPHA: _item_alpha_alpha,
        TokenType.OMEGA_OMEGA: _item_omega_omega,
        TokenType.NABLA: _item_nabla,
        TokenType.QUALIFIED_NAME: _item_qualified_name,
    }

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
        if isinstance(op, Var):
            return self._apply_user_dop_monadic(bound, arg_node)
        if not isinstance(op, str):
            raise SyntaxError_(f"Unknown operator in bound form: {op}")
        handler = self._BOUND_MONADIC_DISPATCH.get(op)
        if handler is not None:
            return handler(self, bound, arg_node)
        raise SyntaxError_(f"Unknown operator in bound form: {op}")

    def _bound_monadic_reduce(self, bound: BoundOperator, arg_node: object) -> object:
        operand = bound.left_operand
        op = bound.operator
        if (bound.left_cat == CAT_VERB
                or isinstance(operand, (AlphaAlpha, OmegaOmega))):
            return DerivedFunc(op, operand, arg_node)
        return DyadicFunc(op, operand, arg_node)

    def _bound_monadic_rank(self, bound: BoundOperator, arg_node: object) -> object:
        rank_node = RankDerived(bound.left_operand, bound.right_operand)
        return MonadicDfnCall(rank_node, arg_node)

    def _bound_monadic_inner(self, bound: BoundOperator, arg_node: object) -> object:
        raise SyntaxError_("Inner product requires two arguments")

    def _bound_monadic_outer(self, bound: BoundOperator, arg_node: object) -> object:
        raise SyntaxError_("Outer product requires two arguments")

    def _bound_monadic_ibeam(self, bound: BoundOperator, arg_node: object) -> object:
        operand = bound.left_operand
        ibeam = IBeamDerived(operand) if isinstance(operand, str) else operand
        return MonadicDfnCall(ibeam, arg_node)

    def _apply_user_dop_monadic(self, bound: BoundOperator, arg_node: object) -> object:
        operand = bound.left_operand
        op_operand = FunctionRef(operand) if isinstance(operand, str) else operand
        if bound.right_operand is not None:
            r_operand = bound.right_operand
            r_operand = FunctionRef(r_operand) if isinstance(r_operand, str) else r_operand
            return DyadicDopCall(bound.operator, op_operand, r_operand, arg_node)
        return MonadicDopCall(bound.operator, op_operand, arg_node)

    _BOUND_MONADIC_DISPATCH: dict[str, Callable[['Parser', BoundOperator, object], object]] = {
        "/": _bound_monadic_reduce,
        "\\": _bound_monadic_reduce,
        "⌿": _bound_monadic_reduce,
        "⍀": _bound_monadic_reduce,
        "⍤": _bound_monadic_rank,
        ".": _bound_monadic_inner,
        "∘.": _bound_monadic_outer,
        "⌶": _bound_monadic_ibeam,
    }

    def _apply_bound_dyadic(self, bound: BoundOperator,
                            left_node: object, right_node: object) -> object:
        """Apply a bound operator (derived verb) dyadically."""
        op = bound.operator
        if isinstance(op, Var):
            return self._apply_user_dop_dyadic(bound, left_node, right_node)
        if not isinstance(op, str):
            raise SyntaxError_(f"Unknown operator in bound dyadic form: {op}")
        handler = self._BOUND_DYADIC_DISPATCH.get(op)
        if handler is not None:
            return handler(self, bound, left_node, right_node)
        raise SyntaxError_(f"Unknown operator in bound dyadic form: {op}")

    def _bound_dyadic_rank(self, bound: BoundOperator,
                           left_node: object, right_node: object) -> object:
        rank_node = RankDerived(bound.left_operand, bound.right_operand)
        return DyadicDfnCall(rank_node, left_node, right_node)

    def _bound_dyadic_inner(self, bound: BoundOperator,
                            left_node: object, right_node: object) -> object:
        return InnerProduct(bound.left_operand, bound.right_operand,
                            left_node, right_node)

    def _bound_dyadic_outer(self, bound: BoundOperator,
                            left_node: object, right_node: object) -> object:
        return OuterProduct(bound.left_operand, left_node, right_node)

    def _bound_dyadic_reduce(self, bound: BoundOperator,
                             left_node: object, right_node: object) -> object:
        operand = bound.left_operand
        op = bound.operator
        if (bound.left_cat == CAT_VERB
                or isinstance(operand, (AlphaAlpha, OmegaOmega))):
            return DerivedFunc(op, operand, right_node)
        return DyadicFunc(op, operand, right_node)

    def _apply_user_dop_dyadic(self, bound: BoundOperator,
                               left_node: object, right_node: object) -> object:
        operand = bound.left_operand
        op_operand = FunctionRef(operand) if isinstance(operand, str) else operand
        if bound.right_operand is not None:
            r_operand = bound.right_operand
            r_operand = FunctionRef(r_operand) if isinstance(r_operand, str) else r_operand
            return DyadicDopCall(bound.operator, op_operand, r_operand, right_node)
        return MonadicDopCall(bound.operator, op_operand, right_node, alpha=left_node)

    _BOUND_DYADIC_DISPATCH: dict[str, Callable[['Parser', BoundOperator, object, object], object]] = {
        "⍤": _bound_dyadic_rank,
        ".": _bound_dyadic_inner,
        "∘.": _bound_dyadic_outer,
        "/": _bound_dyadic_reduce,
        "\\": _bound_dyadic_reduce,
        "⌿": _bound_dyadic_reduce,
        "⍀": _bound_dyadic_reduce,
    }

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

    def _eat(self, token_type: str) -> Token:
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
            and self._peek().type == TokenType.ASSIGN
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
