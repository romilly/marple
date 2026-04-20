
from marple.numpy_array import APLArray, S
from marple.numpy_aplarray import NumpyAPLArray
from marple.errors import LengthError


def resolve_rank_spec(spec: APLArray) -> tuple[int, int, int]:
    """Resolve rank spec to (monadic, left_dyadic, right_dyadic).

    Scalar c     → (c, c, c)
    2-vector b c → (c, b, c)
    3-vector a b c → (a, b, c)
    """
    data = spec.to_list()
    if spec.is_scalar():
        c = int(data[0])
        return (c, c, c)
    if len(data) == 2:
        b, c = int(data[0]), int(data[1])
        return (c, b, c)
    if len(data) == 3:
        a, b, c = int(data[0]), int(data[1]), int(data[2])
        return (a, b, c)
    raise LengthError(f"Rank spec must be 1, 2, or 3 elements, got {len(data)}")


def clamp_rank(k: int, r: int) -> int:
    """Clamp cell rank k to [0, r]. Handle negative (complementary) rank."""
    if k < 0:
        k = r + k
    return max(0, min(k, r))

#TODO: can't we use numpy code here
def decompose(array: APLArray, cell_rank: int) -> tuple[list[int], list[APLArray]]:
    """Decompose array into cells of the given rank.

    Returns (frame_shape, cells) where frame_shape is the leading axes
    and cells is a list of APLArray objects in row-major frame order.
    """
    r = len(array.shape)
    k = clamp_rank(cell_rank, r)
    frame_shape = array.shape[:r - k] if k < r else []
    cell_shape = array.shape[r - k:] if k > 0 else []
    cell_size = 1
    for s in cell_shape:
        cell_size *= s
    if cell_size == 0:
        cell_size = 1
    flat = array.data.flatten()
    n_cells = 1
    for s in frame_shape:
        n_cells *= s
    if n_cells == 0:
        n_cells = 1
    cells: list[APLArray] = []
    for i in range(n_cells):
        cell_data = flat[i * cell_size : (i + 1) * cell_size]
        if cell_shape:
            cell_data = cell_data.reshape(cell_shape)
        cells.append(NumpyAPLArray(list(cell_shape), cell_data))
    return (list(frame_shape), cells)

#TODO: can't we use numpy code here
def reassemble(frame_shape: list[int], cells: list[APLArray]) -> APLArray:
    """Reassemble cells into a single array.

    If all cells have the same shape, result shape is frame_shape + cell_shape.
    If shapes differ, pad with fill elements to max shape.
    """
    from marple.get_numpy import np
    if len(cells) == 0:
        return NumpyAPLArray(frame_shape + [0], np.array([]))
    if len(cells) == 1 and frame_shape == []:
        return cells[0]
    # Determine max cell shape
    max_rank = max(len(c.shape) for c in cells)
    max_shape: list[int] = [0] * max_rank
    for c in cells:
        padded = [1] * (max_rank - len(c.shape)) + c.shape
        for j in range(max_rank):
            max_shape[j] = max(max_shape[j], padded[j])
    result_shape = frame_shape + max_shape
    # Check if all cells are numeric
    all_numeric = all(c.is_numeric() for c in cells)
    all_uniform = all(c.shape == max_shape for c in cells)
    if all_uniform and all_numeric:
        flat_cells = [c.data.flatten() for c in cells]
        result = np.concatenate(tuple(flat_cells))
        return NumpyAPLArray(result_shape, result.reshape(result_shape))
    if all_uniform:
        all_data: list[object] = []
        for c in cells:
            all_data.extend(c.to_list())
        return NumpyAPLArray.array(result_shape, all_data)
    # Padding needed
    max_size = 1
    for s in max_shape:
        max_size *= s
    is_char = any(c.is_char() for c in cells)
    fill = " " if is_char else 0
    if not is_char:
        result = np.zeros(len(cells) * max_size, dtype=np.float64)
        for i, c in enumerate(cells):
            flat = c.data.flatten() if c.is_numeric() else c.data
            result[i * max_size : i * max_size + len(flat)] = flat
        return NumpyAPLArray(result_shape, result.reshape(result_shape))
    all_data = []
    for c in cells:
        cell_data = c.to_list()
        if c.shape == max_shape:
            all_data.extend(cell_data)
        else:
            padded_cell: list[object] = [fill] * max_size
            for j, val in enumerate(cell_data):
                padded_cell[j] = val
            all_data.extend(padded_cell)
    return NumpyAPLArray.array(result_shape, all_data)
