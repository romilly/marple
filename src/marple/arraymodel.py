
try:
    from typing import Any
except ImportError:
    pass

from marple.backend import is_numeric_array, np, to_array, to_list


class APLArray:
    def __init__(self, shape: list[int], data: Any) -> None:
        self.shape = shape
        self.data = to_array(data) if isinstance(data, list) else data

    def is_scalar(self) -> bool:
        return self.shape == []

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, APLArray):
            return NotImplemented
        if self.shape != other.shape:
            return False
        if is_numeric_array(self.data) and is_numeric_array(other.data):
            return bool(np.array_equal(self.data, other.data))
        return to_list(self.data) == to_list(other.data)

    @classmethod
    def array(cls, shape: list[int], data: Any) -> 'APLArray':
        """Factory method for creating arrays. Use this instead of the constructor."""
        return cls(shape, data)

    @classmethod
    def scalar(cls, value: Any) -> 'APLArray':
        """Factory method for creating scalars. Use this instead of S()."""
        return cls([], [value])

    def __repr__(self) -> str:
        if self.is_scalar():
            return f"S({self.data[0]})"
        data_list = to_list(self.data) if is_numeric_array(self.data) else self.data
        return f"APLArray({self.shape}, {data_list})"


def S(value: Any) -> APLArray:
    return APLArray([], [value])
