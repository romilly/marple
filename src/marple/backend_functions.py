from typing import Any, TypeAlias

import numpy.typing as npt

from marple.get_numpy import np

NDArray: TypeAlias = npt.NDArray[Any]


_CHAR_DTYPE: np.dtype[Any] = np.dtype(np.uint32)


def set_char_dtype(dtype: np.dtype[Any]) -> None:
    """Select the dtype used for character data.

    The active dtype is process-global — platforms select it once at startup
    (NumpyAPLArray: uint32; UlabAPLArray: uint16). Callers should save and
    restore the previous value if they need to temporarily switch, e.g. in
    tests.
    """
    global _CHAR_DTYPE
    _CHAR_DTYPE = dtype


def get_char_dtype() -> np.dtype[Any]:
    """Return the currently active char dtype."""
    return _CHAR_DTYPE


def is_char_array(data: NDArray) -> bool:
    """Check if data represents character data (ndarray of codepoints)."""
    return data.dtype == _CHAR_DTYPE


def chars_to_str(data: NDArray) -> str:
    """Convert character array data to a Python string."""
    return ''.join(chr(int(x)) for x in data.flat)


def str_to_char_array(s: str) -> NDArray:
    """Convert a Python string to a numpy array of codepoints."""
    return np.array([ord(c) for c in s], dtype=_CHAR_DTYPE)


def char_fill() -> Any:
    """Return the fill element for character arrays: space codepoint."""
    return _CHAR_DTYPE.type(32)


def to_array(data: list[Any]) -> NDArray:
    """Convert a Python list to a numpy ndarray."""
    return np.array(data)


def to_list(data: NDArray) -> list[Any]:
    """Convert an ndarray to a Python list with native types.

    For 0-d numpy input, returns a 1-element list rather than a bare
    scalar, so `for x in to_list(...)` always works.
    """
    if data.ndim == 0:
        return [data.item()]
    return data.tolist()


def is_numeric_array(data: NDArray) -> bool:
    """Check if data is a numeric ndarray from the active backend.

    uint32 arrays are reserved for character data (Unicode codepoints)
    and are NOT numeric — see is_char_array. The two predicates are
    disjoint, which is what allows the dyadic-arithmetic fast paths
    to use is_numeric_array as a safe gate after the char guards run.
    """
    return data.dtype != _CHAR_DTYPE


def is_int_dtype(arr: NDArray) -> bool:
    """Check if an ndarray has an integer dtype."""
    return np.issubdtype(arr.dtype, np.integer)


def is_float_dtype(arr: NDArray) -> bool:
    """Check if an ndarray has a float dtype."""
    return np.issubdtype(arr.dtype, np.floating)


def maybe_upcast(data: NDArray) -> NDArray:
    """Convert integer arrays to float to prevent overflow."""
    if not is_numeric_array(data) or not is_int_dtype(data):
        return data
    return data.astype(np.float64)


# Module-level comparison tolerance for downcast
_DOWNCAST_CT: float = 1e-14


# TODO: narrow further like Dyalog — int64 → int32 → int8/uint8 by value range,
# producing bool/uint8 when all values are 0 or 1. See git history for context.
def maybe_downcast(data: NDArray, ct: float) -> NDArray:
    """Convert float arrays to int if all elements are close to whole numbers.

    Uses APL tolerance: |value - round(value)| <= ct * max(|value|, |round(value)|)
    """
    if not is_float_dtype(data):
        return data
    if data.size == 0:
        return data
    # Vectorised check: are all values close to whole numbers?
    rounded = np.round(data)
    diff = np.abs(data - rounded)
    if ct == 0:
        if not np.all(diff == 0):
            return data
    else:
        mag = np.maximum(np.abs(data), np.abs(rounded))
        if not np.all(diff <= ct * mag):
            return data
    # All close to integers — downcast only if values fit in int range
    max_val = np.max(np.abs(rounded))
    if max_val > np.float64(np.iinfo(np.int64).max):
        return data
    int_arr = rounded.astype(np.int64)
    if np.all(np.abs(int_arr) <= np.iinfo(np.int32).max):
        return int_arr.astype(np.int32)
    return int_arr


_DR_CODES: dict[np.dtype[Any], int] = {
    np.dtype(np.uint8): 81,
    np.dtype(np.int8): 83,
    np.dtype(np.int16): 163,
    np.dtype(np.int32): 323,
    np.dtype(np.int64): 643,
    np.dtype(np.float32): 325,
    np.dtype(np.float64): 645,
    np.dtype(np.uint32): 320,  # character
}


def data_type_code(data: NDArray) -> int:
    """Return the ⎕DR type code for the given data.

    Encoding: first digits = bit width, last digit = type
    (0=char, 1=boolean, 3=signed int, 5=float, 7=decimal, 9=complex).
    """
    return _DR_CODES.get(data.dtype, 323)


def to_bool_array(data: NDArray | list[int]) -> npt.NDArray[np.uint8]:
    """Convert data to a uint8 boolean array (0/1 values)."""
    return np.asarray(data, dtype=np.uint8)
