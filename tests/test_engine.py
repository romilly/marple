from unittest.mock import patch

from marple.arraymodel import APLArray, S
from marple.engine import Interpreter


class TestConstruction:
    @patch("marple.config.get_default_io", return_value=1)
    def test_construct_default(self, _mock_io: object) -> None:
        interp = Interpreter()
        assert interp.env["⎕IO"] == S(1)

    def test_construct_io_zero(self) -> None:
        interp = Interpreter(io=0)
        assert interp.env["⎕IO"] == S(0)


class TestRun:
    def test_run_scalar(self) -> None:
        interp = Interpreter(io=1)
        result = interp.run("2+3")
        assert result == S(5)

    def test_run_iota_io1(self) -> None:
        interp = Interpreter(io=1)
        result = interp.run("⍳3")
        assert result == APLArray([3], [1, 2, 3])

    def test_run_iota_io0(self) -> None:
        interp = Interpreter(io=0)
        result = interp.run("⍳3")
        assert result == APLArray([3], [0, 1, 2])


class TestAssignmentAndState:
    def test_assignment_persists(self) -> None:
        interp = Interpreter(io=1)
        interp.run("x←5")
        result = interp.run("x+1")
        assert result == S(6)

    def test_instances_isolated(self) -> None:
        a = Interpreter(io=1)
        b = Interpreter(io=1)
        a.run("x←99")
        result = b.run("⎕NC 'x'")
        assert result == S(0)

class TestSystemFunctions:
    def test_quad_ts(self) -> None:
        interp = Interpreter(io=1)
        result = interp.run("⎕TS")
        assert result.shape == [7]

    def test_quad_nl(self) -> None:
        interp = Interpreter(io=1)
        interp.run("foo←{⍵+1}")
        interp.run("bar←{⍵×2}")
        result = interp.run("⎕NL 3")
        assert result.shape[0] == 2

    def test_quad_ex(self) -> None:
        interp = Interpreter(io=1)
        interp.run("x←42")
        interp.run("⎕EX 'x'")
        result = interp.run("⎕NC 'x'")
        assert result == S(0)

    def test_dfn_definition(self) -> None:
        interp = Interpreter(io=1)
        interp.run("double←{⍵+⍵}")
        result = interp.run("double 3")
        assert result == S(6)


class TestOperators:
    def test_reduce(self) -> None:
        interp = Interpreter(io=1)
        result = interp.run("+/⍳5")
        assert result == S(15)
