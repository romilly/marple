"""Tests for Config port and adapters."""

import os

import pytest

from marple.adapters.desktop_config import DesktopConfig
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


class TestDesktopConfig:
    """DesktopConfig reads from a config.ini file."""

    def test_reads_io_from_file(self, tmp_path: object) -> None:
        from pathlib import Path
        p = Path(str(tmp_path)) / "config.ini"
        p.write_text("[defaults]\nio = 0\n")
        cfg = DesktopConfig(str(p))
        assert cfg.get_default_io() == 0

    def test_reads_workspaces_from_file(self, tmp_path: object) -> None:
        from pathlib import Path
        p = Path(str(tmp_path)) / "config.ini"
        p.write_text("[paths]\nworkspaces = /my/workspaces\n")
        cfg = DesktopConfig(str(p))
        assert cfg.get_workspaces_dir() == "/my/workspaces"

    def test_reads_sessions_from_file(self, tmp_path: object) -> None:
        from pathlib import Path
        p = Path(str(tmp_path)) / "config.ini"
        p.write_text("[paths]\nsessions = /my/sessions\n")
        cfg = DesktopConfig(str(p))
        assert cfg.get_sessions_dir() == "/my/sessions"

    def test_defaults_when_no_file(self) -> None:
        cfg = DesktopConfig("/nonexistent/path/config.ini")
        assert cfg.get_default_io() == 1
        assert cfg.get_workspaces_dir() == "workspaces"
        assert cfg.get_sessions_dir() == "sessions"

    def test_defaults_when_section_missing(self, tmp_path: object) -> None:
        from pathlib import Path
        p = Path(str(tmp_path)) / "config.ini"
        p.write_text("[other]\nfoo = bar\n")
        cfg = DesktopConfig(str(p))
        assert cfg.get_default_io() == 1
