
try:
    from typing import Any
except ImportError:
    pass

import os
import sys

from marple.arraymodel import APLArray
from marple.errors import APLError
from marple.interpreter import _DfnBinding, default_env, interpret
from marple.parser import Assignment, Program, parse
try:
    from marple.terminal import read_line
except ImportError:
    read_line = None  # type: ignore[assignment]
try:
    from marple.workspace import save_workspace, load_workspace, list_workspaces
except ImportError:
    save_workspace = load_workspace = list_workspaces = None  # type: ignore[assignment]

try:
    WORKSPACES_ROOT = os.environ.get("MARPLE_WORKSPACES", "workspaces")
except AttributeError:
    WORKSPACES_ROOT = "workspaces"


def _rjust(s, width):
    if len(s) >= width:
        return s
    return " " * (width - len(s)) + s


def _is_char_array(arr: APLArray) -> bool:
    return len(arr.data) > 0 and all(isinstance(x, str) for x in arr.data)


from marple.formatting import format_num as _format_num


def format_result(result: APLArray, env: dict[str, Any] | None = None) -> str:
    pp = 10
    if env is not None:
        pp_val = env.get("⎕PP")
        if pp_val is not None:
            pp = int(pp_val.data[0])
    if result.is_scalar():
        return _format_num(result.data[0], pp)
    if _is_char_array(result):
        if len(result.shape) == 1:
            return "".join(str(x) for x in result.data)
        if len(result.shape) == 2:
            rows, cols = result.shape
            lines = []
            for r in range(rows):
                row_data = result.data[r * cols : (r + 1) * cols]
                lines.append("".join(str(x) for x in row_data))
            return "\n".join(lines)
    if len(result.shape) == 1:
        return " ".join(_format_num(x, pp) for x in result.data)
    if len(result.shape) == 2:
        rows, cols = result.shape
        strs = [_format_num(result.data[r * cols + c], pp) for r in range(rows) for c in range(cols)]
        col_widths = []
        for c in range(cols):
            w = max(len(strs[r * cols + c]) for r in range(rows))
            col_widths.append(w)
        lines = []
        for r in range(rows):
            parts = []
            for c in range(cols):
                parts.append(_rjust(strs[r * cols + c], col_widths[c]))
            lines.append(" ".join(parts))
        return "\n".join(lines)
    return repr(result)


def _is_silent(line: str) -> bool:
    """Check if a line is a comment, bare assignment, or directive (should not print)."""
    stripped = line.strip()
    if stripped.startswith("#"):
        return True
    if stripped.startswith("⍝"):
        return True
    try:
        tree = parse(line)
    except Exception:
        return False
    if isinstance(tree, Assignment):
        return True
    if isinstance(tree, Program):
        return len(tree.statements) > 0 and isinstance(tree.statements[-1], Assignment)
    return False


def _user_names(env: dict[str, Any]) -> list[str]:
    return sorted(
        name for name in env
        if not name.startswith("⎕") and not name.startswith("__")
        and name not in ("⍵", "⍺", "∇")
    )


def _cmd_off(line: str, env: dict[str, Any]) -> bool:
    return True  # signal to break


def _cmd_clear(line: str, env: dict[str, Any]) -> bool:
    env.clear()
    env["__wsid__"] = "CLEAR WS"
    print("CLEAR WS")
    return False


def _cmd_wsid(line: str, env: dict[str, Any]) -> bool:
    parts = line.split(None, 1)
    if len(parts) > 1:
        env["__wsid__"] = parts[1].strip()
        print(parts[1].strip())
    else:
        print(env.get("__wsid__", "CLEAR WS"))
    return False


def _cmd_fns(line: str, env: dict[str, Any]) -> bool:
    parts = line.split(None, 1)
    if len(parts) > 1:
        ns_name = parts[1].strip()
        from marple.interpreter import _get_sys_workspace
        if ns_name.startswith("$"):
            ns_parts = ns_name.split("::")[1:] if "::" in ns_name else []
            sys_ws = _get_sys_workspace()
            ns = sys_ws.resolve(ns_parts) if ns_parts else sys_ws
            if ns is not None and hasattr(ns, "list_names"):
                print("  ".join(ns.list_names()))
            else:
                print(f"Namespace not found: {ns_name}")
        else:
            print(f"Namespace not found: {ns_name}")
    else:
        fns = [n for n in _user_names(env) if isinstance(env[n], _DfnBinding)]
        print("  ".join(fns) if fns else "")
    return False


def _cmd_vars(line: str, env: dict[str, Any]) -> bool:
    vars_ = [n for n in _user_names(env) if isinstance(env[n], APLArray)]
    print("  ".join(vars_) if vars_ else "")
    return False


def _cmd_lib(line: str, env: dict[str, Any]) -> bool:
    workspaces = list_workspaces(WORKSPACES_ROOT)
    print("  ".join(workspaces) if workspaces else "(none)")
    return False


def _cmd_save(line: str, env: dict[str, Any]) -> bool:
    parts = line.split(None, 1)
    if len(parts) > 1:
        env["__wsid__"] = parts[1].strip()
    wsid = env.get("__wsid__", "CLEAR WS")
    if wsid == "CLEAR WS":
        print("ERROR: No workspace ID set. Use )WSID name first.")
        return False
    try:
        save_workspace(env, os.path.join(WORKSPACES_ROOT, wsid))
        print(f"{wsid} SAVED")
    except Exception as e:
        print(f"ERROR: {e}")
    return False


def _cmd_load(line: str, env: dict[str, Any]) -> bool:
    parts = line.split(None, 1)
    if len(parts) < 2:
        print("ERROR: )LOAD requires a workspace name")
        return False
    name = parts[1].strip()
    ws_dir = os.path.join(WORKSPACES_ROOT, name)
    if not os.path.isdir(ws_dir):
        print(f"ERROR: Workspace not found: {name}")
        return False
    env.clear()
    try:
        load_workspace(env, ws_dir)
        print(env.get("__wsid__", name))
    except Exception as e:
        print(f"ERROR: {e}")
    return False


_SYSTEM_COMMANDS: dict[str, Any] = {
    "off": _cmd_off,
    "clear": _cmd_clear,
    "wsid": _cmd_wsid,
    "fns": _cmd_fns,
    "vars": _cmd_vars,
    "lib": _cmd_lib,
    "save": _cmd_save,
    "load": _cmd_load,
}


def _handle_system_command(line: str, env: dict[str, Any]) -> bool:
    """Handle a )command. Returns True if REPL should exit."""
    cmd = line[1:].split()[0].lower() if line[1:].strip() else ""
    handler = _SYSTEM_COMMANDS.get(cmd)
    if handler is not None:
        return handler(line, env)
    print(f"Unknown command: {line}")
    return False


def main() -> None:
    # Check for script mode: marple script.marple
    if len(sys.argv) > 1:
        from marple.script import run_script
        path = sys.argv[1]
        for line in run_script(path):
            print(line)
        return

    env: dict[str, Any] = default_env()
    from marple import __version__ as ver
    print(f"MARPLE v{ver} - Mini APL in Python")
    print("CLEAR WS\n")
    use_terminal = read_line is not None and sys.stdin.isatty()
    while True:
        if use_terminal:
            line = read_line()
        else:
            try:
                line = input("      ")
            except (EOFError, KeyboardInterrupt):
                print()
                break
        if line is None:
            break
        line = line.strip()
        if not line:
            continue
        if line.startswith(")"):
            if _handle_system_command(line, env):
                break
            continue
        try:
            result = interpret(line, env)
            if not _is_silent(line):
                print(format_result(result, env))
        except APLError as e:
            print(e)
        except Exception as e:
            print(f"ERROR: {e}")


if __name__ == "__main__":
    main()
