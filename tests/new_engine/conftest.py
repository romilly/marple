"""Shared fixtures for new engine tests."""

import pytest

from marple.engine import Interpreter


@pytest.fixture
def interp() -> Interpreter:
    """Fresh Interpreter with ⎕IO=1."""
    return Interpreter(io=1)


@pytest.fixture
def interp_io0() -> Interpreter:
    """Fresh Interpreter with ⎕IO=0."""
    return Interpreter(io=0)
