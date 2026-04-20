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
    def char_dtype(cls) -> np.dtype[Any]:
        return np.dtype(np.uint16)

    @classmethod
    @contextmanager
    def strict_numeric_errstate(cls) -> Iterator[None]:
        yield

    @classmethod
    @contextmanager
    def ignoring_numeric_errstate(cls) -> Iterator[None]:
        yield

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
