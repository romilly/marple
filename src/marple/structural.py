
from marple.numpy_array import APLArray, S
from marple.backend_functions import (
    char_fill, is_char_array, np_reshape, to_list,
)
from marple.errors import DomainError, IndexError_, LengthError, RankError
from marple.get_numpy import np


# Monadic structural functions

def shape(omega: APLArray) -> APLArray:
    return APLArray.array([len(omega.shape)], list(omega.shape))


def iota(omega: APLArray) -> APLArray:
    if not omega.is_scalar():
        raise RankError("Monadic ⍳ requires a scalar argument")
    n = int(omega.data.item())
    return APLArray.array([n], list(range(1, n + 1)))


def ravel(omega: APLArray) -> APLArray:
    flat = omega.data.flatten()
    return APLArray([len(flat)], flat)


def reverse(omega: APLArray) -> APLArray:
    """Monadic ⌽: reverse along last axis."""
    if len(omega.shape) <= 1:
        return APLArray.array(list(omega.shape), list(reversed(to_list(omega.data))))
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
        return APLArray.array(list(omega.shape), list(reversed(to_list(omega.data))))
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
        new_shape = [int(alpha.data.item())]
    else:
        new_shape = [int(x) for x in alpha.data]
    total = 1
    for s in new_shape:
        total *= s
    flat = omega.data.flatten()
    if len(flat) == 0:
        # Preserve dtype: fill is char_fill for uint32, 0 otherwise.
        if str(omega.data.dtype) == 'uint32':
            flat = np.array([char_fill()], dtype=np.uint32)
        else:
            flat = np.array([0])
    n = len(flat)
    if total <= n:
        cycled = flat[:total]
    else:
        reps = total // n + 1
        cycled = np.concatenate(tuple([flat] * reps))[:total]
    return APLArray(new_shape, np_reshape(cycled, new_shape))


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
        target = omega.data.item()
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
        val = alpha.data.item()
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
    """Dyadic ,: catenate along last axis.

    Mixed char/numeric catenation coerces via np.concatenate's dtype
    promotion rules (an existing accidental behaviour: chars become
    integer codepoints, or numeric fails to char). This is not strict
    APL — proper behaviour would produce a nested array — but it is
    what marple has always done and no test currently depends on the
    strict semantics.
    """
    if alpha.is_scalar() and omega.is_scalar():
        return APLArray([2], np.concatenate(
            (alpha.data.flatten(), omega.data.flatten())))
    if len(alpha.shape) <= 1 and len(omega.shape) <= 1:
        a = alpha.data.flatten()
        b = omega.data.flatten()
        return APLArray([len(a) + len(b)], np.concatenate((a, b)))
    # Higher rank: catenate along last axis.
    a = alpha.data
    b = omega.data
    if a.ndim < b.ndim:
        a = np_reshape(a, [1] * (b.ndim - a.ndim) + list(a.shape))
    elif b.ndim < a.ndim:
        b = np_reshape(b, [1] * (a.ndim - b.ndim) + list(b.shape))
    result = np.concatenate((a, b), axis=-1)
    return APLArray(list(result.shape), result)


def _fill_element(omega: APLArray) -> object:
    """Return the fill element: char_fill (uint32 32) for char arrays,
    0 for numeric."""
    if is_char_array(omega.data):
        return char_fill()
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


def _build_like(data: list[object], shape: list[int], source: APLArray) -> APLArray:
    """Build an APLArray from a flat list, matching the source's dtype.

    Used by take/drop to keep results consistent with their input:
    a uint32 char input produces a uint32 char output, including for
    empty results and multi-axis reshapes. Going through to_array
    instead would drop empty data to float64 and would not reshape
    a flat list to match a declared higher-rank shape.
    """
    dtype = source.data.dtype
    arr = np.array(data, dtype=dtype) if data else np.array([], dtype=dtype)
    if shape:
        arr = np_reshape(arr, shape)
    return APLArray(shape, arr)


def take(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic ↑: take along each axis. Scalar left → first axis only."""
    counts = [int(x) for x in alpha.data.flatten()]
    fill = _fill_element(omega)
    # Pad counts to match rank (fewer counts → keep trailing axes)
    while len(counts) < len(omega.shape):
        counts.append(omega.shape[len(counts)])
    flat = omega.data.flatten()
    if len(omega.shape) <= 1:
        n = counts[0]
        data = list(flat)
        result, new_len = _take_axis(data, len(data), n, fill)
        return _build_like(result, [new_len], omega)
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
            inner = _build_like(row, inner_shape, omega)
            taken = take(APLArray.array([len(inner_counts)], inner_counts), inner)
            processed.extend(list(taken.data.flatten()))
            inner_shape_out = list(taken.shape)
        return _build_like(processed, [abs_n] + inner_shape_out, omega)
    new_shape = list(omega.shape)
    new_shape[0] = abs_n
    result_data: list[object] = []
    for row in rows:
        result_data.extend(row)
    return _build_like(result_data, new_shape, omega)


def drop(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic ↓: drop along each axis. Scalar left → first axis only."""
    counts = [int(x) for x in alpha.data.flatten()]
    # Pad counts to match rank (fewer counts → keep trailing axes)
    while len(counts) < len(omega.shape):
        counts.append(0)
    flat = omega.data.flatten()
    if len(omega.shape) <= 1:
        n = counts[0]
        data = list(flat)
        if n >= 0:
            result = data[n:]
        else:
            result = data[:n] if n != 0 else data
        return _build_like(result, [len(result)], omega)
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
            inner = _build_like(row, inner_shape, omega)
            dropped = drop(APLArray.array([len(inner_counts)], inner_counts), inner)
            processed.extend(list(dropped.data.flatten()))
            inner_shape_out = list(dropped.shape)
        return _build_like(processed, [kept_rows] + inner_shape_out, omega)
    new_shape = list(omega.shape)
    new_shape[0] = kept_rows
    result_data: list[object] = []
    for row in rows:
        result_data.extend(row)
    return _build_like(result_data, new_shape, omega)


def rotate(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic ⌽: rotate along last axis."""
    n = int(alpha.data.flatten()[0])
    return APLArray(list(omega.shape), np.roll(omega.data, -n, axis=-1))


def rotate_first(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic ⊖: rotate along first axis."""
    n = int(alpha.data.flatten()[0])
    if len(omega.shape) <= 1:
        return rotate(alpha, omega)
    return APLArray(list(omega.shape), np.roll(omega.data, -n, axis=0))


def transpose(omega: APLArray) -> APLArray:
    if len(omega.shape) <= 1:
        return APLArray(list(omega.shape), omega.data.copy())
    if len(omega.shape) != 2:
        raise RankError("Transpose currently supports only rank-2 arrays")
    rows, cols = omega.shape
    return APLArray([cols, rows], omega.data.T.copy())


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
    omega_flat = omega.data.flatten()
    cols = len(omega_flat)
    rows = len(radices)
    result = np.zeros((rows, cols), dtype=np.int64)
    for c in range(cols):
        col = _encode_scalar(radices, int(omega_flat[c]))
        for r in range(rows):
            result[r, c] = col[r]
    return APLArray([rows, cols], result)


def decode(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic ⊥: evaluate ω as a polynomial with bases from α.

    Per ISO/Dyalog "Base Value": the last axis of α and the first
    axis of ω are the digit axis. They must agree in length, OR one
    of them must be a length-1 axis that extends to match the other,
    OR one or both operands may be scalars.

    Result shape is `(¯1↓⍴α),(1↓⍴ω)` — the digit axis is consumed.

    The "first element of α has no effect on the result" rule from
    the spec falls out naturally because the weights vector is built
    from `α[1:]` followed by 1, never using `α[0]`.
    """
    if is_char_array(alpha.data) or is_char_array(omega.data):
        raise DomainError("⊥ is not defined on character data")

    a = alpha.data
    o = omega.data

    # Treat 0-d operands as length-1 along an implicit single axis.
    a_atleast = np.atleast_1d(a)
    o_atleast = np.atleast_1d(o)

    a_n = a_atleast.shape[-1]   # length of α's last axis (digit axis)
    o_n = o_atleast.shape[0]    # length of ω's first axis (digit axis)

    # Result shape (the digit axis is consumed on each side).
    a_outer = list(a.shape[:-1]) if a.ndim >= 1 else []
    o_outer = list(o.shape[1:]) if o.ndim >= 1 else []
    result_shape = a_outer + o_outer

    # Empty digit axis on either side → empty polynomial → 0.
    if a_n == 0 or o_n == 0:
        return APLArray(result_shape,
                        np.zeros(tuple(result_shape) or (), dtype=a.dtype))

    # Conformability: equal lengths, or one is length 1 (extends).
    if a_n != o_n and a_n != 1 and o_n != 1:
        raise LengthError(f"⊥ length mismatch: {a_n} vs {o_n}")
    n = max(a_n, o_n)

    # Broadcast both digit axes to common length n. The non-digit
    # axes of α (everything before the last) and ω (everything after
    # the first) are preserved unchanged.
    a_view = np.broadcast_to(a_atleast, a_atleast.shape[:-1] + (n,))
    o_view = np.broadcast_to(o_atleast, (n,) + o_atleast.shape[1:])

    # Weights along the digit axis: drop the first element of α,
    # append a trailing 1, then cumulative product from the right.
    # For α = [b1, b2, ..., bn], weights = [b2·b3·...·bn, ..., bn, 1].
    ones_tail = np.ones(a_view.shape[:-1] + (1,), dtype=a_view.dtype)
    shifted = np.concatenate([a_view[..., 1:], ones_tail], axis=-1)
    weights = np.flip(np.cumprod(np.flip(shifted, axis=-1), axis=-1), axis=-1)

    # Matrix product: contracts α's last axis with ω's first axis.
    result = weights @ o_view

    return APLArray(result_shape, result)


def replicate(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic /: replicate/compress along the last axis.

    Each element of alpha says how many times to repeat the corresponding
    element along omega's last axis. Scalar alpha extends to match.
    """
    counts = [int(x) for x in alpha.data.flatten()]
    last_axis_len = omega.shape[-1] if omega.shape else 1
    if len(counts) == 1 and last_axis_len > 1:
        counts = counts * last_axis_len
    if len(counts) != last_axis_len:
        raise LengthError(f"Length mismatch: {len(counts)} vs {last_axis_len}")
    result = np.repeat(omega.data, counts, axis=-1)
    return APLArray(list(result.shape), result)


def replicate_first(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic ⌿: replicate/compress along the first axis."""
    if len(omega.shape) <= 1:
        return replicate(alpha, omega)
    counts = [int(x) for x in alpha.data.flatten()]
    first_axis_len = omega.shape[0]
    if len(counts) == 1 and first_axis_len > 1:
        counts = counts * first_axis_len
    if len(counts) != first_axis_len:
        raise LengthError(f"Length mismatch: {len(counts)} vs {first_axis_len}")
    result = np.repeat(omega.data, counts, axis=0)
    return APLArray(list(result.shape), result)


def expand(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic \\: expand along the last axis.

    Where alpha is 0, insert a fill element; where alpha is 1, take the
    next element from omega. The number of 1s in alpha must equal the
    length of omega's last axis.
    """
    mask = [int(x) for x in alpha.data.flatten()]
    fill = _fill_element(omega)
    n_ones = sum(1 for m in mask if m)
    last_axis_len = omega.shape[-1] if omega.shape else 1
    if n_ones != last_axis_len:
        raise LengthError(
            f"Expand: mask has {n_ones} ones but argument has {last_axis_len} elements")
    out_shape = (list(omega.shape[:-1]) + [len(mask)]) if omega.shape else [len(mask)]
    result = np.full(out_shape, fill, dtype=omega.data.dtype)
    one_positions = [i for i, m in enumerate(mask) if m]
    if one_positions:
        result[..., one_positions] = omega.data
    return APLArray(out_shape, result)


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
    flat = omega.data.flatten()
    cell_shape = omega.shape[1:]
    cell_size = 1
    for s in cell_shape:
        cell_size *= s
    if cell_size == 0:
        cell_size = 1
    n_major = omega.shape[0]
    idx_flat = alpha.data.flatten()
    indices = list(idx_flat) if not alpha.is_scalar() else [alpha.data.flatten()[0]]
    result_cells: list[Any] = []
    for idx in indices:
        i = int(idx) - io
        if i < 0 or i >= n_major:
            raise IndexError_(f"{idx} out of range")
        result_cells.append(flat[i * cell_size : (i + 1) * cell_size])
    if len(result_cells) == 0:
        return APLArray.array(cell_shape, [])
    result = np.concatenate(tuple(result_cells))
    if alpha.is_scalar():
        return APLArray(cell_shape, np_reshape(result, cell_shape) if cell_shape else result)
    result_shape = list(alpha.shape) + cell_shape
    return APLArray(result_shape, np_reshape(result, result_shape))
