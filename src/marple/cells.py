
from marple.numpy_array import APLArray, S
from marple.backend_functions import to_list
from marple.errors import LengthError


def resolve_rank_spec(spec: APLArray) -> tuple[int, int, int]:
    """Resolve rank spec to (monadic, left_dyadic, right_dyadic).

    Scalar c     → (c, c, c)
    2-vector b c → (c, b, c)
    3-vector a b c → (a, b, c)
    """
    data = to_list(spec.data)
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
    data = to_list(array.data)
    n_cells = 1
    for s in frame_shape:
        n_cells *= s
    if n_cells == 0:
        n_cells = 1
    cells: list[APLArray] = []
    for i in range(n_cells):
        cell_data = data[i * cell_size : (i + 1) * cell_size]
        cells.append(APLArray.array(list(cell_shape), cell_data))
    return (list(frame_shape), cells)


def reassemble(frame_shape: list[int], cells: list[APLArray]) -> APLArray:
    """Reassemble cells into a single array.

    If all cells have the same shape, result shape is frame_shape + cell_shape.
    If shapes differ, pad with fill elements to max shape.
    """
    if len(cells) == 0:
        return APLArray.array(frame_shape + [0], [])
    if len(cells) == 1 and frame_shape == []:
        return cells[0]
    # Determine max cell shape
    max_rank = max(len(c.shape) for c in cells)
    max_shape: list[int] = [0] * max_rank
    for c in cells:
        # Pad cell shape on the left with 1s to match max_rank
        padded = [1] * (max_rank - len(c.shape)) + c.shape
        for j in range(max_rank):
            max_shape[j] = max(max_shape[j], padded[j])
    # Check if all cells match max_shape (no padding needed)
    all_uniform = all(c.shape == max_shape for c in cells)
    if all_uniform:
        all_data: list[object] = []
        for c in cells:
            all_data.extend(to_list(c.data))
        return APLArray.array(frame_shape + max_shape, all_data)
    # Padding needed
    max_size = 1
    for s in max_shape:
        max_size *= s
    # Determine fill value
    is_char = any(
        len(c.data) > 0 and isinstance(to_list(c.data)[0], str)
        for c in cells
    )
    fill = " " if is_char else 0
    all_data = []
    for c in cells:
        cell_data = to_list(c.data)
        if c.shape == max_shape:
            all_data.extend(cell_data)
        else:
            # Pad: embed cell data in a max_shape-sized block
            padded_cell: list[object] = [fill] * max_size
            # Simple case: 1D padding
            for j, val in enumerate(cell_data):
                padded_cell[j] = val
            all_data.extend(padded_cell)
    return APLArray.array(frame_shape + max_shape, all_data)
