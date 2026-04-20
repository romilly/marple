"""⎕LX (latent expression) tests."""

from marple.ports.array import APLArray, S
from marple.engine import Interpreter
from tests.adapters.fake_filesystem import FakeFileSystem


class TestLXAssignment:
    def test_assign_and_read(self) -> None:
        i = Interpreter(io=1)
        i.run("⎕LX←'2+3'")
        result = i.run("⎕LX")
        assert result.as_str() == "2+3"

    def test_default_empty(self) -> None:
        i = Interpreter(io=1)
        result = i.run("⎕LX")
        assert result.shape == [0]


class TestLXOnLoad:
    def test_executes_on_load(self) -> None:
        from marple.workspace import save_workspace, load_workspace
        fs = FakeFileSystem()
        # Save workspace with ⎕LX
        i = Interpreter(io=1, fs=fs)
        i.run("x←10")
        i.run("⎕LX←'y←x×x'")
        env_dict: dict[str, object] = {}
        for name in i.env.quad_var_names():
            env_dict[name] = i.env[name]
        for name in i.env.user_names():
            env_dict[name] = i.env[name]
        env_dict["__sources__"] = i.env.sources()
        save_workspace(env_dict, "/ws/test", fs=fs)
        # Load into fresh interpreter — ⎕LX should execute
        i2 = Interpreter(io=1, fs=fs)
        load_workspace(i2.env, "/ws/test", evaluate=i2.run, fs=fs)
        assert i2.run("y") == S(100)

    def test_no_lx_no_error(self) -> None:
        from marple.workspace import save_workspace, load_workspace
        fs = FakeFileSystem()
        i = Interpreter(io=1, fs=fs)
        i.run("x←42")
        env_dict: dict[str, object] = {}
        for name in i.env.quad_var_names():
            env_dict[name] = i.env[name]
        for name in i.env.user_names():
            env_dict[name] = i.env[name]
        env_dict["__sources__"] = i.env.sources()
        save_workspace(env_dict, "/ws/test", fs=fs)
        i2 = Interpreter(io=1, fs=fs)
        load_workspace(i2.env, "/ws/test", evaluate=i2.run, fs=fs)
        assert i2.run("x") == S(42)
