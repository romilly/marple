from __future__ import annotations

from marple.arraymodel import APLArray, S


# Monadic structural functions

def shape(omega: APLArray) -> APLArray:
    return APLArray([len(omega.shape)], list(omega.shape))


def iota(omega: APLArray) -> APLArray:
    if not omega.is_scalar():
        raise ValueError("Monadic ⍳ requires a scalar argument")
    n = int(omega.data[0])
    return APLArray([n], list(range(1, n + 1)))


def ravel(omega: APLArray) -> APLArray:
    return APLArray([len(omega.data)], list(omega.data))


def reverse(omega: APLArray) -> APLArray:
    return APLArray(list(omega.shape), list(reversed(omega.data)))


# Dyadic structural functions

def reshape(alpha: APLArray, omega: APLArray) -> APLArray:
    if alpha.is_scalar():
        new_shape = [int(alpha.data[0])]
    else:
        new_shape = [int(x) for x in alpha.data]
    total = 1
    for s in new_shape:
        total *= s
    data = list(omega.data)
    if len(data) == 0:
        raise ValueError("Cannot reshape empty array")
    # Cycle data to fill
    result: list[object] = []
    for i in range(total):
        result.append(data[i % len(data)])
    return APLArray(new_shape, result)


def index_of(alpha: APLArray, omega: APLArray) -> APLArray:
    if omega.is_scalar():
        target = omega.data[0]
        for i, val in enumerate(alpha.data):
            if val == target:
                return S(i + 1)  # APL index origin 1
        return S(len(alpha.data) + 1)  # not found
    targets = omega.data
    results = []
    for target in targets:
        found = False
        for i, val in enumerate(alpha.data):
            if val == target:
                results.append(i + 1)
                found = True
                break
        if not found:
            results.append(len(alpha.data) + 1)
    return APLArray(list(omega.shape), results)


def catenate(alpha: APLArray, omega: APLArray) -> APLArray:
    left = list(alpha.data) if not alpha.is_scalar() else [alpha.data[0]]
    right = list(omega.data) if not omega.is_scalar() else [omega.data[0]]
    return APLArray([len(left) + len(right)], left + right)


def take(alpha: APLArray, omega: APLArray) -> APLArray:
    n = int(alpha.data[0])
    data = list(omega.data)
    if n >= 0:
        result = data[:n]
    else:
        result = data[n:]
    return APLArray([abs(n)], result)


def drop(alpha: APLArray, omega: APLArray) -> APLArray:
    n = int(alpha.data[0])
    data = list(omega.data)
    if n >= 0:
        result = data[n:]
    else:
        result = data[:n]
    return APLArray([len(result)], result)


def rotate(alpha: APLArray, omega: APLArray) -> APLArray:
    n = int(alpha.data[0])
    data = list(omega.data)
    length = len(data)
    if length == 0:
        return APLArray(list(omega.shape), [])
    n = n % length
    result = data[n:] + data[:n]
    return APLArray(list(omega.shape), result)


def transpose(omega: APLArray) -> APLArray:
    if len(omega.shape) <= 1:
        return APLArray(list(omega.shape), list(omega.data))
    if len(omega.shape) != 2:
        raise ValueError("Transpose currently supports only rank-2 arrays")
    rows, cols = omega.shape
    new_data: list[object] = []
    for c in range(cols):
        for r in range(rows):
            new_data.append(omega.data[r * cols + c])
    return APLArray([cols, rows], new_data)


def grade_up(omega: APLArray) -> APLArray:
    # Return 1-based indices that would sort the array ascending
    indexed = list(enumerate(omega.data))
    indexed.sort(key=lambda pair: pair[1])  # type: ignore[arg-type]
    return APLArray([len(omega.data)], [i + 1 for i, _ in indexed])


def grade_down(omega: APLArray) -> APLArray:
    indexed = list(enumerate(omega.data))
    indexed.sort(key=lambda pair: pair[1], reverse=True)  # type: ignore[arg-type]
    return APLArray([len(omega.data)], [i + 1 for i, _ in indexed])


def encode(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic ⊤: represent omega in the radix system given by alpha."""
    if not omega.is_scalar():
        raise ValueError("Encode currently supports only scalar right argument")
    radices = list(alpha.data)
    n = int(omega.data[0])
    result: list[object] = []
    for _ in range(len(radices)):
        result.append(0)
    for i in range(len(radices) - 1, -1, -1):
        r = int(radices[i])
        if r == 0:
            result[i] = n
            n = 0
        else:
            result[i] = n % r
            n = n // r
    return APLArray([len(radices)], result)


def decode(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic ⊥: evaluate omega as a polynomial with bases from alpha."""
    values = list(omega.data)
    if alpha.is_scalar():
        base = alpha.data[0]
        result = 0
        for v in values:
            result = result * int(base) + int(v)  # type: ignore[arg-type]
        return S(result)
    bases = list(alpha.data)
    if len(bases) != len(values):
        raise ValueError(f"Length mismatch: {len(bases)} bases vs {len(values)} values")
    result = 0
    for b, v in zip(bases, values):
        result = result * int(b) + int(v)  # type: ignore[arg-type]
    return S(result)
