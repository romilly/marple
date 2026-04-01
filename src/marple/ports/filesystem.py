"""FileSystem port — abstract interface for file I/O."""

from abc import ABC, abstractmethod


class FileSystem(ABC):
    """Port for filesystem operations."""

    @abstractmethod
    def read_text(self, path: str) -> str:
        """Read a file and return its contents as a string."""
        ...

    @abstractmethod
    def write_text(self, path: str, content: str) -> None:
        """Write a string to a file, creating or overwriting it."""
        ...

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Return True if the path exists (file or directory)."""
        ...

    @abstractmethod
    def is_file(self, path: str) -> bool:
        """Return True if the path is an existing file."""
        ...

    @abstractmethod
    def is_dir(self, path: str) -> bool:
        """Return True if the path is an existing directory."""
        ...

    @abstractmethod
    def delete(self, path: str) -> None:
        """Delete a file. Raises OSError if not found."""
        ...

    @abstractmethod
    def makedirs(self, path: str) -> None:
        """Create a directory and any missing parents."""
        ...

    @abstractmethod
    def listdir(self, path: str) -> list[str]:
        """List entries in a directory."""
        ...

    @abstractmethod
    def delete_dir(self, path: str) -> None:
        """Delete a directory and all its contents."""
        ...
