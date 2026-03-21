from marple.arraymodel import APLArray, S
from marple.functions import (
    add,
    ceiling,
    divide,
    floor,
    maximum,
    minimum,
    multiply,
    negate,
    reciprocal,
    subtract,
)


class TestMonadicScalarFunctions:
    def test_negate_scalar(self) -> None:
        assert negate(S(3)) == S(-3)

    def test_negate_vector(self) -> None:
        assert negate(APLArray([3], [1, 2, 3])) == APLArray([3], [-1, -2, -3])

    def test_reciprocal_scalar(self) -> None:
        assert reciprocal(S(4)) == S(0.25)

    def test_ceiling_scalar(self) -> None:
        assert ceiling(S(2.3)) == S(3)

    def test_floor_scalar(self) -> None:
        assert floor(S(2.7)) == S(2)


class TestDyadicScalarFunctions:
    def test_add_scalars(self) -> None:
        assert add(S(3), S(4)) == S(7)

    def test_add_vectors(self) -> None:
        assert add(APLArray([3], [1, 2, 3]), APLArray([3], [4, 5, 6])) == APLArray(
            [3], [5, 7, 9]
        )

    def test_subtract_scalars(self) -> None:
        assert subtract(S(5), S(3)) == S(2)

    def test_multiply_scalars(self) -> None:
        assert multiply(S(3), S(4)) == S(12)

    def test_divide_scalars(self) -> None:
        assert divide(S(10), S(4)) == S(2.5)

    def test_maximum_scalars(self) -> None:
        assert maximum(S(3), S(5)) == S(5)

    def test_minimum_scalars(self) -> None:
        assert minimum(S(3), S(5)) == S(3)


class TestScalarExtension:
    def test_scalar_plus_vector(self) -> None:
        assert add(S(10), APLArray([3], [1, 2, 3])) == APLArray([3], [11, 12, 13])

    def test_vector_plus_scalar(self) -> None:
        assert add(APLArray([3], [1, 2, 3]), S(10)) == APLArray([3], [11, 12, 13])
