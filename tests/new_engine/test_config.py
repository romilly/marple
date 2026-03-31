"""Tests for Config port and adapters."""

import pytest

from marple.ports.config import Config


class TestConfigABC:
    """Config ABC defines the required interface."""

    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            Config()  # type: ignore[abstract]

    def test_has_get_default_io(self) -> None:
        assert hasattr(Config, "get_default_io")

    def test_has_get_workspaces_dir(self) -> None:
        assert hasattr(Config, "get_workspaces_dir")

    def test_has_get_sessions_dir(self) -> None:
        assert hasattr(Config, "get_sessions_dir")
