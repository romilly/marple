
from marple.numpy_array import APLArray
from marple.backend_functions import chars_to_str


def upper(right: APLArray) -> APLArray:
    text = chars_to_str(right.data)
    return APLArray.array(list(right.shape), list(text.upper()))


def lower(right: APLArray) -> APLArray:
    text = chars_to_str(right.data)
    return APLArray.array(list(right.shape), list(text.lower()))


def trim(right: APLArray) -> APLArray:
    text = chars_to_str(right.data)
    trimmed = text.strip()
    return APLArray.array([len(trimmed)], list(trimmed))
