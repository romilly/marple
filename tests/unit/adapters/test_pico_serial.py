"""Unit tests for PicoConnection's readiness probe.

Uses a FakeSerial test double so the tests run on desktop without hardware.
Hardware-dependent tests live under tests/e2e/hardware/pico/.
"""

from marple.adapters.pico_serial import PicoConnection


class FakeSerial:
    """Simulates a pyserial Serial port for testing PicoConnection."""

    def __init__(self, responses: list[bytes]) -> None:
        self._responses = list(responses)
        self._written: list[bytes] = []

    def readline(self) -> bytes:
        if not self._responses:
            return b""
        return self._responses.pop(0)

    def write(self, data: bytes) -> int:
        self._written.append(data)
        return len(data)

    def flush(self) -> None:
        pass

    def reset_input_buffer(self) -> None:
        pass

    def close(self) -> None:
        pass


class TestWaitReady:
    def test_ready_on_sentinel_response(self) -> None:
        fake = FakeSerial([b"\x00\r\n"])
        conn = PicoConnection.__new__(PicoConnection)
        conn.ser = fake  # type: ignore[assignment]
        conn._wait_ready()
        assert any(b"\n" in w for w in fake._written)

    def test_ready_after_boot_messages(self) -> None:
        fake = FakeSerial([
            b"MicroPython v1.24.1\r\n",
            b"Type 'help()' for more info.\r\n",
            b"\x00\r\n",
        ])
        conn = PicoConnection.__new__(PicoConnection)
        conn.ser = fake  # type: ignore[assignment]
        conn._wait_ready()

    def test_timeout_when_no_response(self) -> None:
        fake = FakeSerial([])
        conn = PicoConnection.__new__(PicoConnection)
        conn.ser = fake  # type: ignore[assignment]
        try:
            conn._wait_ready()
            assert False, "Should have raised TimeoutError"
        except TimeoutError:
            pass
