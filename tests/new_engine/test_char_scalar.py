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
