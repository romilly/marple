"""Serial bridge to a Pico running MARPLE.

CPython-only host-side adapter. Wraps a pyserial connection and speaks
the Pico's eval protocol: hex-encoded UTF-8 expressions, hex-echo from
the Pico, sentinel `\\x00` between responses.

Not deployed to the Pico (pyserial is not available on MicroPython).
"""

import time

import serial


class PicoConnection:
    """Wraps a serial connection to a Pico running MARPLE."""

    SENTINEL = "\x00"

    def __init__(self, port: str, baud: int = 115200, timeout: float = 60) -> None:
        self.ser = self._connect(port, baud, timeout)
        self._wait_ready()

    @staticmethod
    def _connect(port: str, baud: int, timeout: float) -> serial.Serial:
        """Connect to the Pico, retrying until the port appears."""
        ports = [port]
        if "ACM0" in port:
            ports.append(port.replace("ACM0", "ACM1"))
        elif "ACM1" in port:
            ports.append(port.replace("ACM1", "ACM0"))
        deadline = time.time() + timeout
        while time.time() < deadline:
            for p in ports:
                try:
                    return serial.Serial(p, baud, timeout=timeout)
                except serial.SerialException:
                    pass
            time.sleep(0.5)
        raise serial.SerialException(f"Could not connect to Pico on {port}")

    PROBE_RETRIES = 12  # ~60s total with 5s readline timeout

    def _wait_ready(self) -> None:
        """Probe the Pico until the eval loop responds.

        Sends an empty line and waits for the sentinel. Retries to handle
        the case where the Pico is still booting when the probe is sent.
        """
        for _ in range(self.PROBE_RETRIES):
            self.ser.reset_input_buffer()
            self.ser.write(b"\n")
            self.ser.flush()
            while True:
                raw = self.ser.readline()
                if not raw:
                    break  # readline timeout — retry probe
                line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
                if line == self.SENTINEL:
                    return
        raise TimeoutError("Pico did not respond to probe")

    def eval(self, expr: str) -> str:
        """Send an APL expression and return the response text.

        Returns the joined output lines (excluding the sentinel and
        the hex echo). Raises TimeoutError if no sentinel is received.
        """
        encoded = expr.encode("utf-8").hex()
        self.ser.write((encoded + "\n").encode("ascii"))
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
