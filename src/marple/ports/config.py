"""Config port — abstract interface for platform configuration."""

from abc import ABC, abstractmethod


class Config(ABC):
    """Port for reading platform-specific configuration."""

    @abstractmethod
    def get_default_io(self) -> int:
        """Default ⎕IO value (0 or 1)."""
        ...

    @abstractmethod
    def get_workspaces_dir(self) -> str:
        """Root directory for workspace saves."""
        ...

    @abstractmethod
    def get_sessions_dir(self) -> str:
        """Directory for session saves."""
        ...
