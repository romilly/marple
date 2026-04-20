"""AST-based compatibility guards for the Pico deploy.

These tests do not run on a Pico; they analyse the source of the modules
deploy.sh ships and fail the fast suite if they pick up CPython-only
imports (dataclasses, importlib, configparser, os.path) that MicroPython
can't resolve.
"""

import ast

import marple
from marple.engine import Interpreter


def _module_source(relpath: str) -> str:
    with open(relpath) as f:
        return f.read()


def _imports_module(source: str, name: str) -> bool:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == name:
            return True
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == name:
                    return True
    return False


def _uses_os_path(source: str) -> str | None:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute):
            if (isinstance(node.value.value, ast.Name)
                    and node.value.value.id == "os"
                    and node.value.attr == "path"):
                return f"os.path.{node.attr}"
    return None


class TestPicoDeployableAstGuards:
    def test_engine_has_no_dataclasses(self) -> None:
        assert not _imports_module(_module_source("src/marple/engine.py"), "dataclasses")

    def test_executor_has_no_importlib(self) -> None:
        assert not _imports_module(_module_source("src/marple/executor.py"), "importlib")

    def test_pico_config_has_no_configparser(self) -> None:
        assert not _imports_module(
            _module_source("src/marple/adapters/pico_config.py"), "configparser")

    def test_system_commands_has_no_os_path(self) -> None:
        use = _uses_os_path(_module_source("src/marple/system_commands.py"))
        assert use is None, f"system_commands.py uses {use} — breaks MicroPython"

    def test_os_filesystem_has_no_os_path(self) -> None:
        use = _uses_os_path(_module_source("src/marple/adapters/os_filesystem.py"))
        assert use is None, f"os_filesystem.py uses {use} — breaks MicroPython"


class TestPicoEvalImports:
    """Guard the specific import surface pico_eval.py relies on.

    Catches regressions where a rename or refactor breaks the Pico's
    startup sequence even though desktop tests are green.
    """

    def test_pico_eval_module_parses(self) -> None:
        source = _module_source("scripts/pico_eval.py")
        ast.parse(source)  # SyntaxError raises

    def test_pico_eval_uses_ulab_aplarray(self) -> None:
        assert _imports_module(_module_source("scripts/pico_eval.py"),
                               "marple.ulab_aplarray")

    def test_pico_eval_uses_pico_adapters(self) -> None:
        source = _module_source("scripts/pico_eval.py")
        assert _imports_module(source, "marple.adapters.pico_config")
        assert _imports_module(source, "marple.adapters.pico_console")
        assert _imports_module(source, "marple.adapters.pico_timer")

    def test_pico_eval_uses_repl_run_repl(self) -> None:
        assert _imports_module(_module_source("scripts/pico_eval.py"), "marple.repl")

    def test_marple_version_exposed(self) -> None:
        assert hasattr(marple, "__version__")
        assert isinstance(marple.__version__, str)

    def test_interpreter_execute_returns_display_text(self) -> None:
        interp = Interpreter()
        r = interp.execute("2+3")
        assert not r.silent
        assert r.display_text == "5"

    def test_assignment_is_silent(self) -> None:
        interp = Interpreter()
        r = interp.execute("x\u21904")
        assert r.silent
