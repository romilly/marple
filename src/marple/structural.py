from typing import Any

from marple.numpy_array import APLArray, S
from marple.numpy_aplarray import NumpyAPLArray
from marple.backend_functions import (
    char_fill, is_char_array, to_list,
)
from marple.errors import DomainError, IndexError_, LengthError, RankError
from marple.get_numpy import np


# Monadic structural functions

def shape(omega: APLArray) -> APLArray:
    return NumpyAPLArray.array([len(omega.shape)], list(omega.shape))


def iota(omega: APLArray) -> APLArray:
    if not omega.is_scalar():
        raise RankError("Monadic ⍳ requires a scalar argument")
    n = int(omega.data.item())
    return NumpyAPLArray.array([n], list(range(1, n + 1)))


def ravel(omega: APLArray) -> APLArray:
    flat = omega.data.flatten()
    return NumpyAPLArray([len(flat)], flat)


def reverse(omega: APLArray) -> APLArray:
    """Monadic ⌽: reverse along last axis."""
    if len(omega.shape) <= 1:
        return NumpyAPLArray.array(list(omega.shape), list(reversed(to_list(omega.data))))
    # Matrix: reverse each row
    rows, cols = omega.shape[0], omega.shape[-1]
    row_len = cols
    data = list(omega.data)
    result: list[object] = []
    for r in range(len(data) // row_len):
        start = r * row_len
        result.extend(reversed(data[start:start + row_len]))
    return NumpyAPLArray.array(list(omega.shape), result)


def _first_axis_chunk_size(shape: list[int]) -> int:
    """Product of all axes except the first."""
    size = 1
    for s in shape[1:]:
        size *= s
    return size


def reverse_first(omega: APLArray) -> APLArray:
    """Monadic ⊖: reverse along first axis."""
    if len(omega.shape) <= 1:
        return NumpyAPLArray.array(list(omega.shape), list(reversed(to_list(omega.data))))
    chunk = _first_axis_chunk_size(omega.shape)
    n = omega.shape[0]
    data = list(omega.data)
    result: list[object] = []
    for r in range(n - 1, -1, -1):
        start = r * chunk
        result.extend(data[start:start + chunk])
    return NumpyAPLArray.array(list(omega.shape), result)


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
    return NumpyAPLArray(new_shape, cycled.reshape(new_shape))


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
    return NumpyAPLArray.array(list(omega.shape), results)


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
    return NumpyAPLArray.array(list(alpha.shape), results)


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
        return NumpyAPLArray([2], np.concatenate(
            (alpha.data.flatten(), omega.data.flatten())))
    if len(alpha.shape) <= 1 and len(omega.shape) <= 1:
        a = alpha.data.flatten()
        b = omega.data.flatten()
        return NumpyAPLArray([len(a) + len(b)], np.concatenate((a, b)))
    # Higher rank: catenate along last axis.
    a = alpha.data
    b = omega.data
    if a.ndim < b.ndim:
        a = a.reshape([1] * (b.ndim - a.ndim) + list(a.shape))
    elif b.ndim < a.ndim:
        b = b.reshape([1] * (a.ndim - b.ndim) + list(b.shape))
    result = np.concatenate((a, b), axis=-1)
    return NumpyAPLArray(list(result.shape), result)


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
        arr = arr.reshape(shape)
    return NumpyAPLArray(shape, arr)


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
            taken = take(NumpyAPLArray.array([len(inner_counts)], inner_counts), inner)
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
            dropped = drop(NumpyAPLArray.array([len(inner_counts)], inner_counts), inner)
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
    return NumpyAPLArray(list(omega.shape), np.roll(omega.data, -n, axis=-1))


def rotate_first(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic ⊖: rotate along first axis."""
    n = int(alpha.data.flatten()[0])
    if len(omega.shape) <= 1:
        return rotate(alpha, omega)
    return NumpyAPLArray(list(omega.shape), np.roll(omega.data, -n, axis=0))


def transpose_dyadic(alpha: APLArray, omega: APLArray, io: int = 1) -> APLArray:
    """Dyadic ⍉: transpose Y by axis permutation X.

    Per the ISO/Dyalog spec:
      - X must be a simple scalar or vector.
      - The length of X must equal the rank of Y (a scalar X has
        length 1, so it can only transpose a rank-1 Y).
      - The Ith element of X gives the new position for the Ith axis
        of Y.
      - If X repositions multiple axes of Y to the same axis, the
        elements used to fill the resulting axis are those whose
        indices on the relevant Y axes are equal — i.e., diagonal
        extraction. The result rank is `⌈/X - ⎕IO + 1`.
      - The integers in X must form the contiguous range
        `⎕IO..⌈/X` inclusive (no gaps).
      - ⎕IO is an implicit argument.
    """
    if len(alpha.shape) > 1:
        raise RankError("⍉ X must be a scalar or vector")

    # Treat scalar X as length-1 (matches Dyalog: scalar X has tally 1).
    x_atleast = np.atleast_1d(alpha.data)
    x_values = [int(v) for v in x_atleast]

    rank_y = len(omega.shape)

    if len(x_values) != rank_y:
        raise LengthError(
            f"⍉ length of X ({len(x_values)}) must equal rank of Y ({rank_y})")

    # Convert to 0-indexed for numpy.
    x_zero = [v - io for v in x_values]

    # Range check: every X value must be a valid axis index.
    if x_zero and (min(x_zero) < 0 or max(x_zero) >= rank_y):
        raise RankError("⍉ axis index out of range")

    # No-gap check: the values in X must cover [0, max(x_zero)] in
    # 0-indexed terms, with no missing integer.
    if x_zero:
        max_xi = max(x_zero)
        required = set(range(max_xi + 1))
        actual = set(x_zero)
        if not required.issubset(actual):
            raise RankError("⍉ X is missing axis indices in its range")
        n_result_axes = max_xi + 1
    else:
        n_result_axes = 0

    # Result shape: for each result axis k, length is the min over the
    # Y axes that map to it (the diagonal length when there are
    # duplicates).
    result_shape: list[int] = []
    for k in range(n_result_axes):
        y_axes_for_k = [i for i, xi in enumerate(x_zero) if xi == k]
        result_shape.append(min(omega.shape[i] for i in y_axes_for_k))

    # Empty permutation (only valid for scalar Y) → identity.
    if n_result_axes == 0:
        return NumpyAPLArray([], omega.data.copy())

    # Build result coordinates with np.indices, then for each Y axis
    # take the result-coords array at the position x_zero[i]. Tuple-
    # indexing Y with these gives us the diagonal-aware transpose in
    # one numpy operation.
    result_coords = np.indices(tuple(result_shape))
    y_coord_arrays = tuple(result_coords[xi] for xi in x_zero)
    result_data = omega.data[y_coord_arrays]

    return NumpyAPLArray(result_shape, result_data)


def grade_up(omega: APLArray, io: int = 1) -> APLArray:
    indexed = list(enumerate(omega.data))
    indexed.sort(key=lambda pair: pair[1])  # type: ignore[arg-type]
    return NumpyAPLArray.array([len(omega.data)], [i + io for i, _ in indexed])


def grade_down(omega: APLArray, io: int = 1) -> APLArray:
    indexed = list(enumerate(omega.data))
    indexed.sort(key=lambda pair: pair[1], reverse=True)  # type: ignore[arg-type]
    return NumpyAPLArray.array([len(omega.data)], [i + io for i, _ in indexed])


def encode(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic ⊤: represent ω in the number system given by α.

    Per ISO/Dyalog "Representation": both operands must be simple
    numeric arrays. Result shape is (⍴α),⍴ω — α dimensions FIRST,
    then ω dimensions.

    For higher-rank α, the radix vectors are the vectors along α's
    FIRST axis (so for an (n,k) matrix α, the k columns are k
    independent radix systems each of length n).

    A radix of 0 means "fully represent the remaining carry": the
    digit at that position is the entire carry, and the carry
    becomes 0 for any earlier positions.

    If ω exceeds the system's range, the result is the residue
    (×/X)|Y per the spec. This falls out naturally from the modular
    arithmetic.
    """
    if is_char_array(alpha.data) or is_char_array(omega.data):
        raise DomainError("⊤ is not defined on character data")

    a = alpha.data
    o = omega.data

    # Treat 0-d α as length-1 along an implicit single radix axis,
    # but track the original shape for the result.
    a_atleast = np.atleast_1d(a)
    n = a_atleast.shape[0]                    # the radix axis
    other_a_dims = a_atleast.shape[1:]        # axes after the radix axis

    # Result shape per spec: (⍴α),⍴ω
    result_shape = list(a.shape) + list(o.shape)

    # Choose an output dtype that accommodates both operands. For
    # int+int the result stays int; for any float input it becomes
    # float (so float ω is preserved).
    out_dtype = np.result_type(a_atleast.dtype, o.dtype)

    # Empty radix axis → empty result.
    if n == 0:
        return NumpyAPLArray(result_shape,
                        np.zeros(tuple(result_shape), dtype=out_dtype))

    # Carry shape: one carry per (radix-system, ω-value) pair.
    # That is: prepend the "other α dims" to the ω shape.
    carry_shape = other_a_dims + o.shape
    carry = np.broadcast_to(o, carry_shape).astype(out_dtype)

    # Output buffer: (n,) + carry_shape, in the same dtype.
    out = np.empty((n,) + carry_shape, dtype=out_dtype)

    # Walk the radix axis from last (least significant) to first.
    # At each position, peel off one digit and update the carry.
    # `view_shape` reshapes a single radix slice so it broadcasts
    # naturally against the carry across the ω axes.
    view_shape = other_a_dims + (1,) * o.ndim
    for i in range(n - 1, -1, -1):
        radix_i = a_atleast[i].reshape(view_shape)
        zero_mask = (radix_i == 0)
        # Avoid div-by-zero in the unused branch via a safe replacement.
        safe_radix = np.where(zero_mask, 1, radix_i)
        digit = np.where(zero_mask, carry, carry % safe_radix)
        carry = np.where(zero_mask, np.zeros_like(carry), carry // safe_radix)
        out[i] = digit

    return NumpyAPLArray(result_shape, out)


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
        return NumpyAPLArray(result_shape,
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

    return NumpyAPLArray(result_shape, result)


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
    return NumpyAPLArray(list(result.shape), result)


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
    return NumpyAPLArray(list(result.shape), result)


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
    return NumpyAPLArray(out_shape, result)


def matrix_inverse(omega: APLArray) -> APLArray:
    """Monadic ⌹: matrix inverse."""
    if len(omega.shape) != 2 or omega.shape[0] != omega.shape[1]:
        raise RankError("Matrix inverse requires a square matrix")
    try:
        result = np.linalg.inv(omega.data.astype(float))
    except np.linalg.LinAlgError:
        raise DomainError("Singular matrix")
    return NumpyAPLArray(list(omega.shape), result)


def matrix_divide(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic ⌹: solve linear system b⌹A (find x where Ax=b)."""
    from marple.errors import DomainError
    try:
        result = np.linalg.solve(omega.data.astype(float), alpha.data.astype(float))
    except np.linalg.LinAlgError:
        raise DomainError("Singular matrix")
    return NumpyAPLArray(list(result.shape), result)


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
        return NumpyAPLArray.array(cell_shape, [])
    result = np.concatenate(tuple(result_cells))
    if alpha.is_scalar():
        return NumpyAPLArray(cell_shape, result.reshape(cell_shape) if cell_shape else result)
    result_shape = list(alpha.shape) + cell_shape
    return NumpyAPLArray(result_shape, result.reshape(result_shape))
