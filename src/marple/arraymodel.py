"""APLArray re-export for backward compatibility."""

"""APLArray re-export for backward compatibility."""

try:
    from typing import Any
except ImportError:
    pass

from marple.numpy_array import APLArray  # noqa: F401

NumpyArray = APLArray  # backward compat alias


def S(value: Any) -> APLArray:
    return APLArray.scalar(value)
