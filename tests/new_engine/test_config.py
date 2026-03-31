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


class TestInterpreterConfig:
    """Interpreter uses Config for default settings."""

    def test_interpreter_uses_config_io(self) -> None:
        from marple.engine import Interpreter
        cfg = FakeConfig(io=0)
        interp = Interpreter(config=cfg)
        assert interp.env.io == 0

    def test_interpreter_io_param_overrides_config(self) -> None:
        from marple.engine import Interpreter
        cfg = FakeConfig(io=0)
        interp = Interpreter(io=1, config=cfg)
        assert interp.env.io == 1

    def test_interpreter_stores_config(self) -> None:
        from marple.engine import Interpreter
        cfg = FakeConfig()
        interp = Interpreter(config=cfg)
        assert interp.config is cfg


class TestSystemCommandsConfig:
    """System commands use config for workspace directory."""

    def test_lib_uses_config_workspaces_dir(self, tmp_path: object) -> None:
        from pathlib import Path
        from marple.engine import Interpreter
        from marple.system_commands import run_system_command
        ws_dir = Path(str(tmp_path)) / "ws"
        ws_dir.mkdir()
        (ws_dir / "myws").mkdir()
        (ws_dir / "myws" / ".ws").write_text("")
        cfg = FakeConfig(workspaces_dir=str(ws_dir))
        interp = Interpreter(config=cfg)
        output, _ = run_system_command(interp, ")lib")
        assert "myws" in output

    def test_save_uses_config_workspaces_dir(self, tmp_path: object) -> None:
        from pathlib import Path
        from marple.engine import Interpreter
        from marple.system_commands import run_system_command
        ws_dir = Path(str(tmp_path)) / "ws"
        ws_dir.mkdir()
        cfg = FakeConfig(workspaces_dir=str(ws_dir))
        interp = Interpreter(config=cfg)
        interp.run("x←42")
        run_system_command(interp, ")wsid testws")
        output, _ = run_system_command(interp, ")save")
        assert "SAVED" in output
        assert (ws_dir / "testws").is_dir()
