"""Console port — abstract interface for REPL I/O."""

from abc import ABC, abstractmethod


class Console(ABC):
    """Port for reading user input and writing output."""

    @abstractmethod
    def read_line(self, prompt: str) -> str | None:
        """Read a line of input. Returns None on EOF."""
        ...

    @abstractmethod
    def write(self, text: str) -> None:
        """Write text without a trailing newline."""
        ...

    @abstractmethod
    def writeln(self, text: str) -> None:
        """Write text followed by a newline."""
        ...
