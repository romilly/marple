
from marple.ports.array import APLArray, str_to_char_array


def upper(right: APLArray) -> APLArray:
    return APLArray(list(right.shape), str_to_char_array(right.as_str().upper()))


def lower(right: APLArray) -> APLArray:
    return APLArray(list(right.shape), str_to_char_array(right.as_str().lower()))


def trim(right: APLArray) -> APLArray:
    trimmed = right.as_str().strip()
    return APLArray([len(trimmed)], str_to_char_array(trimmed))
