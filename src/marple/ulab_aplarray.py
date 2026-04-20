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
from marple.numpy_array import APLArray


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
