"""Tests for NumpyArray — concrete APLArray subclass."""

from marple.backend import APLArray, NumpyArray


class TestNumpyArrayCreation:
    def test_factory_creates_numpy_array(self) -> None:
        result = APLArray.array([3], [1, 2, 3])
        assert isinstance(result, NumpyArray)

    def test_scalar_factory_creates_numpy_array(self) -> None:
        result = APLArray.scalar(5)
        assert isinstance(result, NumpyArray)


class TestNegate:
    def test_negate_scalar(self) -> None:
        result = APLArray.scalar(3).negate()
        assert result == APLArray.scalar(-3)

    def test_negate_vector(self) -> None:
        result = APLArray.array([3], [1, 2, 3]).negate()
        assert result == APLArray.array([3], [-1, -2, -3])


class TestReciprocal:
    def test_reciprocal_scalar(self) -> None:
        result = APLArray.scalar(4).reciprocal()
        assert result == APLArray.scalar(0.25)

    def test_reciprocal_vector(self) -> None:
        result = APLArray.array([2], [2, 5]).reciprocal()
        assert result == APLArray.array([2], [0.5, 0.2])


class TestCeiling:
    def test_ceiling_scalar(self) -> None:
        assert APLArray.scalar(2.3).ceiling() == APLArray.scalar(3)

    def test_ceiling_vector(self) -> None:
        assert APLArray.array([3], [1.1, 2.5, 3.9]).ceiling() == APLArray.array([3], [2, 3, 4])


class TestFloor:
    def test_floor_scalar(self) -> None:
        assert APLArray.scalar(2.7).floor() == APLArray.scalar(2)

    def test_floor_vector(self) -> None:
        assert APLArray.array([3], [1.1, 2.5, 3.9]).floor() == APLArray.array([3], [1, 2, 3])


class TestExponential:
    def test_exp_zero(self) -> None:
        assert APLArray.scalar(0).exponential() == APLArray.scalar(1)


class TestNaturalLog:
    def test_log_one(self) -> None:
        assert APLArray.scalar(1).natural_log() == APLArray.scalar(0)


class TestAbsoluteValue:
    def test_abs_negative(self) -> None:
        assert APLArray.scalar(-5).absolute_value() == APLArray.scalar(5)

    def test_abs_vector(self) -> None:
        assert APLArray.array([3], [-1, 2, -3]).absolute_value() == APLArray.array([3], [1, 2, 3])


class TestLogicalNot:
    def test_not_zero(self) -> None:
        assert APLArray.scalar(0).logical_not() == APLArray.scalar(1)

    def test_not_one(self) -> None:
        assert APLArray.scalar(1).logical_not() == APLArray.scalar(0)


class TestPiTimes:
    def test_pi_times_one(self) -> None:
        import math
        result = APLArray.scalar(1).pi_times()
        assert abs(result.data[0] - math.pi) < 1e-10


class TestFactorial:
    def test_factorial_five(self) -> None:
        assert APLArray.scalar(5).factorial() == APLArray.scalar(120)


class TestShape:
    def test_shape_vector(self) -> None:
        assert APLArray.array([3], [1, 2, 3]).shape_of() == APLArray.array([1], [3])

    def test_shape_matrix(self) -> None:
        assert APLArray.array([2, 3], [1, 2, 3, 4, 5, 6]).shape_of() == APLArray.array([2], [2, 3])

    def test_shape_scalar(self) -> None:
        assert APLArray.scalar(5).shape_of() == APLArray.array([0], [])


class TestTranspose:
    def test_transpose_vector(self) -> None:
        assert APLArray.array([3], [1, 2, 3]).transpose() == APLArray.array([3], [1, 2, 3])

    def test_transpose_matrix(self) -> None:
        result = APLArray.array([2, 3], [1, 2, 3, 4, 5, 6]).transpose()
        assert result.shape == [3, 2]


class TestMatrixInverse:
    def test_identity_inverse(self) -> None:
        result = APLArray.array([2, 2], [1, 0, 0, 1]).matrix_inverse()
        assert result.shape == [2, 2]


class TestReverse:
    def test_reverse_vector(self) -> None:
        assert APLArray.array([3], [1, 2, 3]).reverse() == APLArray.array([3], [3, 2, 1])

    def test_reverse_matrix(self) -> None:
        assert APLArray.array([2, 3], [1, 2, 3, 4, 5, 6]).reverse() == APLArray.array([2, 3], [3, 2, 1, 6, 5, 4])


class TestReverseFirst:
    def test_reverse_first_vector(self) -> None:
        assert APLArray.array([3], [1, 2, 3]).reverse_first() == APLArray.array([3], [3, 2, 1])

    def test_reverse_first_matrix(self) -> None:
        assert APLArray.array([2, 3], [1, 2, 3, 4, 5, 6]).reverse_first() == APLArray.array([2, 3], [4, 5, 6, 1, 2, 3])


class TestRavel:
    def test_ravel_matrix(self) -> None:
        result = APLArray.array([2, 3], [1, 2, 3, 4, 5, 6]).ravel()
        assert result == APLArray.array([6], [1, 2, 3, 4, 5, 6])

    def test_ravel_scalar(self) -> None:
        result = APLArray.scalar(5).ravel()
        assert result == APLArray.array([1], [5])
