from __future__ import annotations

from marple.arraymodel import APLArray


def nread(right: APLArray) -> APLArray:
    """Read a text file. Right arg is a character vector (filepath).
    Returns a character vector."""
    path = "".join(str(c) for c in right.data)
    with open(path) as f:
        text = f.read()
    chars = list(text)
    return APLArray([len(chars)], chars) if chars else APLArray([0], [])


def nwrite(left: APLArray, right: APLArray) -> APLArray:
    """Write a character vector to a file.
    Left arg is the data (char vector), right arg is the filepath."""
    path = "".join(str(c) for c in right.data)
    text = "".join(str(c) for c in left.data)
    with open(path, "w") as f:
        f.write(text)
    return APLArray([0], [])
