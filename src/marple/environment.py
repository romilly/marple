"""APL environment (workspace state) for MARPLE."""

from typing import Any, Iterator

from marple.arraymodel import APLArray, S


_SYSTEM_DEFAULTS: dict[str, Any] = {
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
        self._data: dict[str, Any] = dict(_SYSTEM_DEFAULTS)
        if io is not None:
            self._data["⎕IO"] = S(io)

    # ── System variable properties ──

    @property
    def io(self) -> int:
        return int(self._data["⎕IO"].data[0])

    @property
    def ct(self) -> float:
        return float(self._data["⎕CT"].data[0])

    @property
    def pp(self) -> int:
        return int(self._data["⎕PP"].data[0])

    @property
    def fr(self) -> int:
        return int(self._data["⎕FR"].data[0])

    # ── Dict-like interface ──

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    def __contains__(self, key: object) -> bool:
        return key in self._data

    def __delitem__(self, key: str) -> None:
        del self._data[key]

    def get(self, key: str, default: Any = None) -> Any:
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
        new._data = dict(self._data)
        return new
