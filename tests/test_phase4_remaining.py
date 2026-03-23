from marple.arraymodel import APLArray, S
from marple.interpreter import interpret, default_env


class TestExecute:
    def test_execute_expression(self) -> None:
        # ⍎'2+3' → 5
        assert interpret("⍎'2+3'") == S(5)

    def test_execute_with_variable(self) -> None:
        env = default_env()
        interpret("x←10", env)
        assert interpret("⍎'x+5'", env) == S(15)


class TestFormat:
    def test_format_scalar(self) -> None:
        # ⍕42 → character vector '42'
        result = interpret("⍕42")
        assert result.data == list("42")

    def test_format_vector(self) -> None:
        result = interpret("⍕1 2 3")
        assert result.data == list("1 2 3")


    def test_dyadic_format_width(self) -> None:
        # 6⍕42 → '    42' (right-aligned in field of width 6)
        result = interpret("6⍕42")
        assert result.data == list("    42")

    def test_dyadic_format_width_precision(self) -> None:
        # 8 2⍕3.14159 → '    3.14' (width 8, 2 decimal places)
        result = interpret("8 2⍕3.14159")
        assert result.data == list("    3.14")

    def test_dyadic_format_vector(self) -> None:
        # 6 2⍕1.5 2.75 → two formatted numbers
        result = interpret("6 2⍕1.5 2.75")
        assert "".join(result.data) == "  1.50  2.75"


class TestReplicate:
    def test_compress(self) -> None:
        # 1 0 1 0 1/1 2 3 4 5 → 1 3 5
        assert interpret("1 0 1 0 1/1 2 3 4 5") == APLArray([3], [1, 3, 5])

    def test_replicate(self) -> None:
        # 1 2 3/4 5 6 → 4 5 5 6 6 6
        assert interpret("1 2 3/4 5 6") == APLArray([6], [4, 5, 5, 6, 6, 6])


class TestExpand:
    def test_expand(self) -> None:
        # 1 0 1 0 1\1 2 3 → 1 0 2 0 3
        result = interpret(r"1 0 1 0 1\1 2 3")
        assert result == APLArray([5], [1, 0, 2, 0, 3])
