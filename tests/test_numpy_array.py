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


class TestRoll:
    def test_roll_scalar_returns_in_range(self) -> None:
        result = APLArray.scalar(6).roll(io=1)
        val = result.data[0]
        assert 1 <= val <= 6

    def test_roll_zero_returns_float(self) -> None:
        result = APLArray.scalar(0).roll(io=1)
        val = result.data[0]
        assert isinstance(val, float)
        assert 0.0 <= val < 1.0

    def test_roll_vector(self) -> None:
        result = APLArray.array([3], [6, 6, 6]).roll(io=1)
        assert result.shape == [3]
        for v in result.data:
            assert 1 <= v <= 6


class TestFormat:
    def test_format_scalar(self) -> None:
        result = APLArray.scalar(42).format()
        assert result == APLArray.array([2], list("42"))

    def test_format_vector(self) -> None:
        result = APLArray.array([3], [1, 2, 3]).format()
        assert result == APLArray.array([5], list("1 2 3"))


class TestGrade:
    def test_grade_up(self) -> None:
        assert APLArray.array([5], [3, 1, 4, 1, 5]).grade_up(io=1) == APLArray.array([5], [2, 4, 1, 3, 5])

    def test_grade_down(self) -> None:
        assert APLArray.array([5], [3, 1, 4, 1, 5]).grade_down(io=1) == APLArray.array([5], [5, 3, 1, 2, 4])

    def test_grade_up_io0(self) -> None:
        assert APLArray.array([3], [3, 1, 4]).grade_up(io=0) == APLArray.array([3], [1, 0, 2])


class TestIota:
    def test_iota_io1(self) -> None:
        assert APLArray.scalar(5).iota(io=1) == APLArray.array([5], [1, 2, 3, 4, 5])

    def test_iota_io0(self) -> None:
        assert APLArray.scalar(3).iota(io=0) == APLArray.array([3], [0, 1, 2])


class TestTally:
    def test_tally_vector(self) -> None:
        assert APLArray.array([5], [1, 2, 3, 4, 5]).tally() == APLArray.scalar(5)

    def test_tally_scalar(self) -> None:
        assert APLArray.scalar(42).tally() == APLArray.scalar(1)

    def test_tally_matrix(self) -> None:
        assert APLArray.array([3, 4], list(range(12))).tally() == APLArray.scalar(3)


class TestConjugate:
    def test_conjugate_real(self) -> None:
        """For real numbers, conjugate is identity."""
        assert APLArray.scalar(5).conjugate() == APLArray.scalar(5)

    def test_conjugate_vector(self) -> None:
        assert APLArray.array([3], [1, 2, 3]).conjugate() == APLArray.array([3], [1, 2, 3])


class TestSignum:
    def test_signum_positive(self) -> None:
        assert APLArray.scalar(42).signum() == APLArray.scalar(1)

    def test_signum_negative(self) -> None:
        assert APLArray.scalar(-7).signum() == APLArray.scalar(-1)

    def test_signum_zero(self) -> None:
        assert APLArray.scalar(0).signum() == APLArray.scalar(0)

    def test_signum_vector(self) -> None:
        assert APLArray.array([3], [-5, 0, 3]).signum() == APLArray.array([3], [-1, 0, 1])


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


# ── Dyadic functions ──

class TestAdd:
    def test_add_scalars(self) -> None:
        assert APLArray.scalar(3).add(APLArray.scalar(4)) == APLArray.scalar(7)

    def test_add_vectors(self) -> None:
        assert APLArray.array([3], [1, 2, 3]).add(APLArray.array([3], [4, 5, 6])) == APLArray.array([3], [5, 7, 9])

    def test_add_scalar_extension(self) -> None:
        assert APLArray.scalar(10).add(APLArray.array([3], [1, 2, 3])) == APLArray.array([3], [11, 12, 13])


class TestSubtract:
    def test_subtract_scalars(self) -> None:
        assert APLArray.scalar(5).subtract(APLArray.scalar(3)) == APLArray.scalar(2)


class TestMultiply:
    def test_multiply_scalars(self) -> None:
        assert APLArray.scalar(3).multiply(APLArray.scalar(4)) == APLArray.scalar(12)


class TestDivide:
    def test_divide_scalars(self) -> None:
        assert APLArray.scalar(10).divide(APLArray.scalar(4)) == APLArray.scalar(2.5)


class TestMaximum:
    def test_maximum_scalars(self) -> None:
        assert APLArray.scalar(3).maximum(APLArray.scalar(5)) == APLArray.scalar(5)


class TestMinimum:
    def test_minimum_scalars(self) -> None:
        assert APLArray.scalar(3).minimum(APLArray.scalar(5)) == APLArray.scalar(3)


class TestPower:
    def test_power_scalars(self) -> None:
        assert APLArray.scalar(2).power(APLArray.scalar(3)) == APLArray.scalar(8)


class TestLogarithm:
    def test_log_base_10(self) -> None:
        assert APLArray.scalar(10).logarithm(APLArray.scalar(100)) == APLArray.scalar(2)


class TestResidue:
    def test_residue(self) -> None:
        assert APLArray.scalar(3).residue(APLArray.scalar(7)) == APLArray.scalar(1)


class TestCircular:
    def test_sin(self) -> None:
        import math
        result = APLArray.scalar(1).circular(APLArray.scalar(0))
        assert abs(result.data[0]) < 1e-10


class TestBinomial:
    def test_binomial(self) -> None:
        assert APLArray.scalar(2).binomial(APLArray.scalar(5)) == APLArray.scalar(10)


class TestLessThan:
    def test_true(self) -> None:
        assert APLArray.scalar(1).less_than(APLArray.scalar(2)) == APLArray.scalar(1)

    def test_false(self) -> None:
        assert APLArray.scalar(3).less_than(APLArray.scalar(2)) == APLArray.scalar(0)

    def test_vector(self) -> None:
        assert APLArray.array([3], [1, 2, 3]).less_than(APLArray.array([3], [2, 2, 2])) == APLArray.array([3], [1, 0, 0])


class TestLessEqual:
    def test_equal(self) -> None:
        assert APLArray.scalar(2).less_equal(APLArray.scalar(2)) == APLArray.scalar(1)


class TestEqual:
    def test_equal(self) -> None:
        assert APLArray.scalar(5).equal(APLArray.scalar(5)) == APLArray.scalar(1)

    def test_not_equal(self) -> None:
        assert APLArray.scalar(5).equal(APLArray.scalar(3)) == APLArray.scalar(0)


class TestGreaterEqual:
    def test_equal(self) -> None:
        assert APLArray.scalar(2).greater_equal(APLArray.scalar(2)) == APLArray.scalar(1)


class TestGreaterThan:
    def test_true(self) -> None:
        assert APLArray.scalar(3).greater_than(APLArray.scalar(2)) == APLArray.scalar(1)


class TestNotEqual:
    def test_true(self) -> None:
        assert APLArray.scalar(1).not_equal(APLArray.scalar(2)) == APLArray.scalar(1)
