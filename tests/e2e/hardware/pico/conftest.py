"""Fixtures for Pico end-to-end tests over USB serial.

Provides a --pico-port option (default /dev/ttyACM0) and auto-skips the
module if no matching serial device is present. The `pico` fixture
creates a PicoConnection for the whole module — the probe is slow so we
amortise it across tests.
"""

from __future__ import annotations

import pathlib
from typing import Generator

import pytest

from marple.adapters.pico_serial import PicoConnection


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--pico-port",
        action="store",
        default="/dev/ttyACM0",
        help="Serial port for the attached Pico (default: /dev/ttyACM0)",
    )


def _port_attached(port: str) -> bool:
    """Check whether the requested port exists, or any /dev/ttyACM* fallback."""
    if pathlib.Path(port).exists():
        return True
    return bool(list(pathlib.Path("/dev").glob("ttyACM*")))


@pytest.fixture(scope="module")
def pico(request: pytest.FixtureRequest) -> Generator[PicoConnection, None, None]:
    port = request.config.getoption("--pico-port")
    if not _port_attached(port):
        pytest.skip(f"No Pico attached at {port}")
    conn = PicoConnection(port)
    yield conn
    conn.close()
