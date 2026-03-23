from marple.arraymodel import APLArray, S
from marple.interpreter import interpret, default_env
from marple.parser import Assignment, parse


class TestChainedAssignment:
    def test_chained_assign(self) -> None:
        env = default_env()
        interpret("y←1+x←⍳4", env)
        assert env["x"] == APLArray([4], [1, 2, 3, 4])
        assert env["y"] == APLArray([4], [2, 3, 4, 5])

    def test_assignment_returns_value(self) -> None:
        env = default_env()
        result = interpret("x←5", env)
        assert result == S(5)


class TestSilentAssignment:
    def test_top_level_assignment_is_silent(self) -> None:
        tree = parse("x←5")
        assert isinstance(tree, Assignment)

    def test_expression_is_not_assignment(self) -> None:
        tree = parse("2+3")
        assert not isinstance(tree, Assignment)

    def test_function_on_assignment_is_not_silent(self) -> None:
        # +x←⍳4 should display because + is applied
        tree = parse("+x←⍳4")
        assert not isinstance(tree, Assignment)
