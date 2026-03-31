"""Tests for Config port and adapters."""

import os

import pytest

from marple.adapters.desktop_config import DesktopConfig
from marple.adapters.pico_config import PicoConfig
from marple.ports.config import Config
from tests.adapters.fake_config import FakeConfig


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


class TestFakeConfig:
    """FakeConfig returns constructor arguments."""

    def test_returns_specified_io(self) -> None:
        cfg = FakeConfig(io=0)
        assert cfg.get_default_io() == 0

    def test_returns_specified_workspaces(self) -> None:
        cfg = FakeConfig(workspaces_dir="/tmp/ws")
        assert cfg.get_workspaces_dir() == "/tmp/ws"

    def test_returns_specified_sessions(self) -> None:
        cfg = FakeConfig(sessions_dir="/tmp/sess")
        assert cfg.get_sessions_dir() == "/tmp/sess"

    def test_defaults(self) -> None:
        cfg = FakeConfig()
        assert cfg.get_default_io() == 1
        assert cfg.get_workspaces_dir() == "workspaces"
        assert cfg.get_sessions_dir() == "sessions"


class TestPicoConfig:
    """PicoConfig reads from a Python dict."""

    def test_reads_io_from_dict(self) -> None:
        cfg = PicoConfig({"io": 0})
        assert cfg.get_default_io() == 0

    def test_reads_workspaces_from_dict(self) -> None:
        cfg = PicoConfig({"workspaces": "/data/ws"})
        assert cfg.get_workspaces_dir() == "/data/ws"

    def test_reads_sessions_from_dict(self) -> None:
        cfg = PicoConfig({"sessions": "/data/sess"})
        assert cfg.get_sessions_dir() == "/data/sess"

    def test_defaults_when_empty_dict(self) -> None:
        cfg = PicoConfig({})
        assert cfg.get_default_io() == 1
        assert cfg.get_workspaces_dir() == "workspaces"
        assert cfg.get_sessions_dir() == "sessions"

    def test_defaults_when_no_dict(self) -> None:
        cfg = PicoConfig()
        assert cfg.get_default_io() == 1
