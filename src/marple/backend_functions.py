from typing import Any, TYPE_CHECKING

import numpy as np
import numpy.typing as npt
NDArray = npt.NDArray[Any]

if TYPE_CHECKING:
    from marple.ports.array import APLArray


# TODO: The design of this module appears to fly in the face of the plan:
# we want (at least) two different backends, one for mainstream numpy, one for the pico2.
# def set_char_dtype(dtype: np.dtype[Any]) -> None:
#     """Select the dtype used for character data.

#     The active dtype is process-global — platforms select it once at startup
#     (NumpyAPLArray: uint32; UlabAPLArray: uint16). Callers should save and
#     restore the previous value if they need to temporarily switch, e.g. in
#     tests.
#     """


def get_backend_class() -> "type[APLArray]":
    """Return the currently active APLArray subclass (defaults to NumpyAPLArray)."""
    global _ACTIVE_BACKEND_CLASS
   # if _ACTIVE_BACKEND_CLASS is None:
    from marple.numpy_aplarray import NumpyAPLArray
    return NumpyAPLArray
    #return _ACTIVE_BACKEND_CLASS


# Module-level comparison tolerance for downcast
_DOWNCAST_CT: float = 1e-14



def maybe_downcast(data: NDArray, ct: float) -> NDArray:
    """Convert float arrays to int if all elements are close to whole numbers.

    Delegates to the active backend class so UlabAPLArray can return data
    unchanged — ulab lacks np.iinfo / np.int64 / np.int32 entirely and its
    int widths are already narrow.
    """
    return get_backend_class().maybe_downcast(data, ct)


def to_bool_array(data: "NDArray | list[int]") -> NDArray:
    """Convert data to a uint8 boolean array (0/1 values)."""
    return np.asarray(data, dtype=np.uint8)
