from __future__ import annotations

from typing import Any


class APLArray:
    def __init__(self, shape: list[int], data: list[Any]) -> None:
        self.shape = shape
        self.data = data

    def is_scalar(self) -> bool:
        return self.shape == []

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, APLArray):
            return NotImplemented
        return self.shape == other.shape and self.data == other.data

    def __repr__(self) -> str:
        if self.is_scalar():
            return f"S({self.data[0]})"
        return f"APLArray({self.shape}, {self.data})"


def S(value: Any) -> APLArray:
    return APLArray([], [value])
