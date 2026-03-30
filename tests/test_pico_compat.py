"""Tests that pico_eval.py imports and API still work."""

import marple
from marple.engine import Interpreter


def test_no_dataclasses_in_engine() -> None:
    """engine.py must not use dataclasses — MicroPython doesn't have them."""
    import ast
    with open("src/marple/engine.py") as f:
        source = f.read()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "dataclasses":
            raise AssertionError("engine.py imports dataclasses — breaks MicroPython")


def test_no_importlib_in_executor() -> None:
    """executor.py must not use importlib — MicroPython doesn't have it."""
    import ast
    with open("src/marple/executor.py") as f:
        source = f.read()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "importlib":
                    raise AssertionError("executor.py imports importlib — breaks MicroPython")


def test_no_os_path_in_os_filesystem() -> None:
    """os_filesystem.py must not use os.path — MicroPython doesn't have it."""
    import ast
    with open("src/marple/adapters/os_filesystem.py") as f:
        source = f.read()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute):
            if (isinstance(node.value.value, ast.Name) and
                    node.value.value.id == "os" and node.value.attr == "path"):
                raise AssertionError(
                    f"os_filesystem.py uses os.path.{node.attr} — breaks MicroPython")


def test_pico_eval_imports() -> None:
    """Simulate the imports pico_eval.py does on startup."""
    from marple.engine import Interpreter  # noqa: F811
    from marple.errors import APLError  # noqa: F401
    import marple as m  # noqa: F401


def test_pico_eval_create_interpreter() -> None:
    """pico_eval.py creates Interpreter() with no arguments."""
    interp = Interpreter()
    assert interp is not None


def test_pico_eval_version_accessible() -> None:
    """pico_eval.py reads marple.__version__ for the banner."""
    assert hasattr(marple, "__version__")
    assert isinstance(marple.__version__, str)


def test_pico_eval_execute_api() -> None:
    """pico_eval.py uses interp.execute() which returns EvalResult."""
    interp = Interpreter()
    r = interp.execute("2+3")
    assert not r.silent
    assert r.display_text == "5"


def test_pico_eval_silent_assignment() -> None:
    """Assignments are silent — pico_eval.py checks r.silent."""
    interp = Interpreter()
    r = interp.execute("x←42")
    assert r.silent


def test_pico_eval_full_startup_sequence() -> None:
    """Simulate the exact startup sequence from pico_eval.py."""
    # Line 31-33: imports
    from marple.engine import Interpreter as Interp  # noqa: F811
    from marple.errors import APLError  # noqa: F401
    import marple as m

    # Line 37: create interpreter
    interp = Interp()

    # Line 43: version string for banner
    banner = "MARPLE v" + m.__version__
    assert "MARPLE v" in banner

    # Lines 65-71: execute and check result
    r = interp.execute("1+1")
    if r.silent:
        output = ""
    else:
        output = r.display_text
    assert output == "2"
