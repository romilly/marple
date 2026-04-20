"""Format (⍕) tests — monadic and dyadic."""

from marple.engine import Interpreter


class TestFormat:
    def test_format_scalar(self) -> None:
        result = Interpreter(io=1).run("⍕42")
        assert result.as_str() == "42"

    def test_format_vector(self) -> None:
        result = Interpreter(io=1).run("⍕1 2 3")
        assert result.as_str() == "1 2 3"

    def test_format_whole_number_float(self) -> None:
        result = Interpreter(io=1).run("⍕1.0")
        assert result.as_str() == "1"

    def test_format_vector_of_floats(self) -> None:
        i = Interpreter(io=1)
        i.run("v←1.0 2.0 3.0")
        result = i.run("⍕v")
        assert result.as_str() == "1 2 3"

    def test_format_negative_whole_float(self) -> None:
        result = Interpreter(io=1).run("⍕¯3.0")
        assert result.as_str() == "¯3"

    def test_dyadic_format_width(self) -> None:
        result = Interpreter(io=1).run("6⍕42")
        assert result.as_str() == "    42"

    def test_dyadic_format_width_precision(self) -> None:
        result = Interpreter(io=1).run("8 2⍕3.14159")
        assert result.as_str() == "    3.14"

    def test_dyadic_format_vector(self) -> None:
        result = Interpreter(io=1).run("6 2⍕1.5 2.75")
        assert result.as_str() == "  1.50  2.75"

    def test_dyadic_format_matrix(self) -> None:
        result = Interpreter(io=1).run("5 2⍕2 3⍴1 2 3 4 5 6")
        assert result.shape == [2, 15]
        assert result.slice_axis(0, 0).as_str() == " 1.00 2.00 3.00"
        assert result.slice_axis(0, 1).as_str() == " 4.00 5.00 6.00"

    def test_dyadic_format_rank3(self) -> None:
        result = Interpreter(io=0).run("5 2⍕2 3 4⍴⍳24")
        assert result.shape == [2, 3, 20]
        # First plane, first row: 0 1 2 3
        assert result.slice_axis(0, 0).slice_axis(0, 0).as_str() == " 0.00 1.00 2.00 3.00"
        # Second plane, last row: 20 21 22 23
        assert result.slice_axis(0, 1).slice_axis(0, 2).as_str() == "20.0021.0022.0023.00"
