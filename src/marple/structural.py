
from marple.numpy_array import APLArray, S
from marple.backend_functions import is_numeric_array, np_reshape, to_list
from marple.errors import DomainError, IndexError_, LengthError, RankError
from marple.get_numpy import np


# Monadic structural functions

def shape(omega: APLArray) -> APLArray:
    return APLArray.array([len(omega.shape)], list(omega.shape))


def iota(omega: APLArray) -> APLArray:
    if not omega.is_scalar():
        raise RankError("Monadic ⍳ requires a scalar argument")
    n = int(omega.data[0])
    return APLArray.array([n], list(range(1, n + 1)))


def ravel(omega: APLArray) -> APLArray:
    return APLArray.array([len(omega.data)], list(omega.data))


def reverse(omega: APLArray) -> APLArray:
    """Monadic ⌽: reverse along last axis."""
    if len(omega.shape) <= 1:
        return APLArray.array(list(omega.shape), list(reversed(omega.data)))
    # Matrix: reverse each row
    rows, cols = omega.shape[0], omega.shape[-1]
    row_len = cols
    data = list(omega.data)
    result: list[object] = []
    for r in range(len(data) // row_len):
        start = r * row_len
        result.extend(reversed(data[start:start + row_len]))
    return APLArray.array(list(omega.shape), result)


def _first_axis_chunk_size(shape: list[int]) -> int:
    """Product of all axes except the first."""
    size = 1
    for s in shape[1:]:
        size *= s
    return size


def reverse_first(omega: APLArray) -> APLArray:
    """Monadic ⊖: reverse along first axis."""
    if len(omega.shape) <= 1:
        return APLArray.array(list(omega.shape), list(reversed(omega.data)))
    chunk = _first_axis_chunk_size(omega.shape)
    n = omega.shape[0]
    data = list(omega.data)
    result: list[object] = []
    for r in range(n - 1, -1, -1):
        start = r * chunk
        result.extend(data[start:start + chunk])
    return APLArray.array(list(omega.shape), result)


# Dyadic structural functions

def reshape(alpha: APLArray, omega: APLArray) -> APLArray:
    if alpha.is_scalar():
        new_shape = [int(alpha.data[0])]
    else:
        new_shape = [int(x) for x in alpha.data]
    total = 1
    for s in new_shape:
        total *= s
    if is_numeric_array(omega.data):
        flat = omega.data.flatten()
        if len(flat) == 0:
            flat = np.array([0])
        n = len(flat)
        if total <= n:
            cycled = flat[:total]
        else:
            reps = total // n + 1
            cycled = np.concatenate([flat] * reps)[:total]
        return APLArray(new_shape, np_reshape(cycled, new_shape))
    # Character data
    data = list(omega.data) if len(omega.data) > 0 else [' ']
    result: list[object] = []
    for i in range(total):
        result.append(data[i % len(data)])
    return APLArray.array(new_shape, result)


def _tolerant_match(a: object, b: object, ct: float) -> bool:
    """Compare two values with tolerance for floats."""
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if ct == 0:
            return a == b
        return abs(float(a) - float(b)) <= ct * max(abs(float(a)), abs(float(b)))
    return a == b


def index_of(alpha: APLArray, omega: APLArray, io: int = 1, ct: float = 0) -> APLArray:
    data = to_list(alpha.data)
    if omega.is_scalar():
        target = omega.data[0]
        for i, val in enumerate(data):
            if _tolerant_match(val, target, ct):
                return S(i + io)
        return S(len(data) + io)
    targets = to_list(omega.data)
    results = []
    for target in targets:
        found = False
        for i, val in enumerate(data):
            if _tolerant_match(val, target, ct):
                results.append(i + io)
                found = True
                break
        if not found:
            results.append(len(data) + io)
    return APLArray.array(list(omega.shape), results)


def membership(alpha: APLArray, omega: APLArray, ct: float = 0) -> APLArray:
    """Dyadic ∈: for each element of alpha, 1 if found in omega, else 0."""
    right_data = to_list(omega.data)
    if alpha.is_scalar():
        val = alpha.data[0]
        for r in right_data:
            if _tolerant_match(val, r, ct):
                return S(1)
        return S(0)
    left_data = to_list(alpha.data)
    results: list[object] = []
    for val in left_data:
        found = 0
        for r in right_data:
            if _tolerant_match(val, r, ct):
                found = 1
                break
        results.append(found)
    return APLArray.array(list(alpha.shape), results)


def catenate(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic ,: catenate along last axis."""
    if alpha.is_scalar() and omega.is_scalar():
        return APLArray.array([2], [alpha.data.flatten()[0], omega.data.flatten()[0]])
    if len(alpha.shape) <= 1 and len(omega.shape) <= 1:
        if is_numeric_array(alpha.data) and is_numeric_array(omega.data):
            a = alpha.data.flatten() if not alpha.is_scalar() else alpha.data.flatten()
            b = omega.data.flatten() if not omega.is_scalar() else omega.data.flatten()
            return APLArray([len(a) + len(b)], np.concatenate([a, b]))
        left = list(alpha.data) if not alpha.is_scalar() else [alpha.data[0]]
        right = list(omega.data) if not omega.is_scalar() else [omega.data[0]]
        return APLArray.array([len(left) + len(right)], left + right)
    # Higher rank: catenate along last axis using numpy
    if is_numeric_array(alpha.data) and is_numeric_array(omega.data):
        # Ensure both have the same number of dimensions
        a = alpha.data
        b = omega.data
        if a.ndim < b.ndim:
            a = np_reshape(a, [1] * (b.ndim - a.ndim) + list(a.shape))
        elif b.ndim < a.ndim:
            b = np_reshape(b, [1] * (a.ndim - b.ndim) + list(b.shape))
        result = np.concatenate([a, b], axis=-1)
        return APLArray(list(result.shape), result)
    # Character fallback
    a_shape = list(alpha.shape) if not alpha.is_scalar() else [1]
    o_shape = list(omega.shape) if not omega.is_scalar() else [1]
    a_cols = a_shape[-1]
    o_cols = o_shape[-1]
    a_flat = alpha.data
    o_flat = omega.data
    n_rows = 1
    for s in a_shape[:-1]:
        n_rows *= s
    result_list: list[object] = []
    for r in range(n_rows):
        result_list.extend(a_flat[r * a_cols:(r + 1) * a_cols])
        result_list.extend(o_flat[r * o_cols:(r + 1) * o_cols])
    new_shape = list(a_shape)
    new_shape[-1] = a_cols + o_cols
    return APLArray.array(new_shape, result_list)


def _fill_element(omega: APLArray) -> object:
    """Return the fill element: ' ' for character arrays, 0 for numeric."""
    if len(omega.data) > 0 and isinstance(omega.data[0], str):
        return " "
    return 0


def _take_axis(data: list[object], axis_len: int, n: int,
               fill: object) -> tuple[list[object], int]:
    """Take n items along one axis. Returns (new_data, new_axis_len)."""
    abs_n = abs(n)
    if n >= 0:
        taken = data[:abs_n]
        pad = [fill] * max(0, abs_n - axis_len)
        return taken + pad, abs_n
    else:
        taken = data[max(0, axis_len + n):]
        pad = [fill] * max(0, abs_n - axis_len)
        return pad + taken, abs_n


def take(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic ↑: take along each axis. Scalar left → first axis only."""
    counts = [int(x) for x in alpha.data.flatten()]
    fill = _fill_element(omega)
    # Pad counts to match rank (fewer counts → keep trailing axes)
    while len(counts) < len(omega.shape):
        counts.append(omega.shape[len(counts)])
    flat = omega.data.flatten() if is_numeric_array(omega.data) else omega.data
    if len(omega.shape) <= 1:
        n = counts[0]
        data = list(flat)
        result, new_len = _take_axis(data, len(data), n, fill)
        return APLArray.array([new_len], result)
    # Multi-axis: take first axis, then recurse on inner
    n = counts[0]
    abs_n = abs(n)
    chunk = _first_axis_chunk_size(omega.shape)
    num_rows = omega.shape[0]
    fill_row = [fill] * chunk
    rows: list[list[object]] = []
    for r in range(abs_n):
        src = r if n >= 0 else num_rows + n + r
        if 0 <= src < num_rows:
            rows.append(list(flat[src * chunk:(src + 1) * chunk]))
        else:
            rows.append(list(fill_row))
    # If more axes to take, apply to each row
    if len(counts) > 1:
        inner_shape = list(omega.shape[1:])
        inner_counts = counts[1:]
        processed: list[object] = []
        inner_shape_out = inner_shape
        for row in rows:
            inner = APLArray.array(list(inner_shape), row)
            taken = take(APLArray.array([len(inner_counts)], inner_counts), inner)
            processed.extend(list(taken.data.flatten()) if is_numeric_array(taken.data) else taken.data)
            inner_shape_out = list(taken.shape)
        new_shape = [abs_n] + inner_shape_out
        return APLArray.array(new_shape, processed)
    new_shape = list(omega.shape)
    new_shape[0] = abs_n
    result_data: list[object] = []
    for row in rows:
        result_data.extend(row)
    return APLArray.array(new_shape, result_data)


def drop(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic ↓: drop along each axis. Scalar left → first axis only."""
    counts = [int(x) for x in alpha.data.flatten()]
    # Pad counts to match rank (fewer counts → keep trailing axes)
    while len(counts) < len(omega.shape):
        counts.append(0)
    flat = omega.data.flatten() if is_numeric_array(omega.data) else omega.data
    if len(omega.shape) <= 1:
        n = counts[0]
        data = list(flat)
        if n >= 0:
            result = data[n:]
        else:
            result = data[:n] if n != 0 else data
        return APLArray.array([len(result)], result)
    # Multi-axis: drop first axis, then recurse on inner
    n = counts[0]
    chunk = _first_axis_chunk_size(omega.shape)
    num_rows = omega.shape[0]
    if n >= 0:
        start = min(n, num_rows)
        kept_rows = num_rows - start
    else:
        start = 0
        kept_rows = max(num_rows + n, 0)
    rows: list[list[object]] = []
    for r in range(kept_rows):
        src = start + r if n >= 0 else r
        rows.append(list(flat[src * chunk:(src + 1) * chunk]))
    if len(counts) > 1:
        inner_shape = list(omega.shape[1:])
        inner_counts = counts[1:]
        processed: list[object] = []
        inner_shape_out = inner_shape
        for row in rows:
            inner = APLArray.array(list(inner_shape), row)
            dropped = drop(APLArray.array([len(inner_counts)], inner_counts), inner)
            processed.extend(list(dropped.data.flatten()) if is_numeric_array(dropped.data) else dropped.data)
            inner_shape_out = list(dropped.shape)
        new_shape = [kept_rows] + inner_shape_out
        return APLArray.array(new_shape, processed)
    new_shape = list(omega.shape)
    new_shape[0] = kept_rows
    result_data: list[object] = []
    for row in rows:
        result_data.extend(row)
    return APLArray.array(new_shape, result_data)


def rotate(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic ⌽: rotate along last axis."""
    n = int(alpha.data.flatten()[0])
    if is_numeric_array(omega.data):
        return APLArray(list(omega.shape), np.roll(omega.data, -n, axis=-1))
    data = omega.data
    if len(omega.shape) <= 1:
        length = len(data)
        if length == 0:
            return APLArray.array(list(omega.shape), [])
        n = n % length
        return APLArray.array(list(omega.shape), data[n:] + data[:n])
    row_len = omega.shape[-1]
    result: list[object] = []
    for i in range(0, len(data), row_len):
        row = data[i:i + row_len]
        k = n % row_len if row_len else 0
        result.extend(row[k:] + row[:k])
    return APLArray.array(list(omega.shape), result)


def rotate_first(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic ⊖: rotate along first axis."""
    n = int(alpha.data.flatten()[0])
    if len(omega.shape) <= 1:
        return rotate(alpha, omega)
    if is_numeric_array(omega.data):
        return APLArray(list(omega.shape), np.roll(omega.data, -n, axis=0))
    chunk = _first_axis_chunk_size(omega.shape)
    num_chunks = omega.shape[0]
    data = omega.data
    n = n % num_chunks if num_chunks else 0
    result: list[object] = []
    for r in range(num_chunks):
        src = (r + n) % num_chunks
        start = src * chunk
        result.extend(data[start:start + chunk])
    return APLArray.array(list(omega.shape), result)


def transpose(omega: APLArray) -> APLArray:
    if len(omega.shape) <= 1:
        return APLArray.array(list(omega.shape), list(omega.data))
    if len(omega.shape) != 2:
        raise RankError("Transpose currently supports only rank-2 arrays")
    rows, cols = omega.shape
    new_data: list[object] = []
    for c in range(cols):
        for r in range(rows):
            new_data.append(omega.data[r * cols + c])
    return APLArray.array([cols, rows], new_data)


def grade_up(omega: APLArray, io: int = 1) -> APLArray:
    indexed = list(enumerate(omega.data))
    indexed.sort(key=lambda pair: pair[1])  # type: ignore[arg-type]
    return APLArray.array([len(omega.data)], [i + io for i, _ in indexed])


def grade_down(omega: APLArray, io: int = 1) -> APLArray:
    indexed = list(enumerate(omega.data))
    indexed.sort(key=lambda pair: pair[1], reverse=True)  # type: ignore[arg-type]
    return APLArray.array([len(omega.data)], [i + io for i, _ in indexed])


def _encode_scalar(radices: list[object], n: int) -> list[int]:
    """Encode a single integer in the given radix system."""
    result = [0] * len(radices)
    for i in range(len(radices) - 1, -1, -1):
        r = int(radices[i])  # type: ignore[arg-type]
        if r == 0:
            result[i] = n
            n = 0
        else:
            result[i] = n % r
            n = n // r
    return result


def encode(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic ⊤: represent omega in the radix system given by alpha."""
    radices = list(alpha.data.flatten())
    if omega.is_scalar():
        encoded = _encode_scalar(radices, int(omega.data.flatten()[0]))
        return APLArray.array([len(radices)], list(encoded))
    # Vector right arg → matrix (radix_len × omega_len)
    omega_flat = omega.data.flatten() if is_numeric_array(omega.data) else omega.data
    cols = len(omega_flat)
    rows = len(radices)
    result = np.zeros((rows, cols), dtype=np.int64)
    for c in range(cols):
        col = _encode_scalar(radices, int(omega_flat[c]))
        for r in range(rows):
            result[r, c] = col[r]
    return APLArray([rows, cols], result)


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
        raise LengthError(f"Length mismatch: {len(bases)} bases vs {len(values)} values")
    result = 0
    for b, v in zip(bases, values):
        result = result * int(b) + int(v)  # type: ignore[arg-type]
    return S(result)


def replicate(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic /: replicate/compress. Each element of alpha says how many
    times to repeat the corresponding element of omega.
    Scalar left argument is extended to match right argument length."""
    counts = [int(x) for x in alpha.data]
    data = list(omega.data)
    # Scalar extension: single count applies to all elements
    if len(counts) == 1 and len(data) > 1:
        counts = counts * len(data)
    if len(counts) != len(data):
        raise LengthError(f"Length mismatch: {len(counts)} vs {len(data)}")
    result: list[object] = []
    for count, val in zip(counts, data):
        for _ in range(count):
            result.append(val)
    return APLArray.array([len(result)], result)


def replicate_first(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic ⌿: replicate/compress along first axis."""
    counts = [int(x) for x in alpha.data.flatten()]
    if len(omega.shape) <= 1:
        return replicate(alpha, omega)
    first = omega.shape[0]
    if len(counts) == 1 and first > 1:
        counts = counts * first
    if len(counts) != first:
        raise LengthError(f"Length mismatch: {len(counts)} vs {first}")
    cell_shape = omega.shape[1:]
    cell_size = 1
    for s in cell_shape:
        cell_size *= s
    flat = omega.data.flatten() if is_numeric_array(omega.data) else omega.data
    result_cells: list[Any] = []
    for i, count in enumerate(counts):
        cell = flat[i * cell_size : (i + 1) * cell_size]
        for _ in range(count):
            result_cells.append(cell)
    total_rows = len(result_cells)
    if total_rows == 0:
        return APLArray([0] + cell_shape, np.array([]))
    result = np.concatenate(result_cells)
    return APLArray([total_rows] + cell_shape, np_reshape(result, [total_rows] + cell_shape))


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
    return APLArray.array([len(result)], result)


def matrix_inverse(omega: APLArray) -> APLArray:
    """Monadic ⌹: matrix inverse."""
    if len(omega.shape) != 2 or omega.shape[0] != omega.shape[1]:
        raise RankError("Matrix inverse requires a square matrix")
    try:
        result = np.linalg.inv(omega.data.astype(float))
    except np.linalg.LinAlgError:
        raise DomainError("Singular matrix")
    return APLArray(list(omega.shape), result)


def matrix_divide(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic ⌹: solve linear system b⌹A (find x where Ax=b)."""
    from marple.errors import DomainError
    try:
        result = np.linalg.solve(omega.data.astype(float), alpha.data.astype(float))
    except np.linalg.LinAlgError:
        raise DomainError("Singular matrix")
    return APLArray(list(result.shape), result)


def from_array(alpha: APLArray, omega: APLArray, io: int = 1) -> APLArray:
    """Dyadic ⌷: select major cells of omega at indices in alpha."""
    if omega.is_scalar():
        raise RankError("requires non-scalar right argument")
    flat = omega.data.flatten() if is_numeric_array(omega.data) else omega.data
    cell_shape = omega.shape[1:]
    cell_size = 1
    for s in cell_shape:
        cell_size *= s
    if cell_size == 0:
        cell_size = 1
    n_major = omega.shape[0]
    idx_flat = alpha.data.flatten() if is_numeric_array(alpha.data) else alpha.data
    indices = list(idx_flat) if not alpha.is_scalar() else [alpha.data.flatten()[0]]
    result_cells: list[Any] = []
    for idx in indices:
        i = int(idx) - io
        if i < 0 or i >= n_major:
            raise IndexError_(f"{idx} out of range")
        result_cells.append(flat[i * cell_size : (i + 1) * cell_size])
    if len(result_cells) == 0:
        return APLArray.array(cell_shape, [])
    result = np.concatenate(result_cells)
    if alpha.is_scalar():
        return APLArray(cell_shape, np_reshape(result, cell_shape) if cell_shape else result)
    result_shape = list(alpha.shape) + cell_shape
    return APLArray(result_shape, np_reshape(result, result_shape))
