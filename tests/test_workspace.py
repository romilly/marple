import os
import tempfile

from marple.arraymodel import APLArray, S
from marple.interpreter import interpret
from marple.workspace import save_workspace, load_workspace, list_workspaces


class TestSaveWorkspace:
    def test_save_creates_directory(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            ws_dir = os.path.join(root, "test_ws")
            env: dict[str, object] = {"__wsid__": "test_ws", "⎕IO": S(1), "x": S(42)}
            save_workspace(env, ws_dir)
            assert os.path.isdir(ws_dir)
            assert os.path.isfile(os.path.join(ws_dir, ".ws"))

    def test_save_scalar_variable(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            ws_dir = os.path.join(root, "test_ws")
            env: dict[str, object] = {"__wsid__": "test_ws", "⎕IO": S(1), "x": S(42)}
            save_workspace(env, ws_dir)
            assert os.path.isfile(os.path.join(ws_dir, "x.apl"))

    def test_save_system_variable(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            ws_dir = os.path.join(root, "test_ws")
            env: dict[str, object] = {"__wsid__": "test_ws", "⎕IO": S(0)}
            save_workspace(env, ws_dir)
            assert os.path.isfile(os.path.join(ws_dir, "__IO.apl"))


class TestLoadWorkspace:
    def test_load_restores_variable(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            ws_dir = os.path.join(root, "test_ws")
            env: dict[str, object] = {"__wsid__": "test_ws", "⎕IO": S(1), "x": S(42)}
            save_workspace(env, ws_dir)
            new_env: dict[str, object] = {}
            load_workspace(new_env, ws_dir)
            assert new_env["x"] == S(42)

    def test_load_restores_wsid(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            ws_dir = os.path.join(root, "test_ws")
            env: dict[str, object] = {"__wsid__": "test_ws", "⎕IO": S(1)}
            save_workspace(env, ws_dir)
            new_env: dict[str, object] = {}
            load_workspace(new_env, ws_dir)
            assert new_env["__wsid__"] == "test_ws"

    def test_load_restores_vector(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            ws_dir = os.path.join(root, "test_ws")
            env: dict[str, object] = {"__wsid__": "test_ws", "⎕IO": S(1), "v": APLArray([3], [1, 2, 3])}
            save_workspace(env, ws_dir)
            new_env: dict[str, object] = {}
            load_workspace(new_env, ws_dir)
            assert new_env["v"] == APLArray([3], [1, 2, 3])

    def test_load_restores_dfn(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            ws_dir = os.path.join(root, "test_ws")
            env: dict[str, object] = {"__wsid__": "test_ws"}
            interpret("double←{⍵+⍵}", env)
            save_workspace(env, ws_dir)
            new_env: dict[str, object] = {}
            load_workspace(new_env, ws_dir)
            assert interpret("double 5", new_env) == S(10)

    def test_load_system_vars_first(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            ws_dir = os.path.join(root, "test_ws")
            env: dict[str, object] = {"__wsid__": "test_ws"}
            interpret("⎕IO←0", env)
            interpret("x←⍳3", env)
            save_workspace(env, ws_dir)
            new_env: dict[str, object] = {}
            load_workspace(new_env, ws_dir)
            # ⎕IO should be 0, so ⍳3 gives 0 1 2
            assert new_env["x"] == APLArray([3], [0, 1, 2])


class TestListWorkspaces:
    def test_list_finds_workspaces(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            # Create two workspaces
            for name in ("alpha", "beta"):
                ws_dir = os.path.join(root, name)
                env: dict[str, object] = {"__wsid__": name, "⎕IO": S(1)}
                save_workspace(env, ws_dir)
            # Create a non-workspace directory
            os.makedirs(os.path.join(root, "notaws"))
            result = list_workspaces(root)
            assert sorted(result) == ["alpha", "beta"]

    def test_list_empty(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            assert list_workspaces(root) == []
