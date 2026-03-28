"""Symbol table for user-defined names in MARPLE."""

from typing import Any

# Name classes (following Dyalog ⎕NC convention)
NC_UNKNOWN = 0
NC_ARRAY = 2
NC_FUNCTION = 3
NC_OPERATOR = 4


class SymbolTable:
    """Tracks user-defined names, their values, and their name classes."""

    def __init__(self) -> None:
        self._values: dict[str, Any] = {}
        self._classes: dict[str, int] = {}

    def bind(self, name: str, value: Any, name_class: int) -> None:
        """Store a name with its value and class."""
        self._values[name] = value
        self._classes[name] = name_class

    def classify(self, name: str, name_class: int) -> None:
        """Set a name's class without storing a value (e.g. system functions)."""
        self._classes[name] = name_class

    def get(self, name: str) -> Any:
        """Return the value bound to a name, or None if not found."""
        return self._values.get(name)

    def name_class(self, name: str) -> int:
        """Return the name class (0 if unknown)."""
        return self._classes.get(name, NC_UNKNOWN)

    def __contains__(self, name: object) -> bool:
        return name in self._values

    def delete(self, name: str) -> bool:
        """Remove a name. Returns True if it existed."""
        found = name in self._values
        self._values.pop(name, None)
        self._classes.pop(name, None)
        return found

    def names_of_class(self, nc: int) -> list[str]:
        """Return sorted list of user names with the given class."""
        return sorted(
            n for n, c in self._classes.items()
            if c == nc and not n.startswith("⎕") and not n.startswith("__")
        )

    def class_dict(self) -> dict[str, int]:
        """Return the raw name-class mapping (for parser compatibility)."""
        return self._classes

    def copy(self) -> 'SymbolTable':
        """Shallow copy of this symbol table."""
        new = SymbolTable()
        new._values = dict(self._values)
        new._classes = dict(self._classes)
        return new
