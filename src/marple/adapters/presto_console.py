"""PrestoConsole — Console wrapper that mirrors I/O to the Presto LCD."""

from marple.ports.console import Console


class PrestoConsole(Console):
    """Wraps another Console and mirrors input/output to the Presto LCD."""

    def __init__(self, inner: Console, lcd: object) -> None:
        self._inner = inner
        self._lcd = lcd

    def read_line(self, prompt: str) -> str | None:
        line = self._inner.read_line(prompt)
        if line is not None and line.strip():
            self._lcd.show_input(line)  # type: ignore[attr-defined]
        return line

    def write(self, text: str) -> None:
        self._inner.write(text)

    def writeln(self, text: str) -> None:
        self._inner.writeln(text)
        self._lcd.show_output(text)  # type: ignore[attr-defined]
