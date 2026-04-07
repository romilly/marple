"""to_array(..., dtype_hint='char') for empty character arrays.

Step 2 of the character uint32 migration plan
(plan/plan-char-uint32-migration.md). The empty case loses type
information — to_array([]) cannot tell empty-char from empty-numeric.
The dtype_hint parameter lets creation sites that *know* they're
producing characters say so.
"""

from marple.backend_functions import to_array
from marple.get_numpy import np


class TestToArrayDtypeHint:
    def test_empty_with_char_hint_is_uint32(self) -> None:
        result = to_array([], dtype_hint='char')
        assert hasattr(result, 'dtype')
        assert str(result.dtype) == 'uint32'
        assert len(result) == 0

    def test_empty_without_hint_unchanged(self) -> None:
        # Existing behaviour: empty input with no hint stays as before.
        result = to_array([])
        assert hasattr(result, 'dtype')
        # Default empty produces a float64 array (current behaviour).
        assert str(result.dtype) != 'uint32'

    def test_nonempty_numeric_with_no_hint_unchanged(self) -> None:
        result = to_array([1, 2, 3])
        assert hasattr(result, 'dtype')
        assert 'int' in str(result.dtype) or 'float' in str(result.dtype)
