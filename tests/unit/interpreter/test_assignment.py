"""Assignment tests."""

from marple.ports.array import APLArray, S
from marple.engine import Interpreter
from marple.parser import Assignment, parse


class TestSimpleAssignment:
    def test_scalar_assignment_stores_value(self) -> None:
        i = Interpreter(io=1)
        i.run("x←3")
        assert i.run("x") == S(3)


    def test_vector_assignment_stores_value(self) -> None:
        i = Interpreter(io=1)
        i.run("x←1 2 3")
        assert i.run("x") == APLArray([3], [1, 2, 3])

    def test_char_assignment_stores_value(self) -> None:
        i = Interpreter(io=1)
        i.run("x←'hello'")
        result = i.run("x")
        assert result.shape == [5]
        assert result.as_str() == "hello"


class TestChainedAssignment:
    def test_chained_assign(self) -> None:
        i = Interpreter(io=1)
        i.run("y←1+x←⍳4")
        assert i.run("x") == APLArray([4], [1, 2, 3, 4])
        assert i.run("y") == APLArray([4], [2, 3, 4, 5])

    def test_assignment_returns_value(self) -> None:
        assert Interpreter(io=1).run("x←5") == S(5)


class TestSilentAssignment:
    """Parser-only tests."""
    def test_top_level_assignment_is_silent(self) -> None:
        assert isinstance(parse("x←5"), Assignment)

    def test_expression_is_not_assignment(self) -> None:
        assert not isinstance(parse("2+3"), Assignment)

    def test_function_on_assignment_is_not_silent(self) -> None:
        assert not isinstance(parse("+x←⍳4"), Assignment)
