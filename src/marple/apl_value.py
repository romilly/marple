"""APL value base class and name class constants for MARPLE."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from marple.nodes import ExecutionContext, Evaluatable, _PowerStrategy
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

    def as_power_strategy(self, ctx: ExecutionContext) -> _PowerStrategy:
        from marple.errors import DomainError
        raise DomainError("⍣ right operand must be integer or function")
