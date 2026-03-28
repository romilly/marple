"""Error trapping tests — new engine."""

from marple.arraymodel import APLArray, S
from marple.engine import Interpreter


class TestEA:
    def test_success(self) -> None:
        assert Interpreter(io=1).run("'0' ⎕EA '2+3'") == S(5)

    def test_failure(self) -> None:
        assert Interpreter(io=1).run("'0' ⎕EA '1÷0'") == S(0)

    def test_error_sets_en(self) -> None:
        i = Interpreter(io=1)
        i.run("'0' ⎕EA '1÷0'")
        result = i.run("⎕EN")
        assert result.data[0] > 0

    def test_error_sets_dm(self) -> None:
        i = Interpreter(io=1)
        i.run("'0' ⎕EA '1÷0'")
        result = i.run("⎕DM")
        assert len(result.data) > 0
