"""Tests for Interpreter.execute() API."""

import pytest

from marple.arraymodel import S
from marple.engine import EvalResult, Interpreter
from marple.errors import DomainError


class TestExecuteExpression:
    def test_returns_eval_result(self) -> None:
        r = Interpreter(io=1).execute("2+3")
        assert isinstance(r, EvalResult)

    def test_display_text(self) -> None:
        r = Interpreter(io=1).execute("2+3")
        assert r.display_text == "5"
        assert r.silent is False

    def test_value(self) -> None:
        r = Interpreter(io=1).execute("2+3")
        assert r.value == S(5)


class TestExecuteSilent:
    def test_assignment_is_silent(self) -> None:
        r = Interpreter(io=1).execute("x←42")
        assert r.silent is True
        assert r.display_text == ""

    def test_comment_is_silent(self) -> None:
        r = Interpreter(io=1).execute("⍝ hello")
        assert r.silent is True

    def test_directive_is_silent(self) -> None:
        r = Interpreter(io=1).execute("#import $::str::upper")
        assert r.silent is True

    def test_multi_statement_last_assign(self) -> None:
        r = Interpreter(io=1).execute("x←1 ⋄ y←2")
        assert r.silent is True


class TestExecuteError:
    def test_error_propagates(self) -> None:
        with pytest.raises(DomainError):
            Interpreter(io=1).execute("1÷0")
