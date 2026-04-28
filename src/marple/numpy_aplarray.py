"""NumpyAPLArray — the APLArray adapter for desktop CPython + numpy.

Implements every port method on `APLArray` using numpy primitives.
The matching Pico adapter is in `src/marple/ulab_aplarray.py`.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import numpy as np
from marple.ports.array import APLArray, str_to_char_array, is_numeric_array, data_type_code, is_int_dtype

def char_fill() -> Any:
    """Return the fill element for character arrays: the space codepoint.

    Returns a plain int; callers pass it to `np.array([char_fill()],
    dtype=get_char_dtype())` which produces a typed scalar. ulab's
    `np.uint16` is not callable (it's an int constant), so the old
    `CHAR_DTYPE(32)` path that worked on CPython fails there — this
    neutral form works on both.
    """
    return 32

class NumpyAPLArray(APLArray):
    """APLArray backed by numpy. Adapter for the desktop platform."""

    @classmethod
    def scalar(cls, value: Any) -> APLArray:
        """Factory method for creating scalars.

        APL shape is `[]`. Underlying storage is 0-d on desktop numpy
        and 1-d length-1 on ulab — see __init__ for the invariant.
        On the port itself (`APLArray.scalar(...)`) dispatches to the
        active adapter.
        """
        if isinstance(value, str):
            return cls([], str_to_char_array(value))
        return cls([], value)

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
        #from marple.backend_functions import is_numeric_array
        if not is_numeric_array(data) or not is_int_dtype(data):
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
        return data_type_code(self.data)

    @staticmethod
    def _first_axis_chunk_size(shape: list[int]) -> int:
        size = 1
        for s in shape[1:]:
            size *= s
        return size

    @staticmethod
    def _fill_element(source: APLArray) -> Any:
        return char_fill() if source.is_char() else 0

    @staticmethod
    def _take_axis(data: list[Any], axis_len: int, n: int,
                   fill: Any) -> tuple[list[Any], int]:
        abs_n = abs(n)
        if n >= 0:
            taken = data[:abs_n]
            pad = [fill] * max(0, abs_n - axis_len)
            return taken + pad, abs_n
        taken = data[max(0, axis_len + n):]
        pad = [fill] * max(0, abs_n - axis_len)
        return pad + taken, abs_n

    @classmethod
    def _build_like(cls, data: list[Any], shape: list[int],
                    source: APLArray) -> APLArray:
        dtype = source.data.dtype
        arr = np.array(data, dtype=dtype) if data else np.array([], dtype=dtype)
        if shape:
            arr = arr.reshape(shape)
        return cls(shape, arr)

    def take(self, other: APLArray) -> APLArray:
        counts = [int(x) for x in self.to_list()]
        fill = self._fill_element(other)
        while len(counts) < len(other.shape):
            counts.append(other.shape[len(counts)])
        flat = other.data.flatten()
        if len(other.shape) <= 1:
            n = counts[0]
            data = list(flat)
            result, new_len = self._take_axis(data, len(data), n, fill)
            return type(other)._build_like(result, [new_len], other)
        n = counts[0]
        abs_n = abs(n)
        chunk = self._first_axis_chunk_size(other.shape)
        num_rows = other.shape[0]
        fill_row = [fill] * chunk
        rows: list[list[Any]] = []
        for r in range(abs_n):
            src = r if n >= 0 else num_rows + n + r
            if 0 <= src < num_rows:
                rows.append(list(flat[src * chunk:(src + 1) * chunk]))
            else:
                rows.append(list(fill_row))
        if len(counts) > 1:
            inner_shape = list(other.shape[1:])
            inner_counts = counts[1:]
            processed: list[Any] = []
            inner_shape_out = inner_shape
            for row in rows:
                inner = type(other)._build_like(row, inner_shape, other)
                taken = type(self).array([len(inner_counts)], inner_counts).take(inner)
                processed.extend(list(taken.data.flatten()))
                inner_shape_out = list(taken.shape)
            return type(other)._build_like(processed, [abs_n] + inner_shape_out, other)
        new_shape = list(other.shape)
        new_shape[0] = abs_n
        result_data: list[Any] = []
        for row in rows:
            result_data.extend(row)
        return type(other)._build_like(result_data, new_shape, other)

    def drop(self, other: APLArray) -> APLArray:
        counts = [int(x) for x in self.to_list()]
        while len(counts) < len(other.shape):
            counts.append(0)
        flat = other.data.flatten()
        if len(other.shape) <= 1:
            n = counts[0]
            data = list(flat)
            if n >= 0:
                result = data[n:]
            else:
                result = data[:n] if n != 0 else data
            return type(other)._build_like(result, [len(result)], other)
        n = counts[0]
        chunk = self._first_axis_chunk_size(other.shape)
        num_rows = other.shape[0]
        if n >= 0:
            start = min(n, num_rows)
            kept_rows = num_rows - start
        else:
            start = 0
            kept_rows = max(num_rows + n, 0)
        rows: list[list[Any]] = []
        for r in range(kept_rows):
            src = start + r if n >= 0 else r
            rows.append(list(flat[src * chunk:(src + 1) * chunk]))
        if len(counts) > 1:
            inner_shape = list(other.shape[1:])
            inner_counts = counts[1:]
            processed: list[Any] = []
            inner_shape_out = inner_shape
            for row in rows:
                inner = type(other)._build_like(row, inner_shape, other)
                dropped = type(self).array([len(inner_counts)], inner_counts).drop(inner)
                processed.extend(list(dropped.data.flatten()))
                inner_shape_out = list(dropped.shape)
            return type(other)._build_like(processed, [kept_rows] + inner_shape_out, other)
        new_shape = list(other.shape)
        new_shape[0] = kept_rows
        result_data: list[Any] = []
        for row in rows:
            result_data.extend(row)
        return type(other)._build_like(result_data, new_shape, other)

    def encode(self, other: APLArray) -> APLArray:
        from marple.errors import DomainError
        if self.is_char() or other.is_char():
            raise DomainError("⊤ is not defined on character data")
        a = self.data
        o = other.data
        a_atleast = np.atleast_1d(a)
        n = a_atleast.shape[0]
        other_a_dims = a_atleast.shape[1:]
        result_shape = list(a.shape) + list(o.shape)
        out_dtype = np.result_type(a_atleast.dtype, o.dtype)
        if n == 0:
            return type(other)(
                result_shape,
                np.zeros(tuple(result_shape), dtype=out_dtype))
        carry_shape = other_a_dims + o.shape
        carry = np.broadcast_to(o, carry_shape).astype(out_dtype)
        out = np.empty((n,) + carry_shape, dtype=out_dtype)
        view_shape = other_a_dims + (1,) * len(o.shape)
        for i in range(n - 1, -1, -1):
            radix_i = a_atleast[i].reshape(view_shape)
            zero_mask = (radix_i == 0)
            safe_radix = np.where(zero_mask, 1, radix_i)
            digit = np.where(zero_mask, carry, carry % safe_radix)
            carry = np.where(zero_mask, np.zeros_like(carry), carry // safe_radix)
            out[i] = digit
        return type(other)(result_shape, out)

    def decode(self, other: APLArray) -> APLArray:
        from marple.errors import DomainError, LengthError
        if self.is_char() or other.is_char():
            raise DomainError("⊥ is not defined on character data")
        a = self.data
        o = other.data
        a_atleast = np.atleast_1d(a)
        o_atleast = np.atleast_1d(o)
        a_n = a_atleast.shape[-1]
        o_n = o_atleast.shape[0]
        a_outer = list(a.shape[:-1]) if len(a.shape) >= 1 else []
        o_outer = list(o.shape[1:]) if len(o.shape) >= 1 else []
        result_shape = a_outer + o_outer
        if a_n == 0 or o_n == 0:
            return type(other)(
                result_shape,
                np.zeros(tuple(result_shape) or (), dtype=a.dtype))
        if a_n != o_n and a_n != 1 and o_n != 1:
            raise LengthError(f"⊥ length mismatch: {a_n} vs {o_n}")
        n = max(a_n, o_n)
        a_view = np.broadcast_to(a_atleast, a_atleast.shape[:-1] + (n,))
        o_view = np.broadcast_to(o_atleast, (n,) + o_atleast.shape[1:])
        ones_tail = np.ones(a_view.shape[:-1] + (1,), dtype=a_view.dtype)
        shifted = np.concatenate([a_view[..., 1:], ones_tail], axis=-1)
        weights = np.flip(np.cumprod(np.flip(shifted, axis=-1), axis=-1), axis=-1)
        result = weights @ o_view
        return type(other)(result_shape, result)

    def from_array(self, other: APLArray, io: int = 1) -> APLArray:
        from marple.errors import IndexError_, RankError
        if other.is_scalar():
            raise RankError("requires non-scalar right argument")
        flat = other.data.flatten()
        cell_shape = other.shape[1:]
        cell_size = 1
        for s in cell_shape:
            cell_size *= s
        if cell_size == 0:
            cell_size = 1
        n_major = other.shape[0]
        idx_flat = self.data.flatten()
        indices = list(idx_flat) if not self.is_scalar() else [self.data.flatten()[0]]
        result_cells: list[Any] = []
        for idx in indices:
            i = int(idx) - io
            if i < 0 or i >= n_major:
                raise IndexError_(f"{idx} out of range")
            result_cells.append(flat[i * cell_size : (i + 1) * cell_size])
        if len(result_cells) == 0:
            return type(other).array(cell_shape, [])
        result = np.concatenate(tuple(result_cells))
        if self.is_scalar():
            return type(other)(cell_shape, result.reshape(cell_shape) if cell_shape else result)
        result_shape = list(self.shape) + cell_shape
        return type(other)(result_shape, result.reshape(result_shape))

    def replicate(self, other: APLArray) -> APLArray:
        from marple.errors import LengthError
        counts = [int(x) for x in self.to_list()]
        last_axis_len = other.shape[-1] if other.shape else 1
        if len(counts) == 1 and last_axis_len > 1:
            counts = counts * last_axis_len
        if len(counts) != last_axis_len:
            raise LengthError(f"Length mismatch: {len(counts)} vs {last_axis_len}")
        result = np.repeat(other.data, counts, axis=-1)
        return type(other)(list(result.shape), result)

    def replicate_first(self, other: APLArray) -> APLArray:
        from marple.errors import LengthError
        if len(other.shape) <= 1:
            return self.replicate(other)
        counts = [int(x) for x in self.to_list()]
        first_axis_len = other.shape[0]
        if len(counts) == 1 and first_axis_len > 1:
            counts = counts * first_axis_len
        if len(counts) != first_axis_len:
            raise LengthError(f"Length mismatch: {len(counts)} vs {first_axis_len}")
        result = np.repeat(other.data, counts, axis=0)
        return type(other)(list(result.shape), result)

    def expand(self, other: APLArray) -> APLArray:
        from marple.errors import LengthError
        mask = [int(x) for x in self.to_list()]
        fill = self._fill_element(other)
        n_ones = sum(1 for m in mask if m)
        last_axis_len = other.shape[-1] if other.shape else 1
        if n_ones != last_axis_len:
            raise LengthError(
                f"Expand: mask has {n_ones} ones but argument has {last_axis_len} elements")
        out_shape = (list(other.shape[:-1]) + [len(mask)]) if other.shape else [len(mask)]
        result = np.full(out_shape, fill, dtype=other.data.dtype)
        one_positions = [i for i, m in enumerate(mask) if m]
        if one_positions:
            result[..., one_positions] = other.data
        return type(other)(out_shape, result)

    def reshape(self, other: APLArray) -> APLArray:
        if self.is_scalar():
            new_shape = [int(self.scalar_value())]
        else:
            new_shape = [int(x) for x in self.to_list()]
        total = 1
        for s in new_shape:
            total *= s
        flat = other.data.flatten()
        if len(flat) == 0:
            if other.data.dtype == self.char_dtype():
                flat = np.array([char_fill()], dtype=self.char_dtype())
            else:
                flat = np.array([0])
        n = len(flat)
        if total <= n:
            cycled = flat[:total]
        else:
            reps = total // n + 1
            cycled = np.concatenate(tuple([flat] * reps))[:total]
        return type(other)(new_shape, cycled.reshape(new_shape))

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
    
