"""APL value base class and name class constants for MARPLE."""

from abc import ABC, abstractmethod

# Name classes (following Dyalog ⎕NC convention)
NC_UNKNOWN = 0
NC_ARRAY = 2
NC_FUNCTION = 3
NC_OPERATOR = 4


class APLValue(ABC):
    """Base class for all APL values (arrays and unapplied functions)."""

    @abstractmethod
    def name_class(self) -> int: ...
