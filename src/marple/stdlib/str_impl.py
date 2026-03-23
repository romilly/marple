
from marple.arraymodel import APLArray


def upper(right: APLArray) -> APLArray:
    chars = [c.upper() if isinstance(c, str) else c for c in right.data]
    return APLArray(list(right.shape), chars)


def lower(right: APLArray) -> APLArray:
    chars = [c.lower() if isinstance(c, str) else c for c in right.data]
    return APLArray(list(right.shape), chars)


def trim(right: APLArray) -> APLArray:
    text = "".join(str(c) for c in right.data)
    trimmed = text.strip()
    return APLArray([len(trimmed)], list(trimmed))
