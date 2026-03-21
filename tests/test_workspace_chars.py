import os
import tempfile

from marple.arraymodel import APLArray, S
from marple.interpreter import interpret
from marple.workspace import save_workspace, load_workspace


class TestWorkspaceCharacterData:
    def test_save_and_load_char_vector(self) -> None:
        env: dict[str, object] = {}
        interpret("x←'HELLO'", env)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".apl", delete=False) as f:
            path = f.name
        try:
            save_workspace(env, path)
            new_env: dict[str, object] = {}
            load_workspace(new_env, path)
            assert new_env["x"] == APLArray([5], list("HELLO"))
        finally:
            os.unlink(path)

    def test_save_and_load_char_matrix(self) -> None:
        env: dict[str, object] = {}
        interpret("x←2 3⍴'CATDOG'", env)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".apl", delete=False) as f:
            path = f.name
        try:
            save_workspace(env, path)
            new_env: dict[str, object] = {}
            load_workspace(new_env, path)
            assert new_env["x"] == APLArray([2, 3], list("CATDOG"))
        finally:
            os.unlink(path)
