"""Tests for PicoConnection readiness probing."""

import io

from marple.web.pico_bridge import PicoConnection


class FakeSerial:
    """Simulates a serial port for testing PicoConnection."""

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
        """Probing with empty line should succeed when Pico returns sentinel."""
        fake = FakeSerial([b"\x00\r\n"])
        conn = PicoConnection.__new__(PicoConnection)
        conn.ser = fake
        # Should not raise
        conn._wait_ready()
        # Should have sent an empty line as probe
        assert any(b"\r\n" in w for w in fake._written)

    def test_ready_after_boot_messages(self) -> None:
        """Should skip boot messages and succeed when sentinel arrives."""
        fake = FakeSerial([
            b"MicroPython v1.24.1\r\n",
            b"Type 'help()' for more info.\r\n",
            b"\x00\r\n",
        ])
        conn = PicoConnection.__new__(PicoConnection)
        conn.ser = fake
        conn._wait_ready()

    def test_timeout_when_no_response(self) -> None:
        """Should raise TimeoutError if Pico never responds."""
        fake = FakeSerial([])  # No responses — simulates timeout
        conn = PicoConnection.__new__(PicoConnection)
        conn.ser = fake
        try:
            conn._wait_ready()
            assert False, "Should have raised TimeoutError"
        except TimeoutError:
            pass
