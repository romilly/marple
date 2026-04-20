
from marple.numpy_array import APLArray
from marple.numpy_aplarray import NumpyAPLArray
from marple.backend_functions import chars_to_str, np_reshape, str_to_char_array


def upper(right: APLArray) -> APLArray:
    text = chars_to_str(right.data)
    data = str_to_char_array(text.upper())
    return NumpyAPLArray(list(right.shape), np_reshape(data, right.shape))


def lower(right: APLArray) -> APLArray:
    text = chars_to_str(right.data)
    data = str_to_char_array(text.lower())
    return NumpyAPLArray(list(right.shape), np_reshape(data, right.shape))


def trim(right: APLArray) -> APLArray:
    text = chars_to_str(right.data)
    trimmed = text.strip()
    return NumpyAPLArray([len(trimmed)], str_to_char_array(trimmed))
