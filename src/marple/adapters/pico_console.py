"""PicoConsole — Console adapter for Pico serial I/O."""

import sys

from marple.ports.console import Console

INPUT_REQUEST = "\x01"


class PicoConsole(Console):
    """Console adapter that reads/writes via streams (default: stdin/stdout).

    For interactive input (⎕/⍞), sends INPUT_REQUEST marker + prompt
    so the client knows to ask the user for input. The client sends
    the response as hex-encoded UTF-8 (matching the eval protocol).
    """

    def __init__(self, input: object = None, output: object = None) -> None:
        self._input = input if input is not None else sys.stdin
        self._output = output if output is not None else sys.stdout

    def read_line(self, prompt: str) -> str | None:
        self._output.write(INPUT_REQUEST + prompt + "\n")
        self._output.flush()
        raw = self._input.readline()
        if not raw:
            return None
        raw = raw.strip()
        try:
            return bytes.fromhex(raw).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return raw

    def write(self, text: str) -> None:
        self._output.write(text)
        self._output.flush()

    def writeln(self, text: str) -> None:
        self._output.write(text + "\n")
        self._output.flush()
