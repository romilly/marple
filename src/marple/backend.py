
import os
try:
    from typing import Any
except ImportError:
    pass

# Backend selection: environment variable overrides auto-detection
try:
    _backend_name = os.environ.get("MARPLE_BACKEND", "auto")
except AttributeError:
    _backend_name = "auto"  # MicroPython has no os.environ

np: Any = None

if _backend_name != "none":
    try:
        import cupy as np  # type: ignore[no-redef]
    except ImportError:
        try:
            import numpy as np  # type: ignore[no-redef]
        except ImportError:
            try:
                import ulab.numpy as np  # type: ignore[no-redef,import-not-found]
            except ImportError:
                try:
                    from ulab import numpy as np  # type: ignore[no-redef,import-not-found]
                except ImportError:
                    np = None

HAS_BACKEND: bool = np is not None

# Module-level comparison tolerance for downcast (updated by interpreter when ⎕CT changes)
_DOWNCAST_CT: float = 1e-14

# Ufunc names that can overflow integer arithmetic
_OVERFLOW_UFUNCS: set[str] = {"add", "subtract", "multiply", "power"}


def to_array(data: list[Any]) -> Any:
    """Convert a Python list to an ndarray if numeric and backend is available."""
    if not HAS_BACKEND or len(data) == 0:
        return data
    if not all(isinstance(x, (int, float)) for x in data):
        return data
    # Preserve integer type: ulab defaults to float, so specify dtype explicitly
    if all(isinstance(x, int) for x in data):
        for dtype_name in ("int32", "int16"):
            dt = getattr(np, dtype_name, None)
            if dt is not None:
                try:
                    arr = np.array(data, dtype=dt)
                except (ValueError, OverflowError):
                    continue
                # Verify no silent overflow (numpy/ulab wrap without error)
                if arr.tolist() == data:
                    return arr
    return np.array(data)


def _to_python(x: Any) -> Any:
    """Convert a numpy scalar to a native Python type."""
    if hasattr(x, "item"):
        return x.item()  # type: ignore[union-attr]
    return x


def to_list(data: Any) -> list[Any]:
    """Convert an ndarray or list to a Python list with native types."""
    if isinstance(data, list):
        # Only convert if list might contain numpy scalars
        if data and hasattr(data[0], "item"):
            return [_to_python(x) for x in data]
        return data
    return data.tolist()  # type: ignore[union-attr]


def is_numeric_array(data: Any) -> bool:
    """Check if data is an ndarray from the active backend."""
    if not HAS_BACKEND:
        return False
    return hasattr(data, "dtype")


def to_bool_array(data: Any) -> Any:
    """Convert data to a uint8 boolean array (0/1 values).

    If no backend, returns the data unchanged.
    """
    if not HAS_BACKEND:
        return data
    dt = getattr(np, "uint8", None)
    if dt is None:
        return data
    if hasattr(data, "dtype"):
        return np.array(data.tolist(), dtype=dt)
    return np.array(data, dtype=dt)


def _is_int_dtype(arr: Any) -> bool:
    """Check if an ndarray has an integer dtype."""
    dtype_str = str(arr.dtype)
    return "int" in dtype_str


def _is_float_dtype(arr: Any) -> bool:
    """Check if an ndarray has a float dtype."""
    dtype_str = str(arr.dtype)
    return "float" in dtype_str


def maybe_upcast(data: Any) -> Any:
    """Convert integer arrays to float to prevent overflow.

    Returns non-array data unchanged.
    """
    if not is_numeric_array(data):
        return data
    if not _is_int_dtype(data):
        return data
    return data.astype(np.float64)


def maybe_downcast_scalar(value: Any, ct: float) -> Any:
    """Downcast a single float value to int if close to a whole number."""
    if not isinstance(value, float):
        return value
    r = round(value)
    diff = abs(value - r)
    mag = max(abs(value), abs(r))
    if ct == 0:
        if diff == 0:
            return r
    elif mag == 0 or diff <= ct * mag:
        return r
    return value


def maybe_downcast(data: Any, ct: float) -> Any:
    """Convert float arrays to int if all elements are close to whole numbers.

    Uses APL tolerance: |value - round(value)| <= ct * max(|value|, |round(value)|)
    Returns non-array or already-integer data unchanged.
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
    # All close to integers — use int32 if values fit, else int64
    int_arr = rounded.astype(np.int64)
    if np.all(np.abs(int_arr) <= np.iinfo(np.int32).max):
        return int_arr.astype(np.int32)
    return int_arr
