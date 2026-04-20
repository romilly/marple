"""UlabAPLArray — APLArray subclass for MicroPython + ulab on the Pico.

Walking-skeleton desk sketch. The class parses and loads on CPython
(where `from marple.get_numpy import np` resolves to real numpy); it is
only *exercised* on hardware, where get_numpy.py is wired to return
`ulab.numpy`.

Overrides three families of hook so the Pico path works without numpy:

1. `char_dtype()` → uint16. ulab caps integer types at 16 bits, so the
   BMP codepoints are stored as uint16 rather than uint32.

2. `strict_numeric_errstate` / `ignoring_numeric_errstate` → no-ops.
   ulab has no equivalent of `np.errstate`; integer arithmetic wraps
   silently and there is no FloatingPointError. The Pico accepts this
   limitation — the alternative (wrap every op with bounds checks) is
   too expensive for a 133 MHz device.

3. `_numeric_dyadic_op` → a trimmed version without `maybe_upcast` or
   try/except FloatingPointError. ulab has no float64, so promotion
   would fail; and without errstate the exception can never fire.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Callable, Iterator

from marple.errors import LengthError
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

        ulab has no `np.round`, no `.astype`, and no `np.iinfo`; each step
        is rebuilt with Python-list primitives. ulab's widest signed int
        on the Pimoroni rp2 build is int16 (±32767), so we keep the float
        result when values overflow that range — wider than staying float
        on desktop would allow, but this is the honest ulab bound.
        """
        if not cls.is_float_dtype(data):
            return data
        if data.size == 0:
            return data
        values = list(data)
        if not all(_isfinite(x) for x in values):
            return data
        rounded = [_round_half_even(x) for x in values]
        if ct == 0:
            for x, r in zip(values, rounded):
                if x != r:
                    return data
        else:
            for x, r in zip(values, rounded):
                mag = max(abs(x), abs(r))
                if abs(x - r) > ct * mag:
                    return data
        INT16_MAX = 32767
        if any(abs(r) > INT16_MAX for r in rounded):
            return data
        return np.array(rounded, dtype=np.int16)


def _isfinite(x: float) -> bool:
    """ulab has np.isfinite but for a scalar we avoid constructing an array."""
    # NaN never equals itself; inf compares False against a finite bound.
    return x == x and x != float("inf") and x != float("-inf")


def _round_half_even(x: float) -> int:
    """Banker's rounding — matches Python's built-in `round()` for floats."""
    return int(round(x))

    def _numeric_dyadic_op(
        self,
        other: APLArray,
        op: Callable[[Any, Any], Any],
        upcast: bool = False,
    ) -> APLArray:
        try:
            result = op(self.data, other.data)
        except ValueError:
            raise LengthError(f"Shape mismatch: {self.shape} vs {other.shape}")
        if not isinstance(result, np.ndarray):
            result = np.asarray(result)
        shape = list(other.shape) if not other.is_scalar() else list(self.shape)
        return type(self).array(shape, result)
