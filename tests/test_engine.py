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
