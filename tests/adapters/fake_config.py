"""FakeConfig — test adapter for Config port."""

from marple.ports.config import Config


class FakeConfig(Config):
    """Config adapter that returns specified values for testing."""

    def __init__(self, io: int = 1,
                 workspaces_dir: str = "workspaces",
                 sessions_dir: str = "sessions") -> None:
        self._io = io
        self._workspaces_dir = workspaces_dir
        self._sessions_dir = sessions_dir

    def get_default_io(self) -> int:
        return self._io

    def get_workspaces_dir(self) -> str:
        return self._workspaces_dir

    def get_sessions_dir(self) -> str:
        return self._sessions_dir
