"""Workspace save/load tests — new engine."""

import os
import tempfile

from marple.ports.array import APLArray, S
from marple.backend_functions import str_to_char_array
from marple.engine import Interpreter
from marple.workspace import save_workspace, load_workspace, list_workspaces


def _save_env_as_dict(interp: Interpreter) -> dict[str, object]:
    """Convert an Interpreter's environment to a dict for save_workspace."""
    env = interp.env
    result: dict[str, object] = {}
    for name in env.quad_var_names():
        result[name] = env[name]
    for name in env.user_names():
        result[name] = env[name]
    result["__sources__"] = env.sources()
    return result


class TestSaveWorkspace:
    def test_save_creates_directory(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            ws_dir = os.path.join(root, "test_ws")
            i = Interpreter(io=1)
            i.run("x←42")
            env_dict = _save_env_as_dict(i)
            save_workspace(env_dict, ws_dir)
            assert os.path.isdir(ws_dir)
            assert os.path.isfile(os.path.join(ws_dir, ".ws"))

    def test_save_scalar_variable(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            ws_dir = os.path.join(root, "test_ws")
            i = Interpreter(io=1)
            i.run("x←42")
            env_dict = _save_env_as_dict(i)
            save_workspace(env_dict, ws_dir)
            assert os.path.isfile(os.path.join(ws_dir, "x.apl"))

    def test_save_system_variable(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            ws_dir = os.path.join(root, "test_ws")
            i = Interpreter(io=0)
            env_dict = _save_env_as_dict(i)
            save_workspace(env_dict, ws_dir)
            assert os.path.isfile(os.path.join(ws_dir, "__IO.apl"))


class TestLoadWorkspace:
    def test_load_restores_variable(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            ws_dir = os.path.join(root, "test_ws")
            i = Interpreter(io=1)
            i.run("x←42")
            env_dict = _save_env_as_dict(i)
            save_workspace(env_dict, ws_dir)
            i2 = Interpreter(io=1)
            load_workspace(i2.env, ws_dir, evaluate=i2.run)
            assert i2.run("x") == S(42)

    def test_load_restores_vector(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            ws_dir = os.path.join(root, "test_ws")
            i = Interpreter(io=1)
            i.run("v←1 2 3")
            env_dict = _save_env_as_dict(i)
            save_workspace(env_dict, ws_dir)
            i2 = Interpreter(io=1)
            load_workspace(i2.env, ws_dir, evaluate=i2.run)
            assert i2.run("v") == APLArray.array([3], [1, 2, 3])

    def test_load_restores_dfn(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            ws_dir = os.path.join(root, "test_ws")
            i = Interpreter(io=1)
            i.run("double←{⍵+⍵}")
            env_dict = _save_env_as_dict(i)
            save_workspace(env_dict, ws_dir)
            i2 = Interpreter(io=1)
            load_workspace(i2.env, ws_dir, evaluate=i2.run)
            assert i2.run("double 5") == S(10)

    def test_load_restores_wsid(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            ws_dir = os.path.join(root, "test_ws")
            i = Interpreter(io=1)
            i.run("⎕WSID←'test_ws'")
            env_dict = _save_env_as_dict(i)
            save_workspace(env_dict, ws_dir)
            i2 = Interpreter(io=1)
            load_workspace(i2.env, ws_dir, evaluate=i2.run)
            wsid = i2.run("⎕WSID")
            assert wsid.as_str() == "test_ws"

    def test_load_system_vars_first(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            ws_dir = os.path.join(root, "test_ws")
            i = Interpreter(io=0)
            i.run("x←⍳3")
            env_dict = _save_env_as_dict(i)
            save_workspace(env_dict, ws_dir)
            i2 = Interpreter(io=1)
            load_workspace(i2.env, ws_dir, evaluate=i2.run)
            # ⎕IO should be restored to 0, so x should be 0 1 2
            assert i2.run("x") == APLArray.array([3], [0, 1, 2])


class TestLoadWorkspaceChars:
    def test_save_and_load_char_scalar(self) -> None:
        # Round-trip a single-character literal through save/load.
        # Regression test for the workspace.py bug where char scalars
        # were formatted as their numeric codepoint (e.g. 'a' → 97)
        # via the dead `isinstance(v, str)` branch in _format_value.
        with tempfile.TemporaryDirectory() as root:
            ws_dir = os.path.join(root, "test_ws")
            i = Interpreter(io=1)
            i.run("c←'a'")
            env_dict = _save_env_as_dict(i)
            save_workspace(env_dict, ws_dir)
            i2 = Interpreter(io=1)
            load_workspace(i2.env, ws_dir, evaluate=i2.run)
            assert i2.run("c") == i.run("'a'")

    def test_save_and_load_char_vector(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            ws_dir = os.path.join(root, "test_ws")
            i = Interpreter(io=1)
            i.run("x←'HELLO'")
            env_dict = _save_env_as_dict(i)
            save_workspace(env_dict, ws_dir)
            i2 = Interpreter(io=1)
            load_workspace(i2.env, ws_dir, evaluate=i2.run)
            result = i2.run("x")
            assert result.shape == [5]
            assert result.as_str() == "HELLO"

    def test_save_and_load_char_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            ws_dir = os.path.join(root, "test_ws")
            i = Interpreter(io=1)
            i.run("x←2 3⍴'CATDOG'")
            env_dict = _save_env_as_dict(i)
            save_workspace(env_dict, ws_dir)
            i2 = Interpreter(io=1)
            load_workspace(i2.env, ws_dir, evaluate=i2.run)
            result = i2.run("x")
            assert result.shape == [2, 3]
            assert result.as_str() == "CATDOG"


class TestListWorkspaces:
    def test_list_finds_workspaces(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            for name in ("alpha", "beta"):
                ws_dir = os.path.join(root, name)
                env: dict[str, object] = {"⎕WSID": APLArray([len(name)], str_to_char_array(name)), "⎕IO": S(1)}
                save_workspace(env, ws_dir)
            os.makedirs(os.path.join(root, "notaws"))
            assert sorted(list_workspaces(root)) == ["alpha", "beta"]

    def test_list_empty(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            assert list_workspaces(root) == []
