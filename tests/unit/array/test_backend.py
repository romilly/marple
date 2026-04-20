import pytest

from marple.get_numpy import np
from marple.backend_functions import (
    is_numeric_array, to_array,
    str_to_char_array, char_fill,
)


class TestToArray:

    def test_numeric_list_becomes_ndarray(self) -> None:
        result = to_array([1, 2, 3])
        assert is_numeric_array(result)


    def test_float_list_becomes_ndarray(self) -> None:
        result = to_array([1.5, 2.5, 3.5])
        assert is_numeric_array(result)

    def test_empty_list_becomes_numpy(self) -> None:
        result = to_array([])
        assert is_numeric_array(result)


    def test_mixed_int_float_becomes_ndarray(self) -> None:
        result = to_array([1, 2.5, 3])
        assert is_numeric_array(result)


    def test_int_list_preserves_int_type(self) -> None:
        result = to_array([1, 2, 3])
        # Elements should remain integers, not become floats
        assert isinstance(result.tolist()[0], int)


    def test_large_int_does_not_overflow_to_int16(self) -> None:
        result = to_array([40000])
        # 40000 exceeds int16 range — must not silently wrap
        assert result.tolist()[0] == 40000


    def test_int_within_range_stays_int(self) -> None:
        result = to_array([100])
        assert isinstance(result.tolist()[0], int)

class TestStrToCharArray:

    def test_basic(self) -> None:
        result = str_to_char_array("ABC")
        assert str(result.dtype) == "uint32"
        assert list(result) == [65, 66, 67]

    def test_empty(self) -> None:
        result = str_to_char_array("")
        assert str(result.dtype) == "uint32"
        assert len(result) == 0

    def test_unicode(self) -> None:
        result = str_to_char_array("⍳")
        assert list(result) == [ord("⍳")]


class TestCharFill:

    def test_is_space_codepoint(self) -> None:
        assert int(char_fill()) == 32

    def test_roundtrips_to_active_char_dtype(self) -> None:
        from marple.backend_functions import get_char_dtype
        arr = np.array([char_fill()], dtype=get_char_dtype())
        assert arr.dtype == get_char_dtype()
        assert int(arr[0]) == 32
