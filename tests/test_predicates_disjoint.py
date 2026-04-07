"""is_numeric_array and is_char_array must be disjoint.

Step 3 of the character uint32 migration plan
(plan/plan-char-uint32-migration.md). Once character data is stored
as uint32 ndarrays, the two predicates need to partition the data
cleanly: any uint32 array is character data, never numeric. Otherwise
consumers using `if is_numeric_array(...)` as a fast path will silently
apply arithmetic to character codepoints.
"""

from marple.backend_functions import is_char_array, is_ndarray, is_numeric_array
from marple.get_numpy import np


class TestPredicatesDisjoint:
    def test_uint32_is_char_not_numeric(self) -> None:
        data = np.array([97, 98, 99], dtype=np.uint32)
        assert is_char_array(data)
        assert not is_numeric_array(data)

    def test_empty_uint32_is_char_not_numeric(self) -> None:
        data = np.array([], dtype=np.uint32)
        assert is_char_array(data)
        assert not is_numeric_array(data)

    def test_int64_is_numeric_not_char(self) -> None:
        data = np.array([1, 2, 3], dtype=np.int64)
        assert is_numeric_array(data)
        assert not is_char_array(data)

    def test_float64_is_numeric_not_char(self) -> None:
        data = np.array([1.0, 2.0], dtype=np.float64)
        assert is_numeric_array(data)
        assert not is_char_array(data)

    def test_int32_is_numeric_not_char(self) -> None:
        data = np.array([1, 2], dtype=np.int32)
        assert is_numeric_array(data)
        assert not is_char_array(data)

    def test_uint8_bool_is_numeric_not_char(self) -> None:
        # Boolean results use uint8 — must remain numeric.
        data = np.array([0, 1, 1], dtype=np.uint8)
        assert is_numeric_array(data)
        assert not is_char_array(data)



class TestIsNdarray:
    """is_ndarray answers the layout question: 'can I call .flatten() on it'.

    It is True for *any* ndarray (numeric or uint32 char), False for
    Python lists. Use is_ndarray for shape/order operations; use
    is_numeric_array for arithmetic dispatch.
    """

    def test_int64_is_ndarray(self) -> None:
        assert is_ndarray(np.array([1, 2], dtype=np.int64))

    def test_float64_is_ndarray(self) -> None:
        assert is_ndarray(np.array([1.0], dtype=np.float64))

    def test_uint32_is_ndarray(self) -> None:
        assert is_ndarray(np.array([97], dtype=np.uint32))

    def test_uint8_is_ndarray(self) -> None:
        assert is_ndarray(np.array([0, 1], dtype=np.uint8))

    def test_list_of_str_is_not_ndarray(self) -> None:
        assert not is_ndarray(['a', 'b'])

    def test_empty_list_is_not_ndarray(self) -> None:
        assert not is_ndarray([])

    def test_python_list_of_int_is_not_ndarray(self) -> None:
        assert not is_ndarray([1, 2, 3])
