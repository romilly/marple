"""AST node classes for MARPLE."""

from abc import ABC, abstractmethod
from typing import Any, Protocol

from marple.arraymodel import APLArray, S
from marple.errors import DomainError, ValueError_


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
        return APLArray([len(self.value)], list(self.value))


class Vector(Node):
    def __init__(self, elements: list[Num]) -> None:
        self.elements = elements
    def execute(self, ctx: ExecutionContext) -> APLArray:
        values = [el.value for el in self.elements]
        return APLArray([len(values)], list(values))


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
    def execute(self, ctx: ExecutionContext) -> APLArray:
        return ctx.eval_sysvar(self.name)


class Index:
    def __init__(self, array: object, indices: list[object | None]) -> None:
        self.array = array
        self.indices = indices
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Index):
            return NotImplemented
        return self.array == other.array and self.indices == other.indices


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


class OmegaOmega:
    """⍵⍵ — right operand reference in a dop."""
    pass


# CAT_EMPTY is a parser category constant needed by BoundOperator's default arg
CAT_EMPTY = 8


class BoundOperator:
    """Operator bound to operand(s), not yet applied to argument."""
    def __init__(self, operator: object, left_operand: object, left_cat: int,
                 right_operand: object = None, right_cat: int = CAT_EMPTY) -> None:
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
        dfn_val = ctx.evaluate(self.dfn)
        operand = ctx.evaluate(self.operand)
        if isinstance(dfn_val, DfnBinding):
            return dfn_val.apply(operand)
        if isinstance(dfn_val, FunctionRef):
            return ctx.dispatch_monadic(dfn_val.glyph, operand)
        raise DomainError(f"Expected dfn, got {type(dfn_val)}")


class DyadicDfnCall(Node):
    def __init__(self, dfn: object, left: object, right: object) -> None:
        self.dfn = dfn
        self.left = left
        self.right = right
    def execute(self, ctx: ExecutionContext) -> APLArray:
        from marple.dfn_binding import DfnBinding
        dfn_val = ctx.evaluate(self.dfn)
        right = ctx.evaluate(self.right)
        left = ctx.evaluate(self.left)
        if isinstance(dfn_val, DfnBinding):
            return dfn_val.apply(right, alpha=left)
        raise DomainError(f"Expected dfn, got {type(dfn_val)}")


class Program(Node):
    def __init__(self, statements: list[object]) -> None:
        self.statements = statements
    def execute(self, ctx: ExecutionContext) -> object:
        result: object = S(0)
        for stmt in self.statements:
            result = ctx.evaluate(stmt)
        return result
