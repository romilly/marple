from marple.ports.array import APLArray, S


class TestMonadicScalarFunctions:
    def test_negate_scalar(self) -> None:
        assert S(3).negate() == S(-3)

    def test_negate_vector(self) -> None:
        assert APLArray.array([3], [1, 2, 3]).negate() == APLArray.array([3], [-1, -2, -3])

    def test_reciprocal_scalar(self) -> None:
        assert S(4).reciprocal() == S(0.25)

    def test_ceiling_scalar(self) -> None:
        assert S(2.3).ceiling() == S(3)

    def test_floor_scalar(self) -> None:
        assert S(2.7).floor() == S(2)


class TestDyadicScalarFunctions:
    def test_add_scalars(self) -> None:
        assert S(3).add(S(4)) == S(7)

    def test_add_vectors(self) -> None:
        assert APLArray.array([3], [1, 2, 3]).add(APLArray.array([3], [4, 5, 6])) == APLArray.array(
            [3], [5, 7, 9]
        )

    def test_subtract_scalars(self) -> None:
        assert S(5).subtract(S(3)) == S(2)

    def test_multiply_scalars(self) -> None:
        assert S(3).multiply(S(4)) == S(12)

    def test_divide_scalars(self) -> None:
        assert S(10).divide(S(4)) == S(2.5)

    def test_maximum_scalars(self) -> None:
        assert S(3).maximum(S(5)) == S(5)

    def test_minimum_scalars(self) -> None:
        assert S(3).minimum(S(5)) == S(3)


class TestScalarExtension:
    def test_scalar_plus_vector(self) -> None:
        assert S(10).add(APLArray.array([3], [1, 2, 3])) == APLArray.array([3], [11, 12, 13])

    def test_vector_plus_scalar(self) -> None:
        assert APLArray.array([3], [1, 2, 3]).add(S(10)) == APLArray.array([3], [11, 12, 13])
