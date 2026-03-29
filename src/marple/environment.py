"""APL environment (workspace state) for MARPLE."""

from typing import Any

from marple.arraymodel import APLArray, S
from marple.ports.filesystem import FileSystem
from marple.symbol_table import SymbolTable


_QUAD_DEFAULTS: dict[str, APLArray] = {
    "⎕IO": S(1),
    "⎕CT": S(1e-14),
    "⎕PP": S(10),
    "⎕EN": S(0),
    "⎕DM": APLArray([0], []),
    "⎕A": APLArray([26], list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")),
    "⎕D": APLArray([10], list("0123456789")),
    "⎕WSID": APLArray([8], list("CLEAR WS")),
    "⎕RL": S(1),
    "⎕FR": S(645),
}


class Environment:
    """APL workspace environment — variables, system settings, and name table."""

    def __init__(self, io: int | None = None,
                 fs: FileSystem | None = None) -> None:
        self._quad_vars: dict[str, APLArray] = dict(_QUAD_DEFAULTS)
        self.symbols = SymbolTable()
        self._locals: dict[str, Any] = {}
        if io is not None:
            self._quad_vars["⎕IO"] = S(io)
        if fs is not None:
            self.fs = fs
        else:
            from marple.adapters.os_filesystem import OsFileSystem
            self.fs = OsFileSystem()

    # ── System variable properties ──

    @property
    def io(self) -> int:
        return int(self._quad_vars["⎕IO"].data[0])

    @property
    def ct(self) -> float:
        return float(self._quad_vars["⎕CT"].data[0])

    @property
    def pp(self) -> int:
        return int(self._quad_vars["⎕PP"].data[0])

    @property
    def fr(self) -> int:
        return int(self._quad_vars["⎕FR"].data[0])

    # ── Symbol table delegation ──

    def bind_name(self, name: str, value: object, name_class: int) -> None:
        """Store a user-defined name with its value and class."""
        self.symbols.bind(name, value, name_class)

    def classify(self, name: str, name_class: int) -> None:
        """Set a name's class without storing a value (e.g. system functions)."""
        self.symbols.classify(name, name_class)

    def name_class(self, name: str) -> int:
        """Return the name class of a name (0 if unknown)."""
        return self.symbols.name_class(name)

    def delete_name(self, name: str) -> bool:
        """Remove a user-defined name. Returns True if it existed."""
        return self.symbols.delete(name)

    def names_of_class(self, nc: int) -> list[str]:
        """Return sorted list of user names with the given class."""
        return self.symbols.names_of_class(nc)

    def class_dict(self) -> dict[str, int]:
        """Return the raw name-class mapping (for parser compatibility)."""
        return self.symbols.class_dict()

    def set_operator_arity(self, name: str, arity: int) -> None:
        """Record the arity of a user-defined operator."""
        self.symbols.set_operator_arity(name, arity)

    def operator_arity_dict(self) -> dict[str, int]:
        """Return the raw operator arity mapping (for parser compatibility)."""
        return self.symbols.operator_arity_dict()

    def set_source(self, name: str, source: str) -> None:
        """Record the source text of a dfn/dop assignment."""
        self.symbols.set_source(name, source)

    def get_source(self, name: str) -> str | None:
        """Return the source text for a name, or None."""
        return self.symbols.get_source(name)

    def sources(self) -> dict[str, str]:
        """Return the raw sources mapping."""
        return self.symbols.sources()

    def quad_var_names(self) -> list[str]:
        """Return sorted list of quad variable names."""
        return sorted(self._quad_vars.keys())

    def user_names(self) -> list[str]:
        """Return sorted list of user-defined names in the symbol table."""
        return sorted(n for n in self.symbols._values.keys()
                       if not n.startswith("__"))

    # ── Dict-like interface ──
    # Lookup order: quad vars, then symbols, then locals (⍵, ⍺, ∇, etc.)

    def __getitem__(self, key: str) -> Any:
        if key in self._quad_vars:
            return self._quad_vars[key]
        val = self.symbols.get(key)
        if val is not None:
            return val
        return self._locals[key]

    def __setitem__(self, key: str, value: Any) -> None:
        if key in self._quad_vars:
            self._quad_vars[key] = value
        else:
            self._locals[key] = value

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        return key in self._quad_vars or key in self.symbols or key in self._locals

    def __delitem__(self, key: str) -> None:
        if key in self._locals:
            del self._locals[key]

    def get(self, key: str, default: Any = None) -> Any:
        if key in self._quad_vars:
            return self._quad_vars[key]
        val = self.symbols.get(key)
        if val is not None:
            return val
        return self._locals.get(key, default)

    def setdefault(self, key: str, default: Any) -> Any:
        return self._locals.setdefault(key, default)

    def pop(self, key: str, *args: Any) -> Any:
        return self._locals.pop(key, *args)

    def items(self) -> Any:
        return self._locals.items()

    def copy(self) -> 'Environment':
        """Copy for dfn local environments.

        Quad vars, symbols, and locals are all copied so that
        assignments inside a dfn do not leak to the caller.
        """
        new = Environment(fs=self.fs)
        new._quad_vars = dict(self._quad_vars)
        new.symbols = self.symbols.copy()
        new._locals = dict(self._locals)
        return new
