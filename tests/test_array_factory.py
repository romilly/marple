"""Tests for APLArray factory methods."""

from marple.arraymodel import APLArray


class TestArrayFactory:
    def test_array_creates_vector(self) -> None:
        result = APLArray.array([3], [1, 2, 3])
        assert result == APLArray([3], [1, 2, 3])


class TestScalarFactory:
    def test_scalar_creates_scalar(self) -> None:
        result = APLArray.scalar(5)
        assert result == APLArray([], [5])
