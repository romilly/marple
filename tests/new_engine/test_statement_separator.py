"""Statement separator tests — new engine."""

from marple.numpy_array import S
from marple.engine import Interpreter


class TestStatementSeparator:
    def test_two_statements_returns_last(self) -> None:
        assert Interpreter(io=1).run("3⋄5") == S(5)

    def test_assignment_then_use(self) -> None:
        assert Interpreter(io=1).run("x←3⋄x+1") == S(4)

    def test_multiple_assignments(self) -> None:
        assert Interpreter(io=1).run("x←2⋄y←3⋄x+y") == S(5)
