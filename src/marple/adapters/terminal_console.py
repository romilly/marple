"""TerminalConsole — real Console adapter for interactive terminal use."""

import sys

from marple.ports.console import Console


class TerminalConsole(Console):
    """Console adapter that reads from stdin and writes to stdout."""

    def __init__(self) -> None:
        self._use_terminal = False
        try:
            from marple.terminal import read_line
            if sys.stdin.isatty():
                self._terminal_read_line = read_line
                self._use_terminal = True
        except ImportError:
            pass

    def read_line(self, prompt: str) -> str | None:
        if self._use_terminal:
            return self._terminal_read_line()
        try:
            return input(prompt)
        except (EOFError, KeyboardInterrupt):
            print()
            return None

    def write(self, text: str) -> None:
        sys.stdout.write(text)
        sys.stdout.flush()

    def writeln(self, text: str) -> None:
        print(text)
