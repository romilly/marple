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

    def transpose_dyadic(self, other: APLArray, io: int = 1) -> APLArray:
        from marple.errors import LengthError, RankError
        if len(self.shape) > 1:
            raise RankError("⍉ X must be a scalar or vector")
        x_atleast = np.atleast_1d(self.data)
        x_values = [int(v) for v in x_atleast]
        rank_y = len(other.shape)
        if len(x_values) != rank_y:
            raise LengthError(
                f"⍉ length of X ({len(x_values)}) must equal rank of Y ({rank_y})")
        x_zero = [v - io for v in x_values]
        if x_zero and (min(x_zero) < 0 or max(x_zero) >= rank_y):
            raise RankError("⍉ axis index out of range")
        if x_zero:
            max_xi = max(x_zero)
            required = set(range(max_xi + 1))
            actual = set(x_zero)
            if not required.issubset(actual):
                raise RankError("⍉ X is missing axis indices in its range")
            n_result_axes = max_xi + 1
        else:
            n_result_axes = 0
        result_shape: list[int] = []
        for k in range(n_result_axes):
            y_axes_for_k = [i for i, xi in enumerate(x_zero) if xi == k]
            result_shape.append(min(other.shape[i] for i in y_axes_for_k))
        if n_result_axes == 0:
            return type(other)([], other.data.copy())
        result_coords = np.indices(tuple(result_shape))
        y_coord_arrays = tuple(result_coords[xi] for xi in x_zero)
        result_data = other.data[y_coord_arrays]
        return type(other)(result_shape, result_data)

    def matrix_inverse(self) -> APLArray:
        from marple.errors import DomainError, RankError
        if len(self.shape) != 2 or self.shape[0] != self.shape[1]:
            raise RankError("Matrix inverse requires a square matrix")
        try:
            result = np.linalg.inv(self.data.astype(float))
        except np.linalg.LinAlgError:
            raise DomainError("Singular matrix")
        return type(self)(list(self.shape), result)

    def matrix_divide(self, other: APLArray) -> APLArray:
        from marple.errors import DomainError
        try:
            result = np.linalg.solve(other.data.astype(float), self.data.astype(float))
        except np.linalg.LinAlgError:
            raise DomainError("Singular matrix")
        return type(self)(list(result.shape), result)

    def catenate(self, other: APLArray) -> APLArray:
        if self.is_scalar() and other.is_scalar():
            return type(self)([2], np.concatenate(
                (self.data.flatten(), other.data.flatten())))
        if len(self.shape) <= 1 and len(other.shape) <= 1:
            a = self.data.flatten()
            b = other.data.flatten()
            return type(self)([len(a) + len(b)], np.concatenate((a, b)))
        a = self.data
        b = other.data
        a_rank = len(a.shape)
        b_rank = len(b.shape)
        if a_rank < b_rank:
            a = a.reshape([1] * (b_rank - a_rank) + list(a.shape))
        elif b_rank < a_rank:
            b = b.reshape([1] * (a_rank - b_rank) + list(b.shape))
        result = np.concatenate((a, b), axis=-1)
        return type(self)(list(result.shape), result)

    def rotate(self, other: APLArray) -> APLArray:
        n = int(self.scalar_value()) if self.is_scalar() else int(self.to_list()[0])
        return type(other)(list(other.shape), np.roll(other.data, -n, axis=-1))

    def rotate_first(self, other: APLArray) -> APLArray:
        n = int(self.scalar_value()) if self.is_scalar() else int(self.to_list()[0])
        if len(other.shape) <= 1:
            return self.rotate(other)
        return type(other)(list(other.shape), np.roll(other.data, -n, axis=0))

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
