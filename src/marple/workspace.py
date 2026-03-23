
import os
from datetime import datetime
try:
    from typing import Any
except ImportError:
    pass

from marple.arraymodel import APLArray, S
from marple.backend import to_list
from marple.interpreter import _DfnClosure, interpret


def _format_value(value: object) -> str | None:
    """Convert an APLArray value to APL source text."""
    if isinstance(value, _DfnClosure):
        return None
    if not isinstance(value, APLArray):
        return None
    if value.is_scalar():
        v = value.data[0]
        if isinstance(v, str):
            return f"'{v}'"
        if isinstance(v, (int, float)) and v < 0:
            return f"¯{abs(v)}"
        return str(v)
    data = to_list(value.data)
    is_char = len(data) > 0 and all(isinstance(x, str) for x in data)
    if is_char:
        char_str = "".join(str(x) for x in data)
        quoted = f"'{char_str}'"
        if len(value.shape) == 1:
            return quoted
        shape_str = " ".join(str(s) for s in value.shape)
        return f"{shape_str}⍴{quoted}"

    def _fmt_num(x: object) -> str:
        if isinstance(x, (int, float)) and x < 0:
            return f"¯{abs(x)}"
        return str(x)

    data_str = " ".join(_fmt_num(x) for x in data)
    if len(value.shape) == 1:
        return data_str
    shape_str = " ".join(str(s) for s in value.shape)
    return f"{shape_str}⍴{data_str}"


def _sysvar_filename(name: str) -> str:
    """Convert system variable name to filesystem-safe filename.
    ⎕IO → __IO.apl"""
    return f"__{name[1:]}.apl"


def _entity_filename(name: str) -> str:
    """Convert entity name to filename."""
    if name.startswith("⎕"):
        return _sysvar_filename(name)
    return f"{name}.apl"


def save_workspace(env: dict[str, Any], ws_dir: str) -> None:
    """Save workspace to a directory with one file per entity."""
    os.makedirs(ws_dir, exist_ok=True)

    # Write .ws marker
    wsid_val = env.get("⎕WSID", env.get("__wsid__", "CLEAR WS"))
    if isinstance(wsid_val, APLArray):
        wsid = "".join(str(c) for c in wsid_val.data)
    else:
        wsid = str(wsid_val)
    with open(os.path.join(ws_dir, ".ws"), "w") as f:
        f.write(f"{wsid}\n{datetime.now().isoformat()}\n")

    # Track which files we write so we can clean up stale ones
    written_files: set[str] = {".ws"}
    sources: dict[str, str] = env.get("__sources__", {})

    # System variables that should not be saved (constants or managed separately)
    _SKIP_QUADS = {"⎕A", "⎕D", "⎕TS", "⎕EN", "⎕DM", "⎕WSID"}

    # Save system variables first
    for name in sorted(env):
        if name.startswith("⎕"):
            if name in _SKIP_QUADS:
                continue
            value = env[name]
            if isinstance(value, APLArray):
                formatted = _format_value(value)
                if formatted is not None:
                    filename = _entity_filename(name)
                    written_files.add(filename)
                    with open(os.path.join(ws_dir, filename), "w") as f:
                        f.write(f"{name}←{formatted}\n")

    # Save user definitions
    for name in sorted(env):
        if name.startswith("⎕") or name.startswith("__"):
            continue
        if name in ("⍵", "⍺", "∇"):
            continue
        value = env[name]
        filename = _entity_filename(name)
        if isinstance(value, _DfnClosure) and name in sources:
            written_files.add(filename)
            with open(os.path.join(ws_dir, filename), "w") as f:
                f.write(f"{sources[name]}\n")
        elif isinstance(value, APLArray):
            formatted = _format_value(value)
            if formatted is not None:
                written_files.add(filename)
                with open(os.path.join(ws_dir, filename), "w") as f:
                    f.write(f"{name}←{formatted}\n")

    # Remove stale .apl files
    for existing in os.listdir(ws_dir):
        if existing.endswith(".apl") and existing not in written_files:
            os.unlink(os.path.join(ws_dir, existing))


def load_workspace(env: dict[str, Any], ws_dir: str) -> None:
    """Load workspace from a directory."""
    # Read .ws marker for WSID
    ws_file = os.path.join(ws_dir, ".ws")
    if os.path.isfile(ws_file):
        with open(ws_file) as f:
            wsid = f.readline().strip()
            env["__wsid__"] = wsid
            env["⎕WSID"] = APLArray([len(wsid)], list(wsid))

    # Collect .apl files, system vars first
    files = sorted(os.listdir(ws_dir))
    sys_files = [f for f in files if f.startswith("__") and f.endswith(".apl")]
    user_files = [f for f in files if not f.startswith("__") and f.endswith(".apl")]

    for filename in sys_files + user_files:
        filepath = os.path.join(ws_dir, filename)
        with open(filepath) as f:
            line = f.read().strip()
            if line:
                interpret(line, env)


def list_workspaces(root: str) -> list[str]:
    """List workspace names under the given root directory."""
    if not os.path.isdir(root):
        return []
    result = []
    for name in sorted(os.listdir(root)):
        ws_dir = os.path.join(root, name)
        if os.path.isdir(ws_dir) and os.path.isfile(os.path.join(ws_dir, ".ws")):
            result.append(name)
    return result
