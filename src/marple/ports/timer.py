"""Timer port — abstract interface for time operations."""

from abc import ABC, abstractmethod


class Timer(ABC):
    """Port for time-related operations (⎕TS, ⎕AI, ⎕DL)."""

    @abstractmethod
    def timestamp(self) -> list[int]:
        """Return [year, month, day, hour, min, sec, ms] for ⎕TS."""
        ...

    @abstractmethod
    def elapsed_ms(self) -> int:
        """Milliseconds since session start, for ⎕AI."""
        ...

    @abstractmethod
    def cpu_ms(self) -> int:
        """CPU time in ms, for ⎕AI. 0 if not available."""
        ...

    @abstractmethod
    def user_id(self) -> int:
        """User ID for ⎕AI. 1000 if not available."""
        ...

    @abstractmethod
    def sleep(self, seconds: float) -> float:
        """Sleep and return actual elapsed seconds, for ⎕DL."""
        ...
