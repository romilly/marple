"""Phase 4 remaining function tests — new engine."""

from marple.arraymodel import APLArray, S
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
        result = Interpreter(io=1).run("⍕42")
        assert result.data == list("42")

    def test_format_vector(self) -> None:
        result = Interpreter(io=1).run("⍕1 2 3")
        assert result.data == list("1 2 3")

    def test_format_whole_number_float(self) -> None:
        result = Interpreter(io=1).run("⍕1.0")
        assert result.data == list("1")

    def test_format_vector_of_floats(self) -> None:
        i = Interpreter(io=1)
        i.run("v←1.0 2.0 3.0")
        result = i.run("⍕v")
        assert result.data == list("1 2 3")

    def test_format_negative_whole_float(self) -> None:
        result = Interpreter(io=1).run("⍕¯3.0")
        assert result.data == list("¯3")

    def test_dyadic_format_width(self) -> None:
        result = Interpreter(io=1).run("6⍕42")
        assert result.data == list("    42")

    def test_dyadic_format_width_precision(self) -> None:
        result = Interpreter(io=1).run("8 2⍕3.14159")
        assert result.data == list("    3.14")

    def test_dyadic_format_vector(self) -> None:
        result = Interpreter(io=1).run("6 2⍕1.5 2.75")
        assert "".join(result.data) == "  1.50  2.75"


class TestReplicate:
    def test_compress(self) -> None:
        assert Interpreter(io=1).run("1 0 1 0 1/1 2 3 4 5") == APLArray([3], [1, 3, 5])

    def test_replicate(self) -> None:
        assert Interpreter(io=1).run("1 2 3/4 5 6") == APLArray([6], [4, 5, 5, 6, 6, 6])

    def test_replicate_scalar_left(self) -> None:
        assert Interpreter(io=1).run("3/1 2 3") == APLArray([9], [1, 1, 1, 2, 2, 2, 3, 3, 3])

    def test_replicate_scalar_both(self) -> None:
        assert Interpreter(io=1).run("2/5") == APLArray([2], [5, 5])


class TestExpand:
    def test_expand(self) -> None:
        result = Interpreter(io=1).run("1 0 1 0 1\\1 2 3")
        assert result == APLArray([5], [1, 0, 2, 0, 3])
