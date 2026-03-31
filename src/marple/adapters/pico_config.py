"""PicoConfig — reads configuration from a Python dict."""

from marple.ports.config import Config


class PicoConfig(Config):
    """Config adapter for MicroPython. Reads from a Python dict."""

    def __init__(self, settings: dict[str, int | str] | None = None) -> None:
        self._settings: dict[str, int | str] = settings if settings is not None else {}

    def get_default_io(self) -> int:
        return int(self._settings.get("io", 1))

    def get_workspaces_dir(self) -> str:
        return str(self._settings.get("workspaces", "workspaces"))

    def get_sessions_dir(self) -> str:
        return str(self._settings.get("sessions", "sessions"))
