from typing import Any, TypeAlias

import numpy.typing as npt

from marple.get_numpy import np

NDArray: TypeAlias = npt.NDArray[Any]


def is_char_array(data: NDArray) -> bool:
    """Check if data represents character data (uint32 ndarray of codepoints)."""
    return str(data.dtype) == 'uint32'


def chars_to_str(data: npt.NDArray[np.uint32]) -> str:
    """Convert character array data (uint32 ndarray) to Python string."""
    return ''.join(chr(int(x)) for x in data.flat)


def str_to_char_array(s: str) -> npt.NDArray[np.uint32]:
    """Convert a Python string to a uint32 numpy array of codepoints."""
    return np.array([ord(c) for c in s], dtype=np.uint32)


def char_fill() -> np.uint32:
    """Return the fill element for character arrays: space as uint32."""
    return np.uint32(32)


def to_array(data: list[Any]) -> NDArray:
    """Convert a Python list to a numpy ndarray."""
    return np.array(data)


def _to_python(x: Any) -> Any:
    """Convert a numpy scalar to a native Python type."""
    if hasattr(x, "item"):
        return x.item()  # type: ignore[union-attr]
    return x


def to_list(data: Any) -> list[Any]:
    """Convert an ndarray or list to a Python list with native types.

    Always returns a Python list — including for 0-d numpy input,
    where `ndarray.tolist()` would otherwise return the bare scalar
    value rather than a 1-element list. Without this guard, every
    `for x in to_list(...)` consumer would break with a TypeError
    after the scalar storage convention migration.
    """
    if isinstance(data, list):
        # Only convert if list might contain numpy scalars
        if data and hasattr(data[0], "item"):
            return [_to_python(x) for x in data]
        return data
    if hasattr(data, "ndim") and data.ndim == 0:
        return [data.item()]
    return data.tolist()  # type: ignore[union-attr]


def is_numeric_array(data: NDArray) -> bool:
    """Check if data is a numeric ndarray from the active backend.

    uint32 arrays are reserved for character data (Unicode codepoints)
    and are NOT numeric — see is_char_array. The two predicates are
    disjoint, which is what allows the dyadic-arithmetic fast paths
    to use is_numeric_array as a safe gate after the char guards run.
    """
    return str(data.dtype) != 'uint32'


def _is_int_dtype(arr: NDArray) -> bool:
    """Check if an ndarray has an integer dtype."""
    dtype_str = str(arr.dtype)
    return "int" in dtype_str


def _is_float_dtype(arr: NDArray) -> bool:
    """Check if an ndarray has a float dtype."""
    dtype_str = str(arr.dtype)
    return "float" in dtype_str


def maybe_upcast(data: NDArray) -> NDArray:
    """Convert integer arrays to float to prevent overflow."""
    if not is_numeric_array(data):
        return data
    if not _is_int_dtype(data):
        return data
    return data.astype(np.float64)


# Module-level comparison tolerance for downcast
_DOWNCAST_CT: float = 1e-14


def maybe_downcast(data: NDArray, ct: float) -> NDArray:
    """Convert float arrays to int if all elements are close to whole numbers.

    Uses APL tolerance: |value - round(value)| <= ct * max(|value|, |round(value)|)
    """
    if not is_numeric_array(data):
        return data
    if _is_int_dtype(data):
        return data
    if not _is_float_dtype(data):
        return data
    if data.size == 0:
        return data
    # Non-finite values (inf, nan) can't be downcast
    if not np.all(np.isfinite(data)):
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


def data_type_code(data: NDArray) -> int:
    """Return the ⎕DR type code for the given data.

    Encoding: first digits = bit width, last digit = type
    (0=char, 1=boolean, 3=signed int, 5=float, 7=decimal, 9=complex).
    """
    if is_numeric_array(data):
        dtype_str = str(data.dtype)
        if "uint8" in dtype_str:
            return 81
        if "int8" in dtype_str and "int16" not in dtype_str and "int32" not in dtype_str and "int64" not in dtype_str:
            return 83
        if "int16" in dtype_str:
            return 163
        if "int32" in dtype_str:
            return 323
        if "int64" in dtype_str:
            return 643
        if _is_float_dtype(data):
            return 645
    if is_char_array(data):
        return 320
    return 323


def to_bool_array(data: Any) -> npt.NDArray[np.uint8]:
    """Convert data to a uint8 boolean array (0/1 values)."""
    dt = getattr(np, "uint8", None)
    if dt is None:
        return data
    if hasattr(data, "dtype"):
        return np.array(data.tolist(), dtype=dt)
    return np.array(data, dtype=dt)
