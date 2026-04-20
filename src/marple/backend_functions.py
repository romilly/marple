import sys
from contextlib import AbstractContextManager
from typing import Any, TYPE_CHECKING

from marple.get_numpy import np

# ulab has no 0-dimensional arrays: np.asarray(7) returns the bare int,
# and reshape(()) silently produces an empty 1-d array rather than a
# rank-0 scalar (verified on-device via mpremote). On MicroPython we
# therefore store APL scalars as 1-d length-1 ndarrays while keeping
# the APL shape []. Non-scalar shapes are identical on both platforms.
# Pattern taken from pre-drop commit 03e7c89.
if sys.implementation.name == "micropython":
    SCALAR_STORAGE_SHAPE: tuple[int, ...] = (1,)
else:
    SCALAR_STORAGE_SHAPE = ()

if TYPE_CHECKING:
    import numpy.typing as npt
    from marple.numpy_array import APLArray
    NDArray = npt.NDArray[Any]
else:
    # MicroPython / ulab has no numpy.typing. Annotations collapse to Any at
    # runtime; pyright reads the TYPE_CHECKING branch.
    NDArray = Any


# Lazily resolved via `get_char_dtype` — avoids a module-load-time call to
# `np.dtype(np.uint32)`, which fails on ulab builds that cap at uint16.
_CHAR_DTYPE: "np.dtype[Any] | None" = None

# Active APLArray subclass — consulted by the module-level errstate helpers
# so that a UlabAPLArray on the Pico can override overflow trapping without
# the callers needing an instance reference. Interpreter sets this on
# construction via `set_backend_class`.
_ACTIVE_BACKEND_CLASS: "type[APLArray] | None" = None


def set_char_dtype(dtype: np.dtype[Any]) -> None:
    """Select the dtype used for character data.

    The active dtype is process-global — platforms select it once at startup
    (NumpyAPLArray: uint32; UlabAPLArray: uint16). Callers should save and
    restore the previous value if they need to temporarily switch, e.g. in
    tests.
    """
    global _CHAR_DTYPE
    _CHAR_DTYPE = dtype


def get_char_dtype() -> "np.dtype[Any]":
    """Return the currently active char dtype.

    First call resolves the default via the active backend class, which
    means a Pico that registers UlabAPLArray before the first character
    array is constructed gets uint16 rather than the numpy-default uint32
    (which ulab cannot represent).
    """
    global _CHAR_DTYPE
    if _CHAR_DTYPE is None:
        _CHAR_DTYPE = get_backend_class().char_dtype()
    return _CHAR_DTYPE


def set_backend_class(cls: "type[APLArray]") -> None:
    """Select the active APLArray subclass for module-level errstate helpers.

    Interpreter calls this at construction so that `strict_numeric_errstate`
    and `ignoring_numeric_errstate` below dispatch to the subclass's hooks
    (e.g. UlabAPLArray's no-op context managers).
    """
    global _ACTIVE_BACKEND_CLASS
    _ACTIVE_BACKEND_CLASS = cls


def get_backend_class() -> "type[APLArray]":
    """Return the currently active APLArray subclass (defaults to NumpyAPLArray)."""
    global _ACTIVE_BACKEND_CLASS
    if _ACTIVE_BACKEND_CLASS is None:
        from marple.numpy_aplarray import NumpyAPLArray
        _ACTIVE_BACKEND_CLASS = NumpyAPLArray
    return _ACTIVE_BACKEND_CLASS


def strict_numeric_errstate() -> AbstractContextManager[None]:
    """Context manager for numeric ops that must trap overflow.

    Dispatches to the active backend class's `strict_numeric_errstate` hook.
    """
    return get_backend_class().strict_numeric_errstate()


def ignoring_numeric_errstate() -> AbstractContextManager[None]:
    """Context manager for numeric ops that suppress overflow warnings.

    Dispatches to the active backend class's `ignoring_numeric_errstate` hook.
    """
    return get_backend_class().ignoring_numeric_errstate()


def is_char_array(data: NDArray) -> bool:
    """Check if data represents character data (ndarray of codepoints)."""
    return data.dtype == get_char_dtype()


def chars_to_str(data: NDArray) -> str:
    """Convert character array data to a Python string."""
    return ''.join(chr(int(x)) for x in data.flat)


def str_to_char_array(s: str) -> NDArray:
    """Convert a Python string to a numpy array of codepoints."""
    return np.array([ord(c) for c in s], dtype=get_char_dtype())


def char_fill() -> Any:
    """Return the fill element for character arrays: the space codepoint.

    Returns a plain int; callers pass it to `np.array([char_fill()],
    dtype=get_char_dtype())` which produces a typed scalar. ulab's
    `np.uint16` is not callable (it's an int constant), so the old
    `CHAR_DTYPE(32)` path that worked on CPython fails there — this
    neutral form works on both.
    """
    return 32


def to_array(data: list[Any]) -> NDArray:
    """Convert a Python list to a numpy ndarray."""
    return np.array(data)


def to_list(data: NDArray) -> list[Any]:
    """Convert an ndarray to a Python list with native types.

    For 0-d numpy input, returns a 1-element list rather than a bare
    scalar, so `for x in to_list(...)` always works.
    """
    if data.ndim == 0:
        return [scalar_item(data)]
    return data.tolist()


def is_numeric_array(data: NDArray) -> bool:
    """Check if data is a numeric ndarray from the active backend.

    Char-dtype arrays are reserved for character data (Unicode codepoints)
    and are NOT numeric — see is_char_array. The two predicates are
    disjoint, which is what allows the dyadic-arithmetic fast paths
    to use is_numeric_array as a safe gate after the char guards run.
    """
    return data.dtype != get_char_dtype()


def scalar_item(x: Any) -> Any:
    """Extract a native Python value from a scalar-like input.

    Handles every flavour of "single value" MARPLE passes around:
      - Python int / float / str — returned unchanged
      - desktop numpy ndarray (0-d or 1-d length-1) — via `.item()`
      - numpy scalar object (np.float64 etc.) — via `.item()`
      - ulab ndarray (1-d length-1) — via `data[0]`, because ulab's
        ndarray has no `.item()` method (verified on-device)

    Platform-agnostic replacement for bare `.item()` on APL scalar
    storage. Pattern taken from pre-drop commit 4e441e0.
    """
    if hasattr(x, "item"):
        return x.item()
    if hasattr(x, "shape"):
        return x[0]
    return x


def is_int_dtype(arr: NDArray) -> bool:
    """Check if an ndarray has an integer dtype.

    Delegates to the active backend class — ulab subclass uses a dtype-
    constant set check since ulab has no `np.issubdtype`.
    """
    return get_backend_class().is_int_dtype(arr)


def is_float_dtype(arr: NDArray) -> bool:
    """Check if an ndarray has a float dtype. Delegates per is_int_dtype."""
    return get_backend_class().is_float_dtype(arr)


def maybe_upcast(data: NDArray) -> NDArray:
    """Convert integer arrays to float to prevent overflow.

    Delegates to the active backend class so UlabAPLArray can skip the
    float64 upcast (ulab has no float64; silent int overflow is accepted).
    """
    return get_backend_class().maybe_upcast(data)


# Module-level comparison tolerance for downcast
_DOWNCAST_CT: float = 1e-14


def maybe_downcast(data: NDArray, ct: float) -> NDArray:
    """Convert float arrays to int if all elements are close to whole numbers.

    Delegates to the active backend class so UlabAPLArray can return data
    unchanged — ulab lacks np.iinfo / np.int64 / np.int32 entirely and its
    int widths are already narrow.
    """
    return get_backend_class().maybe_downcast(data, ct)


_DR_CODES_CACHE: "dict[Any, int] | None" = None

_DR_CODE_SPECS: "list[tuple[str, int]]" = [
    ("uint8", 81),
    ("int8", 83),
    ("int16", 163),
    ("int32", 323),
    ("int64", 643),
    ("float32", 325),
    ("float64", 645),
]


def _build_dr_codes() -> "dict[Any, int]":
    codes: "dict[Any, int]" = {}
    has_dtype_factory = hasattr(np, "dtype")

    def _key(dtype: Any) -> Any:
        # Normalise keys so `codes.get(arr.dtype)` hits: numpy compares
        # np.dtype('uint32') to np.dtype('uint32'), not to the bare
        # np.uint32 type. ulab has no np.dtype factory — bare dtype
        # values there already match `arr.dtype` which is an int.
        if has_dtype_factory:
            try:
                return np.dtype(dtype)
            except (TypeError, ValueError):
                return dtype
        return dtype

    for name, code in _DR_CODE_SPECS:
        dtype = getattr(np, name, None)
        if dtype is None:
            continue
        codes[_key(dtype)] = code
    codes[_key(get_char_dtype())] = 320  # character
    return codes


def data_type_code(data: NDArray) -> int:
    """Return the ⎕DR type code for the given data.

    Encoding: first digits = bit width, last digit = type
    (0=char, 1=boolean, 3=signed int, 5=float, 7=decimal, 9=complex).

    The code table is built lazily on first call so that module load on
    ulab (which lacks e.g. int64) doesn't fail before the Pico eval loop
    has even started.
    """
    global _DR_CODES_CACHE
    if _DR_CODES_CACHE is None:
        _DR_CODES_CACHE = _build_dr_codes()
    return _DR_CODES_CACHE.get(data.dtype, 323)


def to_bool_array(data: "NDArray | list[int]") -> NDArray:
    """Convert data to a uint8 boolean array (0/1 values)."""
    return np.asarray(data, dtype=np.uint8)
