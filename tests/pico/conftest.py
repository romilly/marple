"""Fixtures for Pico end-to-end tests over USB serial."""

import pytest

from marple.web.pico_bridge import PicoConnection


@pytest.fixture(scope="module")
def pico(request: pytest.FixtureRequest) -> PicoConnection:
    """Provide a PicoConnection for the test module.

    Use --pico-port to specify the serial port (default: /dev/ttyACM0).
    """
    port = request.config.getoption("--pico-port")
    conn = PicoConnection(port)
    yield conn
    conn.close()
