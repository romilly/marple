from __future__ import annotations

from typing import Any

from marple.arraymodel import APLArray
from marple.interpreter import _DfnClosure, interpret
from marple.workspace import save_workspace, load_workspace


def _user_names(env: dict[str, Any]) -> list[str]:
    return sorted(
        name for name in env
        if not name.startswith("⎕") and not name.startswith("__")
        and name not in ("⍵", "⍺", "∇")
    )


def main() -> None:
    env: dict[str, Any] = {}
    print("MARPLE - Mini APL in Python\n")
    while True:
        try:
            line = input("      ")
        except (EOFError, KeyboardInterrupt):
            print()
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
            # Display result
            if result.is_scalar():
                print(result.data[0])
            elif len(result.shape) == 1:
                print(" ".join(str(x) for x in result.data))
            elif len(result.shape) == 2:
                rows, cols = result.shape
                for r in range(rows):
                    row_data = result.data[r * cols : (r + 1) * cols]
                    print(" ".join(str(x) for x in row_data))
            else:
                print(result)
        except Exception as e:
            print(f"ERROR: {e}")


if __name__ == "__main__":
    main()
