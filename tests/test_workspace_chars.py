import os
import tempfile

from marple.arraymodel import APLArray, S
from marple.interpreter import interpret
from marple.workspace import save_workspace, load_workspace


class TestWorkspaceCharacterData:
    def test_save_and_load_char_vector(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            ws_dir = os.path.join(root, "test_ws")
            env: dict[str, object] = {"__wsid__": "test_ws"}
            interpret("x←'HELLO'", env)
            save_workspace(env, ws_dir)
            new_env: dict[str, object] = {}
            load_workspace(new_env, ws_dir)
            assert new_env["x"] == APLArray([5], list("HELLO"))

    def test_save_and_load_char_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            ws_dir = os.path.join(root, "test_ws")
            env: dict[str, object] = {"__wsid__": "test_ws"}
            interpret("x←2 3⍴'CATDOG'", env)
            save_workspace(env, ws_dir)
            new_env: dict[str, object] = {}
            load_workspace(new_env, ws_dir)
            assert new_env["x"] == APLArray([2, 3], list("CATDOG"))
