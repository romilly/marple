"""Structural function tests — new engine."""

from marple.numpy_array import APLArray, S
from marple.engine import Interpreter


class TestIota:
    def test_iota(self) -> None:
        assert Interpreter(io=1).run("⍳5") == APLArray.array([5], [1, 2, 3, 4, 5])

    def test_iota_one(self) -> None:
        assert Interpreter(io=1).run("⍳1") == APLArray.array([1], [1])

    def test_iota_zero_origin(self) -> None:
        assert Interpreter(io=0).run("⍳5") == APLArray.array([5], [0, 1, 2, 3, 4])


class TestShape:
    def test_shape_vector(self) -> None:
        assert Interpreter(io=1).run("⍴1 2 3") == APLArray.array([1], [3])

    def test_shape_matrix(self) -> None:
        assert Interpreter(io=1).run("⍴2 3⍴⍳6") == APLArray.array([2], [2, 3])

    def test_shape_scalar(self) -> None:
        assert Interpreter(io=1).run("⍴5") == APLArray.array([0], [])


class TestReshape:
    def test_reshape(self) -> None:
        assert Interpreter(io=1).run("2 3⍴⍳6") == APLArray.array([2, 3], [1, 2, 3, 4, 5, 6])

    def test_reshape_scalar_fill(self) -> None:
        assert Interpreter(io=1).run("2 3⍴1") == APLArray.array([2, 3], [1, 1, 1, 1, 1, 1])

    def test_reshape_scalar_to_vector(self) -> None:
        assert Interpreter(io=1).run("3⍴5") == APLArray.array([3], [5, 5, 5])

    def test_reshape_vector(self) -> None:
        assert Interpreter(io=1).run("5⍴1 2 3") == APLArray.array([5], [1, 2, 3, 1, 2])

    def test_reshape_cycle(self) -> None:
        assert Interpreter(io=1).run("2 3⍴1 2") == APLArray.array([2, 3], [1, 2, 1, 2, 1, 2])


class TestRavel:
    def test_ravel(self) -> None:
        assert Interpreter(io=1).run(",2 3⍴⍳6") == APLArray.array([6], [1, 2, 3, 4, 5, 6])

    def test_ravel_vector(self) -> None:
        assert Interpreter(io=1).run(",1 2 3") == APLArray.array([3], [1, 2, 3])

    def test_ravel_scalar(self) -> None:
        assert Interpreter(io=1).run(",5") == APLArray.array([1], [5])


class TestReverse:
    def test_reverse(self) -> None:
        assert Interpreter(io=1).run("⌽1 2 3") == APLArray.array([3], [3, 2, 1])


class TestRotate:
    def test_rotate(self) -> None:
        assert Interpreter(io=1).run("1⌽1 2 3") == APLArray.array([3], [2, 3, 1])

    def test_rotate_left(self) -> None:
        assert Interpreter(io=1).run("1⌽1 2 3 4 5") == APLArray.array([5], [2, 3, 4, 5, 1])

    def test_rotate_right(self) -> None:
        assert Interpreter(io=1).run("¯1⌽1 2 3 4 5") == APLArray.array([5], [5, 1, 2, 3, 4])


class TestTakeAndDrop:
    def test_take(self) -> None:
        assert Interpreter(io=1).run("3↑⍳5") == APLArray.array([3], [1, 2, 3])

    def test_take_from_front(self) -> None:
        assert Interpreter(io=1).run("2↑1 2 3 4 5") == APLArray.array([2], [1, 2])

    def test_take_from_end(self) -> None:
        assert Interpreter(io=1).run("¯2↑1 2 3 4 5") == APLArray.array([2], [4, 5])

    def test_drop(self) -> None:
        assert Interpreter(io=1).run("2↓⍳5") == APLArray.array([3], [3, 4, 5])

    def test_drop_from_front(self) -> None:
        assert Interpreter(io=1).run("2↓1 2 3 4 5") == APLArray.array([3], [3, 4, 5])

    def test_drop_from_end(self) -> None:
        assert Interpreter(io=1).run("¯2↓1 2 3 4 5") == APLArray.array([3], [1, 2, 3])


class TestCatenate:
    def test_catenate(self) -> None:
        assert Interpreter(io=1).run("1 2 3,4 5") == APLArray.array([5], [1, 2, 3, 4, 5])

    def test_catenate_vectors(self) -> None:
        assert Interpreter(io=1).run("1 2 3,4 5 6") == APLArray.array([6], [1, 2, 3, 4, 5, 6])

    def test_catenate_scalar_to_vector(self) -> None:
        assert Interpreter(io=1).run("0,1 2 3") == APLArray.array([4], [0, 1, 2, 3])


class TestTranspose:
    def test_transpose(self) -> None:
        i = Interpreter(io=1)
        result = i.run("⍉2 3⍴⍳6")
        assert result.shape == [3, 2]


class TestEncodeDecode:
    def test_encode(self) -> None:
        assert Interpreter(io=1).run("2 2 2⊤7") == APLArray.array([3], [1, 1, 1])

    def test_decode(self) -> None:
        assert Interpreter(io=1).run("2 2 2⊥1 1 1") == S(7)


class TestTally:
    def test_tally_vector(self) -> None:
        assert Interpreter(io=1).run("≢1 2 3") == S(3)

    def test_tally_scalar(self) -> None:
        assert Interpreter(io=1).run("≢5") == S(1)


class TestGrade:
    def test_grade_up(self) -> None:
        assert Interpreter(io=1).run("⍋3 1 4 1 5") == APLArray.array([5], [2, 4, 1, 3, 5])

    def test_grade_down(self) -> None:
        assert Interpreter(io=1).run("⍒3 1 4 1 5") == APLArray.array([5], [5, 3, 1, 2, 4])

    def test_grade_up_io0(self) -> None:
        assert Interpreter(io=0).run("⍋3 1 4") == APLArray.array([3], [1, 0, 2])


class TestReplicate:
    def test_replicate(self) -> None:
        assert Interpreter(io=1).run("1 0 1/1 2 3") == APLArray.array([2], [1, 3])


class TestExpand:
    def test_expand(self) -> None:
        result = Interpreter(io=1).run("1 0 1\\1 2")
        assert result.shape == [3]


class TestIndexOf:
    def test_index_of(self) -> None:
        assert Interpreter(io=1).run("3 1 4 1 5⍳4") == S(3)

    def test_index_of_not_found(self) -> None:
        assert Interpreter(io=1).run("3 1 4⍳99") == S(4)

    def test_index_of_io0(self) -> None:
        assert Interpreter(io=0).run("10 20 30⍳20") == S(1)


class TestMembership:
    def test_membership(self) -> None:
        assert Interpreter(io=1).run("2 3∈1 2 3 4 5") == APLArray.array([2], [1, 1])


class TestFrom:
    def test_from(self) -> None:
        assert Interpreter(io=1).run("2⌷10 20 30") == S(20)


class TestMatch:
    def test_match(self) -> None:
        assert Interpreter(io=1).run("(1 2 3)≡(1 2 3)") == S(1)
        assert Interpreter(io=1).run("(1 2 3)≡(1 2 4)") == S(0)

    def test_not_match(self) -> None:
        assert Interpreter(io=1).run("(1 2 3)≢(1 2 4)") == S(1)


class TestMatrixInverse:
    def test_identity(self) -> None:
        result = Interpreter(io=1).run("⌹2 2⍴1 0 0 1")
        assert result.shape == [2, 2]
