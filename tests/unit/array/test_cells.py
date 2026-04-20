from marple.ports.array import APLArray, S
from marple.cells import clamp_rank, decompose, reassemble, resolve_rank_spec


class TestResolveRankSpec:
    def test_scalar(self) -> None:
        assert resolve_rank_spec(S(1)) == (1, 1, 1)

    def test_two_vector(self) -> None:
        assert resolve_rank_spec(APLArray.array([2], [0, 1])) == (1, 0, 1)

    def test_three_vector(self) -> None:
        assert resolve_rank_spec(APLArray.array([3], [2, 0, 1])) == (2, 0, 1)


class TestClampRank:
    def test_positive_within_range(self) -> None:
        assert clamp_rank(1, 3) == 1

    def test_positive_exceeds_rank(self) -> None:
        assert clamp_rank(5, 3) == 3

    def test_negative(self) -> None:
        # ¯1 on rank 3 → 3-1 = 2
        assert clamp_rank(-1, 3) == 2

    def test_negative_clamped(self) -> None:
        assert clamp_rank(-5, 3) == 0

    def test_zero(self) -> None:
        assert clamp_rank(0, 3) == 0


class TestDecompose:
    def test_vector_rank0(self) -> None:
        # Vector decomposed into scalars
        frame, cells = decompose(APLArray.array([3], [10, 20, 30]), 0)
        assert frame == [3]
        assert len(cells) == 3
        assert cells[0] == S(10)
        assert cells[2] == S(30)

    def test_vector_rank1(self) -> None:
        # Whole vector is one cell
        v = APLArray.array([3], [10, 20, 30])
        frame, cells = decompose(v, 1)
        assert frame == []
        assert len(cells) == 1
        assert cells[0] == v

    def test_matrix_rank1(self) -> None:
        # 3×4 matrix → 3 row vectors
        m = APLArray.array([3, 4], list(range(1, 13)))
        frame, cells = decompose(m, 1)
        assert frame == [3]
        assert len(cells) == 3
        assert cells[0] == APLArray.array([4], [1, 2, 3, 4])
        assert cells[2] == APLArray.array([4], [9, 10, 11, 12])

    def test_matrix_rank0(self) -> None:
        # 2×3 matrix → 6 scalars
        m = APLArray.array([2, 3], [1, 2, 3, 4, 5, 6])
        frame, cells = decompose(m, 0)
        assert frame == [2, 3]
        assert len(cells) == 6

    def test_matrix_rank2(self) -> None:
        # Whole matrix is one cell
        m = APLArray.array([2, 3], [[1, 2, 3], [4, 5, 6]])
        frame, cells = decompose(m, 2)
        assert frame == []
        assert len(cells) == 1
        assert cells[0] == m

    def test_rank3_rank1(self) -> None:
        # 2×3×4 → 6 vectors of length 4
        a = APLArray.array([2, 3, 4], list(range(1, 25)))
        frame, cells = decompose(a, 1)
        assert frame == [2, 3]
        assert len(cells) == 6
        assert cells[0] == APLArray.array([4], [1, 2, 3, 4])

    def test_rank3_rank2(self) -> None:
        # 2×3×4 → 2 matrices of 3×4
        a = APLArray.array([2, 3, 4], list(range(1, 25)))
        frame, cells = decompose(a, 2)
        assert frame == [2]
        assert len(cells) == 2
        assert cells[0] == APLArray.array([3, 4], [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]])


class TestReassemble:
    def test_scalars_to_vector(self) -> None:
        cells = [S(10), S(20), S(30)]
        result = reassemble([3], cells)
        assert result == APLArray.array([3], [10, 20, 30])

    def test_vectors_to_matrix(self) -> None:
        cells = [APLArray.array([4], [1, 2, 3, 4]), APLArray.array([4], [5, 6, 7, 8])]
        result = reassemble([2], cells)
        assert result == APLArray.array([2, 4], [[1, 2, 3, 4], [5, 6, 7, 8]])

    def test_single_cell_empty_frame(self) -> None:
        cell = APLArray.array([3], [1, 2, 3])
        result = reassemble([], [cell])
        assert result == cell

    def test_padding_different_lengths(self) -> None:
        # Two vectors of different lengths → pad shorter with 0
        cells = [APLArray.array([3], [1, 2, 3]), APLArray.array([2], [4, 5])]
        result = reassemble([2], cells)
        assert result == APLArray.array([2, 3], [[1, 2, 3], [4, 5, 0]])
