"""Single-character literals must be scalars (rank 0), not 1-vectors.

Every APL (and J) treats `'a'` as a scalar with empty shape. Marple was
wrapping every string literal in a 1-element vector regardless of length,
which broke scalar/rank semantics for character data.
"""

from marple.engine import Interpreter
from marple.ports.array import APLArray, S


class TestSingleCharIsScalar:
    def test_single_char_literal_is_scalar(self) -> None:
        result = Interpreter(io=1).run("'a'")
        assert result.is_scalar()
        assert result.shape == []

    def test_shape_of_single_char_is_empty(self) -> None:
        # ⍴'a' should be the empty vector (shape of a scalar)
        result = Interpreter(io=1).run("⍴'a'")
        assert result.shape == [0]

    def test_equal_chars_returns_scalar(self) -> None:
        assert Interpreter(io=1).run("'a'='a'") == S(1)

    def test_not_equal_chars_returns_scalar(self) -> None:
        assert Interpreter(io=1).run("'a'≠'b'") == S(1)

    def test_less_than_chars_returns_scalar(self) -> None:
        assert Interpreter(io=1).run("'a'<'b'") == S(1)

    def test_multi_char_literal_is_vector(self) -> None:
        # 'ab' must remain a 2-vector
        result = Interpreter(io=1).run("'ab'")
        assert result.shape == [2]

    def test_empty_string_literal(self) -> None:
        # '' must remain a 0-element character vector, not a scalar
        result = Interpreter(io=1).run("''")
        assert result.shape == [0]

    def test_empty_string_is_char_array(self) -> None:
        # '' is character data, not numeric. Empty string used to silently
        # produce a float64 empty array — this pins Step 2 of the migration.
        result = Interpreter(io=1).run("''")
        assert result.is_char()

    def test_multi_char_literal_is_char(self) -> None:
        # Non-empty string literals must be character data.
        result = Interpreter(io=1).run("'abc'")
        assert result.is_char()
        assert result.as_str() == "abc"


class TestCharScalarSemantics:
    """Char scalars extracted by indexing must match char literals.

    The underlying storage for `'ABCDEF'[3]` and `'C'` should be
    identical: both scalar (shape []), both char-dtype (uint32 on
    numpy / uint16 on ulab), both holding codepoint 67. Tests use APL
    `≡` rather than display strings — ≡ compares structure + value,
    independent of how format_result chooses to render the result.
    """

    def test_indexed_char_scalar_matches_char_literal(self) -> None:
        # 'ABCDEF'[3] with ⎕IO=1 is the 3rd char, 'C'.
        assert Interpreter(io=1).run("'ABCDEF'[3] ≡ 'C'") == S(1)

    def test_indexed_char_scalar_equals_char_literal(self) -> None:
        # = is element-wise equality; on scalars it's the same as ≡.
        assert Interpreter(io=1).run("'ABCDEF'[3] = 'C'") == S(1)

    def test_indexed_char_scalar_distinct_from_codepoint(self) -> None:
        # A char scalar holding codepoint 67 is NOT equal to the integer
        # 67 — mixed-type comparison via = must reject (DomainError) or
        # return false, not accidentally succeed on numeric identity.
        # Use ≡ which returns 0 for differing dtypes rather than erroring.
        assert Interpreter(io=1).run("'ABCDEF'[3] ≡ 67") == S(0)
