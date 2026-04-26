"""`arr.is_char()` and `arr.is_numeric()` must be disjoint.

Any APLArray is either character or numeric, never both. A consumer
using `if arr.is_numeric()` as a fast path would silently apply
arithmetic to character codepoints if these predicates overlapped.
"""

from marple.numpy_aplarray import NumpyAPLArray
from marple.backend_functions import str_to_char_array

from marple.adapters.numpy_array_builder import BUILDER


class TestPredicatesDisjoint:
    def test_char_vector_is_char_not_numeric(self) -> None:
        a = BUILDER.apl_array([3], str_to_char_array("abc"))
        assert a.is_char()
        assert not a.is_numeric()

    def test_empty_char_vector_is_char_not_numeric(self) -> None:
        a = BUILDER.apl_array([0], str_to_char_array(""))
        assert a.is_char()
        assert not a.is_numeric()

    def test_int_vector_is_numeric_not_char(self) -> None:
        a = BUILDER.apl_array([3], [1, 2, 3])
        assert a.is_numeric()
        assert not a.is_char()

    def test_float_vector_is_numeric_not_char(self) -> None:
        a = BUILDER.apl_array([2], [1.0, 2.0])
        assert a.is_numeric()
        assert not a.is_char()

    def test_boolean_result_is_numeric_not_char(self) -> None:
        # Results of comparisons are boolean/numeric, never char.
        a = BUILDER.apl_array([3], [1, 2, 3])
        b = BUILDER.apl_array([3], [2, 2, 2])
        result = a.less_than(b)
        assert result.is_numeric()
        assert not result.is_char()
