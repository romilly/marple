"""PicoConsole — Console adapter for Pico serial I/O.

Handles hex-encoded UTF-8 input and sentinel framing for the
serial protocol used by PicoConnection on the host.
"""

import sys

from marple.ports.console import Console


SENTINEL = "\x00"


class PicoConsole(Console):
    """Console adapter for Pico serial I/O.

    read_line: reads hex-encoded UTF-8 from input, sends sentinel
    before each read (except the first) to signal response complete.
    writeln/write: writes text to output.
    """

    def __init__(self, input: object = None, output: object = None) -> None:
        self._input = input if input is not None else sys.stdin
        self._output = output if output is not None else sys.stdout
        self._needs_sentinel = False

    def _println(self, text: str) -> None:
        """Write a line using print() to self._output for reliable serial output."""
        print(text, file=self._output)

    def read_line(self, prompt: str) -> str | None:
        if self._needs_sentinel:
            self._println(SENTINEL)
            self._needs_sentinel = False
        raw = self._input.readline()
        if not raw:
            return None
        raw = raw.strip()
        if not raw:
            # Empty line — mark that a sentinel is needed, return empty
            self._needs_sentinel = True
            return ""
        try:
            return bytes.fromhex(raw).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return raw

    def write(self, text: str) -> None:
        print(text, end="", file=self._output)

    def writeln(self, text: str) -> None:
        self._println(text)
        self._needs_sentinel = True
