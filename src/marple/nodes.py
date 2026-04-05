"""AST node classes for MARPLE."""


from abc import ABC, abstractmethod
from typing import Any, Protocol, Generator

from marple.numpy_array import APLArray, S
from marple.backend_functions import is_numeric_array, np_reshape
from marple.errors import DomainError, ValueError_


def _product(*lists: list[int]) -> Generator[tuple[int, ...], None, None]:
    """Simple replacement for itertools.product (MicroPython compatible)."""
    if not lists:
        yield ()
        return
    for item in lists[0]:
        for rest in _product(*lists[1:]):
            yield (item,) + rest


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
        result = np.dot(alpha.data, omega.data)
        # TODO: 2 lines below look redundant.
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
    result = np.zeros(result_shape, dtype=float)
    a_outer = [range(s) for s in a_shape[:-1]]
    b_outer = [range(s) for s in b_shape[1:]]
    for a_idx in _product(*a_outer):
        for b_idx in _product(*b_outer):
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
    # Fast path: use numpy ufunc.outer (not available on ulab)
    if is_numeric_array(alpha.data) and is_numeric_array(omega.data):
        ufunc_name = _OUTER_UFUNCS.get(glyph)
        if ufunc_name is not None:
            ufunc = getattr(np, ufunc_name, None)
            if ufunc is not None and hasattr(ufunc, 'outer'):
                result = ufunc.outer(alpha.data.flatten(), omega.data.flatten())
                result_shape = alpha.shape + omega.shape
                return APLArray(result_shape, np_reshape(result, result_shape))
    # General path
    op = _INNER_SCALAR_OPS.get(glyph)
    if op is None:
        raise DomainError(f"Unknown function for outer product: {glyph}")
    result_shape = alpha.shape + omega.shape
    if not result_shape:
        return S(op(alpha.data[()], omega.data[()]))
    result = np.zeros(result_shape, dtype=float)
    a_indices = [range(s) for s in alpha.shape]
    b_indices = [range(s) for s in omega.shape]
    for a_idx in _product(*a_indices):
        for b_idx in _product(*b_indices):
            result[a_idx + b_idx] = op(alpha.data[a_idx], omega.data[b_idx])
    return APLArray(result_shape, result)


class ExecutionContext(Protocol):
    """Interface that AST nodes use to evaluate sub-expressions."""
    env: Any
    def evaluate(self, node: object) -> APLArray: ...
    def dispatch_monadic(self, glyph: str, operand: APLArray) -> APLArray: ...
    def dispatch_dyadic(self, glyph: str, left: APLArray, right: APLArray) -> APLArray: ...
    def apply_derived(self, operator: str, function: object, operand: APLArray) -> APLArray: ...
    def assign(self, name: str, value_node: object) -> APLArray: ...
    def eval_sysvar(self, name: str) -> APLArray: ...
    def create_binding(self, dfn_node: object) -> object: ...
    def dispatch_sys_monadic(self, name: str, operand_node: object) -> APLArray: ...
    def apply_rank_monadic(self, rank_node: object, operand_node: object) -> APLArray: ...
    def resolve_dyadic(self, fn: object) -> Any: ...
    def dispatch_sys_dyadic(self, name: str, left_node: object, right_node: object) -> APLArray: ...
    def apply_rank_dyadic(self, rank_node: object, left_node: object, right_node: object) -> APLArray: ...
    def apply_power_monadic(self, power_node: object, operand_node: object) -> APLArray: ...
    def apply_power_dyadic(self, power_node: object, left_node: object, right_node: object) -> APLArray: ...
    def resolve_qualified(self, parts: list[str]) -> object: ...
    def call_ibeam(self, path: str, operand: APLArray) -> APLArray: ...


class Node(ABC):
    """Abstract base for all AST nodes that can be evaluated."""
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__dict__ == other.__dict__
    @abstractmethod
    def execute(self, ctx: ExecutionContext) -> object: ...


class Num(Node):
    def __init__(self, value: int | float) -> None:
        self.value = value
    def execute(self, ctx: ExecutionContext) -> APLArray:
        value = self.value
        if isinstance(value, float) and ctx.env.fr == 1287:
            from decimal import Decimal
            value = Decimal(str(self.value))
        return S(value)


class Str(Node):
    def __init__(self, value: str) -> None:
        self.value = value
    def execute(self, ctx: ExecutionContext) -> APLArray:
        return APLArray.array([len(self.value)], list(self.value))


class Vector(Node):
    def __init__(self, elements: list[Num]) -> None:
        self.elements = elements
    def execute(self, ctx: ExecutionContext) -> APLArray:
        values = [el.value for el in self.elements]
        return APLArray.array([len(values)], list(values))


class MonadicFunc(Node):
    def __init__(self, function: str, operand: object) -> None:
        self.function = function
        self.operand = operand
    def execute(self, ctx: ExecutionContext) -> APLArray:
        operand = ctx.evaluate(self.operand)
        return ctx.dispatch_monadic(self.function, operand)


class DyadicFunc(Node):
    def __init__(self, function: str, left: object, right: object) -> None:
        self.function = function
        self.left = left
        self.right = right
    def execute(self, ctx: ExecutionContext) -> APLArray:
        right = ctx.evaluate(self.right)
        left = ctx.evaluate(self.left)
        return ctx.dispatch_dyadic(self.function, left, right)


class Assignment(Node):
    def __init__(self, name: str, value: object) -> None:
        self.name = name
        self.value = value
    def execute(self, ctx: ExecutionContext) -> APLArray:
        return ctx.assign(self.name, self.value)


class Var(Node):
    def __init__(self, name: str) -> None:
        self.name = name
    def execute(self, ctx: ExecutionContext) -> APLArray:
        if self.name not in ctx.env:
            raise ValueError_(f"Undefined variable: {self.name}")
        return ctx.env[self.name]


class QualifiedVar(Node):
    def __init__(self, parts: list[str]) -> None:
        self.parts = parts
    def execute(self, ctx: ExecutionContext) -> object:
        return ctx.resolve_qualified(self.parts)


class DerivedFunc(Node):
    def __init__(self, operator: str, function, operand: object) -> None:
        self.operator = operator
        self.function = function
        self.operand = operand
    def execute(self, ctx: ExecutionContext) -> APLArray:
        operand = ctx.evaluate(self.operand)
        return ctx.apply_derived(self.operator, self.function, operand)


class MonadicDopCall(Node):
    """User-defined operator applied: (operand op) argument
    or: left (operand op) right (when derived verb is used dyadically)"""
    def __init__(self, op_name: object, operand: object, argument: object,
                 alpha: object = None) -> None:
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


class DyadicDopCall(Node):
    """User-defined operator applied dyadically: left (operand op) right"""
    def __init__(self, op_name: object, operand: object, left: object, right: object) -> None:
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


class RankDerived:
    """Unapplied rank-derived function: f⍤k"""
    def __init__(self, function: object, rank_spec: object) -> None:
        self.function = function
        self.rank_spec = rank_spec
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RankDerived):
            return NotImplemented
        return self.function == other.function and self.rank_spec == other.rank_spec


class PowerDerived:
    """Unapplied power-derived function: f⍣g"""
    def __init__(self, function: object, right_operand: object) -> None:
        self.function = function
        self.right_operand = right_operand


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


class IBeamDerived(Node):
    """I-beam derived function: ⌶'module.function'"""
    def __init__(self, path: str) -> None:
        self.path = path
    def execute(self, ctx: ExecutionContext) -> object:
        return self


class InnerProduct(Node):
    def __init__(self, left_fn, right_fn, left: object, right: object) -> None:
        self.left_fn = left_fn
        self.right_fn = right_fn
        self.left = left
        self.right = right
    def execute(self, ctx: ExecutionContext) -> APLArray:
        omega = ctx.evaluate(self.right)
        alpha = ctx.evaluate(self.left)
        return _inner_product(self.left_fn, self.right_fn, alpha, omega)


class OuterProduct(Node):
    def __init__(self, function, left: object, right: object) -> None:
        self.function = function
        self.left = left
        self.right = right
    def execute(self, ctx: ExecutionContext) -> APLArray:
        omega = ctx.evaluate(self.right)
        alpha = ctx.evaluate(self.left)
        return _outer_product(self.function, alpha, omega)


class SysVar(Node):
    def __init__(self, name: str) -> None:
        self.name = name
    def execute(self, ctx: ExecutionContext) -> APLArray:
        return ctx.eval_sysvar(self.name)


class Index(Node):
    def __init__(self, array: object, indices: list[object | None]) -> None:
        self.array = array
        self.indices = indices
    def execute(self, ctx: ExecutionContext) -> APLArray:
        from marple.backend_functions import to_list
        array = ctx.evaluate(self.array)
        io = ctx.env.io
        flat = array.data.flatten() if is_numeric_array(array.data) else array.data
        axis_indices: list[list[int]] = []
        idx_shapes: list[list[int]] = []
        for axis, idx_node in enumerate(self.indices):
            if idx_node is None:
                axis_indices.append(list(range(array.shape[axis])))
                idx_shapes.append([array.shape[axis]])
            else:
                idx = ctx.evaluate(idx_node)
                idx_flat = idx.data.flatten() if is_numeric_array(idx.data) else idx.data
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
            result_data = np.empty(max(1, n_results), dtype=float)
            idx = 0
            for combo in _product(*axis_indices):
                offset = int(sum(i * s for i, s in zip(combo, strides)))
                result_data[idx] = flat[offset]
                idx += 1
            result_shape: list[int] = []
            for s in idx_shapes:
                result_shape.extend(s)
            if not result_shape:
                return S(result_data[0])
            return APLArray(result_shape, np_reshape(result_data[:idx], result_shape))
        # Character data
        result_list: list[object] = []
        for combo in _product(*axis_indices):
            offset = int(sum(i * s for i, s in zip(combo, strides)))
            result_list.append(flat[offset])
        result_shape = []
        for s in idx_shapes:
            result_shape.extend(s)
        if not result_shape:
            return S(result_list[0])
        return APLArray.array(result_shape, result_list)


class Omega(Node):
    def execute(self, ctx: ExecutionContext) -> APLArray:
        if "⍵" not in ctx.env:
            raise ValueError_("⍵ used outside of dfn")
        return ctx.env["⍵"]


class Alpha(Node):
    def execute(self, ctx: ExecutionContext) -> APLArray:
        if "⍺" not in ctx.env:
            raise ValueError_("⍺ used outside of dfn")
        return ctx.env["⍺"]


class FunctionRef(Node):
    """A reference to a primitive function glyph, used as a dop operand."""
    def __init__(self, glyph: str) -> None:
        self.glyph = glyph
    def execute(self, ctx: ExecutionContext) -> object:
        return self


class AlphaAlpha(Node):
    """⍺⍺ — left operand reference in a dop."""
    def execute(self, ctx: ExecutionContext) -> object:
        if "⍺⍺" not in ctx.env:
            raise ValueError_("⍺⍺ used outside of dop")
        return ctx.env["⍺⍺"]


class OmegaOmega(Node):
    """⍵⍵ — right operand reference in a dop."""
    def execute(self, ctx: ExecutionContext) -> object:
        if "⍵⍵" not in ctx.env:
            raise ValueError_("⍵⍵ used outside of dop")
        return ctx.env["⍵⍵"]


# CAT_EMPTY is a parser category constant needed by BoundOperator's default arg
CAT_EMPTY = 8


class BoundOperator:
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


class FmtArgs:
    """List of semicolon-separated arguments for ⎕FMT."""
    def __init__(self, args: list[object]) -> None:
        self.args = args
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FmtArgs):
            return NotImplemented
        return self.args == other.args


class Nabla(Node):
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


class Dfn(Node):
    def __init__(self, body: list[object]) -> None:
        self.body = body
    def execute(self, ctx: ExecutionContext) -> object:
        return ctx.create_binding(self)


class MonadicDfnCall(Node):
    def __init__(self, dfn: object, operand: object) -> None:
        self.dfn = dfn
        self.operand = operand
    def execute(self, ctx: ExecutionContext) -> APLArray:
        from marple.dfn_binding import DfnBinding
        if isinstance(self.dfn, SysVar):
            return ctx.dispatch_sys_monadic(self.dfn.name, self.operand)
        if isinstance(self.dfn, RankDerived):
            return ctx.apply_rank_monadic(self.dfn, self.operand)
        if isinstance(self.dfn, PowerDerived):
            return ctx.apply_power_monadic(self.dfn, self.operand)
        dfn_val = ctx.evaluate(self.dfn)
        operand = ctx.evaluate(self.operand)
        if isinstance(dfn_val, DfnBinding):
            return dfn_val.apply(operand)
        if isinstance(dfn_val, FunctionRef):
            return ctx.dispatch_monadic(dfn_val.glyph, operand)
        if isinstance(dfn_val, IBeamDerived):
            return ctx.call_ibeam(dfn_val.path, operand)
        # Old-style _DfnBinding from namespace system — wrap and apply
        if hasattr(dfn_val, 'dfn') and hasattr(dfn_val, 'env'):
            binding = DfnBinding(getattr(dfn_val, 'dfn'), ctx.env)
            return binding.apply(operand)
        raise DomainError(f"Expected dfn, got {type(dfn_val)}")


class DyadicDfnCall(Node):
    def __init__(self, dfn: object, left: object, right: object) -> None:
        self.dfn = dfn
        self.left = left
        self.right = right
    def execute(self, ctx: ExecutionContext) -> APLArray:
        from marple.dfn_binding import DfnBinding
        if isinstance(self.dfn, SysVar):
            return ctx.dispatch_sys_dyadic(self.dfn.name, self.left, self.right)
        if isinstance(self.dfn, RankDerived):
            return ctx.apply_rank_dyadic(self.dfn, self.left, self.right)
        if isinstance(self.dfn, PowerDerived):
            return ctx.apply_power_dyadic(self.dfn, self.left, self.right)
        dfn_val = ctx.evaluate(self.dfn)
        right = ctx.evaluate(self.right)
        left = ctx.evaluate(self.left)
        if isinstance(dfn_val, DfnBinding):
            return dfn_val.apply(right, alpha=left)
        if isinstance(dfn_val, FunctionRef):
            return ctx.dispatch_dyadic(dfn_val.glyph, left, right)
        raise DomainError(f"Expected dfn, got {type(dfn_val)}")


class Program(Node):
    def __init__(self, statements: list[object]) -> None:
        self.statements = statements
    def execute(self, ctx: ExecutionContext) -> object:
        result: object = S(0)
        for stmt in self.statements:
            result = ctx.evaluate(stmt)
        return result
