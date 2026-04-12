"""AST node classes for MARPLE."""


from abc import ABC, abstractmethod
from itertools import product
from typing import Any, Protocol

from marple.numpy_array import APLArray, S
from marple.backend_functions import is_numeric_array, maybe_upcast
from marple.errors import DomainError, ValueError_
from marple.symbol_table import NC_FUNCTION, APLValue


_INNER_SCALAR_OPS: dict[str, Any] = {
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


_OUTER_UFUNCS: dict[str, Any] = {
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
    def evaluate(self, node: 'Evaluatable') -> APLArray: ...
    def dispatch_monadic(self, glyph: str, operand: APLArray) -> APLArray: ...
    def dispatch_dyadic(self, glyph: str, left: APLArray, right: APLArray) -> APLArray: ...
    def apply_derived(self, operator: str, function: object, operand: APLArray) -> APLArray: ...
    def assign(self, name: str, value_node: 'Evaluatable | UnappliedFunction') -> APLArray: ...
    def eval_sysvar(self, name: str) -> APLArray: ...
    def create_binding(self, dfn_node: 'Evaluatable') -> object: ...
    def dispatch_sys_monadic(self, name: str, operand_node: 'Evaluatable') -> APLArray: ...
    def dispatch_sys_dyadic(self, name: str, left_node: 'Evaluatable', right_node: 'Evaluatable') -> APLArray: ...
    def apply_func_monadic(self, func: object, omega: 'APLArray') -> 'APLArray': ...
    def apply_func_dyadic(self, func: object, alpha: 'APLArray', omega: 'APLArray') -> 'APLArray': ...
    def resolve_qualified(self, parts: list[str]) -> object: ...
    def call_ibeam(self, path: str, operand: APLArray) -> APLArray: ...


class Node(ABC):
    """Abstract base for all items on the parser stack."""
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__dict__ == other.__dict__


class Marker(Node):
    """Sentinel for LP, RP, and END positions on the parser stack."""


_MARKER = Marker()


class Evaluatable(Node):
    """A Node that can be executed to produce a value."""
    @abstractmethod
    def execute(self, ctx: ExecutionContext) -> object: ...


class Literal(Evaluatable):
    """Wrapper: an already-evaluated APLArray as a Node."""
    def __init__(self, value: APLArray) -> None:
        self.value = value
    def execute(self, ctx: ExecutionContext) -> APLArray:
        return self.value


class Num(Evaluatable):
    def __init__(self, value: int | float) -> None:
        self.value = value
    def execute(self, ctx: ExecutionContext) -> APLArray:
        value = self.value
        if isinstance(value, float) and ctx.env.fr == 1287:
            from decimal import Decimal
            value = Decimal(str(self.value))
        return S(value)


class Str(Evaluatable):
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


class Vector(Evaluatable):
    def __init__(self, elements: list[Num]) -> None:
        self.elements = elements
    def execute(self, ctx: ExecutionContext) -> APLArray:
        values = [el.value for el in self.elements]
        return APLArray.array([len(values)], list(values))


class Zilde(Evaluatable):
    """⍬ — the empty numeric vector literal (equivalent to ⍳0)."""
    def execute(self, ctx: ExecutionContext) -> APLArray:
        return APLArray.array([0], [])


class MonadicFunc(Evaluatable):
    def __init__(self, function: str, operand: Evaluatable) -> None:
        self.function = function
        self.operand = operand
    def execute(self, ctx: ExecutionContext) -> APLArray:
        operand = ctx.evaluate(self.operand)
        return ctx.dispatch_monadic(self.function, operand)


class DyadicFunc(Evaluatable):
    def __init__(self, function: str, left: Evaluatable, right: Evaluatable) -> None:
        self.function = function
        self.left = left
        self.right = right
    def execute(self, ctx: ExecutionContext) -> APLArray:
        right = ctx.evaluate(self.right)
        left = ctx.evaluate(self.left)
        return ctx.dispatch_dyadic(self.function, left, right)


class Assignment(Evaluatable):
    def __init__(self, name: str, value: object) -> None:
        self.name = name
        self.value = value
    def execute(self, ctx: ExecutionContext) -> APLArray:
        return ctx.assign(self.name, self.value)


class Var(Evaluatable):
    def __init__(self, name: str) -> None:
        self.name = name
    def execute(self, ctx: ExecutionContext) -> APLArray:
        if self.name not in ctx.env:
            raise ValueError_(f"Undefined variable: {self.name}")
        return ctx.env[self.name]


class QualifiedVar(Evaluatable):
    def __init__(self, parts: list[str]) -> None:
        self.parts = parts
    def execute(self, ctx: ExecutionContext) -> object:
        return ctx.resolve_qualified(self.parts)


class DerivedFunc(Evaluatable):
    def __init__(self, operator: str, function: object, operand: Evaluatable) -> None:
        self.operator = operator
        self.function = function
        self.operand = operand
    def execute(self, ctx: ExecutionContext) -> APLArray:
        operand = ctx.evaluate(self.operand)
        return ctx.apply_derived(self.operator, self.function, operand)


class MonadicDopCall(Evaluatable):
    """User-defined operator applied: (operand op) argument
    or: left (operand op) right (when derived verb is used dyadically)"""
    def __init__(self, op_name: Evaluatable, operand: Evaluatable, argument: Evaluatable,
                 alpha: Evaluatable | None = None) -> None:
        self.op_name = op_name
        self.operand = operand
        self.argument = argument
        self.alpha = alpha
    def execute(self, ctx: ExecutionContext) -> APLArray:
        from marple.dfn_binding import DfnBinding
        dop_val = ctx.evaluate(self.op_name)
        if not isinstance(dop_val, DfnBinding):
            raise DomainError(f"Expected operator, got {type(dop_val)}")
        operand = ctx.evaluate(self.operand)
        argument = ctx.evaluate(self.argument)
        alpha = ctx.evaluate(self.alpha) if self.alpha is not None else None
        return dop_val.apply(argument, alpha_alpha=operand, alpha=alpha)


class DyadicDopCall(Evaluatable):
    """User-defined operator applied dyadically: left (operand op) right"""
    def __init__(self, op_name: Evaluatable, operand: Evaluatable, left: Evaluatable, right: Evaluatable) -> None:
        self.op_name = op_name
        self.operand = operand
        self.left = left
        self.right = right
    def execute(self, ctx: ExecutionContext) -> APLArray:
        from marple.dfn_binding import DfnBinding
        dop_val = ctx.evaluate(self.op_name)
        if not isinstance(dop_val, DfnBinding):
            raise DomainError(f"Expected operator, got {type(dop_val)}")
        left_operand = ctx.evaluate(self.operand)    # ⍺⍺
        right_operand = ctx.evaluate(self.left)      # ⍵⍵
        argument = ctx.evaluate(self.right)           # ⍵
        return dop_val.apply(argument, alpha_alpha=left_operand, omega_omega=right_operand)


class UnappliedFunction(APLValue):
    """Base class for all unapplied APL function values."""

    def name_class(self) -> int:
        return NC_FUNCTION

    @abstractmethod
    def apply_monadic(self, ctx: 'ExecutionContext', operand_node: 'Evaluatable') -> 'APLArray': ...

    @abstractmethod
    def apply_dyadic(self, ctx: 'ExecutionContext', left_node: 'Evaluatable', right_node: 'Evaluatable') -> 'APLArray': ...


class RankDerived(UnappliedFunction):
    """Unapplied rank-derived function: f⍤k"""
    def __init__(self, function: object, rank_spec: object) -> None:
        self.function = function
        self.rank_spec = rank_spec
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RankDerived):
            return NotImplemented
        return self.function == other.function and self.rank_spec == other.rank_spec
    def apply_monadic(self, ctx: ExecutionContext, operand_node: Evaluatable) -> APLArray:
        from marple.cells import clamp_rank, decompose, reassemble, resolve_rank_spec
        omega = ctx.evaluate(operand_node)
        rank_spec_val = ctx.evaluate(self.rank_spec)
        a, _, _ = resolve_rank_spec(rank_spec_val)
        k = clamp_rank(a, len(omega.shape))
        frame_shape, cells = decompose(omega, k)
        results = [ctx.apply_func_monadic(self.function, cell) for cell in cells]
        return reassemble(frame_shape, results)

    def apply_dyadic(self, ctx: ExecutionContext, left_node: Evaluatable, right_node: Evaluatable) -> APLArray:
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
        results = [ctx.apply_func_dyadic(self.function, lc, rc) for lc, rc in pairs]
        return reassemble(frame, results)


class PowerDerived(UnappliedFunction):
    """Unapplied power-derived function: f⍣g"""
    def __init__(self, function: object, right_operand: object) -> None:
        self.function = function
        self.right_operand = right_operand

    def _resolve_right(self, ctx: ExecutionContext) -> object:
        """Resolve the right operand — may be a FunctionRef, Node, or value."""
        right_op = self.right_operand
        if isinstance(right_op, (UnappliedFunction, APLArray)):
            return right_op
        return ctx.evaluate(right_op)

    def _test_convergence(self, func: object, left: APLArray,
                          right: APLArray, ctx: ExecutionContext) -> APLArray:
        """Apply convergence test function dyadically."""
        if isinstance(func, FunctionRef):
            if func.glyph == "≡":
                return S(1 if left == right else 0)
            if func.glyph == "=":
                return S(1 if left.data.item() == right.data.item() else 0)
        return ctx.apply_func_dyadic(func, left, right)

    def apply_monadic(self, ctx: ExecutionContext, operand_node: Evaluatable) -> APLArray:
        omega = ctx.evaluate(operand_node)
        right_val = self._resolve_right(ctx)
        if isinstance(right_val, APLArray) and right_val.is_scalar():
            n = int(right_val.data.item())
            if n < 0:
                raise DomainError("DOMAIN ERROR: inverse (⍣ with negative) not supported")
            result = omega
            for _ in range(n):
                result = ctx.apply_func_monadic(self.function, result)
            return result
        if isinstance(right_val, UnappliedFunction):
            prev = omega
            while True:
                curr = ctx.apply_func_monadic(self.function, prev)
                test = self._test_convergence(right_val, curr, prev, ctx)
                if test.data.item():
                    return curr
                prev = curr
        raise DomainError("⍣ right operand must be integer or function")

    def apply_dyadic(self, ctx: ExecutionContext, left_node: Evaluatable, right_node: Evaluatable) -> APLArray:
        alpha = ctx.evaluate(left_node)
        omega = ctx.evaluate(right_node)
        right_val = self._resolve_right(ctx)
        if isinstance(right_val, APLArray) and right_val.is_scalar():
            n = int(right_val.data.item())
            if n < 0:
                raise DomainError("DOMAIN ERROR: inverse (⍣ with negative) not supported")
            result = omega
            for _ in range(n):
                result = ctx.apply_func_dyadic(self.function, alpha, result)
            return result
        if isinstance(right_val, UnappliedFunction):
            prev = omega
            while True:
                curr = ctx.apply_func_dyadic(self.function, alpha, prev)
                test = self._test_convergence(right_val, curr, prev, ctx)
                if test.data.item():
                    return curr
                prev = curr
        raise DomainError("⍣ right operand must be integer or function")


class CommuteDerived(UnappliedFunction):
    """Unapplied commute-derived function: f⍨

    Monadic application:  f⍨ ω  ≡  ω f ω    (apply with both sides)
    Dyadic application:   α f⍨ ω ≡  ω f α    (swap arguments)

    The argument is evaluated ONCE in the monadic case, even though
    it appears on both sides of the underlying call.
    """
    def __init__(self, function: object) -> None:
        self.function = function
    def apply_monadic(self, ctx: ExecutionContext, operand_node: Evaluatable) -> APLArray:
        """f⍨ ω ≡ ω f ω. Evaluates ω exactly once."""
        omega = ctx.evaluate(operand_node)
        return ctx.apply_func_dyadic(self.function, omega, omega)
    def apply_dyadic(self, ctx: ExecutionContext, left_node: Evaluatable, right_node: Evaluatable) -> APLArray:
        """α f⍨ ω ≡ ω f α (swap arguments)."""
        alpha = ctx.evaluate(left_node)
        omega = ctx.evaluate(right_node)
        return ctx.apply_func_dyadic(self.function, omega, alpha)


class BesideDerived(UnappliedFunction):
    """Unapplied beside-derived function: f∘g

    Monadic application:  (f∘g) ω  ≡  f (g ω)
    Dyadic application:   α (f∘g) ω ≡  α f (g ω)

    `g` is always applied monadically; `f` is applied monadically
    for monadic derived-function calls and dyadically for dyadic
    derived-function calls.
    """
    def __init__(self, f: object, g: object) -> None:
        self.f = f
        self.g = g
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BesideDerived):
            return NotImplemented
        return self.f == other.f and self.g == other.g
    def apply_monadic(self, ctx: ExecutionContext, operand_node: Evaluatable) -> APLArray:
        """(f∘g) ω ≡ f (g ω)."""
        omega = ctx.evaluate(operand_node)
        g_result = ctx.apply_func_monadic(self.g, omega)
        return ctx.apply_func_monadic(self.f, g_result)
    def apply_dyadic(self, ctx: ExecutionContext, left_node: Evaluatable, right_node: Evaluatable) -> APLArray:
        """α (f∘g) ω ≡ α f (g ω)."""
        alpha = ctx.evaluate(left_node)
        omega = ctx.evaluate(right_node)
        g_result = ctx.apply_func_monadic(self.g, omega)
        return ctx.apply_func_dyadic(self.f, alpha, g_result)


class AtopDerived(UnappliedFunction):
    """(g h) — 2-train atop.

    Monadic: (g h) ω   ≡ g (h ω)
    Dyadic:  α (g h) ω ≡ g (α h ω)
    """
    def __init__(self, g: object, h: object) -> None:
        self.g = g
        self.h = h
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AtopDerived):
            return NotImplemented
        return self.g == other.g and self.h == other.h
    def apply_monadic(self, ctx: ExecutionContext, operand_node: Evaluatable) -> APLArray:
        """(g h) ω ≡ g (h ω)."""
        omega = ctx.evaluate(operand_node)
        h_result = ctx.apply_func_monadic(self.h, omega)
        return ctx.apply_func_monadic(self.g, h_result)
    def apply_dyadic(self, ctx: ExecutionContext, left_node: Evaluatable, right_node: Evaluatable) -> APLArray:
        """α (g h) ω ≡ g (α h ω)."""
        alpha = ctx.evaluate(left_node)
        omega = ctx.evaluate(right_node)
        h_result = ctx.apply_func_dyadic(self.h, alpha, omega)
        return ctx.apply_func_monadic(self.g, h_result)


class ForkDerived(UnappliedFunction):
    """(f g h) — 3-train fork.

    f may be a function or an array (Agh-fork).
    Monadic: (f g h) ω   ≡ (f ω) g (h ω)
    Dyadic:  α (f g h) ω ≡ (α f ω) g (α h ω)
    When f is an array: (A g h) ω ≡ A g (h ω)
    """
    def __init__(self, f: object, g: object, h: object) -> None:
        self.f = f
        self.g = g
        self.h = h
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ForkDerived):
            return NotImplemented
        return self.f == other.f and self.g == other.g and self.h == other.h
    def _resolve_f(self, ctx: ExecutionContext) -> object:
        """Resolve f to an APLArray (Agh-fork) or leave as function."""
        if isinstance(self.f, Node):
            return ctx.evaluate(self.f)
        return self.f

    def apply_monadic(self, ctx: ExecutionContext, operand_node: Evaluatable) -> APLArray:
        """(f g h) ω ≡ (f ω) g (h ω). Agh-fork: A g (h ω)."""
        omega = ctx.evaluate(operand_node)
        right = ctx.apply_func_monadic(self.h, omega)
        f_val = self._resolve_f(ctx)
        if isinstance(f_val, APLArray):
            left = f_val
        else:
            left = ctx.apply_func_monadic(f_val, omega)
        return ctx.apply_func_dyadic(self.g, left, right)

    def apply_dyadic(self, ctx: ExecutionContext, left_node: Evaluatable, right_node: Evaluatable) -> APLArray:
        """α (f g h) ω ≡ (α f ω) g (α h ω)."""
        alpha = ctx.evaluate(left_node)
        omega = ctx.evaluate(right_node)
        right = ctx.apply_func_dyadic(self.h, alpha, omega)
        f_val = self._resolve_f(ctx)
        if isinstance(f_val, APLArray):
            left = f_val
        else:
            left = ctx.apply_func_dyadic(f_val, alpha, omega)
        return ctx.apply_func_dyadic(self.g, left, right)


class ReduceDerived(UnappliedFunction):
    """Unapplied reduce-derived function: f/ or f⌿"""
    def __init__(self, operator: str, function: object) -> None:
        self.operator = operator
        self.function = function
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ReduceDerived):
            return NotImplemented
        return self.operator == other.operator and self.function == other.function
    def apply_monadic(self, ctx: ExecutionContext, operand_node: Evaluatable) -> APLArray:
        from marple.operator_binding import DerivedFunctionBinding
        operand = ctx.evaluate(operand_node)
        return DerivedFunctionBinding().apply(self.operator, self.function, operand)
    def apply_dyadic(self, ctx: ExecutionContext, left_node: Evaluatable, right_node: Evaluatable) -> APLArray:
        raise DomainError("Reduce cannot be applied dyadically")


class ScanDerived(UnappliedFunction):
    """Unapplied scan-derived function: f\\ or f⍀"""
    def __init__(self, operator: str, function: object) -> None:
        self.operator = operator
        self.function = function
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ScanDerived):
            return NotImplemented
        return self.operator == other.operator and self.function == other.function
    def apply_monadic(self, ctx: ExecutionContext, operand_node: Evaluatable) -> APLArray:
        from marple.operator_binding import DerivedFunctionBinding
        operand = ctx.evaluate(operand_node)
        return DerivedFunctionBinding().apply(self.operator, self.function, operand)
    def apply_dyadic(self, ctx: ExecutionContext, left_node: Evaluatable, right_node: Evaluatable) -> APLArray:
        raise DomainError("Scan cannot be applied dyadically")


class IBeamDerived(UnappliedFunction, Evaluatable):
    """I-beam derived function: ⌶'module.function'"""
    def __init__(self, path: str) -> None:
        self.path = path
    def execute(self, ctx: ExecutionContext) -> object:
        return self
    def apply_monadic(self, ctx: ExecutionContext, operand_node: Evaluatable) -> APLArray:
        operand = ctx.evaluate(operand_node)
        return ctx.call_ibeam(self.path, operand)
    def apply_dyadic(self, ctx: ExecutionContext, left_node: Evaluatable, right_node: Evaluatable) -> APLArray:
        raise DomainError("Dyadic i-beam not yet supported")


class InnerProduct(Evaluatable):
    def __init__(self, left_fn: object, right_fn: object, left: Evaluatable, right: Evaluatable) -> None:
        self.left_fn = left_fn
        self.right_fn = right_fn
        self.left = left
        self.right = right
    def execute(self, ctx: ExecutionContext) -> APLArray:
        omega = ctx.evaluate(self.right)
        alpha = ctx.evaluate(self.left)
        left = self.left_fn.glyph if isinstance(self.left_fn, FunctionRef) else self.left_fn
        right = self.right_fn.glyph if isinstance(self.right_fn, FunctionRef) else self.right_fn
        return _inner_product(left, right, alpha, omega)


class OuterProduct(Evaluatable):
    def __init__(self, function: object, left: Evaluatable, right: Evaluatable) -> None:
        self.function = function
        self.left = left
        self.right = right
    def execute(self, ctx: ExecutionContext) -> APLArray:
        omega = ctx.evaluate(self.right)
        alpha = ctx.evaluate(self.left)
        fn = self.function.glyph if isinstance(self.function, FunctionRef) else self.function
        return _outer_product(fn, alpha, omega)


class SysVar(Evaluatable):
    def __init__(self, name: str) -> None:
        self.name = name
    def execute(self, ctx: ExecutionContext) -> APLArray:
        return ctx.eval_sysvar(self.name)


class Index(Evaluatable):
    def __init__(self, array: Evaluatable, indices: list[Evaluatable | None]) -> None:
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


class Omega(Evaluatable):
    def execute(self, ctx: ExecutionContext) -> APLArray:
        if "⍵" not in ctx.env:
            raise ValueError_("⍵ used outside of dfn")
        return ctx.env["⍵"]


class Alpha(Evaluatable):
    def execute(self, ctx: ExecutionContext) -> APLArray:
        if "⍺" not in ctx.env:
            raise ValueError_("⍺ used outside of dfn")
        return ctx.env["⍺"]


class FunctionRef(UnappliedFunction, Evaluatable):
    """A reference to a primitive function glyph, used as a dop operand."""
    def __init__(self, glyph: str) -> None:
        self.glyph = glyph
    def execute(self, ctx: ExecutionContext) -> object:
        return self
    def apply_monadic(self, ctx: ExecutionContext, operand_node: Evaluatable) -> APLArray:
        operand = ctx.evaluate(operand_node)
        return ctx.dispatch_monadic(self.glyph, operand)
    def apply_dyadic(self, ctx: ExecutionContext, left_node: Evaluatable, right_node: Evaluatable) -> APLArray:
        left = ctx.evaluate(left_node)
        right = ctx.evaluate(right_node)
        return ctx.dispatch_dyadic(self.glyph, left, right)


class AlphaAlpha(Evaluatable):
    """⍺⍺ — left operand reference in a dop."""
    def execute(self, ctx: ExecutionContext) -> object:
        if "⍺⍺" not in ctx.env:
            raise ValueError_("⍺⍺ used outside of dop")
        return ctx.env["⍺⍺"]


class OmegaOmega(Evaluatable):
    """⍵⍵ — right operand reference in a dop."""
    def execute(self, ctx: ExecutionContext) -> object:
        if "⍵⍵" not in ctx.env:
            raise ValueError_("⍵⍵ used outside of dop")
        return ctx.env["⍵⍵"]


# CAT_EMPTY is a parser category constant needed by BoundOperator's default arg
CAT_EMPTY = 8


class BoundOperator(Node):
    """Operator bound to operand(s), not yet applied to argument."""
    def __init__(self, operator: str | Var,
                 left_operand, left_cat: int,
                 right_operand=None,
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


class FmtArgs(Node):
    """List of semicolon-separated arguments for ⎕FMT."""
    def __init__(self, args: list[object]) -> None:
        self.args = args
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FmtArgs):
            return NotImplemented
        return self.args == other.args


class Nabla(Evaluatable):
    def execute(self, ctx: ExecutionContext) -> object:
        if "∇" not in ctx.env:
            raise ValueError_("∇ used outside of dfn")
        return ctx.env["∇"]


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


class Dfn(Evaluatable):
    def __init__(self, body: list[object]) -> None:
        self.body = body
    def execute(self, ctx: ExecutionContext) -> object:
        return ctx.create_binding(self)


class MonadicDfnCall(Evaluatable):
    def __init__(self, dfn: Evaluatable | UnappliedFunction, operand: Evaluatable) -> None:
        self.dfn = dfn
        self.operand = operand
    def execute(self, ctx: ExecutionContext) -> APLArray:
        from marple.dfn_binding import DfnBinding
        if isinstance(self.dfn, SysVar):
            return ctx.dispatch_sys_monadic(self.dfn.name, self.operand)
        if isinstance(self.dfn, UnappliedFunction):
            return self.dfn.apply_monadic(ctx, self.operand)
        dfn_val = ctx.evaluate(self.dfn)
        if isinstance(dfn_val, UnappliedFunction):
            return dfn_val.apply_monadic(ctx, self.operand)
        operand = ctx.evaluate(self.operand)
        if isinstance(dfn_val, DfnBinding):
            return dfn_val.apply(operand)
        # Old-style _DfnBinding from namespace system — wrap and apply
        if hasattr(dfn_val, 'dfn') and hasattr(dfn_val, 'env'):
            binding = DfnBinding(getattr(dfn_val, 'dfn'), ctx.env)
            return binding.apply(operand)
        raise DomainError(f"Expected dfn, got {type(dfn_val)}")


class DyadicDfnCall(Evaluatable):
    def __init__(self, dfn: Evaluatable | UnappliedFunction, left: Evaluatable, right: Evaluatable) -> None:
        self.dfn = dfn
        self.left = left
        self.right = right
    def execute(self, ctx: ExecutionContext) -> APLArray:
        from marple.dfn_binding import DfnBinding
        if isinstance(self.dfn, SysVar):
            return ctx.dispatch_sys_dyadic(self.dfn.name, self.left, self.right)
        if isinstance(self.dfn, UnappliedFunction):
            return self.dfn.apply_dyadic(ctx, self.left, self.right)
        dfn_val = ctx.evaluate(self.dfn)
        if isinstance(dfn_val, UnappliedFunction):
            return dfn_val.apply_dyadic(ctx, self.left, self.right)
        raise DomainError(f"Expected dfn, got {type(dfn_val)}")


class Program(Evaluatable):
    def __init__(self, statements: list[object]) -> None:
        self.statements = statements
    def execute(self, ctx: ExecutionContext) -> object:
        result: object = S(0)
        for stmt in self.statements:
            result = ctx.evaluate(stmt)
        return result
