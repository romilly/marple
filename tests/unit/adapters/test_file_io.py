"""File I/O tests via FakeFileSystem — new engine."""

import pytest

from marple.ports.array import APLArray, S, str_to_char_array
from marple.engine import Interpreter
from marple.errors import DomainError
from tests.adapters.fake_filesystem import FakeFileSystem
from marple.adapters.numpy_array_builder import BUILDER


class TestNReadNWrite:
    def test_write_then_read(self) -> None:
        fs = FakeFileSystem()
        i = Interpreter(io=1, fs=fs)
        i.run("'hello world' ⎕NWRITE '/tmp/test.txt'")
        result = i.run("⎕NREAD '/tmp/test.txt'")
        assert result.as_str() == "hello world"

    def test_read_missing_file(self) -> None:
        fs = FakeFileSystem()
        i = Interpreter(io=1, fs=fs)
        with pytest.raises(FileNotFoundError):
            i.run("⎕NREAD '/tmp/nope.txt'")


class TestNExists:
    def test_exists_true(self) -> None:
        fs = FakeFileSystem({"/tmp/yes.txt": "data"})
        i = Interpreter(io=1, fs=fs)
        assert i.run("⎕NEXISTS '/tmp/yes.txt'") == S(1)

    def test_exists_false(self) -> None:
        fs = FakeFileSystem()
        i = Interpreter(io=1, fs=fs)
        assert i.run("⎕NEXISTS '/tmp/no.txt'") == S(0)


class TestNDelete:
    def test_delete_existing(self) -> None:
        fs = FakeFileSystem({"/tmp/del.txt": "bye"})
        i = Interpreter(io=1, fs=fs)
        i.run("⎕NDELETE '/tmp/del.txt'")
        assert i.run("⎕NEXISTS '/tmp/del.txt'") == S(0)

    def test_delete_missing(self) -> None:
        fs = FakeFileSystem()
        i = Interpreter(io=1, fs=fs)
        with pytest.raises(DomainError):
            i.run("⎕NDELETE '/tmp/nope.txt'")


class TestCSV:
    def test_csv_numeric(self) -> None:
        fs = FakeFileSystem({"/data.csv": "x,y\n1,10\n2,20\n3,30\n"})
        i = Interpreter(io=1, fs=fs)
        result = i.run("⎕CSV '/data.csv'")
        assert result == S(3)
        assert i.run("x") == APLArray.array([3], [1, 2, 3])
        assert i.run("y") == APLArray.array([3], [10, 20, 30])

    def test_csv_text(self) -> None:
        fs = FakeFileSystem({"/data.csv": "name,val\nAlice,10\nBob,20\n"})
        i = Interpreter(io=1, fs=fs)
        i.run("⎕CSV '/data.csv'")
        name_result = i.run("name")
        assert name_result.shape[0] == 2
        row0 = name_result.slice_axis(0, 0).as_str().rstrip()
        assert row0 == "Alice"


class TestWorkspaceWithFakeFS:
    def test_save_and_load(self) -> None:
        from marple.workspace import save_workspace, load_workspace
        fs = FakeFileSystem()
        # Save
        i = Interpreter(io=1, fs=fs)
        i.run("x←42")
        i.run("⎕WSID←'test_ws'")
        env_dict: dict[str, object] = {}
        for name in i.env.quad_var_names():
            env_dict[name] = i.env[name]
        for name in i.env.user_names():
            env_dict[name] = i.env[name]
        env_dict["__sources__"] = i.env.sources()
        save_workspace(env_dict, "/ws/test_ws", fs=fs)
        # Load into fresh interpreter
        i2 = Interpreter(io=1, fs=fs)
        load_workspace(i2.env, "/ws/test_ws", evaluate=i2.run, fs=fs)
        assert i2.run("x") == S(42)

    def test_list_workspaces(self) -> None:
        from marple.workspace import save_workspace, list_workspaces
        fs = FakeFileSystem()
        for name in ("alpha", "beta"):
            env: dict[str, object] = {"⎕WSID": BUILDER.apl_array([len(name)], str_to_char_array(name)), "⎕IO": S(1)}
            save_workspace(env, f"/ws/{name}", fs=fs)
        assert sorted(list_workspaces("/ws", fs=fs)) == ["alpha", "beta"]


class TestScriptWithFakeFS:
    def test_run_script(self) -> None:
        from marple.script import run_script
        fs = FakeFileSystem({"/test.apl": "x←10\nx+5\n"})
        output = run_script("/test.apl", fs=fs)
        assert any("15" in line for line in output)
