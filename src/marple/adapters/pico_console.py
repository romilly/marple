"""PicoConsole — Console adapter for Pico USB-CDC serial I/O.

The Pico speaks a tiny line protocol over its USB-CDC serial:
  - Host sends one line of hex-encoded UTF-8 per expression
  - Pico responds with zero or more output lines
  - Pico emits a single-char sentinel (\\x00) between responses so the
    host knows the response is complete

`read_line` consumes one hex-encoded line; `writeln` / `write` emit raw
text on stdout. The first call does NOT send a sentinel (there's no prior
response to terminate); subsequent calls do.
"""

import sys
from typing import Any

from marple.ports.console import Console


SENTINEL = "\x00"


class PicoConsole(Console):
    """Console adapter for Pico serial I/O."""

    def __init__(self, input: Any = None, output: Any = None) -> None:
        self._input: Any = input if input is not None else sys.stdin
        self._output: Any = output if output is not None else sys.stdout
        self._first_read = True

    def _println(self, text: str) -> None:
        print(text, file=self._output)

    def read_line(self, prompt: str) -> str | None:
        if not self._first_read:
            self._println(SENTINEL)
        self._first_read = False
        raw = self._input.readline()
        if not raw:
            return None
        raw = raw.strip()
        if not raw:
            return ""
        try:
            return bytes.fromhex(raw).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return raw

    def write(self, text: str) -> None:
        print(text, end="", file=self._output)

    def writeln(self, text: str) -> None:
        self._println(text)
