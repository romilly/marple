from typing import Any, TYPE_CHECKING

import numpy as np
import numpy.typing as npt
NDArray = npt.NDArray[Any]

if TYPE_CHECKING:
    from marple.ports.array import APLArray
else:
    # MicroPython / ulab has no numpy.typing. Annotations collapse to Any at
    # runtime; pyright reads the TYPE_CHECKING branch.
    NDArray = Any




# TODO: The design of this module appears to fly in the face of the plan:
# we want (at least) two different backends, one for mainstream numpy, one for the pico2.
# def set_char_dtype(dtype: np.dtype[Any]) -> None:
#     """Select the dtype used for character data.

#     The active dtype is process-global — platforms select it once at startup
#     (NumpyAPLArray: uint32; UlabAPLArray: uint16). Callers should save and
#     restore the previous value if they need to temporarily switch, e.g. in
#     tests.
#     """

def get_char_dtype():
    """Return the currently active char dtype.
    """
    return np.uint32


def get_backend_class() -> "type[APLArray]":
    """Return the currently active APLArray subclass (defaults to NumpyAPLArray)."""
    global _ACTIVE_BACKEND_CLASS
   # if _ACTIVE_BACKEND_CLASS is None:
    from marple.numpy_aplarray import NumpyAPLArray
    return NumpyAPLArray
    #return _ACTIVE_BACKEND_CLASS



def char_fill() -> Any:
    """Return the fill element for character arrays: the space codepoint.

    Returns a plain int; callers pass it to `np.array([char_fill()],
    dtype=get_char_dtype())` which produces a typed scalar. ulab's
    `np.uint16` is not callable (it's an int constant), so the old
    `CHAR_DTYPE(32)` path that worked on CPython fails there — this
    neutral form works on both.
    """
    return 32

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


def numeric_upcast_dtype() -> Any:
    """Widest float dtype the active backend supports. Delegates to the
    backend class's classmethod — see APLArray.numeric_upcast_dtype.
    """
    return get_backend_class().numeric_upcast_dtype()


def maybe_downcast(data: NDArray, ct: float) -> NDArray:
    """Convert float arrays to int if all elements are close to whole numbers.

    Delegates to the active backend class so UlabAPLArray can return data
    unchanged — ulab lacks np.iinfo / np.int64 / np.int32 entirely and its
    int widths are already narrow.
    """
    return get_backend_class().maybe_downcast(data, ct)


DR_CODE_SPECS: "dict[str, int]" = {
    "uint8": 81,
    "int8": 83,
    "int16": 163,
    "uint32": 320,
    "int32": 323,
    "int64": 643,
    "float32": 325,
    "float64": 645,
}


def data_type_code(data: NDArray) -> int:
    """Return the ⎕DR type code for the given data.

    Encoding: first digits = bit width, last digit = type
    (0=char, 1=boolean, 3=signed int, 5=float, 7=decimal, 9=complex).
    """
    return DR_CODE_SPECS[data.dtype.name]


def to_bool_array(data: "NDArray | list[int]") -> NDArray:
    """Convert data to a uint8 boolean array (0/1 values)."""
    return np.asarray(data, dtype=np.uint8)
