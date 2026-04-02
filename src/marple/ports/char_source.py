"""CharSource port — abstract interface for raw character input."""

from abc import ABC, abstractmethod


class CharSource(ABC):
    """Port for reading individual characters from an input device."""

    @abstractmethod
    def read_char(self) -> str:
        """Read one character. Returns '' on EOF."""
        ...

    @abstractmethod
    def start(self) -> None:
        """Enter raw mode (if needed). Called before reading."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Restore normal mode. Called after reading."""
        ...
