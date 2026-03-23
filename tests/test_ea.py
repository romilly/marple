from marple.arraymodel import APLArray, S
from marple.errors import DomainError
from marple.interpreter import interpret, default_env
import pytest


class TestDivisionByZero:
    def test_divide_by_zero_raises(self) -> None:
        with pytest.raises(DomainError):
            interpret("1÷0")


class TestQuadEA:
    def test_success_returns_result(self) -> None:
        assert interpret("'0' ⎕EA '2+3'") == S(5)

    def test_failure_returns_alternate(self) -> None:
        assert interpret("'0' ⎕EA '1÷0'") == S(0)

    def test_failure_with_expression_alternate(self) -> None:
        assert interpret("'42' ⎕EA '1÷0'") == S(42)


class TestQuadEN:
    def test_fresh_session(self) -> None:
        env = default_env()
        assert interpret("⎕EN", env) == S(0)

    def test_after_error(self) -> None:
        env = default_env()
        interpret("'0' ⎕EA '1÷0'", env)
        assert interpret("⎕EN", env) == S(3)  # DomainError

    def test_not_reset_by_success(self) -> None:
        env = default_env()
        interpret("'0' ⎕EA '1÷0'", env)
        interpret("'0' ⎕EA '2+3'", env)
        assert interpret("⎕EN", env) == S(3)

    def test_index_error_code(self) -> None:
        env = default_env()
        interpret("'0' ⎕EA '10⌷⍳5'", env)
        assert interpret("⎕EN", env) == S(6)  # IndexError_

    def test_length_error_code(self) -> None:
        env = default_env()
        interpret("'0' ⎕EA '1 2+1 2 3'", env)
        assert interpret("⎕EN", env) == S(4)  # LengthError

    def test_en_via_ea(self) -> None:
        env = default_env()
        result = interpret("'⎕EN' ⎕EA '1÷0'", env)
        assert result == S(3)
