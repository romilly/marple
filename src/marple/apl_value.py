"""APL value base class and name class constants for MARPLE."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from marple.nodes import ExecutionContext, Evaluatable
    from marple.numpy_array import APLArray

# Name classes (following Dyalog ⎕NC convention)
NC_UNKNOWN = 0
NC_ARRAY = 2
NC_FUNCTION = 3
NC_OPERATOR = 4


class APLValue(ABC):
    """Base class for all APL values (arrays and unapplied functions)."""

    @abstractmethod
    def name_class(self) -> int: ...

    def apply_to_monadic(self, ctx: ExecutionContext, omega: APLArray) -> APLArray:
        from marple.errors import DomainError
        raise DomainError(f"Cannot apply {type(self).__name__} as a function")

    def apply_to_dyadic(self, ctx: ExecutionContext, alpha: APLArray, omega: APLArray) -> APLArray:
        from marple.errors import DomainError
        raise DomainError(f"Cannot apply {type(self).__name__} as a function")

    def call_monadic(self, ctx: ExecutionContext, operand: Evaluatable) -> APLArray:
        from marple.errors import DomainError
        raise DomainError(f"Cannot call {type(self).__name__} as a function")

    def call_dyadic(self, ctx: ExecutionContext, left: Evaluatable, right: Evaluatable) -> APLArray:
        from marple.errors import DomainError
        raise DomainError(f"Cannot call {type(self).__name__} as a function")

    def apply_monadic_dop(self, ctx: ExecutionContext, argument: APLArray,
                          operand: APLValue, alpha: APLArray | None = None) -> APLArray:
        from marple.errors import DomainError
        raise DomainError(f"Cannot apply {type(self).__name__} as an operator")

    def apply_dyadic_dop(self, ctx: ExecutionContext, argument: APLArray,
                         left_operand: APLValue, right_operand: APLValue) -> APLArray:
        from marple.errors import DomainError
        raise DomainError(f"Cannot apply {type(self).__name__} as an operator")

    def as_power_strategy(self, ctx: ExecutionContext) -> PowerStrategy:
        from marple.errors import DomainError
        raise DomainError("⍣ right operand must be integer or function")


class PowerStrategy(ABC):
    """Iteration strategy for the power operator (f⍣g)."""
    @abstractmethod
    def iterate(self, step: Callable[[APLArray], APLArray], omega: APLArray) -> APLArray: ...


class PowerByCount(PowerStrategy):
    """Repeat f exactly n times."""
    def __init__(self, n: int) -> None:
        from marple.errors import DomainError
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
    def __init__(self, test_fn: APLValue, ctx: ExecutionContext) -> None:
        self.test_fn = test_fn
        self.ctx = ctx
    def iterate(self, step: Callable[[APLArray], APLArray], omega: APLArray) -> APLArray:
        prev = omega
        while True:
            curr = step(prev)
            if self.test_fn.apply_to_dyadic(self.ctx, curr, prev).data.item():
                return curr
            prev = curr
