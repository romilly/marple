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

 


def np_repeat(arr: Any, counts: Any, axis: int) -> Any:
    """Platform-agnostic ndarray.repeat along a single axis.

    Delegates to `np.repeat` when available (CPython numpy). On ulab
    (no np.repeat, no fancy indexing, no `.astype`) rebuilds the result
    via Python-list iteration for rank 1 and rank 2 — the shapes marple
    actually hits.

    `counts` is a sequence of ints (one per element along `axis`) or a
    scalar (applied to every element) — both forms match np.repeat.
    """
    if hasattr(np, "repeat"):
        return np.repeat(arr, counts, axis=axis)
    rank = len(arr.shape)
    axis_len = arr.shape[axis if axis >= 0 else rank + axis]
    if isinstance(counts, int):
        counts_list = [counts] * axis_len
    else:
        counts_list = [int(c) for c in counts]
        if len(counts_list) == 1 and axis_len > 1:
            counts_list = counts_list * axis_len
    if rank == 1:
        values = list(arr)
        out = [v for v, c in zip(values, counts_list) for _ in range(c)]
        return np.array(out, dtype=arr.dtype)
    if rank == 2:
        rows = [list(r) for r in arr]
        if axis in (-1, 1):
            new_rows = [
                [v for v, c in zip(row, counts_list) for _ in range(c)]
                for row in rows
            ]
        elif axis == 0:
            new_rows = [
                list(row) for row, c in zip(rows, counts_list)
                for _ in range(c)
            ]
        else:
            raise ValueError("axis {} out of range for rank 2".format(axis))
        return np.array(new_rows, dtype=arr.dtype)
    raise NotImplementedError(
        "np_repeat fallback supports rank \u2264 2 (got {})".format(rank))


def np_reshape(arr: Any, *shape: Any) -> Any:
    """Platform-agnostic ndarray.reshape.

    ulab's reshape rejects list shapes (`TypeError: shape must be integer
    or tuple of integers`) and rejects the multi-arg form
    (`.reshape(2, 3)` raises "takes 2 positional arguments"). CPython
    numpy accepts all three. This helper accepts any of:
      - single int:      np_reshape(arr, 5)
      - single list:     np_reshape(arr, [2, 3])
      - single tuple:    np_reshape(arr, (2, 3))
      - multi-arg ints:  np_reshape(arr, 2, 3)
    and always passes a tuple to the underlying .reshape.

    Pattern from pre-drop commit f49195e~ which re-adopts here.
    """
    if len(shape) == 1:
        s = shape[0]
        if isinstance(s, int):
            return arr.reshape((s,))
        if isinstance(s, tuple):
            return arr.reshape(s)
        return arr.reshape(tuple(s))
    return arr.reshape(tuple(shape))



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


_DR_CODES_CACHE: "dict[Any, int] | None" = None

_DR_CODE_SPECS: "list[tuple[str, int]]" = [
    ("uint8", 81),
    ("int8", 83),
    ("int16", 163),
    ("unit32", 320),
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
