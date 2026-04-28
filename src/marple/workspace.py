from typing import Any, Callable

from marple.ports.array import APLArray, str_to_char_array
from marple.ports.filesystem import FileSystem
from marple.adapters.numpy_array_builder import BUILDER


def _is_dfn_binding(value: object) -> bool:
    """Check if value is any kind of dfn binding (old or new)."""
    return hasattr(value, 'dfn') and hasattr(value, 'env')


def _format_value(value: object) -> str | None:
    """Convert an APLArray value to APL source text."""
    if _is_dfn_binding(value):
        return None
    if not isinstance(value, APLArray):
        return None
    if value.is_scalar():
        if value.is_char():
            return f"'{value.as_str()}'"
        v = value.scalar_value()
        if isinstance(v, (int, float)) and v < 0:
            return f"¯{abs(v)}"
        return str(v)
    data = value.to_list()
    if value.is_char():
        quoted = f"'{value.as_str()}'"
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


def _default_fs() -> FileSystem:
    from marple.adapters.os_filesystem import OsFileSystem
    return OsFileSystem()


def save_workspace(env: dict[str, Any], ws_dir: str,
                   fs: FileSystem | None = None) -> None:
    """Save workspace to a directory with one file per entity."""
    if fs is None:
        fs = _default_fs()
    fs.makedirs(ws_dir)

    # Write .ws marker
    wsid_val = env.get("⎕WSID")
    if wsid_val is None:
        wsid = "CLEAR WS"
    else:
        wsid = wsid_val.as_str()
    fs.write_text(ws_dir + "/" + ".ws", wsid + "\n")

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
                if formatted is not None and formatted != "":
                    filename = _entity_filename(name)
                    written_files.add(filename)
                    fs.write_text(ws_dir + "/" + filename,
                                  f"{name}←{formatted}\n")

    # Save user definitions
    for name in sorted(env):
        if name.startswith("⎕") or name.startswith("__"):
            continue
        if name in ("⍵", "⍺", "∇"):
            continue
        value = env[name]
        filename = _entity_filename(name)
        if _is_dfn_binding(value) and name in sources:
            written_files.add(filename)
            fs.write_text(ws_dir + "/" + filename,
                          f"{sources[name]}\n")
        elif isinstance(value, APLArray):
            formatted = _format_value(value)
            if formatted is not None:
                written_files.add(filename)
                fs.write_text(ws_dir + "/" + filename,
                              f"{name}←{formatted}\n")

    # Remove stale .apl files
    for existing in fs.listdir(ws_dir):
        if existing.endswith(".apl") and existing not in written_files:
            fs.delete(ws_dir + "/" + existing)


def load_workspace(env: Any, ws_dir: str,
                    evaluate: Callable[[str], Any] | None = None,
                    fs: FileSystem | None = None) -> APLArray | None:
    """Load workspace from a directory.

    If evaluate is provided, it's called to execute each line.
    Returns the latent-expression (⎕LX) result if the workspace
    defines one and it evaluates to an APLArray, otherwise None.
    """
    if fs is None:
        fs = _default_fs()
    # Read .ws marker for WSID
    ws_file = ws_dir + "/" + ".ws"
    if fs.is_file(ws_file):
        text = fs.read_text(ws_file)
        wsid = text.split("\n")[0].strip()
        env["⎕WSID"] = BUILDER.apl_array([len(wsid)], str_to_char_array(wsid))

    # Collect .apl files, system vars first
    files = sorted(fs.listdir(ws_dir))
    sys_files = [f for f in files if f.startswith("__") and f.endswith(".apl")]
    user_files = [f for f in files if not f.startswith("__") and f.endswith(".apl")]

    if evaluate is None:
        raise ValueError("evaluate callable is required for load_workspace")

    for filename in sys_files + user_files:
        filepath = ws_dir + "/" + filename
        line = fs.read_text(filepath).strip()
        if line:
            evaluate(line)

    # Execute latent expression if present
    lx = env.get("⎕LX") if hasattr(env, 'get') else env.get("⎕LX")
    if lx is not None and isinstance(lx, APLArray):
        lx_text = lx.as_str()
        if lx_text.strip():
            result = evaluate(lx_text)
            if isinstance(result, APLArray):
                return result
    return None


def list_workspaces(root: str, fs: FileSystem | None = None) -> list[str]:
    """List workspace names under the given root directory."""
    if fs is None:
        fs = _default_fs()
    if not fs.is_dir(root):
        return []
    result = []
    for name in sorted(fs.listdir(root)):
        ws_dir = root + "/" + name
        if fs.is_dir(ws_dir) and fs.is_file(ws_dir + "/" + ".ws"):
            result.append(name)
    return result
