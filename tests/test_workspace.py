import os
import tempfile

from marple.arraymodel import APLArray, S
from marple.workspace import save_workspace, load_workspace


class TestSaveWorkspace:
    def test_save_and_load_scalar(self) -> None:
        env: dict[str, object] = {"⎕IO": S(1), "x": S(42)}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".apl", delete=False) as f:
            path = f.name
        try:
            save_workspace(env, path)
            new_env: dict[str, object] = {}
            load_workspace(new_env, path)
            assert new_env["x"] == S(42)
        finally:
            os.unlink(path)

    def test_save_and_load_vector(self) -> None:
        env: dict[str, object] = {"⎕IO": S(1), "v": APLArray([3], [1, 2, 3])}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".apl", delete=False) as f:
            path = f.name
        try:
            save_workspace(env, path)
            new_env: dict[str, object] = {}
            load_workspace(new_env, path)
            assert new_env["v"] == APLArray([3], [1, 2, 3])
        finally:
            os.unlink(path)

    def test_save_and_load_dfn(self) -> None:
        from marple.interpreter import interpret
        env: dict[str, object] = {}
        interpret("double←{⍵+⍵}", env)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".apl", delete=False) as f:
            path = f.name
        try:
            save_workspace(env, path)
            new_env: dict[str, object] = {}
            load_workspace(new_env, path)
            assert interpret("double 5", new_env) == S(10)
        finally:
            os.unlink(path)

    def test_skips_system_variables(self) -> None:
        env: dict[str, object] = {"⎕IO": S(0), "x": S(1)}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".apl", delete=False) as f:
            path = f.name
        try:
            save_workspace(env, path)
            content = open(path).read()
            assert "⎕IO←0" in content
            assert "x←1" in content
        finally:
            os.unlink(path)
