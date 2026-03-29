"""FakeConsole — test adapter for Console port."""

from marple.ports.console import Console


class FakeConsole(Console):
    """Console adapter that uses scripted inputs and captures output."""

    def __init__(self, inputs: list[str]) -> None:
        self._inputs = list(inputs)
        self._output: list[str] = []

    def read_line(self, prompt: str) -> str | None:
        if not self._inputs:
            return None
        return self._inputs.pop(0)

    def write(self, text: str) -> None:
        self._output.append(text)

    def writeln(self, text: str) -> None:
        self._output.append(text + "\n")

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
