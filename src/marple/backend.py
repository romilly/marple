
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


def to_array(data: list[Any]) -> Any:
    """Convert a Python list to an ndarray if numeric and backend is available."""
    if not HAS_BACKEND or len(data) == 0:
        return data
    if not all(isinstance(x, (int, float)) for x in data):
        return data
    return np.array(data)


def to_list(data: Any) -> list[Any]:
    """Convert an ndarray to a Python list. Pass lists through unchanged."""
    if isinstance(data, list):
        return data
    return data.tolist()  # type: ignore[union-attr]


def is_numeric_array(data: Any) -> bool:
    """Check if data is an ndarray from the active backend."""
    if not HAS_BACKEND:
        return False
    return hasattr(data, "dtype")
