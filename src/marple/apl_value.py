"""APL value base class and name class constants for MARPLE."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable

from marple.errors import DomainError

if TYPE_CHECKING:
    from marple.executor import Applicable, Executor, Executable, OperatorOperand
    from marple.numpy_array import APLArray

# Name classes (following Dyalog ⎕NC convention)
NC_UNKNOWN = 0
NC_ARRAY = 2
NC_FUNCTION = 3
NC_OPERATOR = 4


class APLValue(ABC):
    """Base class for all APL values: APLArray, Function, Operator."""

    @abstractmethod
    def name_class(self) -> int: ...


class Function(APLValue):
    """An APL function value: can be applied to one or two array arguments."""

    def name_class(self) -> int:
        return NC_FUNCTION

    @abstractmethod
    def apply_monadic(self, ctx: Executor, operand_node: Executable) -> APLArray: ...

    @abstractmethod
    def apply_dyadic(self, ctx: Executor, left_node: Executable, right_node: Executable) -> APLArray: ...

    def apply_to_monadic(self, ctx: Executor, omega: APLArray) -> APLArray:
        from marple.executor import Literal
        return self.apply_monadic(ctx, Literal(omega))

    def apply_to_dyadic(self, ctx: Executor, alpha: APLArray, omega: APLArray) -> APLArray:
        from marple.executor import Literal
        return self.apply_dyadic(ctx, Literal(alpha), Literal(omega))

    def as_power_strategy(self, ctx: Executor) -> PowerStrategy:
        return PowerByConvergence(self, ctx)


class Operator(APLValue):
    """An APL operator value: takes function operand(s) and derives a function."""

    def name_class(self) -> int:
        return NC_OPERATOR

    def derive_monadic(self, operand: OperatorOperand) -> Function:
        raise DomainError(f"{type(self).__name__} is not a monadic operator")

    def derive_dyadic(self, left: OperatorOperand, right: OperatorOperand) -> Function:
        raise DomainError(f"{type(self).__name__} is not a dyadic operator")

    def apply_monadic_dop(self, ctx: Executor, argument: APLArray,
                          operand: APLValue, alpha: APLArray | None = None) -> APLArray:
        raise DomainError(f"Cannot apply {type(self).__name__} as an operator")

    def apply_dyadic_dop(self, ctx: Executor, argument: APLArray,
                         left_operand: APLValue, right_operand: APLValue) -> APLArray:
        raise DomainError(f"Cannot apply {type(self).__name__} as an operator")


class PowerStrategy(ABC):
    """Iteration strategy for the power operator (f⍣g)."""
    @abstractmethod
    def iterate(self, step: Callable[[APLArray], APLArray], omega: APLArray) -> APLArray: ...


class PowerByCount(PowerStrategy):
    """Repeat f exactly n times."""
    def __init__(self, n: int) -> None:
        if n < 0:
            raise DomainError("DOMAIN ERROR: inverse (⍣ with negative) not supported")
        self.n = n
    def iterate(self, step: Callable[[APLArray], APLArray], omega: APLArray) -> APLArray:
        result = omega
        for _ in range(self.n):
            result = step(result)
        return result


class PowerByConvergence(PowerStrategy):
    """Repeat f until test_fn says consecutive results match."""
    def __init__(self, test_fn: 'Function', ctx: Executor) -> None:
        self.test_fn = test_fn
        self.ctx = ctx
    def iterate(self, step: Callable[[APLArray], APLArray], omega: APLArray) -> APLArray:
        prev = omega
        while True:
            curr = step(prev)
            if self.test_fn.apply_to_dyadic(self.ctx, curr, prev).scalar_value():
                return curr
            prev = curr
