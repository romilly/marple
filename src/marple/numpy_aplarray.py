"""NumpyAPLArray — the APLArray adapter for desktop CPython + numpy.

Implements every port method on `APLArray` using numpy primitives.
The matching Pico adapter is in `src/marple/ulab_aplarray.py`.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from marple.get_numpy import np
from marple.ports.array import APLArray


class NumpyAPLArray(APLArray):
    """APLArray backed by numpy. Adapter for the desktop platform."""

    @classmethod
    def char_dtype(cls) -> Any:
        return np.uint32

    @classmethod
    @contextmanager
    def strict_numeric_errstate(cls) -> Iterator[None]:
        with np.errstate(over="raise", invalid="raise"):
            yield

    @classmethod
    @contextmanager
    def ignoring_numeric_errstate(cls) -> Iterator[None]:
        with np.errstate(over="ignore", invalid="ignore"):
            yield

    @classmethod
    def is_int_dtype(cls, arr: Any) -> bool:
        return bool(np.issubdtype(arr.dtype, np.integer))

    @classmethod
    def is_float_dtype(cls, arr: Any) -> bool:
        return bool(np.issubdtype(arr.dtype, np.floating))

    @classmethod
    def maybe_upcast(cls, data: Any) -> Any:
        from marple.backend_functions import is_numeric_array
        if not is_numeric_array(data) or not cls.is_int_dtype(data):
            return data
        return data.astype(np.float64)

    @classmethod
    def numeric_upcast_dtype(cls) -> Any:
        return np.float64

    @classmethod
    def reshape_ndarray(cls, arr: Any, shape: Any) -> Any:
        return arr.reshape(shape)

    @classmethod
    def repeat_ndarray(cls, arr: Any, counts: Any, axis: int) -> Any:
        return np.repeat(arr, counts, axis=axis)

    @classmethod
    def gather_ndarray(cls, data: Any, axis_indices: "list[list[int]]") -> Any:
        idx_arrays = [np.asarray(ax) for ax in axis_indices]
        return data[np.ix_(*idx_arrays)].flatten()

    def as_str(self) -> str:
        return ''.join(chr(int(x)) for x in self.data.flat)

    def is_char(self) -> bool:
        return self.data.dtype == self.char_dtype()

    def is_numeric(self) -> bool:
        return self.data.dtype != self.char_dtype()

    def to_list(self) -> list[Any]:
        if len(self.data.shape) == 0:
            return [self.data.item()]
        return self.data.tolist()

    def dtype_code(self) -> int:
        from marple.backend_functions import data_type_code
        return data_type_code(self.data)

    def slice_axis(self, axis: int, index: int) -> APLArray:
        rank = len(self.shape)
        if axis < 0 or axis >= rank:
            raise ValueError(
                "axis {} out of range for rank-{} array".format(axis, rank))
        idx = tuple(index if i == axis else slice(None) for i in range(rank))
        sliced = self.data[idx]
        new_shape = [s for i, s in enumerate(self.shape) if i != axis]
        return type(self)(new_shape, sliced)

    @classmethod
    def maybe_downcast(cls, data: Any, ct: float) -> Any:
        if not cls.is_float_dtype(data):
            return data
        if data.size == 0:
            return data
        rounded = np.round(data)
        diff = np.abs(data - rounded)
        if ct == 0:
            if not np.all(diff == 0):
                return data
        else:
            mag = np.maximum(np.abs(data), np.abs(rounded))
            if not np.all(diff <= ct * mag):
                return data
        max_val = np.max(np.abs(rounded))
        if max_val > np.float64(np.iinfo(np.int64).max):
            return data
        int_arr = rounded.astype(np.int64)
        if np.all(np.abs(int_arr) <= np.iinfo(np.int32).max):
            return int_arr.astype(np.int32)
        return int_arr
