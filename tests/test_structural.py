from marple.arraymodel import APLArray, S
from marple.interpreter import interpret


class TestShape:
    def test_shape_of_scalar(self) -> None:
        # ⍴5 → empty vector
        assert interpret("⍴5") == APLArray([0], [])

    def test_shape_of_vector(self) -> None:
        # ⍴1 2 3 → 3
        assert interpret("⍴1 2 3") == APLArray([1], [3])


class TestReshape:
    def test_reshape_scalar_to_vector(self) -> None:
        # 3⍴5 → 5 5 5
        assert interpret("3⍴5") == APLArray([3], [5, 5, 5])

    def test_reshape_vector(self) -> None:
        # 5⍴1 2 3 → 1 2 3 1 2
        assert interpret("5⍴1 2 3") == APLArray([5], [1, 2, 3, 1, 2])


class TestIota:
    def test_iota_generates_sequence(self) -> None:
        # ⍳5 → 1 2 3 4 5 (APL index origin 1)
        assert interpret("⍳5") == APLArray([5], [1, 2, 3, 4, 5])

    def test_iota_one(self) -> None:
        assert interpret("⍳1") == APLArray([1], [1])


class TestIndexOf:
    def test_index_of_found(self) -> None:
        # 1 2 3 4 5⍳3 → 3
        assert interpret("1 2 3 4 5⍳3") == S(3)

    def test_index_of_not_found(self) -> None:
        # 1 2 3⍳5 → 4 (one beyond length)
        assert interpret("1 2 3⍳5") == S(4)


class TestRavel:
    def test_ravel_vector(self) -> None:
        # ,1 2 3 → 1 2 3 (identity for vectors)
        assert interpret(",1 2 3") == APLArray([3], [1, 2, 3])

    def test_ravel_scalar(self) -> None:
        # ,5 → vector of length 1
        assert interpret(",5") == APLArray([1], [5])


class TestCatenate:
    def test_catenate_vectors(self) -> None:
        # 1 2 3,4 5 6 → 1 2 3 4 5 6
        assert interpret("1 2 3,4 5 6") == APLArray([6], [1, 2, 3, 4, 5, 6])

    def test_catenate_scalar_to_vector(self) -> None:
        # 0,1 2 3 → 0 1 2 3
        assert interpret("0,1 2 3") == APLArray([4], [0, 1, 2, 3])


class TestTake:
    def test_take_from_front(self) -> None:
        # 2↑1 2 3 4 5 → 1 2
        assert interpret("2↑1 2 3 4 5") == APLArray([2], [1, 2])

    def test_take_from_end(self) -> None:
        # ¯2↑1 2 3 4 5 → 4 5
        assert interpret("¯2↑1 2 3 4 5") == APLArray([2], [4, 5])


class TestDrop:
    def test_drop_from_front(self) -> None:
        # 2↓1 2 3 4 5 → 3 4 5
        assert interpret("2↓1 2 3 4 5") == APLArray([3], [3, 4, 5])

    def test_drop_from_end(self) -> None:
        # ¯2↓1 2 3 4 5 → 1 2 3
        assert interpret("¯2↓1 2 3 4 5") == APLArray([3], [1, 2, 3])


class TestReverse:
    def test_reverse_vector(self) -> None:
        # ⌽1 2 3 → 3 2 1
        assert interpret("⌽1 2 3") == APLArray([3], [3, 2, 1])


class TestRotate:
    def test_rotate_left(self) -> None:
        # 1⌽1 2 3 4 5 → 2 3 4 5 1
        assert interpret("1⌽1 2 3 4 5") == APLArray([5], [2, 3, 4, 5, 1])

    def test_rotate_right(self) -> None:
        # ¯1⌽1 2 3 4 5 → 5 1 2 3 4
        assert interpret("¯1⌽1 2 3 4 5") == APLArray([5], [5, 1, 2, 3, 4])
