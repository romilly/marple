"""DefaultConfig — hardcoded defaults with no platform dependencies."""

from marple.ports.config import Config


class DefaultConfig(Config):
    """Config adapter that returns hardcoded defaults.

    Safe to import on any platform — no configparser, os.path, or
    other CPython-specific modules.
    """

    def get_default_io(self) -> int:
        return 1

    def get_workspaces_dir(self) -> str:
        return "workspaces"

    def get_sessions_dir(self) -> str:
        return "sessions"
