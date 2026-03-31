"""PicoConsole — Console adapter for Pico serial I/O."""

import sys

from marple.ports.console import Console


class PicoConsole(Console):
    """Console adapter that reads/writes via streams (default: stdin/stdout)."""

    def __init__(self, input: object = None, output: object = None) -> None:
        self._input = input if input is not None else sys.stdin
        self._output = output if output is not None else sys.stdout

    def read_line(self, prompt: str) -> str | None:
        if prompt:
            self._output.write(prompt)
            self._output.flush()
        line = self._input.readline()
        if not line:
            return None
        return line.rstrip("\n")

    def write(self, text: str) -> None:
        self._output.write(text)
        self._output.flush()

    def writeln(self, text: str) -> None:
        self._output.write(text + "\n")
        self._output.flush()
