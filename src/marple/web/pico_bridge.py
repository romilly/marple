"""Serial bridge to a Pico running MARPLE."""

import time

import serial


class PicoConnection:
    """Wraps a serial connection to a Pico running MARPLE."""

    SENTINEL = "\x00"

    def __init__(self, port: str, baud: int = 115200, timeout: float = 10) -> None:
        self.ser = self._connect(port, baud, timeout)
        time.sleep(1)
        self._drain()

    @staticmethod
    def _connect(port: str, baud: int, timeout: float) -> serial.Serial:
        """Try the given port, then the alternate ACM port if it fails."""
        try:
            return serial.Serial(port, baud, timeout=timeout)
        except serial.SerialException:
            if "ACM0" in port:
                alt = port.replace("ACM0", "ACM1")
            elif "ACM1" in port:
                alt = port.replace("ACM1", "ACM0")
            else:
                raise
            return serial.Serial(alt, baud, timeout=timeout)

    def _drain(self) -> None:
        """Discard any buffered output from the Pico."""
        while self.ser.in_waiting:
            self.ser.read(self.ser.in_waiting)
            time.sleep(0.1)

    def eval(self, expr: str) -> str:
        """Send an APL expression and return the response text.

        Returns the joined output lines (excluding the sentinel and
        the hex echo). Raises TimeoutError if no sentinel is received.
        """
        encoded = expr.encode("utf-8").hex()
        self.ser.write((encoded + "\r\n").encode("ascii"))
        self.ser.flush()

        lines: list[str] = []
        while True:
            raw = self.ser.readline()
            if not raw:
                raise TimeoutError(
                    f"Pico did not respond to: {expr!r}\n"
                    f"Partial output: {lines}"
                )
            line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
            if line == self.SENTINEL:
                break
            if line == encoded:
                continue
            lines.append(line)
        return "\n".join(lines)

    def eval_silent(self, expr: str) -> None:
        """Send an expression that produces no output (e.g. assignment).

        Waits for the sentinel. Raises AssertionError if the Pico
        returns an error.
        """
        result = self.eval(expr)
        assert "ERROR" not in result, f"Unexpected error for {expr!r}: {result}"

    def close(self) -> None:
        self.ser.close()
