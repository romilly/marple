from __future__ import annotations


class APLError(Exception):
    """Base class for APL errors."""
    code: int = 0
    name: str = "ERROR"

    def __init__(self, message: str = "") -> None:
        self.message = message
        super().__init__(f"{self.name}: {message}" if message else self.name)


class SyntaxError_(APLError):
    code = 1
    name = "SYNTAX ERROR"


class ValueError_(APLError):
    code = 2
    name = "VALUE ERROR"


class DomainError(APLError):
    code = 3
    name = "DOMAIN ERROR"


class LengthError(APLError):
    code = 4
    name = "LENGTH ERROR"


class RankError(APLError):
    code = 5
    name = "RANK ERROR"


class IndexError_(APLError):
    code = 6
    name = "INDEX ERROR"


class LimitError(APLError):
    code = 7
    name = "LIMIT ERROR"


class WSFullError(APLError):
    code = 8
    name = "WS FULL"


class SecurityError(APLError):
    code = 9
    name = "SECURITY ERROR"


class DependencyError(APLError):
    code = 10
    name = "DEPENDENCY ERROR"


class ClassError(APLError):
    code = 11
    name = "CLASS ERROR"
