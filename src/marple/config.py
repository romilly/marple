"""User configuration for MARPLE.

Reads ~/.marple/config.ini if it exists. Example:

    [defaults]
    io = 0

    [paths]
    workspaces = ~/marple-workspaces
    sessions = ~/marple-sessions
"""
import os
from configparser import ConfigParser


_CONFIG_DIR = os.path.expanduser("~/.marple")
_CONFIG_PATH = os.path.join(_CONFIG_DIR, "config.ini")

_config = ConfigParser()
if os.path.exists(_CONFIG_PATH):
    _config.read(_CONFIG_PATH)


def get_default_io() -> int:
    """Default ⎕IO value (0 or 1)."""
    return _config.getint("defaults", "io", fallback=1)


def get_workspaces_dir() -> str:
    """Root directory for workspace saves."""
    path = _config.get("paths", "workspaces", fallback="workspaces")
    return os.path.expanduser(path)


def get_sessions_dir() -> str:
    """Directory for session saves."""
    path = _config.get("paths", "sessions", fallback="sessions")
    return os.path.expanduser(path)
