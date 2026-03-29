"""System command dispatcher for MARPLE.

Returns strings instead of printing — usable by REPL, web server, and Jupyter.
"""

import os

from marple.arraymodel import APLArray
from marple.engine import Interpreter


def run_system_command(interp: Interpreter, line: str) -> tuple[str, bool]:
    """Execute a system command. Returns (output_text, should_exit)."""
    cmd = line[1:].split()[0].lower() if line[1:].strip() else ""
    handler = _COMMANDS.get(cmd)
    if handler is not None:
        return handler(interp, line)
    return f"Unknown command: {line}", False


def _cmd_off(interp: Interpreter, line: str) -> tuple[str, bool]:
    return "", True


def _cmd_clear(interp: Interpreter, line: str) -> tuple[str, bool]:
    from marple.environment import Environment
    interp.env = Environment(io=1)
    return "CLEAR WS", False


def _cmd_wsid(interp: Interpreter, line: str) -> tuple[str, bool]:
    parts = line.split(None, 1)
    if len(parts) > 1:
        name = parts[1].strip()
        interp.env["⎕WSID"] = APLArray([len(name)], list(name))
        return name, False
    return "".join(str(c) for c in interp.env["⎕WSID"].data), False


def _cmd_fns(interp: Interpreter, line: str) -> tuple[str, bool]:
    parts = line.split(None, 1)
    if len(parts) > 1:
        ns_name = parts[1].strip()
        if ns_name.startswith("$"):
            from marple.namespace import load_system_workspace
            import marple.stdlib
            f = marple.stdlib.__file__
            stdlib_path = f[:f.rfind("/")] if "/" in f else f[:f.rfind("\\")]
            sys_ws = load_system_workspace(stdlib_path)
            ns_parts = ns_name.split("::")[1:] if "::" in ns_name else []
            ns = sys_ws.resolve(ns_parts) if ns_parts else sys_ws
            if ns is not None and hasattr(ns, "list_names"):
                return "  ".join(ns.list_names()), False
            return f"Namespace not found: {ns_name}", False
        return f"Namespace not found: {ns_name}", False
    names = [name for name, _ in interp.env.list_functions()]
    return "  ".join(names), False


def _cmd_vars(interp: Interpreter, line: str) -> tuple[str, bool]:
    names = [name for name, _ in interp.env.list_variables()]
    return "  ".join(names), False


def _cmd_lib(interp: Interpreter, line: str) -> tuple[str, bool]:
    from marple.workspace import list_workspaces
    from marple.config import get_workspaces_dir
    ws_root = get_workspaces_dir()
    workspaces = list_workspaces(ws_root)
    return "  ".join(workspaces) if workspaces else "(none)", False


def _cmd_save(interp: Interpreter, line: str) -> tuple[str, bool]:
    from marple.workspace import save_workspace
    from marple.config import get_workspaces_dir
    parts = line.split(None, 1)
    if len(parts) > 1:
        name = parts[1].strip()
        interp.env["⎕WSID"] = APLArray([len(name)], list(name))
    wsid = "".join(str(c) for c in interp.env["⎕WSID"].data)
    if wsid == "CLEAR WS":
        return "ERROR: No workspace ID set. Use )WSID name first.", False
    ws_root = get_workspaces_dir()
    env_dict: dict[str, object] = {}
    for name in interp.env.quad_var_names():
        env_dict[name] = interp.env[name]
    for name in interp.env.user_names():
        env_dict[name] = interp.env[name]
    env_dict["__sources__"] = interp.env.sources()
    env_dict["__wsid__"] = wsid
    try:
        save_workspace(env_dict, os.path.join(ws_root, wsid))
        return f"{wsid} SAVED", False
    except Exception as e:
        return f"ERROR: {e}", False


def _cmd_load(interp: Interpreter, line: str) -> tuple[str, bool]:
    from marple.workspace import load_workspace
    from marple.config import get_workspaces_dir
    parts = line.split(None, 1)
    if len(parts) < 2:
        return "ERROR: )LOAD requires a workspace name", False
    name = parts[1].strip()
    ws_root = get_workspaces_dir()
    ws_dir = os.path.join(ws_root, name)
    if not os.path.isdir(ws_dir):
        return f"ERROR: Workspace not found: {name}", False
    from marple.environment import Environment
    interp.env = Environment(io=1)
    try:
        from marple.formatting import format_result
        lx_result = load_workspace(interp.env, ws_dir, evaluate=interp.run)
        wsid = "".join(str(c) for c in interp.env["⎕WSID"].data)
        output = wsid
        if lx_result is not None:
            output += "\n" + format_result(lx_result, interp.env)
        return output, False
    except Exception as e:
        return f"ERROR: {e}", False


from typing import Callable

_CmdFn = Callable[[Interpreter, str], tuple[str, bool]]

_COMMANDS: dict[str, _CmdFn] = {
    "off": _cmd_off,
    "clear": _cmd_clear,
    "wsid": _cmd_wsid,
    "fns": _cmd_fns,
    "vars": _cmd_vars,
    "lib": _cmd_lib,
    "save": _cmd_save,
    "load": _cmd_load,
}
