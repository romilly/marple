"""UlabAPLArray — APLArray subclass for MicroPython + ulab on the Pico.

Walking-skeleton desk sketch. The class parses and loads on CPython
(where `from marple.get_numpy import np` resolves to real numpy); it is
only *exercised* on hardware, where get_numpy.py is wired to return
`ulab.numpy`.

Overrides backend hooks so the Pico path works on ulab:

1. `char_dtype()` → uint16. ulab caps unsigned integer types at 16 bits,
   so BMP codepoints are stored as uint16 rather than uint32.

2. `strict_numeric_errstate` / `ignoring_numeric_errstate` → no-ops.
   ulab has no `np.errstate` equivalent; integer arithmetic wraps
   silently and there is no FloatingPointError to catch.

3. `is_int_dtype` / `is_float_dtype` → dtype-constant set membership
   (ulab has no np.issubdtype; its dtype tokens are small ints).

4. `maybe_upcast` → rebuilds int data as float32 via np.array(list, …)
   (ulab has no .astype and no float64).

5. `maybe_downcast` → vectorised floor-based round + tolerance check +
   one-shot Python-list convert to int16 at the end (ulab has no
   np.round, .astype, np.iinfo).

`_numeric_dyadic_op` is NOT overridden: the cast hooks above make the
inherited APLArray implementation ulab-safe.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from marple.get_numpy import np
from marple.ports.array import APLArray


class UlabAPLArray(APLArray):
    """APLArray backed by ulab on MicroPython."""

    @classmethod
    def char_dtype(cls) -> Any:
        return np.uint16

    @classmethod
    @contextmanager
    def strict_numeric_errstate(cls) -> Iterator[None]:
        yield

    @classmethod
    @contextmanager
    def ignoring_numeric_errstate(cls) -> Iterator[None]:
        yield

    # --- numeric-cast hooks -------------------------------------------------
    # ulab's dtype tokens are small integers (the struct-format chars) rather
    # than numpy.dtype objects, and np.issubdtype / np.iinfo / float64 don't
    # exist. Override the numpy defaults with ulab-compatible versions.

    # ulab dtype constants present on the Pimoroni rp2 build:
    #   np.uint8=66, np.int8=98, np.uint16=72, np.int16=104, np.float=102.
    # Build the sets lazily so a missing attr (e.g. uint32) doesn't crash
    # module load.
    _INT_DTYPES: "frozenset[Any] | None" = None
    _FLOAT_DTYPES: "frozenset[Any] | None" = None

    @classmethod
    def _int_dtypes(cls) -> "frozenset[Any]":
        if cls._INT_DTYPES is None:
            vals: list[Any] = []
            for name in ("uint8", "int8", "uint16", "int16"):
                v = getattr(np, name, None)
                if v is not None:
                    vals.append(v)
            cls._INT_DTYPES = frozenset(vals)
        return cls._INT_DTYPES

    @classmethod
    def _float_dtypes(cls) -> "frozenset[Any]":
        if cls._FLOAT_DTYPES is None:
            vals: list[Any] = []
            for name in ("float", "float32"):
                v = getattr(np, name, None)
                if v is not None:
                    vals.append(v)
            cls._FLOAT_DTYPES = frozenset(vals)
        return cls._FLOAT_DTYPES

    @classmethod
    def is_int_dtype(cls, arr: Any) -> bool:
        return arr.dtype in cls._int_dtypes()

    @classmethod
    def is_float_dtype(cls, arr: Any) -> bool:
        return arr.dtype in cls._float_dtypes()

    @classmethod
    def numeric_upcast_dtype(cls) -> Any:
        # ulab has no float64; float is float32 on the Pimoroni build.
        return np.float

    @classmethod
    def maybe_upcast(cls, data: Any) -> Any:
        """Upcast int data to ulab's widest float (float32) before arithmetic.

        Desktop uses float64 for overflow protection; ulab's widest is
        float32, which still beats silent int16 overflow. Most ulab data
        is already float because `np.array([1,2,3])` returns float32 —
        so this is usually a no-op. The int-dtype branch handles the
        cases where someone explicitly constructed with an int dtype.
        """
        from marple.backend_functions import is_numeric_array
        if not is_numeric_array(data) or not cls.is_int_dtype(data):
            return data
        # ulab has no .astype; rebuild as float. Acceptable for the
        # small-array sizes the Pico handles.
        return np.array(list(data), dtype=np.float)

    @classmethod
    def maybe_downcast(cls, data: Any, ct: float) -> Any:
        """Recover integer result from float array when values are whole.

        Vectorised via ulab primitives (isfinite, floor, abs, maximum, all,
        max plus operator overloads). ulab has no `np.round`, so we use
        `floor(x + 0.5)` — round-half-up, which is fine for the integer-
        recovery tolerance check (exact halves fail the
        `|x - rounded| <= ct * mag` bound and never pass).

        Final float→int conversion goes through a one-shot Python list
        because ulab has no `.astype`; `np.array(list, dtype=np.int16)`
        does the typed rebuild. ulab's widest signed int on this build is
        int16 (±32767); values outside that range keep their float form.
        """
        if not cls.is_float_dtype(data):
            return data
        if data.size == 0:
            return data
        if not np.all(np.isfinite(data)):
            return data
        rounded = np.floor(data + 0.5)
        diff = abs(data - rounded)
        if ct == 0:
            if not np.all(diff == 0):
                return data
        else:
            mag = np.maximum(abs(data), abs(rounded))
            if not np.all(diff <= ct * mag):
                return data
        if float(np.max(abs(rounded))) > 32767:
            return data
        data_rank = len(data.shape)
        flat = rounded.flatten() if data_rank > 1 else rounded
        int_flat = np.array([int(x) for x in flat], dtype=np.int16)
        return cls.reshape_ndarray(int_flat, data.shape) if data_rank > 1 else int_flat

    def as_str(self) -> str:
        return ''.join(chr(int(x)) for x in self.data.flat)

    def is_char(self) -> bool:
        return self.data.dtype == self.char_dtype()

    def is_numeric(self) -> bool:
        return self.data.dtype != self.char_dtype()

    def to_list(self) -> list[Any]:
        if len(self.data.shape) == 0:
            return [self.data[0]] if hasattr(self.data, "shape") else [self.data]
        return self.data.tolist()

    def dtype_code(self) -> int:
        from marple.backend_functions import data_type_code
        return data_type_code(self.data)

    @staticmethod
    def _first_axis_chunk_size(shape: list[int]) -> int:
        size = 1
        for s in shape[1:]:
            size *= s
        return size

    @staticmethod
    def _fill_element(source: APLArray) -> Any:
        from marple.backend_functions import char_fill
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
            arr = cls.reshape_ndarray(arr, shape)
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

    def replicate(self, other: APLArray) -> APLArray:
        from marple.errors import LengthError
        counts = [int(x) for x in self.to_list()]
        last_axis_len = other.shape[-1] if other.shape else 1
        if len(counts) == 1 and last_axis_len > 1:
            counts = counts * last_axis_len
        if len(counts) != last_axis_len:
            raise LengthError(f"Length mismatch: {len(counts)} vs {last_axis_len}")
        result = self.repeat_ndarray(other.data, counts, axis=-1)
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
        result = self.repeat_ndarray(other.data, counts, axis=0)
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
        rank = len(other.shape)
        if rank <= 1:
            src = list(other.data.flatten())
            out: list[Any] = []
            i = 0
            for m in mask:
                if m:
                    out.append(src[i])
                    i += 1
                else:
                    out.append(fill)
            return type(other)([len(mask)],
                               np.array(out, dtype=other.data.dtype))
        if rank != 2:
            raise NotImplementedError(
                "expand rank > 2 not supported on ulab")
        rows = other.shape[0]
        new_cols = len(mask)
        out_rows: list[list[Any]] = []
        for r in range(rows):
            src = list(other.data[r])
            row_out: list[Any] = []
            i = 0
            for m in mask:
                if m:
                    row_out.append(src[i])
                    i += 1
                else:
                    row_out.append(fill)
            out_rows.append(row_out)
        flat = [v for row in out_rows for v in row]
        data = np.array(flat, dtype=other.data.dtype)
        return type(other)([rows, new_cols],
                           self.reshape_ndarray(data, [rows, new_cols]))

    def reshape(self, other: APLArray) -> APLArray:
        from marple.backend_functions import char_fill, get_char_dtype
        if self.is_scalar():
            new_shape = [int(self.scalar_value())]
        else:
            new_shape = [int(x) for x in self.to_list()]
        total = 1
        for s in new_shape:
            total *= s
        flat = other.data.flatten()
        if len(flat) == 0:
            if other.data.dtype == get_char_dtype():
                flat = np.array([char_fill()], dtype=get_char_dtype())
            else:
                flat = np.array([0])
        n = len(flat)
        if total <= n:
            cycled = flat[:total]
        else:
            reps = total // n + 1
            cycled = np.concatenate(tuple([flat] * reps))[:total]
        return type(other)(new_shape, self.reshape_ndarray(cycled, new_shape))

    def transpose_dyadic(self, other: APLArray, io: int = 1) -> APLArray:
        # Needs np.indices + fancy indexing, neither available on ulab.
        raise NotImplementedError("transpose_dyadic not available on ulab")

    def matrix_inverse(self) -> APLArray:
        # ulab has no np.linalg; matrix inverse requires it.
        raise NotImplementedError("matrix_inverse not available on ulab")

    def matrix_divide(self, other: APLArray) -> APLArray:
        # ulab has no np.linalg; linear solve requires it.
        raise NotImplementedError("matrix_divide not available on ulab")

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
            a = self.reshape_ndarray(a, [1] * (b_rank - a_rank) + list(a.shape))
        elif b_rank < a_rank:
            b = self.reshape_ndarray(b, [1] * (a_rank - b_rank) + list(b.shape))
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
        """ulab has no fancy indexing beyond `data[i]` for first-axis;
        column slices on rank 2 go through a Python loop.
        """
        rank = len(self.shape)
        if axis < 0 or axis >= rank:
            raise ValueError(
                "axis {} out of range for rank-{} array".format(axis, rank))
        if axis == 0:
            sliced = self.data[index]
        elif rank == 2 and axis == 1:
            sliced = np.array(
                [row[index] for row in self.data], dtype=self.data.dtype)
        else:
            raise NotImplementedError(
                "slice_axis rank > 2 with axis > 0 not supported on ulab")
        new_shape = [s for i, s in enumerate(self.shape) if i != axis]
        return type(self)(new_shape, sliced)

    # --- ndarray-level structural hooks -------------------------------------
    # ulab's reshape rejects list shapes and multi-arg form; it has no
    # np.repeat and no np.ix_ / fancy indexing. Each method rebuilds via
    # Python iteration over ranks 1 and 2 (ulab's Pimoroni build caps at
    # rank 2). Higher ranks raise on this platform.

    @classmethod
    def reshape_ndarray(cls, arr: Any, shape: Any) -> Any:
        if isinstance(shape, int):
            return arr.reshape((shape,))
        if isinstance(shape, tuple):
            return arr.reshape(shape)
        return arr.reshape(tuple(shape))

    @classmethod
    def repeat_ndarray(cls, arr: Any, counts: Any, axis: int) -> Any:
        rank = len(arr.shape)
        axis_len = arr.shape[axis if axis >= 0 else rank + axis]
        if isinstance(counts, int):
            counts_list = [counts] * axis_len
        else:
            counts_list = [int(c) for c in counts]
            if len(counts_list) == 1 and axis_len > 1:
                counts_list = counts_list * axis_len
        if rank == 1:
            values = list(arr)
            out = [v for v, c in zip(values, counts_list) for _ in range(c)]
            return np.array(out, dtype=arr.dtype)
        if rank == 2:
            rows = [list(r) for r in arr]
            if axis in (-1, 1):
                new_rows = [
                    [v for v, c in zip(row, counts_list) for _ in range(c)]
                    for row in rows
                ]
            elif axis == 0:
                new_rows = [
                    list(row) for row, c in zip(rows, counts_list)
                    for _ in range(c)
                ]
            else:
                raise ValueError("axis {} out of range for rank 2".format(axis))
            return np.array(new_rows, dtype=arr.dtype)
        raise NotImplementedError(
            "repeat_ndarray supports rank \u2264 2 (got {})".format(rank))

    @classmethod
    def gather_ndarray(cls, data: Any, axis_indices: "list[list[int]]") -> Any:
        rank = len(data.shape)
        if rank != len(axis_indices):
            raise ValueError(
                "axis_indices count ({}) doesn't match data rank ({})"
                .format(len(axis_indices), rank))
        if rank == 1:
            idx = axis_indices[0]
            return np.array([data[int(i)] for i in idx], dtype=data.dtype)
        if rank == 2:
            row_idx, col_idx = axis_indices
            rows = [list(r) for r in data]
            out = [rows[int(r)][int(c)] for r in row_idx for c in col_idx]
            return np.array(out, dtype=data.dtype)
        raise NotImplementedError(
            "gather_ndarray supports rank \u2264 2 (got {})".format(rank))
