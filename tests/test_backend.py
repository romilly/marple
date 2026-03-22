import pytest

from marple.backend import HAS_BACKEND, is_numeric_array, to_array, to_list

needs_backend = pytest.mark.skipif(not HAS_BACKEND, reason="no numpy backend")


class TestToArray:
    @needs_backend
    def test_numeric_list_becomes_ndarray(self) -> None:
        result = to_array([1, 2, 3])
        assert is_numeric_array(result)

    @needs_backend
    def test_float_list_becomes_ndarray(self) -> None:
        result = to_array([1.5, 2.5, 3.5])
        assert is_numeric_array(result)

    def test_char_list_stays_list(self) -> None:
        result = to_array(["a", "b", "c"])
        assert isinstance(result, list)
        assert not is_numeric_array(result)

    def test_empty_list_stays_list(self) -> None:
        result = to_array([])
        assert isinstance(result, list)

    @needs_backend
    def test_mixed_int_float_becomes_ndarray(self) -> None:
        result = to_array([1, 2.5, 3])
        assert is_numeric_array(result)

    def test_no_backend_returns_list(self) -> None:
        if HAS_BACKEND:
            pytest.skip("backend is available")
        result = to_array([1, 2, 3])
        assert isinstance(result, list)


class TestToList:
    @needs_backend
    def test_ndarray_to_list(self) -> None:
        arr = to_array([1, 2, 3])
        result = to_list(arr)
        assert isinstance(result, list)
        assert result == [1, 2, 3]

    def test_list_passes_through(self) -> None:
        original = [1, 2, 3]
        assert to_list(original) is original

    def test_char_list_passes_through(self) -> None:
        original = ["a", "b"]
        assert to_list(original) is original
