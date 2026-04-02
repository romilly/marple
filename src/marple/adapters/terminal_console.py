"""TerminalConsole — real Console adapter for interactive terminal use."""

import sys

from marple.ports.console import Console


class TerminalConsole(Console):
    """Console adapter that reads from stdin and writes to stdout.

    Uses GlyphLineEditor with UnixCharSource for backtick→glyph
    translation when running in a Unix terminal. Falls back to
    plain input() otherwise.
    """

    def __init__(self) -> None:
        self._editor = None
        try:
            from marple.adapters.unix_char_source import UnixCharSource
            from marple.terminal import GlyphLineEditor
            if sys.stdin.isatty():
                self._editor = GlyphLineEditor(
                    UnixCharSource(),
                    lambda s: (sys.stdout.write(s), sys.stdout.flush()),
                )
        except ImportError:
            pass

    def read_line(self, prompt: str) -> str | None:
        if self._editor is not None:
            return self._editor.read_line(prompt)
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
