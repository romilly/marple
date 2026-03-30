"""BufferedConsole — captures output for retrieval by PRIDE, Jupyter, etc."""

from marple.ports.console import Console


class BufferedConsole(Console):
    """Console adapter that buffers output for programmatic retrieval."""

    def __init__(self) -> None:
        self._output: list[str] = []

    def read_line(self, prompt: str) -> str | None:
        return None

    def write(self, text: str) -> None:
        self._output.append(text)

    def writeln(self, text: str) -> None:
        self._output.append(text + "\n")

    def clear(self) -> None:
        """Clear the output buffer."""
        self._output.clear()

    @property
    def output(self) -> str:
        """Return all captured output as a single string."""
        return "".join(self._output)

    @property
    def output_lines(self) -> list[str]:
        """Return captured output split into lines (no trailing empties)."""
        text = self.output
        if text.endswith("\n"):
            text = text[:-1]
        return text.split("\n") if text else []
