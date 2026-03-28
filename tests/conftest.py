"""Shared fixtures for the MARPLE test suite."""

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--pico-port",
        default="/dev/ttyACM0",
        help="Serial port for Pico (default: /dev/ttyACM0)",
    )
