"""Tests for )DROP system command."""

from marple.engine import Interpreter
from marple.system_commands import run_system_command
from tests.adapters.fake_config import FakeConfig
from tests.adapters.fake_filesystem import FakeFileSystem


class TestDropWorkspace:
    def test_drop_removes_workspace(self) -> None:
        fs = FakeFileSystem({
            "/ws/mywork/.ws": "mywork\n",
            "/ws/mywork/x.apl": "x←42\n",
        })
        cfg = FakeConfig(workspaces_dir="/ws")
        interp = Interpreter(config=cfg, fs=fs)
        output, _ = run_system_command(interp, ")drop mywork")
        assert "mywork" in output
        assert not fs.is_dir("/ws/mywork")

    def test_drop_nonexistent_workspace_errors(self) -> None:
        fs = FakeFileSystem({})
        cfg = FakeConfig(workspaces_dir="/ws")
        interp = Interpreter(config=cfg, fs=fs)
        output, _ = run_system_command(interp, ")drop nosuch")
        assert "ERROR" in output or "not found" in output.lower()

    def test_drop_requires_name(self) -> None:
        fs = FakeFileSystem({})
        cfg = FakeConfig(workspaces_dir="/ws")
        interp = Interpreter(config=cfg, fs=fs)
        output, _ = run_system_command(interp, ")drop")
        assert "ERROR" in output
