from __future__ import annotations

from typing import Any

import sys

from marple.arraymodel import APLArray
from marple.interpreter import _DfnClosure, interpret
from marple.terminal import read_line
from marple.workspace import save_workspace, load_workspace


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
        lines = []
        for r in range(rows):
            row_data = result.data[r * cols : (r + 1) * cols]
            lines.append(" ".join(str(x) for x in row_data))
        return "\n".join(lines)
    return repr(result)


def _user_names(env: dict[str, Any]) -> list[str]:
    return sorted(
        name for name in env
        if not name.startswith("⎕") and not name.startswith("__")
        and name not in ("⍵", "⍺", "∇")
    )


def main() -> None:
    env: dict[str, Any] = {}
    print("MARPLE - Mini APL in Python\n")
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
            env.clear()
            print("CLEAR WS")
            continue
        if line == ")fns":
            fns = [n for n in _user_names(env) if isinstance(env[n], _DfnClosure)]
            print("  ".join(fns) if fns else "")
            continue
        if line == ")vars":
            vars_ = [n for n in _user_names(env) if isinstance(env[n], APLArray)]
            print("  ".join(vars_) if vars_ else "")
            continue
        if line.startswith(")save"):
            parts = line.split(None, 1)
            path = parts[1] if len(parts) > 1 else "workspace.apl"
            try:
                save_workspace(env, path)
                print(f"Saved: {path}")
            except Exception as e:
                print(f"ERROR: {e}")
            continue
        if line.startswith(")load"):
            parts = line.split(None, 1)
            path = parts[1] if len(parts) > 1 else "workspace.apl"
            try:
                load_workspace(env, path)
                print(f"Loaded: {path}")
            except Exception as e:
                print(f"ERROR: {e}")
            continue
        try:
            result = interpret(line, env)
            print(format_result(result))
        except Exception as e:
            print(f"ERROR: {e}")


if __name__ == "__main__":
    main()
