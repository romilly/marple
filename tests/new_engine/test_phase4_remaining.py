"""Phase 4 remaining function tests — new engine."""

from marple.numpy_array import APLArray, S
from marple.engine import Interpreter


class TestExecute:
    def test_execute_expression(self) -> None:
        assert Interpreter(io=1).run("⍎'2+3'") == S(5)

    def test_execute_with_variable(self) -> None:
        i = Interpreter(io=1)
        i.run("x←10")
        assert i.run("⍎'x+5'") == S(15)


class TestFormat:
    def test_format_scalar(self) -> None:
        from marple.backend_functions import chars_to_str
        result = Interpreter(io=1).run("⍕42")
        assert chars_to_str(result.data) == "42"

    def test_format_vector(self) -> None:
        from marple.backend_functions import chars_to_str
        result = Interpreter(io=1).run("⍕1 2 3")
        assert chars_to_str(result.data) == "1 2 3"

    def test_format_whole_number_float(self) -> None:
        from marple.backend_functions import chars_to_str
        result = Interpreter(io=1).run("⍕1.0")
        assert chars_to_str(result.data) == "1"

    def test_format_vector_of_floats(self) -> None:
        from marple.backend_functions import chars_to_str
        i = Interpreter(io=1)
        i.run("v←1.0 2.0 3.0")
        result = i.run("⍕v")
        assert chars_to_str(result.data) == "1 2 3"

    def test_format_negative_whole_float(self) -> None:
        from marple.backend_functions import chars_to_str
        result = Interpreter(io=1).run("⍕¯3.0")
        assert chars_to_str(result.data) == "¯3"

    def test_dyadic_format_width(self) -> None:
        from marple.backend_functions import chars_to_str
        result = Interpreter(io=1).run("6⍕42")
        assert chars_to_str(result.data) == "    42"

    def test_dyadic_format_width_precision(self) -> None:
        from marple.backend_functions import chars_to_str
        result = Interpreter(io=1).run("8 2⍕3.14159")
        assert chars_to_str(result.data) == "    3.14"

    def test_dyadic_format_vector(self) -> None:
        from marple.backend_functions import chars_to_str
        result = Interpreter(io=1).run("6 2⍕1.5 2.75")
        assert chars_to_str(result.data) == "  1.50  2.75"

    def test_dyadic_format_matrix(self) -> None:
        from marple.backend_functions import chars_to_str
        result = Interpreter(io=1).run("5 2⍕2 3⍴1 2 3 4 5 6")
        assert result.shape == [2, 15]
        assert chars_to_str(result.data[0]) == " 1.00 2.00 3.00"
        assert chars_to_str(result.data[1]) == " 4.00 5.00 6.00"

    def test_dyadic_format_rank3(self) -> None:
        from marple.backend_functions import chars_to_str
        result = Interpreter(io=0).run("5 2⍕2 3 4⍴⍳24")
        assert result.shape == [2, 3, 20]
        # First plane, first row: 0 1 2 3
        assert chars_to_str(result.data[0][0]) == " 0.00 1.00 2.00 3.00"
        # Second plane, last row: 20 21 22 23
        assert chars_to_str(result.data[1][2]) == "20.0021.0022.0023.00"


class TestReplicate:
    def test_compress(self) -> None:
        assert Interpreter(io=1).run("1 0 1 0 1/1 2 3 4 5") == APLArray.array([3], [1, 3, 5])

    def test_replicate(self) -> None:
        assert Interpreter(io=1).run("1 2 3/4 5 6") == APLArray.array([6], [4, 5, 5, 6, 6, 6])

    def test_replicate_scalar_left(self) -> None:
        assert Interpreter(io=1).run("3/1 2 3") == APLArray.array([9], [1, 1, 1, 2, 2, 2, 3, 3, 3])

    def test_replicate_scalar_both(self) -> None:
        assert Interpreter(io=1).run("2/5") == APLArray.array([2], [5, 5])


class TestExpand:
    def test_expand(self) -> None:
        result = Interpreter(io=1).run("1 0 1 0 1\\1 2 3")
        assert result == APLArray.array([5], [1, 0, 2, 0, 3])
