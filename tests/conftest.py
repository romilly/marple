"""Shared fixtures for the MARPLE test suite."""

from typing import Any

import pytest

from marple.arraymodel import APLArray
from marple.engine import Interpreter
from marple.interpreter import default_env, interpret


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--pico-port",
        default="/dev/ttyACM0",
        help="Serial port for Pico (default: /dev/ttyACM0)",
    )


class OldEngine:
    """Wraps the old interpret() function."""
    def __init__(self) -> None:
        self.env: dict[str, Any] = default_env()

    def run(self, source: str) -> APLArray:
        return interpret(source, self.env)


class NewEngine:
    """Wraps the new Interpreter class."""
    def __init__(self) -> None:
        self._interp = Interpreter(io=1)

    @property
    def env(self) -> Any:
        return self._interp.env

    def run(self, source: str) -> APLArray:
        return self._interp.run(source)


@pytest.fixture(params=["old", "new"])
def engine(request: pytest.FixtureRequest) -> OldEngine | NewEngine:
    """Provides both old and new engines for dual-engine testing."""
    if request.param == "old":
        return OldEngine()
    return NewEngine()
