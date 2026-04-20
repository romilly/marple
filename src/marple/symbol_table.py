"""Symbol table for user-defined names in MARPLE."""

from __future__ import annotations

from typing import TYPE_CHECKING

from marple.apl_value import APLValue, NC_ARRAY, NC_FUNCTION, NC_OPERATOR, NC_UNKNOWN

if TYPE_CHECKING:
    from marple.ports.array import APLArray


class SymbolTable:
    """Tracks user-defined names, their values, and their name classes.

    Values are stored in typed dicts by name class: _arrays for NC_ARRAY,
    _functions for NC_FUNCTION, _operators for NC_OPERATOR. System names
    (⎕-prefixed) that have a class but no stored value use _system_classes.
    """

    def __init__(self) -> None:
        self._arrays: dict[str, APLArray] = {}
        self._functions: dict[str, APLValue] = {}
        self._operators: dict[str, APLValue] = {}
        self._system_classes: dict[str, int] = {}
        self._operator_arity: dict[str, int] = {}
        self._sources: dict[str, str] = {}

    _CLASS_TO_ATTR = {
        NC_ARRAY: '_arrays',
        NC_FUNCTION: '_functions',
        NC_OPERATOR: '_operators',
    }

    def bind(self, name: str, value: APLValue, name_class: int) -> None:
        """Store a name with its value and class."""
        # Remove from any previous dict (name class may change on reassignment)
        self._remove_value(name)
        attr = self._CLASS_TO_ATTR.get(name_class)
        if attr is not None:
            getattr(self, attr)[name] = value
        self._system_classes.pop(name, None)

    def classify(self, name: str, name_class: int) -> None:
        """Set a name's class, moving it between value dicts if it has a stored value."""
        val = self.get(name)
        if val is not None:
            self._remove_value(name)
            attr = self._CLASS_TO_ATTR.get(name_class)
            if attr is not None:
                getattr(self, attr)[name] = val
        else:
            self._system_classes[name] = name_class

    def get(self, name: str) -> APLValue | None:
        """Return the value bound to a name, or None if not found."""
        for d in (self._arrays, self._functions, self._operators):
            if name in d:
                return d[name]
        return None

    def name_class(self, name: str) -> int:
        """Return the name class (0 if unknown)."""
        if name in self._arrays:
            return NC_ARRAY
        if name in self._functions:
            return NC_FUNCTION
        if name in self._operators:
            return NC_OPERATOR
        return self._system_classes.get(name, NC_UNKNOWN)

    def __contains__(self, name: object) -> bool:
        return (name in self._arrays
                or name in self._functions
                or name in self._operators)

    def set_operator_arity(self, name: str, arity: int) -> None:
        """Record the arity (1=monadic, 2=dyadic) of a user-defined operator."""
        self._operator_arity[name] = arity

    def operator_arity_dict(self) -> dict[str, int]:
        """Return the raw operator arity mapping (for parser compatibility)."""
        return self._operator_arity

    def set_source(self, name: str, source: str) -> None:
        """Record the source text of a dfn/dop assignment."""
        self._sources[name] = source

    def get_source(self, name: str) -> str | None:
        """Return the source text for a name, or None."""
        return self._sources.get(name)

    def sources(self) -> dict[str, str]:
        """Return the raw sources mapping."""
        return self._sources

    def _remove_value(self, name: str) -> bool:
        """Remove a name from whichever value dict holds it. Returns True if found."""
        for d in (self._arrays, self._functions, self._operators):
            if name in d:
                del d[name]
                return True
        return False

    def delete(self, name: str) -> bool:
        """Remove a name. Returns True if it existed."""
        found = self._remove_value(name)
        self._system_classes.pop(name, None)
        self._operator_arity.pop(name, None)
        self._sources.pop(name, None)
        return found

    def _user_names(self, d: dict[str, APLValue]) -> list[str]:
        """Return sorted user names from a value dict, excluding system names."""
        return sorted(n for n in d if not n.startswith("⎕") and not n.startswith("__"))

    def names_of_class(self, nc: int) -> list[str]:
        """Return sorted list of user names with the given class."""
        attr = self._CLASS_TO_ATTR.get(nc)
        if attr is None:
            return []
        return self._user_names(getattr(self, attr))

    def arrays(self) -> list[tuple[str, APLArray]]:
        """Return sorted list of (name, value) for user arrays."""
        return sorted(
            (n, v) for n, v in self._arrays.items()
            if not n.startswith("⎕") and not n.startswith("__")
        )

    def functions(self) -> list[tuple[str, APLValue]]:
        """Return sorted list of (name, value) for user functions."""
        return sorted(
            (n, v) for n, v in self._functions.items()
            if not n.startswith("⎕") and not n.startswith("__")
        )

    def operators(self) -> list[tuple[str, APLValue]]:
        """Return sorted list of (name, value) for user operators."""
        return sorted(
            (n, v) for n, v in self._operators.items()
            if not n.startswith("⎕") and not n.startswith("__")
        )

    def class_dict(self) -> dict[str, int]:
        """Return the raw name-class mapping (for parser compatibility)."""
        result = dict(self._system_classes)
        for n in self._arrays:
            result[n] = NC_ARRAY
        for n in self._functions:
            result[n] = NC_FUNCTION
        for n in self._operators:
            result[n] = NC_OPERATOR
        return result

    def copy(self) -> SymbolTable:
        """Shallow copy of this symbol table."""
        new = SymbolTable()
        new._arrays = dict(self._arrays)
        new._functions = dict(self._functions)
        new._operators = dict(self._operators)
        new._system_classes = dict(self._system_classes)
        new._operator_arity = dict(self._operator_arity)
        new._sources = dict(self._sources)
        return new
