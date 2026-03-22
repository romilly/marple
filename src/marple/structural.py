from __future__ import annotations

from marple.arraymodel import APLArray, S
from marple.backend import to_list


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


def index_of(alpha: APLArray, omega: APLArray, io: int = 1) -> APLArray:
    if omega.is_scalar():
        target = omega.data[0]
        for i, val in enumerate(alpha.data):
            if val == target:
                return S(i + io)
        return S(len(alpha.data) + io)  # not found
    targets = omega.data
    results = []
    for target in targets:
        found = False
        for i, val in enumerate(alpha.data):
            if val == target:
                results.append(i + io)
                found = True
                break
        if not found:
            results.append(len(alpha.data) + io)
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


def grade_up(omega: APLArray, io: int = 1) -> APLArray:
    indexed = list(enumerate(omega.data))
    indexed.sort(key=lambda pair: pair[1])  # type: ignore[arg-type]
    return APLArray([len(omega.data)], [i + io for i, _ in indexed])


def grade_down(omega: APLArray, io: int = 1) -> APLArray:
    indexed = list(enumerate(omega.data))
    indexed.sort(key=lambda pair: pair[1], reverse=True)  # type: ignore[arg-type]
    return APLArray([len(omega.data)], [i + io for i, _ in indexed])


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


def replicate(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic /: replicate/compress. Each element of alpha says how many
    times to repeat the corresponding element of omega."""
    counts = [int(x) for x in alpha.data]
    data = list(omega.data)
    if len(counts) != len(data):
        raise ValueError(f"Length mismatch: {len(counts)} vs {len(data)}")
    result: list[object] = []
    for count, val in zip(counts, data):
        for _ in range(count):
            result.append(val)
    return APLArray([len(result)], result)


def expand(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic \\: expand. Insert fill elements (0) where alpha is 0."""
    mask = [int(x) for x in alpha.data]
    data = list(omega.data)
    result: list[object] = []
    data_idx = 0
    for m in mask:
        if m:
            if data_idx < len(data):
                result.append(data[data_idx])
                data_idx += 1
            else:
                result.append(0)
        else:
            result.append(0)
    return APLArray([len(result)], result)


def matrix_inverse(omega: APLArray) -> APLArray:
    """Monadic ⌹: matrix inverse using Gauss-Jordan elimination."""
    if len(omega.shape) != 2 or omega.shape[0] != omega.shape[1]:
        raise ValueError("Matrix inverse requires a square matrix")
    n = omega.shape[0]
    # Build augmented matrix [A|I]
    aug: list[list[float]] = []
    for i in range(n):
        row = [float(omega.data[i * n + j]) for j in range(n)]
        ident = [1.0 if j == i else 0.0 for j in range(n)]
        aug.append(row + ident)
    # Gauss-Jordan elimination
    for col in range(n):
        max_row = col
        for row in range(col + 1, n):
            if abs(aug[row][col]) > abs(aug[max_row][col]):
                max_row = row
        aug[col], aug[max_row] = aug[max_row], aug[col]
        pivot = aug[col][col]
        if abs(pivot) < 1e-15:
            raise ValueError("Singular matrix")
        for j in range(2 * n):
            aug[col][j] /= pivot
        for row in range(n):
            if row != col:
                factor = aug[row][col]
                for j in range(2 * n):
                    aug[row][j] -= factor * aug[col][j]
    result: list[object] = []
    for i in range(n):
        for j in range(n):
            result.append(aug[i][n + j])
    return APLArray([n, n], result)


def matrix_divide(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic ⌹: solve linear system b⌹A (find x where Ax=b)."""
    inv = matrix_inverse(omega)
    n = inv.shape[0]
    b = list(alpha.data)
    result: list[object] = []
    for i in range(n):
        val = 0.0
        for j in range(n):
            val += float(inv.data[i * n + j]) * float(b[j])
        result.append(val)
    return APLArray([n], result)


def from_array(alpha: APLArray, omega: APLArray, io: int = 1) -> APLArray:
    """Dyadic ⌷: select major cells of omega at indices in alpha."""
    if omega.is_scalar():
        raise ValueError("RANK ERROR: From requires non-scalar right argument")
    data = to_list(omega.data)
    cell_shape = omega.shape[1:]
    cell_size = 1
    for s in cell_shape:
        cell_size *= s
    if cell_size == 0:
        cell_size = 1
    n_major = omega.shape[0]
    indices = to_list(alpha.data) if not alpha.is_scalar() else [alpha.data[0]]
    result: list[object] = []
    for idx in indices:
        i = int(idx) - io
        if i < 0 or i >= n_major:
            raise ValueError(f"INDEX ERROR: {idx} out of range")
        result.extend(data[i * cell_size : (i + 1) * cell_size])
    if alpha.is_scalar():
        return APLArray(cell_shape, result)
    return APLArray(list(alpha.shape) + cell_shape, result)
