"""Execute (⍎) tests."""

from marple.ports.array import S
from marple.engine import Interpreter


class TestExecute:
    def test_execute_expression(self) -> None:
        assert Interpreter(io=1).run("⍎'2+3'") == S(5)

    def test_execute_with_variable(self) -> None:
        i = Interpreter(io=1)
        i.run("x←10")
        assert i.run("⍎'x+5'") == S(15)
