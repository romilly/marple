"""DesktopConfig — reads configuration from ~/.marple/config.ini."""

import os
from configparser import ConfigParser

from marple.ports.config import Config


class DesktopConfig(Config):
    """Config adapter that reads from an INI file using ConfigParser."""

    def __init__(self, path: str | None = None) -> None:
        if path is None:
            path = os.path.join(os.path.expanduser("~"), ".marple", "config.ini")
        self._parser = ConfigParser()
        if os.path.exists(path):
            self._parser.read(path)

    def get_default_io(self) -> int:
        return self._parser.getint("defaults", "io", fallback=1)

    def get_workspaces_dir(self) -> str:
        path = self._parser.get("paths", "workspaces", fallback="workspaces")
        return os.path.expanduser(path)

    def get_sessions_dir(self) -> str:
        path = self._parser.get("paths", "sessions", fallback="sessions")
        return os.path.expanduser(path)
