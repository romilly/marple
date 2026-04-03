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
