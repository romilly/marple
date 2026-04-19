"""Error trapping tests — new engine."""

import pytest

from marple.numpy_array import APLArray, S
from marple.engine import Interpreter
from marple.errors import DomainError


class TestDivisionByZero:
    def test_divide_by_zero_raises(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).run("1÷0")


class TestEA:
    def test_success(self) -> None:
        assert Interpreter(io=1).run("'0' ⎕EA '2+3'") == S(5)

    def test_failure(self) -> None:
        assert Interpreter(io=1).run("'0' ⎕EA '1÷0'") == S(0)

    def test_failure_with_expression_alternate(self) -> None:
        assert Interpreter(io=1).run("'42' ⎕EA '1÷0'") == S(42)

    def test_error_sets_en(self) -> None:
        i = Interpreter(io=1)
        i.run("'0' ⎕EA '1÷0'")
        result = i.run("⎕EN")
        assert result.data.item() > 0

    def test_error_sets_dm(self) -> None:
        i = Interpreter(io=1)
        i.run("'0' ⎕EA '1÷0'")
        result = i.run("⎕DM")
        assert len(result.data) > 0


class TestEN:
    def test_fresh_session(self) -> None:
        assert Interpreter(io=1).run("⎕EN") == S(0)

    def test_after_error(self) -> None:
        i = Interpreter(io=1)
        i.run("'0' ⎕EA '1÷0'")
        assert i.run("⎕EN") == S(3)  # DomainError

    def test_not_reset_by_success(self) -> None:
        i = Interpreter(io=1)
        i.run("'0' ⎕EA '1÷0'")
        i.run("'0' ⎕EA '2+3'")
        assert i.run("⎕EN") == S(3)

    def test_index_error_code(self) -> None:
        i = Interpreter(io=1)
        i.run("'0' ⎕EA '10⌷⍳5'")
        assert i.run("⎕EN") == S(6)  # IndexError_

    def test_length_error_code(self) -> None:
        i = Interpreter(io=1)
        i.run("'0' ⎕EA '1 2+1 2 3'")
        assert i.run("⎕EN") == S(4)  # LengthError

    def test_en_via_ea(self) -> None:
        i = Interpreter(io=1)
        result = i.run("'⎕EN' ⎕EA '1÷0'")
        assert result == S(3)
