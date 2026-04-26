from typing import Callable

from marple.apl_value import Function, Operator
from marple.errors import SyntaxError_
from marple.executor import ( 
    Adverb,
    make_adverb,
    make_conjunction,
    ReduceAdverb,
    ScanAdverb,
    InnerProductConjunction,
    OuterProductAdverb,
    Alpha,
    AlphaAlpha,
    AlphaDefault,
    Applicable,
    AssignmentArrow,
    Assignment,
    Conjunction,
    AtopDerived,
    BesideDerived,
    BoundOperator,
    CAT_EMPTY,
    CommuteDerived,
    DerivedFunc,
    Dfn,
    DyadicDfnCall,
    DyadicDopCall,
    DyadicFunc,
    Executable,
    Executor,
    OperatorOperand,
    Reference,
    FmtArgs,
    ForkDerived,
    Marker,
    _MARKER,
    PrimitiveFunction,
    Guard,
    Index,
    MonadicDfnCall,
    MonadicDopCall,
    MonadicFunc,
    Nabla,
    Node,
    Num,
    Omega,
    OmegaOmega,
    PowerDerived,
    Program,
    QualifiedVar,
    RankDerived,
    ReduceDerived,
    ScanDerived,
    Str,
    SysVar,
    SysFunc,
    UnappliedFunction,
    Var,
    Vector,
    Zilde,
)
from marple.tokenizer import (
    Token,
    Tokenizer,
    AssignToken,
    DiamondToken,
    EofToken,
    GuardToken,
    LBraceToken,
    LBracketToken,
    LParenToken,
    OperatorToken,
    RBraceToken,
    RBracketToken,
    RParenToken,
    SemicolonToken,
)



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

# Adverbs that also have dyadic function meanings — compress,
# replicate, expand, and replicate-first. When one of these appears
# as the left operand of a conjunction with no function available
# on its left as an operator-operand, it is promoted to its function
# role via PrimitiveFunction (see Case 4.5 in `_stack_parse`). `⍨` is
# excluded because commute is a pure operator with no dyadic
# function meaning; `⍀` is excluded because dyadic `⍀` is not yet
# registered in dyadic_functions.
_ADV_AS_FN_GLYPHS = frozenset({"/", "\\", "⌿"})

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

    def __init__(self, tokens: list[Node], name_table: dict[str, int] | None = None,
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
        if op in ("/", "\\", "⌿", "⍀", "∘.", "⍨", "⌶"):
            return CAT_ADV
        if op in ("⍤", "⍣", ".", "∘"):
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

    def _classify_sysvar(self, node: 'SysVar | SysFunc') -> int:
        """Classify a system variable or function node. `SysFunc`
        is a verb; plain `SysVar` is a noun."""
        return CAT_VERB if isinstance(node, SysFunc) else CAT_NOUN

    def _classify_dfn(self, dfn: Dfn) -> int:
        """Classify a dfn as verb, adverb, or conjunction."""
        if _ast_contains(dfn, OmegaOmega):
            return CAT_CONJ
        if _ast_contains(dfn, AlphaAlpha):
            return CAT_ADV
        return CAT_VERB

    # ── Item building (token → classified items) ──

    def _build_items(self) -> list[tuple[int, Node]]:
        """Build classified items from current position to expression end.

        Advances self._pos as tokens are consumed. Stops at statement
        boundaries (⋄, :, }, ], ;, EOF) at paren depth 0.
        """
        items: list[tuple[int, Node]] = []
        paren_depth = 0
        stop_types: tuple[type[Token], ...] = (
            DiamondToken, GuardToken, RBraceToken,
            RBracketToken, SemicolonToken, EofToken,
            LBracketToken,
        )

        while self._pos < len(self._tokens):
            tok = self._current()

            if paren_depth == 0 and isinstance(tok, stop_types):
                break

            # Parens need inline handling — they track paren_depth state
            if isinstance(tok, LParenToken):
                items.append((CAT_LP, _MARKER))
                self._pos += 1
                paren_depth += 1
                continue
            # TODO: that break looks suspicious: would it hide a syntax error?
            if isinstance(tok, RParenToken):
                paren_depth -= 1
                if paren_depth < 0:
                    break
                items.append((CAT_RP, _MARKER))
                self._pos += 1
                # (expr)[idx] — bracket index binds to parenthesised expression
                if (paren_depth == 0
                        and self._pos < len(self._tokens)
                        and isinstance(self._current(), LBracketToken)):
                    # Reduce the paren group we just closed, then apply [idx]
                    lp_pos = len(items) - 1
                    while lp_pos >= 0 and items[lp_pos][0] != CAT_LP:
                        lp_pos -= 1
                    if lp_pos >= 0:
                        paren_items = items[lp_pos + 1:-1]  # between LP and RP
                        inner = self._stack_parse(paren_items)
                        node = self._parse_bracket_index(inner)
                        items[lp_pos:] = [(CAT_NOUN, node)]
                continue

            handler = self._ITEM_DISPATCH.get(type(tok))
            if handler is not None:
                handler(self, tok, items)
            else:
                raise SyntaxError_(f"Unexpected token: {tok}")

        return items

    def _item_lbrace(self, tok: object, items: list[tuple[int, Node]]) -> None:
        dfn = self._parse_dfn()
        cat = self._classify_dfn(dfn)
        items.append((cat, dfn))

    def _item_number(self, tok: object, items: list[tuple[int, Node]]) -> None:
        node: Executable = self._parse_array()
        if isinstance(self._current(), LBracketToken):
            node = self._parse_bracket_index(node)
        items.append((CAT_NOUN, node))

    def _item_string(self, tok: object, items: list[tuple[int, Node]]) -> None:
        assert isinstance(tok, Str)
        self._pos += 1
        node: object = tok
        if isinstance(self._current(), LBracketToken):
            node = self._parse_bracket_index(tok)
        items.append((CAT_NOUN, node))

    def _item_function(self, tok: object, items: list[tuple[int, Node]]) -> None:
        assert isinstance(tok, PrimitiveFunction)
        self._pos += 1
        items.append((CAT_VERB, tok))

    def _item_operator(self, tok: object, items: list[tuple[int, Node]]) -> None:
        assert isinstance(tok, OperatorToken)
        op = tok.glyph
        self._pos += 1
        next_tok = self._current()
        if (op == "∘" and self._pos < len(self._tokens)
                and isinstance(next_tok, OperatorToken)
                and next_tok.glyph == "."):
            self._pos += 1
            fn_node = self._current()
            if not isinstance(fn_node, PrimitiveFunction):
                raise SyntaxError_(f"Expected primitive function after ∘., got {fn_node}")
            self._pos += 1
            bound = BoundOperator(make_adverb("∘."), fn_node, CAT_VERB)
            items.append((CAT_VERB, bound))
        else:
            cat = self._classify_operator(op)
            axis: Executable | None = None
            if cat == CAT_ADV and op in ("/", "\\", "⌿", "⍀") \
                    and isinstance(self._current(), LBracketToken):
                axis = self._parse_axis_spec()
            op_node: Adverb | Conjunction = (
                make_adverb(op, axis) if cat == CAT_ADV else make_conjunction(op)
            )
            items.append((cat, op_node))

    def _parse_axis_spec(self) -> Executable:
        """Parse a bracketed axis expression: `[expr]`."""
        self._eat(LBracketToken)
        start = self._pos
        depth = 0
        while self._pos < len(self._tokens):
            tok = self._current()
            if isinstance(tok, LBracketToken):
                depth += 1
            elif isinstance(tok, RBracketToken):
                if depth == 0:
                    break
                depth -= 1
            self._pos += 1
        if self._pos >= len(self._tokens):
            raise SyntaxError_("Unterminated axis specifier")
        axis_tokens = self._tokens[start:self._pos]
        self._eat(RBracketToken)
        if not axis_tokens:
            raise SyntaxError_("Empty axis specifier")
        sub_parser = Parser(axis_tokens + [EofToken()],
                             self._name_table, self._operator_arity)
        return sub_parser.parse()

    def _item_assign(self, tok: object, items: list[tuple[int, Node]]) -> None:
        self._pos += 1
        items.append((CAT_ASGN, AssignmentArrow()))

    def _item_id(self, tok: object, items: list[tuple[int, Node]]) -> None:
        assert isinstance(tok, Var)
        self._pos += 1
        if isinstance(self._current(), LBracketToken):
            items.append((CAT_NOUN, self._parse_bracket_index(tok)))
        elif isinstance(self._current(), AssignToken):
            items.append((CAT_NOUN, tok))
        else:
            items.append((self._classify_name(tok.name), tok))

    def _item_sysvar(self, tok: object, items: list[tuple[int, Node]]) -> None:
        assert isinstance(tok, (SysVar, SysFunc))
        self._pos += 1
        if isinstance(self._current(), LBracketToken):
            items.append((CAT_NOUN, self._parse_bracket_index(tok)))
        elif isinstance(self._current(), AssignToken):
            items.append((CAT_NOUN, tok))
        elif (tok.name == "⎕FMT"
              and isinstance(self._current(), LParenToken)):
            items.append((CAT_VERB, tok))
            items.append((CAT_NOUN, self._parse_fmt_args()))
        else:
            items.append((self._classify_sysvar(tok), tok))

    def _item_omega(self, tok: object, items: list[tuple[int, Node]]) -> None:
        assert isinstance(tok, Omega)
        self._pos += 1
        items.append((CAT_NOUN, tok))

    def _item_alpha(self, tok: object, items: list[tuple[int, Node]]) -> None:
        assert isinstance(tok, Alpha)
        self._pos += 1
        items.append((CAT_NOUN, tok))

    def _item_alpha_alpha(self, tok: object, items: list[tuple[int, Node]]) -> None:
        assert isinstance(tok, AlphaAlpha)
        self._pos += 1
        items.append((CAT_NOUN, tok))

    def _item_omega_omega(self, tok: object, items: list[tuple[int, Node]]) -> None:
        assert isinstance(tok, OmegaOmega)
        self._pos += 1
        items.append((CAT_NOUN, tok))

    def _item_nabla(self, tok: object, items: list[tuple[int, Node]]) -> None:
        assert isinstance(tok, Nabla)
        self._pos += 1
        items.append((CAT_VERB, tok))

    def _item_zilde(self, tok: object, items: list[tuple[int, Node]]) -> None:
        assert isinstance(tok, Zilde)
        self._pos += 1
        items.append((CAT_NOUN, tok))

    def _item_qualified_name(self, tok: object, items: list[tuple[int, Node]]) -> None:
        assert isinstance(tok, QualifiedVar)
        self._pos += 1
        items.append((CAT_NOUN, tok))

    _ITEM_DISPATCH: dict[type, Callable[['Parser', object, list[tuple[int, Node]]], None]] = {
        LBraceToken: _item_lbrace,
        Num: _item_number,
        Str: _item_string,
        PrimitiveFunction: _item_function,
        OperatorToken: _item_operator,
        AssignToken: _item_assign,
        Var: _item_id,
        SysVar: _item_sysvar,
        SysFunc: _item_sysvar,
        Omega: _item_omega,
        Alpha: _item_alpha,
        AlphaAlpha: _item_alpha_alpha,
        OmegaOmega: _item_omega_omega,
        Nabla: _item_nabla,
        QualifiedVar: _item_qualified_name,
        Zilde: _item_zilde,
    }

    def _parse_fmt_args(self) -> FmtArgs:
        """Parse (val1;val2;...) for ⎕FMT. Similar to bracket indexing."""
        self._eat(LParenToken)
        args: list[Executable] = []
        args.append(self._parse_statement())
        while isinstance(self._current(), SemicolonToken):
            self._eat(SemicolonToken)
            args.append(self._parse_statement())
        self._eat(RParenToken)
        return FmtArgs(args)

    def _is_callable_noun(self, node: object) -> bool:
        """Check if a NOUN-classified node can act as a function.
        Returns True for: ⍺⍺, ⍵⍵, ∇, all Vars (may be dynamically-defined
        functions), QualifiedVars, system functions, Dfns."""
        if isinstance(node, (AlphaAlpha, OmegaOmega, Nabla, Dfn)):
            return True
        if isinstance(node, (Var, QualifiedVar)):
            return True
        if isinstance(node, SysFunc):
            return True
        return False

    # ── AST construction helpers ──

    @staticmethod
    def _as_evaluatable(item: Node) -> Executable:
        """Narrow a stack item to Executable. Items classified as
        CAT_NOUN or used as operands are always Executable; anything
        else (typically a BoundOperator left on the stack because
        no derivation path matched) is a syntax error."""
        if not isinstance(item, Executable):
            raise SyntaxError_(f"Cannot evaluate {type(item).__name__} as an expression")
        return item

    def _make_monadic(self, verb_node: Node, arg_node: Executable) -> Executable:
        """Create AST node for monadic verb application."""
        if isinstance(verb_node, PrimitiveFunction):
            return MonadicFunc(verb_node.glyph, arg_node)
        if isinstance(verb_node, BoundOperator):
            return self._apply_bound_monadic(verb_node, arg_node)
        if isinstance(verb_node, (Reference, UnappliedFunction)):
            return MonadicDfnCall(verb_node, arg_node)
        raise SyntaxError_(f"Cannot apply as monadic function: {type(verb_node)}")

    def _make_dyadic(self, verb_node: Node, left_node: Executable,
                     right_node: Executable) -> Executable:
        """Create AST node for dyadic verb application."""
        if isinstance(verb_node, PrimitiveFunction):
            return DyadicFunc(verb_node.glyph, left_node, right_node)
        if isinstance(verb_node, BoundOperator):
            return self._apply_bound_dyadic(verb_node, left_node, right_node)
        if isinstance(verb_node, (Reference, UnappliedFunction)):
            return DyadicDfnCall(verb_node, left_node, right_node)
        raise SyntaxError_(f"Cannot apply as dyadic function: {type(verb_node)}")

    def _apply_bound_monadic(self, bound: BoundOperator,
                             arg_node: Executable) -> Executable:
        """Apply a bound operator (derived verb) monadically."""
        op = bound.operator
        if isinstance(op, Var):
            return self._apply_user_dop_monadic(bound, arg_node)
        if not isinstance(op, (Adverb, Conjunction)):
            raise SyntaxError_(f"Unknown operator in bound form: {op}")
        if isinstance(op, (ReduceAdverb, ScanAdverb)):
            return self._bound_monadic_reduce(bound, arg_node)
        if isinstance(op, (InnerProductConjunction, OuterProductAdverb)):
            raise SyntaxError_(f"{type(op).__name__} requires two arguments")
        return MonadicDfnCall(self._bound_to_derived(bound), arg_node)

    def _bound_monadic_reduce(self, bound: BoundOperator, arg_node: Executable) -> Executable:
        assert isinstance(bound.operator, (ReduceAdverb, ScanAdverb))
        operand = bound.left_operand
        if (bound.left_cat == CAT_VERB
                or isinstance(operand, (AlphaAlpha, OmegaOmega))):
            assert isinstance(operand, Executable)
            return DerivedFunc(bound.operator, operand, arg_node)
        return DyadicFunc(bound.operator.symbol, self._as_evaluatable(operand), arg_node)

    def _apply_user_dop_monadic(self, bound: BoundOperator, arg_node: Executable) -> Executable:
        assert isinstance(bound.operator, Var)
        operand = self._as_evaluatable(bound.left_operand)
        if bound.right_operand is not None:
            return DyadicDopCall(bound.operator, operand, self._as_evaluatable(bound.right_operand), arg_node)
        return MonadicDopCall(bound.operator, operand, arg_node)

    def _apply_bound_dyadic(self, bound: BoundOperator,
                            left_node: Executable, right_node: Executable) -> Executable:
        """Apply a bound operator (derived verb) dyadically."""
        op = bound.operator
        if isinstance(op, Var):
            return self._apply_user_dop_dyadic(bound, left_node, right_node)
        if not isinstance(op, (Adverb, Conjunction)):
            raise SyntaxError_(f"Unknown operator in bound dyadic form: {op}")
        if isinstance(op, (ReduceAdverb, ScanAdverb)):
            return self._bound_dyadic_reduce(bound, left_node, right_node)
        return DyadicDfnCall(self._bound_to_derived(bound), left_node, right_node)

    def _bound_dyadic_reduce(self, bound: BoundOperator,
                             left_node: Executable, right_node: Executable) -> Executable:
        assert isinstance(bound.operator, (ReduceAdverb, ScanAdverb))
        operand = bound.left_operand
        if (bound.left_cat == CAT_VERB
                or isinstance(operand, (AlphaAlpha, OmegaOmega))):
            assert isinstance(operand, Executable)
            return DerivedFunc(bound.operator, operand, right_node)
        return DyadicFunc(bound.operator.symbol, self._as_evaluatable(operand), right_node)

    def _apply_user_dop_dyadic(self, bound: BoundOperator,
                               left_node: Executable, right_node: Executable) -> Executable:
        assert isinstance(bound.operator, Var)
        operand = self._as_evaluatable(bound.left_operand)
        if bound.right_operand is not None:
            return DyadicDopCall(bound.operator, operand, self._as_evaluatable(bound.right_operand), right_node)
        return MonadicDopCall(bound.operator, operand, right_node, alpha=left_node)

    def _resolve_right_operand(self, bound: BoundOperator) -> 'OperatorOperand':
        """Resolve the right operand of a conjunction (must exist)."""
        assert bound.right_operand is not None
        return self._resolve_operand(bound.right_operand)

    def _resolve_operand(self, operand: Node) -> 'OperatorOperand':
        """Resolve an operator operand. May be applicable (most operators)
        or a non-applicable Executable (numeric rank spec, power count)."""
        if isinstance(operand, BoundOperator):
            return self._bound_to_derived(operand)
        assert isinstance(operand, OperatorOperand)
        return operand

    def _bound_to_derived(self, bound: BoundOperator) -> UnappliedFunction:
        """Convert a BoundOperator to its unwrapped derived-function
        form, for storage in a variable via assignment.

        Resolves operands then delegates to the operator's own
        derive_monadic / derive_dyadic so the dispatch lives with the
        operator type, not here.
        """
        op = bound.operator
        assert isinstance(op, Operator)
        left = self._resolve_operand(bound.left_operand)
        if isinstance(op, Adverb):
            result = op.derive_monadic(left)
        elif isinstance(op, Conjunction):
            right = self._resolve_right_operand(bound)
            result = op.derive_dyadic(left, right)
        else:
            raise SyntaxError_(f"Cannot store operator {op} as a function")
        assert isinstance(result, UnappliedFunction)
        return result

    def _build_train(self, items: list[OperatorOperand]) -> UnappliedFunction:
        """Build a train node from items (source left-to-right order).

          2 items → AtopDerived(g, h)
          3 items → ForkDerived(f, g, h)

        Items at positions other than ForkDerived.f must be Applicable
        (functions). ForkDerived.f can be a non-applicable Executable
        in the Agh-fork form `(A g h)`.
        """
        def _require_fn(item: 'OperatorOperand', position: str) -> Applicable:
            if not isinstance(item, Applicable):
                raise SyntaxError_(f"{position} of train must be a function")
            return item
        if len(items) == 2:
            return AtopDerived(_require_fn(items[0], "g"), _require_fn(items[1], "h"))
        if len(items) == 3:
            return ForkDerived(items[0], _require_fn(items[1], "g"), _require_fn(items[2], "h"))
        # N items: bind rightmost 3 into a fork, recurse on (N-2) items
        inner = ForkDerived(
            _require_fn(items[-3], "f"),
            _require_fn(items[-2], "g"),
            _require_fn(items[-1], "h"),
        )
        return self._build_train(items[:-3] + [inner])

    def _resolve_assignment_value(self, value_node: Node,
                                  value_cat: int) -> Executable | UnappliedFunction:
        """Convert a Case 6 value_node into a form that `ctx.assign`
        can store directly.

        Node subclasses (including PrimitiveFunction) are returned as-is.
        BoundOperator instances from derived functions unwrap to the
        appropriate *Derived class so that applying `f` later
        dispatches correctly.
        """
        if isinstance(value_node, BoundOperator):
            return self._bound_to_derived(value_node)
        if isinstance(value_node, (Executable, UnappliedFunction)):
            return value_node
        raise SyntaxError_(f"Invalid assignment value: {value_node}")

    # ── Iverson's stack-based parsing algorithm ──

    def _stack_parse(self, items: list[tuple[int, Node]]) -> Executable:
        """Run Iverson's 9-case stack-based parser on classified items.

        Items are processed right-to-left. The stack grows upward.
        stack[-1] = r0 (top/newest), stack[-2] = r1, etc.
        """
        stack: list[tuple[int, Node]] = []
        # Items in left-to-right order; pop from right = read right-to-left
        # END marker at position 0 = popped last = leftmost sentinel
        input_q = [(CAT_END, _MARKER)] + items

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
                arg_node = self._as_evaluatable(stack[-3][1])
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
                arg_node = self._as_evaluatable(stack[-3][1])
                result = self._make_monadic(verb_node, arg_node)
                stack[-3:-1] = [(CAT_NOUN, result)]
                matched = True

            # Case 2: Monadic fn (conjunction context) — C  N  V  N
            elif (c0 == CAT_CONJ and c1 == CAT_NOUN
                    and c2 == CAT_VERB and c3 == CAT_NOUN):
                verb_node = stack[-3][1]
                arg_node = self._as_evaluatable(stack[-4][1])
                result = self._make_monadic(verb_node, arg_node)
                stack[-4:-2] = [(CAT_NOUN, result)]
                matched = True

            # Case 3: Dyadic function — E/N/A/V/←/LP  N  V  N
            elif (c0 in _CTX_DYAD
                    and c1 == CAT_NOUN and c2 == CAT_VERB
                    and c3 == CAT_NOUN):
                left_node = self._as_evaluatable(stack[-2][1])
                verb_node = stack[-3][1]
                right_node = self._as_evaluatable(stack[-4][1])
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
                left_node = self._as_evaluatable(stack[-2][1])
                verb_node = stack[-3][1]
                right_node = self._as_evaluatable(stack[-4][1])
                result = self._make_dyadic(verb_node, left_node, right_node)
                stack[-4:-1] = [(CAT_NOUN, result)]
                matched = True

            # Case 3.6: Deep monadic chain — N(callable) N(callable) N
            # E.g. `⍺⍺ ⍺⍺ ⍵`: bind deeper pair first for right-to-left eval
            elif (c0 in _CTX_DYAD
                    and c2 == CAT_NOUN and c3 == CAT_NOUN
                    and self._is_callable_noun(stack[-3][1])):
                verb_node = stack[-3][1]
                arg_node = self._as_evaluatable(stack[-4][1])
                result = self._make_monadic(verb_node, arg_node)
                stack[-4:-2] = [(CAT_NOUN, result)]
                matched = True

            # Case 4: Adverb binding — E/N/A/V/←/LP  N/V  A  —
            elif (c0 in _CTX_DYAD
                    and c1 in (CAT_NOUN, CAT_VERB) and c2 == CAT_ADV):
                operand_node = stack[-2][1]
                operand_cat = stack[-2][0]
                adv_node = stack[-3][1]
                assert isinstance(adv_node, (Adverb, Var))
                assert isinstance(operand_node, (Node, BoundOperator))
                bound = BoundOperator(adv_node, operand_node, operand_cat)
                stack[-3:-1] = [(CAT_VERB, bound)]
                matched = True

            # Case 4.5: Adverb-as-function promotion for / \ ⌿ when
            # used as the left operand to a conjunction. Fires only
            # when a "closed" left context (END, LP, ASGN) makes it
            # impossible for an operator-operand to ever arrive for
            # the adverb. This implements Dyalog's rule: "/ is a
            # function unless it has a function operand on its left".
            elif (c0 in (CAT_END, CAT_LP, CAT_ASGN)
                    and c1 == CAT_ADV
                    and c2 == CAT_CONJ
                    and isinstance(stack[-2][1], (ReduceAdverb, ScanAdverb))
                    and stack[-2][1].symbol in _ADV_AS_FN_GLYPHS):
                adv = stack[-2][1]
                stack[-2] = (CAT_VERB, PrimitiveFunction(adv.symbol))
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
                assert isinstance(conj_node, (Conjunction, Var))
                assert isinstance(left_operand, (Node, BoundOperator))
                assert isinstance(right_operand, (Node, BoundOperator))
                bound = BoundOperator(conj_node, left_operand, left_cat,
                                      right_operand, right_cat)
                stack[-4:-1] = [(CAT_VERB, bound)]
                matched = True

            # Case 6.5: Train reduction — LP V V ... boundary
            # Also accepts a leading NOUN for Agh-fork: (A g h)
            elif (c0 in (CAT_LP, CAT_ASGN, CAT_END)
                    and c1 in (CAT_VERB, CAT_NOUN)
                    and c2 == CAT_VERB):
                train_items: list[OperatorOperand] = []
                leading_noun = False
                i = 2
                while i <= len(stack):
                    cat, _node = stack[-i]
                    if cat == CAT_VERB:
                        train_items.append(self._resolve_operand(_node))
                    elif cat == CAT_NOUN and len(train_items) == 0:
                        assert isinstance(_node, OperatorOperand)
                        train_items.append(_node)
                        leading_noun = True
                    else:
                        break
                    i += 1
                # A leading noun is only valid in a 3-train (Agh-fork).
                # In longer trains it would end up as atop's g, which
                # is nonsense — don't match, let the parser error.
                if leading_noun and len(train_items) != 3:
                    pass
                elif len(train_items) >= 2:
                    train = self._build_train(train_items)
                    stack[-(i - 1):-1] = [(CAT_VERB, train)]
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
                value_node = self._resolve_assignment_value(value_node, value_cat)
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

        # Extract result — should be END + single result on stack
        results = [(cat, node) for cat, node in stack if cat != CAT_END and not isinstance(node, Marker)]
        if len(results) == 0:
            return Num(0)
        if len(results) > 1:
            raise SyntaxError_(
                "Expression could not be fully parsed"
            )
        return self._as_evaluatable(results[0][1])

    def _current(self) -> Node:
        return self._tokens[self._pos]

    def _peek(self) -> 'Node | None':
        if self._pos + 1 < len(self._tokens):
            return self._tokens[self._pos + 1]
        return None

    def _eat(self, token_type: type) -> 'Node':
        token = self._current()
        if not isinstance(token, token_type):
            raise SyntaxError_(f"Expected {token_type.__name__}, got {type(token).__name__}")
        self._pos += 1
        return token

    def _parse_dfn(self) -> Dfn:
        """Parse a dfn: { statement (⋄ statement)* }"""
        self._eat(LBraceToken)
        statements: list[Executable | Guard | AlphaDefault] = []
        while not isinstance(self._current(), (RBraceToken, EofToken)):
            stmt = self._parse_dfn_statement()
            statements.append(stmt)
            if isinstance(self._current(), DiamondToken):
                self._eat(DiamondToken)
        if isinstance(self._current(), EofToken):
            raise SyntaxError_("Unmatched {")
        self._eat(RBraceToken)
        return Dfn(statements)

    def _parse_dfn_statement(self) -> Executable | Guard | AlphaDefault:
        """Parse a statement inside a dfn, handling guards and ⍺← default."""
        # Check for ⍺← default
        peek = self._peek()
        if (
            isinstance(self._current(), Alpha)
            and peek is not None
            and isinstance(peek, AssignToken)
        ):
            self._pos += 1  # consume ⍺
            self._eat(AssignToken)
            default = self._parse_statement()
            return AlphaDefault(default)

        stmt = self._parse_statement()
        # Check for guard: expr : expr
        if isinstance(self._current(), GuardToken):
            self._eat(GuardToken)
            body = self._parse_statement()
            return Guard(stmt, body)
        return stmt

    def _parse_atom(self) -> Executable:
        token = self._current()
        if isinstance(token, LParenToken):
            return self._parse_paren()
        if isinstance(token, LBraceToken):
            return self._parse_dfn()
        if isinstance(token, Executable):
            # Value tokens (Num, Str, Var, PrimitiveFunction, Omega,
            # Alpha, AlphaAlpha, OmegaOmega, Nabla, Zilde, SysVar,
            # SysFunc, QualifiedVar) are already AST nodes.
            self._pos += 1
            return token
        raise SyntaxError_(f"Unexpected token: {token}")

    def _parse_paren(self) -> Executable:
        """Parse `(expr)` or the bare-function-glyph form `(+)`/`(-)`."""
        self._eat(LParenToken)
        # Bare function glyph as operand: (-), (+), (⍳), etc.
        next_tok = self._current()
        if (
            isinstance(next_tok, PrimitiveFunction)
            and self._pos + 1 < len(self._tokens)
            and isinstance(self._tokens[self._pos + 1], RParenToken)
        ):
            self._pos += 1
            self._eat(RParenToken)
            return next_tok
        result = self._parse_statement()
        self._eat(RParenToken)
        return result

    def _parse_atom_with_index(self) -> Executable:
        """Parse an atom, then check for bracket indexing."""
        atom = self._parse_atom()
        if isinstance(self._current(), LBracketToken):
            return self._parse_bracket_index(atom)
        return atom

    def _parse_bracket_index(self, array: Executable) -> Index:
        """Parse [idx] or [i1;i2;…] — each slot may be empty."""
        self._eat(LBracketToken)
        indices: list[Executable | None] = []
        while True:
            # Peek: an empty slot is one where the next token is the
            # slot terminator (; or ]) rather than the start of an expr.
            if isinstance(self._current(), (SemicolonToken, RBracketToken)):
                indices.append(None)
            else:
                indices.append(self._parse_statement())
            if isinstance(self._current(), RBracketToken):
                break
            self._eat(SemicolonToken)
        self._eat(RBracketToken)
        return Index(array, indices)

    _ARRAY_START_TYPES: tuple[type, ...] = (
        Num, LParenToken, Var,
        Omega, Alpha, AlphaAlpha,
        OmegaOmega, Nabla,
        LBraceToken, Str, QualifiedVar,
        SysVar, SysFunc, Zilde,
    )

    def _is_array_start(self) -> bool:
        return isinstance(self._current(), self._ARRAY_START_TYPES)

    def _parse_array(self) -> Executable:
        """Parse one or more adjacent numeric atoms as a vector,
        or a single non-numeric atom."""
        first = self._parse_atom_with_index()
        if not isinstance(first, Num):
            return first
        elements: list[Num] = [first]
        while isinstance(self._current(), Num):
            token = self._current()
            assert isinstance(token, Num)
            self._pos += 1
            elements.append(token)
        if len(elements) == 1:
            return elements[0]
        return Vector(elements)

    def _parse_function_expr(self) -> tuple[str, str | None]:
        """Parse a function glyph, possibly followed by an operator.
        Returns (function_glyph, operator_glyph_or_None)."""
        func_node = self._current()
        if not isinstance(func_node, PrimitiveFunction):
            raise SyntaxError_(f"Expected function, got {func_node}")
        self._pos += 1
        if isinstance(self._current(), OperatorToken):
            op_token = self._current()
            assert isinstance(op_token, OperatorToken)
            self._pos += 1
            return func_node.glyph, op_token.glyph
        return func_node.glyph, None

    def _parse_statement(self) -> Executable:
        """Parse a statement using Iverson's stack-based algorithm."""
        items = self._build_items()
        if not items:
            return Num(0)
        result = self._stack_parse(items)
        # Handle trailing bracket indexing: result[idx]
        if (self._pos < len(self._tokens)
                and isinstance(self._current(), LBracketToken)):
            result = self._parse_bracket_index(result)
        return result

    def parse(self) -> Executable:
        # Empty input (e.g. comment-only line) → return Num(0) as no-op
        if isinstance(self._current(), EofToken):
            return Num(0)
        statements = [self._parse_statement()]
        while isinstance(self._current(), DiamondToken):
            self._eat(DiamondToken)
            statements.append(self._parse_statement())
        if not isinstance(self._current(), EofToken):
            raise SyntaxError_(f"Unexpected token after expression: {self._current()}")
        if len(statements) == 1:
            return statements[0]
        return Program(statements)


def parse(source: str, name_table: dict[str, int] | None = None,
          operator_arity: dict[str, int] | None = None) -> Executable:
    tokens = Tokenizer(source).tokenize()
    return Parser(tokens, name_table, operator_arity).parse()


def is_balanced(source: str) -> bool:
    """Check if braces and brackets are balanced.

    Returns True if the source has matching { } pairs.
    Returns False if there are unclosed openers (incomplete input).
    """
    depth = 0
    in_string = False
    for ch in source:
        if ch == "'" and not in_string:
            in_string = True
        elif ch == "'" and in_string:
            in_string = False
        elif not in_string:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
    return depth == 0
