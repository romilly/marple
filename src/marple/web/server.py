"""MARPLE Web REPL server.

Usage:
    python -m marple.web.server [--port PORT]
"""

import html
import json
from pathlib import Path
from typing import Any

from aiohttp import web

from marple.arraymodel import APLArray
from marple.engine import Interpreter
from marple.environment import Environment
from marple.errors import APLError
from marple.repl import format_result, _is_silent

STATIC_DIR = Path(__file__).parent / "static"
INPUT_INDENT = "      "


def _is_dfn_binding(value: object) -> bool:
    """Check if value is any kind of dfn binding."""
    return hasattr(value, 'dfn') and hasattr(value, 'env')


class WebSession:
    """Wraps an interpreter for web use."""

    def __init__(self) -> None:
        self.interp = Interpreter()
        self.transcript: list[tuple[str, str]] = []

    def evaluate(self, expr: str) -> str:
        """Evaluate an APL expression. Return an HTML fragment."""
        input_html = html.escape(INPUT_INDENT + expr)
        try:
            result = self.interp.run(expr)
            if _is_silent(expr):
                self.transcript.append((expr, ""))
                return (
                    f'<div class="entry">'
                    f'<pre class="input">{input_html}</pre>'
                    f"</div>"
                )
            output = format_result(result, self.interp.env)
            self.transcript.append((expr, output))
            output_html = html.escape(output)
            return (
                f'<div class="entry">'
                f'<pre class="input">{input_html}</pre>'
                f'<pre class="output">{output_html}</pre>'
                f"</div>"
            )
        except APLError as e:
            self.transcript.append((expr, "ERROR: " + str(e)))
            error_html = html.escape(str(e))
            return (
                f'<div class="entry">'
                f'<pre class="input">{input_html}</pre>'
                f'<pre class="error">{error_html}</pre>'
                f"</div>"
            )

    def system_command(self, cmd: str) -> str:
        """Execute a system command. Return an HTML fragment."""
        input_html = html.escape(INPUT_INDENT + cmd)
        output = self._run_system_command(cmd)
        parts = [f'<pre class="input">{input_html}</pre>']
        if output:
            output_html = html.escape(output)
            parts.append(f'<pre class="output">{output_html}</pre>')
        return f'<div class="entry">{"".join(parts)}</div>'

    def _ws_clear(self, cmd: str) -> str:
        self.interp = Interpreter()
        return "CLEAR WS"

    def _ws_vars(self, cmd: str) -> str:
        names = self.interp.env.names_of_class(2)  # NC_ARRAY
        return "  ".join(names)

    def _ws_fns(self, cmd: str) -> str:
        names = self.interp.env.names_of_class(3)  # NC_FUNCTION
        return "  ".join(names)

    def _ws_wsid(self, cmd: str) -> str:
        parts = cmd.split(None, 1)
        if len(parts) > 1:
            name = parts[1].strip()
            self.interp.env["⎕WSID"] = APLArray([len(name)], list(name))
            return name
        return "".join(str(c) for c in self.interp.env["⎕WSID"].data)

    def _ws_save(self, cmd: str) -> str:
        import os
        from marple.workspace import save_workspace
        from marple.config import get_workspaces_dir
        parts = cmd.split(None, 1)
        if len(parts) > 1:
            name = parts[1].strip()
            self.interp.env["⎕WSID"] = APLArray([len(name)], list(name))
        wsid = "".join(str(c) for c in self.interp.env["⎕WSID"].data)
        if wsid == "CLEAR WS":
            return "ERROR: No workspace ID set. Use )WSID name first."
        ws_root = get_workspaces_dir()
        env_dict: dict[str, object] = {}
        for name in self.interp.env.quad_var_names():
            env_dict[name] = self.interp.env[name]
        for name in self.interp.env.user_names():
            env_dict[name] = self.interp.env[name]
        env_dict["__sources__"] = self.interp.env.sources()
        env_dict["__wsid__"] = wsid
        try:
            save_workspace(env_dict, os.path.join(ws_root, wsid))
            return f"{wsid} SAVED"
        except Exception as e:
            return f"ERROR: {e}"

    def _ws_load(self, cmd: str) -> str:
        import os
        from marple.workspace import load_workspace
        from marple.config import get_workspaces_dir
        parts = cmd.split(None, 1)
        if len(parts) < 2:
            return "ERROR: )LOAD requires a workspace name"
        name = parts[1].strip()
        ws_root = get_workspaces_dir()
        ws_dir = os.path.join(ws_root, name)
        if not os.path.isdir(ws_dir):
            return f"ERROR: Workspace not found: {name}"
        self.interp = Interpreter()
        try:
            load_workspace(self.interp.env, ws_dir, evaluate=self.interp.run)
            wsid = "".join(str(c) for c in self.interp.env["⎕WSID"].data)
            return wsid
        except Exception as e:
            return f"ERROR: {e}"

    def _ws_lib(self, cmd: str) -> str:
        from marple.workspace import list_workspaces
        from marple.config import get_workspaces_dir
        ws_root = get_workspaces_dir()
        workspaces = list_workspaces(ws_root)
        return "  ".join(workspaces) if workspaces else "(none)"

    _SYS_COMMANDS: dict[str, str] = {
        "clear": "_ws_clear", "vars": "_ws_vars",
        "fns": "_ws_fns", "wsid": "_ws_wsid",
        "save": "_ws_save", "load": "_ws_load",
        "lib": "_ws_lib",
    }

    def _run_system_command(self, cmd: str) -> str:
        """Execute a system command and return the output string."""
        word = cmd[1:].split()[0].lower() if cmd[1:].strip() else ""
        method_name = self._SYS_COMMANDS.get(word)
        if method_name is not None:
            return getattr(self, method_name)(cmd)
        return f"Unknown command: {cmd}"

    def workspace_fragment(self) -> str:
        """Return an HTML fragment listing variables and functions."""
        vars_list = []
        fns_list = []
        for name in self.interp.env.user_names():
            val = self.interp.env[name]
            if isinstance(val, APLArray):
                shape_str = " ".join(str(s) for s in val.shape) if val.shape else "scalar"
                vars_list.append(
                    f'<div class="ws-item" data-name="{html.escape(name)}">'
                    f'{html.escape(name)} '
                    f'<span class="ws-shape">{shape_str}</span></div>'
                )
            elif _is_dfn_binding(val):
                fns_list.append(
                    f'<div class="ws-item" data-name="{html.escape(name)}">'
                    f'{html.escape(name)}</div>'
                )
        parts = []
        if vars_list:
            parts.append('<div class="ws-section"><h4>Variables</h4>'
                         + "".join(vars_list) + "</div>")
        if fns_list:
            parts.append('<div class="ws-section"><h4>Functions</h4>'
                         + "".join(fns_list) + "</div>")
        return "".join(parts)

    def save_session(self, name: str, sessions_dir: str) -> None:
        """Save the session transcript as a markdown file."""
        import os
        from datetime import datetime
        os.makedirs(sessions_dir, exist_ok=True)
        path = os.path.join(sessions_dir, name + ".md")
        lines = [f"# MARPLE Session — {name}",
                 f"Saved: {datetime.now().isoformat(timespec='seconds')}",
                 "", "```apl"]
        for expr, output in self.transcript:
            lines.append(INPUT_INDENT + expr)
            if output:
                lines.append(output)
        lines.append("```")
        lines.append("")
        with open(path, "w") as f:
            f.write("\n".join(lines))

    def load_session(self, name: str, sessions_dir: str) -> str:
        """Load a session from markdown, display saved transcript as-is."""
        import os
        path = os.path.join(sessions_dir, name + ".md")
        with open(path) as f:
            text = f.read()
        self.interp = Interpreter()
        self.transcript.clear()
        fragments: list[str] = []
        in_code = False
        current_input: str | None = None
        output_lines: list[str] = []
        for line in text.split("\n"):
            if line.strip().startswith("```apl"):
                in_code = True
                continue
            if line.strip().startswith("```"):
                if current_input is not None:
                    fragments.append(
                        self._format_entry(current_input, "\n".join(output_lines)))
                    self.transcript.append((current_input, "\n".join(output_lines)))
                in_code = False
                continue
            if not in_code:
                continue
            if line.startswith(INPUT_INDENT):
                if current_input is not None:
                    fragments.append(
                        self._format_entry(current_input, "\n".join(output_lines)))
                    self.transcript.append((current_input, "\n".join(output_lines)))
                current_input = line[len(INPUT_INDENT):]
                output_lines = []
            else:
                output_lines.append(line)
        return "".join(fragments)

    @staticmethod
    def _format_entry(expr: str, output: str) -> str:
        """Format an input/output pair as an HTML fragment."""
        input_html = html.escape(INPUT_INDENT + expr)
        parts = [f'<pre class="input">{input_html}</pre>']
        if output:
            output_html = html.escape(output)
            parts.append(f'<pre class="output">{output_html}</pre>')
        return f'<div class="entry">{"".join(parts)}</div>'

    @staticmethod
    def list_sessions(sessions_dir: str) -> list[str]:
        """List available session names."""
        import os
        if not os.path.isdir(sessions_dir):
            return []
        return sorted(
            f[:-3] for f in os.listdir(sessions_dir) if f.endswith(".md")
        )


async def handle_index(request: web.Request) -> web.StreamResponse:
    path = STATIC_DIR / "desktop.html"
    return web.FileResponse(path)


async def handle_health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def handle_config(request: web.Request) -> web.Response:
    has_pico = request.app.get("pico") is not None
    return web.json_response({"pico_available": has_pico})


async def handle_workspace(request: web.Request) -> web.Response:
    session: WebSession = request.app["session"]
    fragment = session.workspace_fragment()
    return web.Response(text=fragment, content_type="text/html")


async def handle_eval(request: web.Request) -> web.Response:
    data = await request.post()
    expr = data.get("expr", "")
    if not expr:
        return web.Response(status=400, text="Empty expression")
    session: WebSession = request.app["session"]
    fragment = session.evaluate(str(expr))
    return web.Response(text=fragment, content_type="text/html")


async def handle_system(request: web.Request) -> web.Response:
    data = await request.post()
    cmd = data.get("cmd", "")
    if not cmd:
        return web.Response(status=400, text="Empty command")
    session: WebSession = request.app["session"]
    fragment = session.system_command(str(cmd))
    return web.Response(text=fragment, content_type="text/html")


def _pico_eval_html(expr: str, result_text: str) -> str:
    """Format a Pico eval result as an HTML fragment."""
    input_html = html.escape(INPUT_INDENT + expr)
    if result_text.startswith("ERROR:"):
        error_html = html.escape(result_text[7:])
        return (
            f'<div class="entry">'
            f'<pre class="input">{input_html}</pre>'
            f'<pre class="error">{error_html}</pre>'
            f"</div>"
        )
    parts = [f'<pre class="input">{input_html}</pre>']
    if result_text:
        output_html = html.escape(result_text)
        parts.append(f'<pre class="output">{output_html}</pre>')
    return f'<div class="entry">{"".join(parts)}</div>'


class WSHandler:
    """Handles WebSocket messages for a single connection."""

    def __init__(self, ws: web.WebSocketResponse, app: web.Application) -> None:
        self.ws = ws
        self.session: WebSession = app["session"]
        self.pico = app.get("pico")
        self.sessions_dir: str = app.get("sessions_dir", "sessions")
        self.mode = "local"
        self._dispatch: dict[str, Any] = {
            "mode": self._handle_mode,
            "eval": self._handle_eval,
            "system": self._handle_system,
            "save_session": self._handle_save_session,
            "load_session": self._handle_load_session,
            "list_sessions": self._handle_list_sessions,
            "check_session": self._handle_check_session,
            "delete_session": self._handle_delete_session,
        }

    async def handle_message(self, data: dict[str, Any]) -> None:
        msg_type = data.get("type")
        handler = self._dispatch.get(str(msg_type))
        if handler is not None:
            await handler(data)
        else:
            await self.ws.send_json({"type": "error", "message": "Unknown message type: " + str(msg_type)})

    async def _handle_mode(self, data: dict[str, Any]) -> None:
        new_mode = data.get("mode", "")
        if new_mode == "pico" and self.pico is None:
            await self.ws.send_json({"type": "error", "message": "No Pico connected"})
        elif new_mode in ("local", "pico"):
            self.mode = new_mode
            await self.ws.send_json({"type": "mode_changed", "mode": self.mode})
        else:
            await self.ws.send_json({"type": "error", "message": "Invalid mode: " + str(new_mode)})

    async def _handle_eval(self, data: dict[str, Any]) -> None:
        import asyncio
        expr = data.get("expr", "")
        if self.mode == "pico" and self.pico is not None:
            try:
                result_text = await asyncio.get_event_loop().run_in_executor(
                    None, self.pico.eval, expr
                )
            except Exception as e:
                result_text = "ERROR: " + str(e)
            fragment = _pico_eval_html(expr, result_text)
            await self.ws.send_json({"type": "result", "html": fragment})
        else:
            try:
                fragment = self.session.evaluate(expr)
                await self.ws.send_json({"type": "result", "html": fragment})
                await self.ws.send_json({"type": "workspace", "html": self.session.workspace_fragment()})
            except Exception as e:
                error_html = html.escape(str(e))
                await self.ws.send_json({"type": "result", "html":
                    f'<div class="entry"><pre class="input">      {html.escape(expr)}</pre>'
                    f'<pre class="error">{error_html}</pre></div>'})

    async def _handle_system(self, data: dict[str, Any]) -> None:
        cmd = data.get("cmd", "")
        fragment = self.session.system_command(cmd)
        await self.ws.send_json({"type": "result", "html": fragment})
        await self.ws.send_json({"type": "workspace", "html": self.session.workspace_fragment()})

    async def _handle_save_session(self, data: dict[str, Any]) -> None:
        name = data.get("name", "")
        try:
            self.session.save_session(name, self.sessions_dir)
            await self.ws.send_json({"type": "session_saved", "name": name})
        except Exception as e:
            await self.ws.send_json({"type": "error", "message": str(e)})

    async def _handle_load_session(self, data: dict[str, Any]) -> None:
        name = data.get("name", "")
        try:
            html_content = self.session.load_session(name, self.sessions_dir)
            await self.ws.send_json({"type": "session_loaded", "html": html_content})
            await self.ws.send_json({"type": "workspace", "html": self.session.workspace_fragment()})
        except Exception as e:
            await self.ws.send_json({"type": "error", "message": str(e)})

    async def _handle_list_sessions(self, data: dict[str, Any]) -> None:
        sessions = WebSession.list_sessions(self.sessions_dir)
        await self.ws.send_json({"type": "session_list", "sessions": sessions})

    async def _handle_check_session(self, data: dict[str, Any]) -> None:
        import os
        name = data.get("name", "")
        path = os.path.join(self.sessions_dir, name + ".md")
        await self.ws.send_json({"type": "session_exists", "name": name, "exists": os.path.isfile(path)})

    async def _handle_delete_session(self, data: dict[str, Any]) -> None:
        import os
        name = data.get("name", "")
        path = os.path.join(self.sessions_dir, name + ".md")
        if os.path.isfile(path):
            os.remove(path)
            await self.ws.send_json({"type": "session_deleted", "name": name})
        else:
            await self.ws.send_json({"type": "error", "message": "Session not found: " + name})


async def handle_ws(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    handler = WSHandler(ws, request.app)

    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            try:
                data = json.loads(msg.data)
            except (json.JSONDecodeError, ValueError):
                await ws.send_json({"type": "error", "message": "Invalid JSON"})
                continue
            await handler.handle_message(data)
        elif msg.type in (web.WSMsgType.ERROR, web.WSMsgType.CLOSE):
            break

    return ws


def create_app() -> web.Application:
    app = web.Application()
    app["session"] = WebSession()
    app.router.add_get("/", handle_index)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/config", handle_config)
    app.router.add_get("/workspace", handle_workspace)
    app.router.add_post("/eval", handle_eval)
    app.router.add_post("/system", handle_system)
    app.router.add_get("/ws", handle_ws)
    return app


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8888)
    parser.add_argument("--pico-port", type=str, default=None,
                        help="Serial port for Pico (e.g. /dev/ttyACM0)")
    args = parser.parse_args()
    app = create_app()
    if args.pico_port:
        from marple.web.pico_bridge import PicoConnection
        print(f"Connecting to Pico on {args.pico_port}...")
        app["pico"] = PicoConnection(args.pico_port)
        print("Pico connected.")
    print(f"MARPLE Web REPL: http://localhost:{args.port}/")
    try:
        web.run_app(app, port=args.port, print=None, handle_signals=True)
    except KeyboardInterrupt:
        pass
