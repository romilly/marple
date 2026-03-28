"""APL environment (workspace state) for MARPLE."""

from typing import Any

from marple.arraymodel import APLArray, S


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
        self._data: dict[str, Any] = {}
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

    def __getitem__(self, key: str) -> Any:
        if key in self._quad_vars:
            return self._quad_vars[key]
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        if key in self._quad_vars:
            self._quad_vars[key] = value
        else:
            self._data[key] = value

    def __contains__(self, key: object) -> bool:
        return key in self._quad_vars or key in self._data

    def __delitem__(self, key: str) -> None:
        del self._data[key]

    def get(self, key: str, default: Any = None) -> Any:
        if key in self._quad_vars:
            return self._quad_vars[key]
        return self._data.get(key, default)

    def setdefault(self, key: str, default: Any) -> Any:
        return self._data.setdefault(key, default)

    def pop(self, key: str, *args: Any) -> Any:
        return self._data.pop(key, *args)

    def items(self) -> Any:
        return self._data.items()

    def copy(self) -> 'Environment':
        """Shallow copy — new Environment sharing the same value objects."""
        new = Environment.__new__(Environment)
        new._quad_vars = self._quad_vars
        new._data = dict(self._data)
        return new
