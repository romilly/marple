"""Tests for NumpyArray — concrete APLArray subclass."""

from marple.backend import APLArray, NumpyArray


class TestNumpyArrayCreation:
    def test_factory_creates_numpy_array(self) -> None:
        result = APLArray.array([3], [1, 2, 3])
        assert isinstance(result, NumpyArray)

    def test_scalar_factory_creates_numpy_array(self) -> None:
        result = APLArray.scalar(5)
        assert isinstance(result, NumpyArray)
