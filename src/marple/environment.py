"""APL environment (workspace state) for MARPLE."""

from typing import Any

from marple.arraymodel import APLArray, S
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

    def __init__(self, io: int | None = None) -> None:
        self._quad_vars: dict[str, APLArray] = dict(_QUAD_DEFAULTS)
        self.symbols = SymbolTable()
        self._locals: dict[str, Any] = {}
        if io is not None:
            self._quad_vars["⎕IO"] = S(io)

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
        """Shallow copy for dfn local environments.

        Quad vars are shared (same reference). Symbols and locals are copied.
        """
        new = Environment.__new__(Environment)
        new._quad_vars = self._quad_vars
        new.symbols = self.symbols.copy()
        new._locals = dict(self._locals)
        return new
