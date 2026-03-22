from __future__ import annotations

from typing import Any

import os
import sys

from marple.arraymodel import APLArray
from marple.interpreter import _DfnClosure, interpret
from marple.parser import Assignment, Program, parse
from marple.terminal import read_line
from marple.workspace import save_workspace, load_workspace, list_workspaces

WORKSPACES_ROOT = os.environ.get("MARPLE_WORKSPACES", "workspaces")


def _is_char_array(arr: APLArray) -> bool:
    return len(arr.data) > 0 and all(isinstance(x, str) for x in arr.data)


def format_result(result: APLArray) -> str:
    if result.is_scalar():
        return str(result.data[0])
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
        return " ".join(str(x) for x in result.data)
    if len(result.shape) == 2:
        rows, cols = result.shape
        strs = [str(x) for x in result.data]
        col_widths = []
        for c in range(cols):
            w = max(len(strs[r * cols + c]) for r in range(rows))
            col_widths.append(w)
        lines = []
        for r in range(rows):
            parts = []
            for c in range(cols):
                parts.append(strs[r * cols + c].rjust(col_widths[c]))
            lines.append(" ".join(parts))
        return "\n".join(lines)
    return repr(result)


def _is_silent(line: str) -> bool:
    """Check if a line is a bare assignment (should not print)."""
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


def main() -> None:
    # Check for script mode: marple script.marple
    if len(sys.argv) > 1:
        from marple.script import run_script
        path = sys.argv[1]
        for line in run_script(path):
            print(line)
        return

    env: dict[str, Any] = {"__wsid__": "CLEAR WS"}
    from importlib.metadata import version
    try:
        ver = version("marple")
    except Exception:
        ver = "unknown"
    print(f"MARPLE v{ver} - Mini APL in Python")
    print("CLEAR WS\n")
    use_terminal = sys.stdin.isatty()
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
        if line == ")off":
            break
        if line == ")clear":
            wsid = env.get("__wsid__", "CLEAR WS")
            env.clear()
            env["__wsid__"] = "CLEAR WS"
            print("CLEAR WS")
            continue
        if line == ")wsid" or line == ")WSID":
            print(env.get("__wsid__", "CLEAR WS"))
            continue
        if line.startswith(")wsid ") or line.startswith(")WSID "):
            new_wsid = line.split(None, 1)[1].strip()
            env["__wsid__"] = new_wsid
            print(f"WAS {env.get('__wsid__', 'CLEAR WS')}" if False else new_wsid)
            continue
        if line == ")fns":
            fns = [n for n in _user_names(env) if isinstance(env[n], _DfnClosure)]
            print("  ".join(fns) if fns else "")
            continue
        if line == ")vars":
            vars_ = [n for n in _user_names(env) if isinstance(env[n], APLArray)]
            print("  ".join(vars_) if vars_ else "")
            continue
        if line == ")lib" or line == ")LIB":
            workspaces = list_workspaces(WORKSPACES_ROOT)
            if workspaces:
                print("  ".join(workspaces))
            else:
                print("(none)")
            continue
        if line.startswith(")save") or line.startswith(")SAVE"):
            parts = line.split(None, 1)
            if len(parts) > 1:
                env["__wsid__"] = parts[1].strip()
            wsid = env.get("__wsid__", "CLEAR WS")
            if wsid == "CLEAR WS":
                print("ERROR: No workspace ID set. Use )WSID name first.")
                continue
            ws_dir = os.path.join(WORKSPACES_ROOT, wsid)
            try:
                save_workspace(env, ws_dir)
                print(f"{wsid} SAVED")
            except Exception as e:
                print(f"ERROR: {e}")
            continue
        if line.startswith(")load") or line.startswith(")LOAD"):
            parts = line.split(None, 1)
            if len(parts) < 2:
                print("ERROR: )LOAD requires a workspace name")
                continue
            name = parts[1].strip()
            ws_dir = os.path.join(WORKSPACES_ROOT, name)
            if not os.path.isdir(ws_dir):
                print(f"ERROR: Workspace not found: {name}")
                continue
            env.clear()
            try:
                load_workspace(env, ws_dir)
                print(env.get("__wsid__", name))
            except Exception as e:
                print(f"ERROR: {e}")
            continue
        try:
            result = interpret(line, env)
            if not _is_silent(line):
                print(format_result(result))
        except Exception as e:
            print(f"ERROR: {e}")


if __name__ == "__main__":
    main()
