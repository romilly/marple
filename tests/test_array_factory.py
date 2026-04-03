"""Tests for APLArray factory methods."""

from marple.arraymodel import APLArray
from marple.backend import NumpyArray


class TestArrayFactory:
    def test_array_creates_vector(self) -> None:
        result = APLArray.array([3], [1, 2, 3])
        assert isinstance(result, NumpyArray)
        assert result.shape == [3]

    def test_array_creates_correct_data(self) -> None:
        result = APLArray.array([3], [1, 2, 3])
        assert list(result.data) == [1, 2, 3]


class TestScalarFactory:
    def test_scalar_creates_scalar(self) -> None:
        result = APLArray.scalar(5)
        assert isinstance(result, NumpyArray)
        assert result.is_scalar()
        assert result.data[0] == 5
