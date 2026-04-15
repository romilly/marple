"""AST node classes for MARPLE."""


from abc import ABC, abstractmethod
from itertools import product
from typing import Any, Callable, Protocol

from marple.numpy_array import APLArray, S
from marple.backend_functions import is_numeric_array, maybe_upcast
from marple.errors import DomainError, SyntaxError_, ValueError_
from marple.apl_value import NC_FUNCTION, APLValue, Function, Operator, PowerByConvergence, PowerByCount, PowerStrategy


_INNER_SCALAR_OPS: dict[str, Callable[[Any, Any], Any]] = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "×": lambda a, b: a * b,
    "÷": lambda a, b: a / b,
    "⌈": lambda a, b: max(a, b),
    "⌊": lambda a, b: min(a, b),
    "*": lambda a, b: a ** b,
    "|": lambda a, b: b % a,
    "∧": lambda a, b: int(bool(a) and bool(b)),
    "∨": lambda a, b: int(bool(a) or bool(b)),
    "=": lambda a, b: int(a == b),
    "≠": lambda a, b: int(a != b),
    "<": lambda a, b: int(a < b),
    "≤": lambda a, b: int(a <= b),
    ">": lambda a, b: int(a > b),
    "≥": lambda a, b: int(a >= b),
}


def _inner_product(
    reduce_glyph: str, apply_glyph: str, alpha: APLArray, omega: APLArray,
) -> APLArray:
    """Compute inner product: alpha reduce_fn.apply_fn omega.

    Result shape is (¯1↓⍴alpha),(1↓⍴omega).
    Last axis of alpha must match first axis of omega.
    """
    from marple.errors import DomainError, LengthError
    from marple.get_numpy import np
    reduce_op = _INNER_SCALAR_OPS.get(reduce_glyph)
    apply_op = _INNER_SCALAR_OPS.get(apply_glyph)
    if reduce_op is None:
        raise DomainError(f"Unknown function for inner product: {reduce_glyph}")
    if apply_op is None:
        raise DomainError(f"Unknown function for inner product: {apply_glyph}")
    a_shape = alpha.shape if alpha.shape else [1]
    b_shape = omega.shape if omega.shape else [1]
    k = a_shape[-1]
    if k != b_shape[0]:
        raise LengthError(f"Inner product length error: {a_shape} vs {b_shape}")
    # Fast path: +.× uses np.dot (correct when at least one arg is rank ≤ 2)
    if (reduce_glyph == "+" and apply_glyph == "×"
            and is_numeric_array(alpha.data) and is_numeric_array(omega.data)
            and (len(a_shape) <= 2 or len(b_shape) <= 2)):
        try:
            with np.errstate(over="raise", invalid="raise"):
                result = np.dot(maybe_upcast(alpha.data), maybe_upcast(omega.data))
        except FloatingPointError:
            raise DomainError("arithmetic overflow in inner product")
        if not hasattr(result, 'shape') or result.shape == ():
            return S(int(result) if float(result) == int(result) else float(result))
        return APLArray(list(result.shape), result)
    result_shape = a_shape[:-1] + b_shape[1:]
    if not result_shape:
        paired = [apply_op(alpha.data[(p,)], omega.data[(p,)]) for p in range(k)]
        acc = paired[-1]
        for i in range(len(paired) - 2, -1, -1):
            acc = reduce_op(paired[i], acc)
        return S(acc)
    result = np.zeros(tuple(result_shape))
    a_outer = [range(s) for s in a_shape[:-1]]
    b_outer = [range(s) for s in b_shape[1:]]
    for a_idx in product(*a_outer):
        for b_idx in product(*b_outer):
            paired = [apply_op(alpha.data[a_idx + (p,)], omega.data[(p,) + b_idx])
                      for p in range(k)]
            acc = paired[-1]
            for i in range(len(paired) - 2, -1, -1):
                acc = reduce_op(paired[i], acc)
            result[a_idx + b_idx] = acc
    return APLArray(result_shape, result)


_OUTER_UFUNCS: dict[str, str] = {
    "+": 'add',
    "-": 'subtract',
    "×": 'multiply',
    "÷": 'true_divide',
    "⌈": 'maximum',
    "⌊": 'minimum',
    "*": 'power',
    "=": 'equal',
    "≠": 'not_equal',
    "<": 'less',
    "≤": 'less_equal',
    ">": 'greater',
    "≥": 'greater_equal',
}


def _outer_product(glyph: str, alpha: APLArray, omega: APLArray) -> APLArray:
    """Compute outer product: alpha ∘.func omega."""
    from marple.errors import DomainError
    from marple.get_numpy import np
    # Fast path: use numpy ufunc.outer for numeric operands.
    if is_numeric_array(alpha.data) and is_numeric_array(omega.data):
        ufunc_name = _OUTER_UFUNCS.get(glyph)
        if ufunc_name is not None:
            ufunc = getattr(np, ufunc_name, None)
            if ufunc is not None and hasattr(ufunc, 'outer'):
                try:
                    with np.errstate(over="raise", invalid="raise"):
                        result = ufunc.outer(
                            maybe_upcast(alpha.data.flatten()),
                            maybe_upcast(omega.data.flatten()),
                        )
                except FloatingPointError:
                    raise DomainError("arithmetic overflow in outer product")
                result_shape = alpha.shape + omega.shape
                return APLArray(result_shape, result.reshape(result_shape))
    # General path
    op = _INNER_SCALAR_OPS.get(glyph)
    if op is None:
        raise DomainError(f"Unknown function for outer product: {glyph}")
    result_shape = alpha.shape + omega.shape
    if not result_shape:
        try:
            with np.errstate(over="raise", invalid="raise"):
                return S(op(alpha.data[()], omega.data[()]))
        except FloatingPointError:
            raise DomainError("arithmetic overflow in outer product")
    result = np.zeros(tuple(result_shape))
    a_indices = [range(s) for s in alpha.shape]
    b_indices = [range(s) for s in omega.shape]
    try:
        with np.errstate(over="raise", invalid="raise"):
            for a_idx in product(*a_indices):
                for b_idx in product(*b_indices):
                    result[a_idx + b_idx] = op(alpha.data[a_idx], omega.data[b_idx])
    except FloatingPointError:
        raise DomainError("arithmetic overflow in outer product")
    return APLArray(result_shape, result)


class ExecutionContext(Protocol):
    """Interface that AST nodes use to evaluate sub-expressions."""
    env: Any
    def evaluate(self, node: 'Executable') -> APLArray: ...
    def dispatch_monadic(self, glyph: str, operand: APLArray) -> APLArray: ...
    def dispatch_dyadic(self, glyph: str, left: APLArray, right: APLArray) -> APLArray: ...
    def apply_derived(self, operator: str, function: 'Executable', operand: APLArray, axis: int | None = None) -> APLArray: ...
    def assign(self, name: str, value_node: 'Executable | UnappliedFunction') -> APLArray: ...
    def eval_sysvar(self, name: str) -> APLArray: ...
    def create_binding(self, dfn_node: 'Dfn') -> APLValue: ...
    def dispatch_sys_monadic(self, name: str, operand_node: 'Executable') -> APLArray: ...
    def dispatch_sys_dyadic(self, name: str, left_node: 'Executable', right_node: 'Executable') -> APLArray: ...
    def resolve_qualified(self, parts: list[str]) -> APLValue: ...


class Node(ABC):
    """Abstract base for all items on the parser stack."""
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__dict__ == other.__dict__


class Adverb(Operator, Node):
    """Abstract base: a monadic operator on the parser stack.

    Concrete subclasses per glyph (CommuteAdverb, ReduceAdverb, …)
    override derive_monadic with glyph-specific behaviour. The base
    carries no state; instances are only created via `make_adverb`.
    """


class Conjunction(Operator, Node):
    """Abstract base: a dyadic operator on the parser stack.

    Concrete subclasses per glyph (RankConjunction, PowerConjunction,
    BesideConjunction, InnerProductConjunction) override derive_dyadic.
    The base carries no state.
    """


class CommuteAdverb(Adverb):
    """Monadic operator ⍨ — commute."""
    def derive_monadic(self, operand: 'Applicable') -> Function:
        return CommuteDerived(operand)


class ReduceAdverb(Adverb):
    """Monadic operator / or ⌿ — reduce along last or first axis.

    Carries the symbol (/ vs ⌿ — default axis distinction) and an
    optional explicit axis from a bracketed specifier `/[k]`.
    """
    def __init__(self, symbol: str, axis: 'Executable | None' = None) -> None:
        self.symbol = symbol
        self.axis = axis

    def derive_monadic(self, operand: 'Applicable') -> Function:
        return ReduceDerived(self, operand)


class ScanAdverb(Adverb):
    """Monadic operator \\ or ⍀ — scan along last or first axis."""
    def __init__(self, symbol: str, axis: 'Executable | None' = None) -> None:
        self.symbol = symbol
        self.axis = axis

    def derive_monadic(self, operand: 'Applicable') -> Function:
        return ScanDerived(self, operand)


class RankConjunction(Conjunction):
    """Dyadic operator ⍤ — rank."""
    def derive_dyadic(self, left: 'Applicable', right: 'Applicable') -> Function:
        assert isinstance(right, Executable)
        return RankDerived(left, right)


class PowerConjunction(Conjunction):
    """Dyadic operator ⍣ — power."""
    def derive_dyadic(self, left: 'Applicable', right: 'Applicable') -> Function:
        assert isinstance(right, Executable)
        return PowerDerived(left, right)


class BesideConjunction(Conjunction):
    """Dyadic operator ∘ — composition / beside."""
    def derive_dyadic(self, left: 'Applicable', right: 'Applicable') -> Function:
        return BesideDerived(left, right)


class InnerProductConjunction(Conjunction):
    """Dyadic operator `.` — inner product (e.g. +.× for dot-product / matrix-multiply)."""
    def derive_dyadic(self, left: 'Applicable', right: 'Applicable') -> Function:
        assert isinstance(left, PrimitiveFunction)
        assert isinstance(right, PrimitiveFunction)
        return InnerDerived(left, right)


class OuterProductAdverb(Adverb):
    """Monadic operator `∘.` — outer product (e.g. ∘.× for multiplication table).

    Parser combines the `∘`, `.`, and the function token into a pre-bound
    unit at parse time; the function becomes the single operand here.
    """
    def derive_monadic(self, operand: 'Applicable') -> Function:
        assert isinstance(operand, PrimitiveFunction)
        return OuterDerived(operand)


class IBeamAdverb(Adverb):
    """Monadic operator ⌶ — selects a built-in i-beam service by integer code.

    `(A⌶)` derives a function that, when applied, evaluates A, looks up
    the registered Python implementation, and invokes it.
    """
    def derive_monadic(self, operand: 'Applicable') -> Function:
        assert isinstance(operand, Executable)
        return IBeamFunction(operand)


_ADVERB_FACTORIES: dict[str, Callable[[str, 'Executable | None'], Adverb]] = {
    "⍨": lambda _s, _a: CommuteAdverb(),
    "/": lambda s, a: ReduceAdverb(s, a),
    "⌿": lambda s, a: ReduceAdverb(s, a),
    "\\": lambda s, a: ScanAdverb(s, a),
    "⍀": lambda s, a: ScanAdverb(s, a),
    "∘.": lambda _s, _a: OuterProductAdverb(),
    "⌶": lambda _s, _a: IBeamAdverb(),
}


_CONJUNCTION_FACTORIES: dict[str, Callable[[], Conjunction]] = {
    "⍤": RankConjunction,
    "⍣": PowerConjunction,
    "∘": BesideConjunction,
    ".": InnerProductConjunction,
}


def make_adverb(symbol: str, axis: 'Executable | None' = None) -> Adverb:
    """Construct the Adverb subclass for a glyph. Raises on unknown glyph.

    `axis` is an Executable for bracketed forms like /[k]; only reduce
    and scan variants consult it, others ignore.
    """
    factory = _ADVERB_FACTORIES.get(symbol)
    if factory is None:
        raise ValueError_(f"Unknown adverb glyph: {symbol}")
    return factory(symbol, axis)


def make_conjunction(symbol: str) -> Conjunction:
    """Construct the Conjunction subclass for a glyph. Raises on unknown glyph."""
    factory = _CONJUNCTION_FACTORIES.get(symbol)
    if factory is None:
        raise ValueError_(f"Unknown conjunction glyph: {symbol}")
    return factory()


class AssignmentArrow(Node):
    """Sentinel for the assignment arrow (←) on the parser stack."""


class Marker(Node):
    """Sentinel for LP, RP, and END positions on the parser stack."""


_MARKER = Marker()


class Executable(Node):
    """A Node that can be executed to produce a value.

    Convenience apply/call/dop/power methods execute then dispatch;
    each narrows the executed value to the kind it needs (Function,
    Operator, or — for power — APLArray).
    """
    @abstractmethod
    def execute(self, ctx: ExecutionContext) -> APLValue: ...

    def _as_function(self, ctx: ExecutionContext) -> Function:
        val = self.execute(ctx)
        if not isinstance(val, Function):
            raise DomainError(f"Cannot apply {type(val).__name__} as a function")
        return val

    def _as_operator(self, ctx: ExecutionContext) -> Operator:
        val = self.execute(ctx)
        if not isinstance(val, Operator):
            raise DomainError(f"Cannot apply {type(val).__name__} as an operator")
        return val

    def apply_to_monadic(self, ctx: ExecutionContext, omega: APLArray) -> APLArray:
        return self._as_function(ctx).apply_to_monadic(ctx, omega)

    def apply_to_dyadic(self, ctx: ExecutionContext, alpha: APLArray, omega: APLArray) -> APLArray:
        return self._as_function(ctx).apply_to_dyadic(ctx, alpha, omega)

    def apply_monadic(self, ctx: ExecutionContext, operand_node: 'Executable') -> APLArray:
        return self._as_function(ctx).apply_monadic(ctx, operand_node)

    def apply_dyadic(self, ctx: ExecutionContext, left_node: 'Executable', right_node: 'Executable') -> APLArray:
        return self._as_function(ctx).apply_dyadic(ctx, left_node, right_node)

    def apply_monadic_dop(self, ctx: ExecutionContext, argument: APLArray,
                          operand: APLValue, alpha: APLArray | None = None) -> APLArray:
        return self._as_operator(ctx).apply_monadic_dop(ctx, argument, operand, alpha)

    def apply_dyadic_dop(self, ctx: ExecutionContext, argument: APLArray,
                         left_operand: APLValue, right_operand: APLValue) -> APLArray:
        return self._as_operator(ctx).apply_dyadic_dop(ctx, argument, left_operand, right_operand)

    def as_power_strategy(self, ctx: ExecutionContext) -> 'PowerStrategy':
        val = self.execute(ctx)
        if not isinstance(val, (Function, APLArray)):
            raise DomainError("⍣ right operand must be integer or function")
        return val.as_power_strategy(ctx)


class Reference(Executable):
    """An Executable that does not compute, but resolves to a value.

    A Reference produces an existing value by name/operand lookup
    rather than by computing a new array. `resolve()` is the truthful
    operation — it returns whatever the resolution yields (an
    APLArray, Function, or Operator). `execute()` is a thin shim
    that just forwards to `resolve()`, keeping Reference usable
    where an Executable is expected. Array-narrowing happens at
    `ctx.evaluate`, the same place it happens for any Executable.

    Examples: `Var`, `AlphaAlpha`/`OmegaOmega`, `Nabla`, `Dfn`.
    """
    @abstractmethod
    def resolve(self, ctx: ExecutionContext) -> APLValue: ...

    def execute(self, ctx: ExecutionContext) -> APLValue:
        return self.resolve(ctx)


# `Applicable` is the set of things that can be applied as a function:
# Function values, and Executable AST nodes that execute or resolve
# to one (Reference is an Executable subclass). Runtime union so
# both type annotations and isinstance checks work (Python 3.10+
# supports `isinstance(x, A | B)`).
Applicable = Function | Executable


class Literal(Executable):
    """Wrapper: an already-evaluated APLArray as a Node."""
    def __init__(self, value: APLArray) -> None:
        self.value = value
    def execute(self, ctx: ExecutionContext) -> APLArray:
        return self.value


class Num(Executable):
    def __init__(self, value: int | float) -> None:
        self.value = value
    def execute(self, ctx: ExecutionContext) -> APLArray:
        value = self.value
        if isinstance(value, float) and ctx.env.fr == 1287:
            from decimal import Decimal
            value = Decimal(str(self.value))
        return S(value)


class Str(Executable):
    def __init__(self, value: str) -> None:
        self.value = value
    def execute(self, ctx: ExecutionContext) -> APLArray:
        # All string literals are uint32 character arrays.
        # Single-char literals are scalars (shape []) backed by 0-d
        # uint32 data, constructed via S() so the storage convention
        # matches numeric scalars.
        from marple.backend_functions import str_to_char_array
        if len(self.value) == 1:
            return S(self.value)
        return APLArray([len(self.value)], str_to_char_array(self.value))


class Vector(Executable):
    def __init__(self, elements: list[Num]) -> None:
        self.elements = elements
    def execute(self, ctx: ExecutionContext) -> APLArray:
        values = [el.value for el in self.elements]
        return APLArray.array([len(values)], list(values))


class Zilde(Executable):
    """⍬ — the empty numeric vector literal (equivalent to ⍳0)."""
    def execute(self, ctx: ExecutionContext) -> APLArray:
        return APLArray.array([0], [])


class MonadicFunc(Executable):
    def __init__(self, function: str, operand: Executable) -> None:
        self.function = function
        self.operand = operand
    def execute(self, ctx: ExecutionContext) -> APLArray:
        operand = ctx.evaluate(self.operand)
        return ctx.dispatch_monadic(self.function, operand)


class DyadicFunc(Executable):
    def __init__(self, function: str, left: Executable, right: Executable) -> None:
        self.function = function
        self.left = left
        self.right = right
    def execute(self, ctx: ExecutionContext) -> APLArray:
        right = ctx.evaluate(self.right)
        left = ctx.evaluate(self.left)
        return ctx.dispatch_dyadic(self.function, left, right)


class Assignment(Executable):
    def __init__(self, name: str, value: 'Executable | UnappliedFunction') -> None:
        self.name = name
        self.value = value
    def execute(self, ctx: ExecutionContext) -> APLArray:
        return ctx.assign(self.name, self.value)


class Var(Reference):
    def __init__(self, name: str) -> None:
        self.name = name
    def resolve(self, ctx: ExecutionContext) -> APLValue:
        if self.name not in ctx.env:
            raise ValueError_(f"Undefined variable: {self.name}")
        return ctx.env[self.name]


class QualifiedVar(Reference):
    def __init__(self, parts: list[str]) -> None:
        self.parts = parts
    def resolve(self, ctx: ExecutionContext) -> APLValue:
        return ctx.resolve_qualified(self.parts)


def _resolve_axis(op: 'ReduceAdverb | ScanAdverb', ctx: 'ExecutionContext') -> int | None:
    """Evaluate the bracketed axis expression on a reduce/scan operator.

    Returns a 0-based axis index (with ⎕IO adjustment applied), or None
    if the operator carries no explicit axis (the backend will apply
    the per-glyph default).
    """
    if op.axis is None:
        return None
    value = ctx.evaluate(op.axis)
    if list(value.shape) != []:
        raise DomainError("Axis specifier must be a scalar")
    axis_io = int(value.data.item())
    return axis_io - ctx.env.io


class DerivedFunc(Executable):
    def __init__(self, operator: 'ReduceAdverb | ScanAdverb', function: Executable, operand: Executable) -> None:
        self.operator = operator
        self.function = function
        self.operand = operand
    def execute(self, ctx: ExecutionContext) -> APLArray:
        operand = ctx.evaluate(self.operand)
        axis = _resolve_axis(self.operator, ctx)
        return ctx.apply_derived(self.operator.symbol, self.function, operand, axis)


class MonadicDopCall(Executable):
    """User-defined operator applied: (operand op) argument
    or: left (operand op) right (when derived verb is used dyadically)"""
    def __init__(self, op_name: 'Executable', operand: Executable, argument: Executable,
                 alpha: Executable | None = None) -> None:
        self.op_name = op_name
        self.operand = operand
        self.argument = argument
        self.alpha = alpha
    def execute(self, ctx: ExecutionContext) -> APLArray:
        operand = self.operand.execute(ctx)
        argument = ctx.evaluate(self.argument)
        alpha = ctx.evaluate(self.alpha) if self.alpha is not None else None
        return self.op_name.apply_monadic_dop(ctx, argument, operand, alpha)


class DyadicDopCall(Executable):
    """User-defined operator applied dyadically: left (operand op) right"""
    def __init__(self, op_name: 'Executable', operand: Executable, left: Executable, right: Executable) -> None:
        self.op_name = op_name
        self.operand = operand
        self.left = left
        self.right = right
    def execute(self, ctx: ExecutionContext) -> APLArray:
        left_operand = self.operand.execute(ctx)    # ⍺⍺
        right_operand = self.left.execute(ctx)      # ⍵⍵
        argument = ctx.evaluate(self.right)           # ⍵
        return self.op_name.apply_dyadic_dop(ctx, argument, left_operand, right_operand)


class UnappliedFunction(Function, Node):
    """Bridge class for function values that also participate as AST nodes.

    All apply/call behaviour is inherited from `Function`. Node is
    inherited so derived-function values can live on the parser stack
    alongside other nodes.
    """


class RankDerived(UnappliedFunction):
    """Unapplied rank-derived function: f⍤k"""
    def __init__(self, function: Applicable, rank_spec: Executable) -> None:
        self.function = function
        self.rank_spec = rank_spec
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RankDerived):
            return NotImplemented
        return self.function == other.function and self.rank_spec == other.rank_spec
    def apply_monadic(self, ctx: ExecutionContext, operand_node: Executable) -> APLArray:
        from marple.cells import clamp_rank, decompose, reassemble, resolve_rank_spec
        omega = ctx.evaluate(operand_node)
        rank_spec_val = ctx.evaluate(self.rank_spec)
        a, _, _ = resolve_rank_spec(rank_spec_val)
        k = clamp_rank(a, len(omega.shape))
        frame_shape, cells = decompose(omega, k)
        results = [self.function.apply_to_monadic(ctx, cell) for cell in cells]
        return reassemble(frame_shape, results)

    def apply_dyadic(self, ctx: ExecutionContext, left_node: Executable, right_node: Executable) -> APLArray:
        from marple.cells import clamp_rank, decompose, reassemble, resolve_rank_spec
        from marple.errors import LengthError
        alpha = ctx.evaluate(left_node)
        omega = ctx.evaluate(right_node)
        rank_spec_val = ctx.evaluate(self.rank_spec)
        _, b_rank, c_rank = resolve_rank_spec(rank_spec_val)
        b = clamp_rank(b_rank, len(alpha.shape))
        c = clamp_rank(c_rank, len(omega.shape))
        left_frame, left_cells = decompose(alpha, b)
        right_frame, right_cells = decompose(omega, c)
        if left_frame == right_frame:
            pairs = list(zip(left_cells, right_cells))
            frame = left_frame
        elif left_frame == []:
            pairs = [(left_cells[0], rc) for rc in right_cells]
            frame = right_frame
        elif right_frame == []:
            pairs = [(lc, right_cells[0]) for lc in left_cells]
            frame = left_frame
        else:
            raise LengthError(f"Frame mismatch: {left_frame} vs {right_frame}")
        results = [self.function.apply_to_dyadic(ctx, lc, rc) for lc, rc in pairs]
        return reassemble(frame, results)



class PowerDerived(UnappliedFunction):
    """Unapplied power-derived function: f⍣g"""
    def __init__(self, function: Applicable, right_operand: Applicable) -> None:
        self.function = function
        self.right_operand = right_operand

    def _resolve_strategy(self, ctx: ExecutionContext) -> PowerStrategy:
        """Resolve the right operand to an iteration strategy."""
        return self.right_operand.as_power_strategy(ctx)

    def apply_monadic(self, ctx: ExecutionContext, operand_node: Executable) -> APLArray:
        omega = ctx.evaluate(operand_node)
        strategy = self._resolve_strategy(ctx)
        return strategy.iterate(lambda o: self.function.apply_to_monadic(ctx, o), omega)

    def apply_dyadic(self, ctx: ExecutionContext, left_node: Executable, right_node: Executable) -> APLArray:
        alpha = ctx.evaluate(left_node)
        omega = ctx.evaluate(right_node)
        strategy = self._resolve_strategy(ctx)
        return strategy.iterate(lambda o: self.function.apply_to_dyadic(ctx, alpha, o), omega)


class CommuteDerived(UnappliedFunction):
    """Unapplied commute-derived function: f⍨

    Monadic application:  f⍨ ω  ≡  ω f ω    (apply with both sides)
    Dyadic application:   α f⍨ ω ≡  ω f α    (swap arguments)

    The argument is evaluated ONCE in the monadic case, even though
    it appears on both sides of the underlying call.
    """
    def __init__(self, function: Applicable) -> None:
        self.function = function
    def apply_monadic(self, ctx: ExecutionContext, operand_node: Executable) -> APLArray:
        """f⍨ ω ≡ ω f ω. Evaluates ω exactly once."""
        omega = ctx.evaluate(operand_node)
        return self.function.apply_to_dyadic(ctx, omega, omega)
    def apply_dyadic(self, ctx: ExecutionContext, left_node: Executable, right_node: Executable) -> APLArray:
        """α f⍨ ω ≡ ω f α (swap arguments)."""
        alpha = ctx.evaluate(left_node)
        omega = ctx.evaluate(right_node)
        return self.function.apply_to_dyadic(ctx, omega, alpha)


class BesideDerived(UnappliedFunction):
    """Unapplied beside-derived function: f∘g

    Monadic application:  (f∘g) ω  ≡  f (g ω)
    Dyadic application:   α (f∘g) ω ≡  α f (g ω)

    `g` is always applied monadically; `f` is applied monadically
    for monadic derived-function calls and dyadically for dyadic
    derived-function calls.
    """
    def __init__(self, f: Applicable, g: Applicable) -> None:
        self.f = f
        self.g = g
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BesideDerived):
            return NotImplemented
        return self.f == other.f and self.g == other.g
    def apply_monadic(self, ctx: ExecutionContext, operand_node: Executable) -> APLArray:
        """(f∘g) ω ≡ f (g ω)."""
        omega = ctx.evaluate(operand_node)
        g_result = self.g.apply_to_monadic(ctx, omega)
        return self.f.apply_to_monadic(ctx, g_result)
    def apply_dyadic(self, ctx: ExecutionContext, left_node: Executable, right_node: Executable) -> APLArray:
        """α (f∘g) ω ≡ α f (g ω)."""
        alpha = ctx.evaluate(left_node)
        omega = ctx.evaluate(right_node)
        g_result = self.g.apply_to_monadic(ctx, omega)
        return self.f.apply_to_dyadic(ctx, alpha, g_result)


class AtopDerived(UnappliedFunction):
    """(g h) — 2-train atop.

    Monadic: (g h) ω   ≡ g (h ω)
    Dyadic:  α (g h) ω ≡ g (α h ω)
    """
    def __init__(self, g: Applicable, h: Applicable) -> None:
        self.g = g
        self.h = h
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AtopDerived):
            return NotImplemented
        return self.g == other.g and self.h == other.h
    def apply_monadic(self, ctx: ExecutionContext, operand_node: Executable) -> APLArray:
        """(g h) ω ≡ g (h ω)."""
        omega = ctx.evaluate(operand_node)
        h_result = self.h.apply_to_monadic(ctx, omega)
        return self.g.apply_to_monadic(ctx, h_result)
    def apply_dyadic(self, ctx: ExecutionContext, left_node: Executable, right_node: Executable) -> APLArray:
        """α (g h) ω ≡ g (α h ω)."""
        alpha = ctx.evaluate(left_node)
        omega = ctx.evaluate(right_node)
        h_result = self.h.apply_to_dyadic(ctx, alpha, omega)
        return self.g.apply_to_monadic(ctx, h_result)


class ForkDerived(UnappliedFunction):
    """(f g h) — 3-train fork.

    f may be a function or an array (Agh-fork).
    Monadic: (f g h) ω   ≡ (f ω) g (h ω)
    Dyadic:  α (f g h) ω ≡ (α f ω) g (α h ω)
    When f is an array: (A g h) ω ≡ A g (h ω)
    """
    def __init__(self, f: Applicable, g: Applicable, h: Applicable) -> None:
        self.f = f
        self.g = g
        self.h = h
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ForkDerived):
            return NotImplemented
        return self.f == other.f and self.g == other.g and self.h == other.h
    def _resolve_f(self, ctx: ExecutionContext) -> APLValue:
        """Resolve f to an APLArray (Agh-fork) or leave as function."""
        if isinstance(self.f, Executable):
            return self.f.execute(ctx)
        assert isinstance(self.f, APLValue)
        return self.f

    def apply_monadic(self, ctx: ExecutionContext, operand_node: Executable) -> APLArray:
        """(f g h) ω ≡ (f ω) g (h ω). Agh-fork: A g (h ω)."""
        omega = ctx.evaluate(operand_node)
        right = self.h.apply_to_monadic(ctx, omega)
        f_val = self._resolve_f(ctx)
        if isinstance(f_val, APLArray):
            left = f_val
        elif isinstance(f_val, Applicable):
            left = f_val.apply_to_monadic(ctx, omega)
        else:
            raise DomainError(f"Expected function or array in fork, got {type(f_val)}")
        return self.g.apply_to_dyadic(ctx, left, right)

    def apply_dyadic(self, ctx: ExecutionContext, left_node: Executable, right_node: Executable) -> APLArray:
        """α (f g h) ω ≡ (α f ω) g (α h ω)."""
        alpha = ctx.evaluate(left_node)
        omega = ctx.evaluate(right_node)
        right = self.h.apply_to_dyadic(ctx, alpha, omega)
        f_val = self._resolve_f(ctx)
        if isinstance(f_val, APLArray):
            left = f_val
        elif isinstance(f_val, Applicable):
            left = f_val.apply_to_dyadic(ctx, alpha, omega)
        else:
            raise DomainError(f"Expected function or array in fork, got {type(f_val)}")
        return self.g.apply_to_dyadic(ctx, left, right)


class ReduceDerived(UnappliedFunction):
    """Unapplied reduce-derived function: f/ or f⌿"""
    def __init__(self, operator: 'ReduceAdverb', function: Applicable) -> None:
        self.operator = operator
        self.function = function
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ReduceDerived):
            return NotImplemented
        return self.operator == other.operator and self.function == other.function
    def apply_monadic(self, ctx: ExecutionContext, operand_node: Executable) -> APLArray:
        from marple.operator_binding import DerivedFunctionBinding
        operand = ctx.evaluate(operand_node)
        axis = _resolve_axis(self.operator, ctx)
        return DerivedFunctionBinding().apply(self.operator.symbol, self.function, operand, axis)
    def apply_dyadic(self, ctx: ExecutionContext, left_node: Executable, right_node: Executable) -> APLArray:
        raise DomainError("Reduce cannot be applied dyadically")


class ScanDerived(UnappliedFunction):
    """Unapplied scan-derived function: f\\ or f⍀"""
    def __init__(self, operator: 'ScanAdverb', function: Applicable) -> None:
        self.operator = operator
        self.function = function
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ScanDerived):
            return NotImplemented
        return self.operator == other.operator and self.function == other.function
    def apply_monadic(self, ctx: ExecutionContext, operand_node: Executable) -> APLArray:
        from marple.operator_binding import DerivedFunctionBinding
        operand = ctx.evaluate(operand_node)
        axis = _resolve_axis(self.operator, ctx)
        return DerivedFunctionBinding().apply(self.operator.symbol, self.function, operand, axis)
    def apply_dyadic(self, ctx: ExecutionContext, left_node: Executable, right_node: Executable) -> APLArray:
        raise DomainError("Scan cannot be applied dyadically")


class IBeamFunction(UnappliedFunction):
    """Derived function (A⌶): applies built-in i-beam service A.

    Stores the AST for A so the integer is evaluated per apply; the
    registry lookup then dispatches to the Python implementation.
    """
    def __init__(self, code_node: Executable) -> None:
        self.code_node = code_node
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, IBeamFunction):
            return NotImplemented
        return self.code_node == other.code_node
    def _resolve(self, ctx: ExecutionContext) -> Callable[[APLArray, APLArray | None], APLArray]:
        from marple.ibeam_registry import lookup
        code_val = ctx.evaluate(self.code_node)
        code = int(code_val.data.item())
        return lookup(code)
    def apply_monadic(self, ctx: ExecutionContext, operand_node: Executable) -> APLArray:
        impl = self._resolve(ctx)
        omega = ctx.evaluate(operand_node)
        return impl(omega, None)
    def apply_dyadic(self, ctx: ExecutionContext, left_node: Executable, right_node: Executable) -> APLArray:
        impl = self._resolve(ctx)
        omega = ctx.evaluate(right_node)
        alpha = ctx.evaluate(left_node)
        return impl(omega, alpha)


class InnerDerived(UnappliedFunction):
    """Stored function form of `.` — inner product f.g."""
    def __init__(self, left_fn: 'PrimitiveFunction', right_fn: 'PrimitiveFunction') -> None:
        self.left_fn = left_fn
        self.right_fn = right_fn
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, InnerDerived):
            return NotImplemented
        return self.left_fn == other.left_fn and self.right_fn == other.right_fn
    def apply_monadic(self, ctx: ExecutionContext, operand_node: Executable) -> APLArray:
        raise DomainError("Inner product cannot be applied monadically")
    def apply_dyadic(self, ctx: ExecutionContext, left_node: Executable, right_node: Executable) -> APLArray:
        omega = ctx.evaluate(right_node)
        alpha = ctx.evaluate(left_node)
        return _inner_product(self.left_fn.glyph, self.right_fn.glyph, alpha, omega)


class OuterDerived(UnappliedFunction):
    """Stored function form of `∘.` — outer product ∘.g."""
    def __init__(self, function: 'PrimitiveFunction') -> None:
        self.function = function
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, OuterDerived):
            return NotImplemented
        return self.function == other.function
    def apply_monadic(self, ctx: ExecutionContext, operand_node: Executable) -> APLArray:
        raise DomainError("Outer product cannot be applied monadically")
    def apply_dyadic(self, ctx: ExecutionContext, left_node: Executable, right_node: Executable) -> APLArray:
        omega = ctx.evaluate(right_node)
        alpha = ctx.evaluate(left_node)
        return _outer_product(self.function.glyph, alpha, omega)


class SysVar(Executable):
    """A readable system variable (⎕IO, ⎕FR, ⎕RL, ⎕TS, ⎕WSID, …)."""
    def __init__(self, name: str) -> None:
        self.name = name
    def execute(self, ctx: ExecutionContext) -> APLArray:
        return ctx.eval_sysvar(self.name)


class SysFunc(Function, Executable):
    """A callable system function (⎕NC, ⎕CR, ⎕FX, ⎕UCS, …).

    Inherits Function so apply_monadic/apply_dyadic dispatches the
    standard way; inherits Executable so it can act as an expression
    node that self-evaluates (like PrimitiveFunction).
    """
    def __init__(self, name: str) -> None:
        self.name = name
    def execute(self, ctx: ExecutionContext) -> APLValue:
        return self
    def apply_monadic(self, ctx: ExecutionContext, operand_node: Executable) -> APLArray:
        return ctx.dispatch_sys_monadic(self.name, operand_node)
    def apply_dyadic(self, ctx: ExecutionContext, left_node: Executable, right_node: Executable) -> APLArray:
        return ctx.dispatch_sys_dyadic(self.name, left_node, right_node)


class Index(Executable):
    def __init__(self, array: Executable, indices: list[Executable | None]) -> None:
        self.array = array
        self.indices = indices
    def execute(self, ctx: ExecutionContext) -> APLArray:
        from marple.backend_functions import to_list
        array = ctx.evaluate(self.array)
        io = ctx.env.io
        flat = array.data.flatten()
        axis_indices: list[list[int]] = []
        idx_shapes: list[list[int]] = []
        for axis, idx_node in enumerate(self.indices):
            if idx_node is None:
                axis_indices.append(list(range(array.shape[axis])))
                idx_shapes.append([array.shape[axis]])
            else:
                idx = ctx.evaluate(idx_node)
                idx_flat = idx.data.flatten()
                vals = list(idx_flat) if not idx.is_scalar() else [idx.data.flatten()[0]]
                axis_indices.append([int(v) - io for v in vals])
                idx_shapes.append(idx.shape if not idx.is_scalar() else [])
        for axis in range(len(self.indices), len(array.shape)):
            axis_indices.append(list(range(array.shape[axis])))
            idx_shapes.append([array.shape[axis]])
        strides = [1] * len(array.shape)
        for i in range(len(array.shape) - 2, -1, -1):
            strides[i] = strides[i + 1] * array.shape[i + 1]
        from marple.get_numpy import np
        if is_numeric_array(array.data):
            n_results = 1
            for ai in axis_indices:
                n_results *= len(ai)
            result_data = np.zeros(int(max(1, n_results)))
            idx = 0
            for combo in product(*axis_indices):
                offset = int(sum(i * s for i, s in zip(combo, strides)))
                result_data[idx] = flat[offset]
                idx += 1
            result_shape: list[int] = []
            for s in idx_shapes:
                result_shape.extend(s)
            if not result_shape:
                return S(result_data[0])
            return APLArray(result_shape, result_data[:idx].reshape(result_shape))
        # Character data
        result_list: list[object] = []
        for combo in product(*axis_indices):
            offset = int(sum(i * s for i, s in zip(combo, strides)))
            result_list.append(flat[offset])
        result_shape = []
        for s in idx_shapes:
            result_shape.extend(s)
        if not result_shape:
            return S(result_list[0])
        return APLArray.array(result_shape, result_list)


class Omega(Executable):
    def execute(self, ctx: ExecutionContext) -> APLArray:
        if "⍵" not in ctx.env:
            raise ValueError_("⍵ used outside of dfn")
        return ctx.env["⍵"]


class Alpha(Executable):
    def execute(self, ctx: ExecutionContext) -> APLArray:
        if "⍺" not in ctx.env:
            raise ValueError_("⍺ used outside of dfn")
        return ctx.env["⍺"]


class PrimitiveFunction(UnappliedFunction, Executable):  # Executable for execute()
    """A reference to a primitive function glyph."""
    def __init__(self, glyph: str) -> None:
        self.glyph = glyph
    def execute(self, ctx: ExecutionContext) -> APLValue:
        return self
    def apply_monadic(self, ctx: ExecutionContext, operand_node: Executable) -> APLArray:
        operand = ctx.evaluate(operand_node)
        return ctx.dispatch_monadic(self.glyph, operand)
    def apply_dyadic(self, ctx: ExecutionContext, left_node: Executable, right_node: Executable) -> APLArray:
        left = ctx.evaluate(left_node)
        right = ctx.evaluate(right_node)
        return ctx.dispatch_dyadic(self.glyph, left, right)


class AlphaAlpha(Reference):
    """⍺⍺ — left operand reference in a dop."""
    def resolve(self, ctx: ExecutionContext) -> APLValue:
        if "⍺⍺" not in ctx.env:
            raise ValueError_("⍺⍺ used outside of dop")
        return ctx.env["⍺⍺"]


class OmegaOmega(Reference):
    """⍵⍵ — right operand reference in a dop."""
    def resolve(self, ctx: ExecutionContext) -> APLValue:
        if "⍵⍵" not in ctx.env:
            raise ValueError_("⍵⍵ used outside of dop")
        return ctx.env["⍵⍵"]


# CAT_EMPTY is a parser category constant needed by BoundOperator's default arg
CAT_EMPTY = 8


class BoundOperator(Node):
    """Operator bound to operand(s), not yet applied to argument."""
    def __init__(self, operator: 'Adverb | Conjunction | Var',
                 left_operand: Node, left_cat: int,
                 right_operand: Node | None = None,
                 right_cat: int = CAT_EMPTY) -> None:
        self.operator = operator
        self.left_operand = left_operand
        self.left_cat = left_cat
        self.right_operand = right_operand
        self.right_cat = right_cat
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BoundOperator):
            return NotImplemented
        return (self.operator == other.operator and
                self.left_operand == other.left_operand and
                self.right_operand == other.right_operand)


class FmtArgs(Executable):
    """List of semicolon-separated arguments for ⎕FMT."""
    def __init__(self, args: list[Executable]) -> None:
        self.args = args
    def execute(self, ctx: ExecutionContext) -> APLArray:
        raise DomainError("FmtArgs cannot be evaluated directly")
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FmtArgs):
            return NotImplemented
        return self.args == other.args


class Nabla(Reference):
    def resolve(self, ctx: ExecutionContext) -> APLValue:
        if "∇" not in ctx.env:
            raise ValueError_("∇ used outside of dfn")
        return ctx.env["∇"]


class Guard(Node):
    def __init__(self, condition: Executable, body: Executable) -> None:
        self.condition = condition
        self.body = body


class AlphaDefault(Node):
    def __init__(self, default: Executable) -> None:
        self.default = default


class Dfn(Reference):
    def __init__(self, body: list[Executable | Guard | AlphaDefault]) -> None:
        self.body = body
    def resolve(self, ctx: ExecutionContext) -> APLValue:
        return ctx.create_binding(self)
    def is_operator(self) -> bool:
        """True if the body references ⍺⍺ or ⍵⍵ — i.e. the dfn is a dop."""
        return _dfn_references(self, (AlphaAlpha, OmegaOmega))


def _dfn_references(node: object, targets: tuple[type, ...]) -> bool:
    """Recursively check whether an AST subtree contains any target-type node."""
    if isinstance(node, targets):
        return True
    if isinstance(node, Node):
        for val in node.__dict__.values():
            if _dfn_references(val, targets):
                return True
    elif isinstance(node, (list, tuple)):
        for item in node:
            if _dfn_references(item, targets):
                return True
    return False


class MonadicDfnCall(Executable):
    def __init__(self, dfn: Applicable, operand: Executable) -> None:
        self.dfn = dfn
        self.operand = operand
    def execute(self, ctx: ExecutionContext) -> APLArray:
        return self.dfn.apply_monadic(ctx, self.operand)


class DyadicDfnCall(Executable):
    def __init__(self, dfn: Applicable, left: Executable, right: Executable) -> None:
        self.dfn = dfn
        self.left = left
        self.right = right
    def execute(self, ctx: ExecutionContext) -> APLArray:
        return self.dfn.apply_dyadic(ctx, self.left, self.right)


class Program(Executable):
    def __init__(self, statements: list[Executable]) -> None:
        self.statements = statements
    def execute(self, ctx: ExecutionContext) -> APLArray:
        result: APLArray = S(0)
        for stmt in self.statements:
            result = ctx.evaluate(stmt)
        return result
