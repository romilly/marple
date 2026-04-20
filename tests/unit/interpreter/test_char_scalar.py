"""Single-character literals must be scalars (rank 0), not 1-vectors.

Every APL (and J) treats `'a'` as a scalar with empty shape. Marple was
wrapping every string literal in a 1-element vector regardless of length,
which broke scalar/rank semantics for character data.
"""

from marple.engine import Interpreter
from marple.numpy_array import APLArray, S


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
        from marple.backend_functions import is_char_array
        result = Interpreter(io=1).run("''")
        assert is_char_array(result.data)

    def test_multi_char_literal_is_uint32(self) -> None:
        # Step 4: non-empty string literals must be uint32 ndarrays.
        from marple.backend_functions import is_char_array
        result = Interpreter(io=1).run("'abc'")
        assert str(result.data.dtype) == 'uint32'
        assert is_char_array(result.data)
        # Codepoints check
        assert list(result.data) == [97, 98, 99]


class TestCharScalarDisplay:
    """Char scalars must format as the character, not the codepoint.

    The uint32 char storage migration (v0.7.15) swapped data[0] from a
    Python str to an int codepoint, but format_result's scalar branch
    never learned to consult is_char_array — so `'a'` has been showing as
    "97" on desktop since that migration. No prior test exercised
    display_text on char scalars, so it slipped through.
    """

    def test_single_char_literal_displays_as_char(self) -> None:
        assert Interpreter(io=1).execute("'a'").display_text == "a"

    def test_indexed_char_scalar_displays_as_char(self) -> None:
        # 'ABCDEF'[3] with ⎕IO=1 is the 3rd char, 'C'.
        assert Interpreter(io=1).execute("'ABCDEF'[3]").display_text == "C"

    def test_char_vector_still_displays_as_string(self) -> None:
        # Rank-1 char arrays weren't affected; this just pins the contract.
        assert Interpreter(io=1).execute("'abc'").display_text == "abc"
