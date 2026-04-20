
from marple.numpy_array import APLArray
from marple.numpy_aplarray import NumpyAPLArray
from marple.backend_functions import chars_to_str, str_to_char_array


def upper(right: APLArray) -> APLArray:
    text = chars_to_str(right.data)
    # APLArray.__init__ handles reshape (including scalar storage on ulab
    # where shape=[] maps to (1,) not ()) so we pass flat data + APL shape.
    return NumpyAPLArray(list(right.shape), str_to_char_array(text.upper()))


def lower(right: APLArray) -> APLArray:
    text = chars_to_str(right.data)
    return NumpyAPLArray(list(right.shape), str_to_char_array(text.lower()))


def trim(right: APLArray) -> APLArray:
    text = chars_to_str(right.data)
    trimmed = text.strip()
    return NumpyAPLArray([len(trimmed)], str_to_char_array(trimmed))
