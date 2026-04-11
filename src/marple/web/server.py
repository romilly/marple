"""MARPLE Web REPL server.

Usage:
    python -m marple.web.server [--port PORT]
"""

import asyncio
import html
import json
from pathlib import Path
from typing import Any

from aiohttp import web

from marple.adapters.pride_console import PrideConsole
from marple.numpy_array import APLArray
from marple.engine import Interpreter
from marple.ports.config import Config
from marple.environment import Environment
from marple.errors import APLError
from marple.formatting import format_result

STATIC_DIR = Path(__file__).parent / "static"
INPUT_INDENT = "      "


def _is_dfn_binding(value: object) -> bool:
    """Check if value is any kind of dfn binding."""
    return hasattr(value, 'dfn') and hasattr(value, 'env')


class WebSession:
    """Wraps an interpreter for web use."""

    def __init__(self, config: 'Config | None' = None) -> None:
        self._console = PrideConsole()
        self.interp = Interpreter(console=self._console, config=config)
        self.transcript: list[tuple[str, str]] = []

    def evaluate(self, expr: str) -> str:
        """Evaluate an APL expression. Return an HTML fragment."""
        input_html = html.escape(INPUT_INDENT + expr)
        self._console.clear()
        try:
            r = self.interp.execute(expr)
            console_output = self._console.output
            if r.silent and not console_output:
                self.transcript.append((expr, ""))
                return (
                    f'<div class="entry">'
                    f'<pre class="input">{input_html}</pre>'
                    f"</div>"
                )
            output = console_output + r.display_text if not r.silent else console_output.rstrip("\n")
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
        from marple.system_commands import run_system_command
        input_html = html.escape(INPUT_INDENT + cmd)
        output, _ = run_system_command(self.interp, cmd)
        parts = [f'<pre class="input">{input_html}</pre>']
        if output:
            output_html = html.escape(output)
            parts.append(f'<pre class="output">{output_html}</pre>')
        return f'<div class="entry">{"".join(parts)}</div>'

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
        self._console = PrideConsole()
        self.interp = Interpreter(console=self._console, config=self.interp.config)
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
    from marple import __version__
    return web.json_response({"version": __version__})


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


class WSHandler:
    """Handles WebSocket messages for a single connection."""

    def __init__(self, ws: web.WebSocketResponse, app: web.Application) -> None:
        self.ws = ws
        self.session: WebSession = app["session"]
        self.sessions_dir: str = app.get("sessions_dir", self.session.interp.config.get_sessions_dir())
        self._dispatch: dict[str, Any] = {
            "eval": self._handle_eval,
            "system": self._handle_system,
            "input_response": self._handle_input_response,
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

    async def _handle_eval(self, data: dict[str, Any]) -> None:
        expr = data.get("expr", "")
        # Fire-and-forget: eval runs in background so the message loop
        # stays free to deliver input_response messages.
        asyncio.ensure_future(self._eval_with_input(expr))

    async def _handle_input_response(self, data: dict[str, Any]) -> None:
        text = data.get("text", "")
        self.session._console.provide_input(text)

    async def _eval_with_input(self, expr: str) -> None:
        """Run evaluate in a thread, polling for input requests."""
        console = self.session._console
        loop = asyncio.get_event_loop()
        eval_future = loop.run_in_executor(None, self.session.evaluate, expr)

        while not eval_future.done():
            prompt = await loop.run_in_executor(
                None, console.wait_for_prompt, 0.1)
            if prompt is not None:
                await self.ws.send_json({
                    "type": "input_request",
                    "prompt": prompt,
                })

        try:
            fragment = eval_future.result()
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
    from marple.adapters.desktop_config import DesktopConfig
    app = web.Application()
    app["session"] = WebSession(config=DesktopConfig())
    app.router.add_get("/", handle_index)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/config", handle_config)
    app.router.add_get("/workspace", handle_workspace)
    app.router.add_post("/eval", handle_eval)
    app.router.add_post("/system", handle_system)
    app.router.add_get("/ws", handle_ws)
    return app


def _print_banner(host: str, port: int) -> None:
    """Print startup banner, including a LAN-access note if bound publicly."""
    from marple import __version__
    print(f"MARPLE v{__version__} web server")
    if host in ("0.0.0.0", "::"):
        print(f"  Local:  http://localhost:{port}/")
        try:
            import socket
            lan_host = socket.gethostname()
            print(f"  LAN:    http://{lan_host}:{port}/")
        except OSError:
            pass
        print(f"  Bound to {host} — accessible from any device on this network.")
        print("  Home LAN use only: no authentication, no HTTPS.")
    else:
        print(f"  http://{host}:{port}/")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(prog="marple-server")
    parser.add_argument("--port", type=int, default=8888)
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Network interface to bind. 0.0.0.0 = all interfaces "
             "(LAN-accessible, default). 127.0.0.1 = localhost only.",
    )
    args = parser.parse_args()
    app = create_app()
    _print_banner(args.host, args.port)
    try:
        web.run_app(app, host=args.host, port=args.port,
                    print=None, handle_signals=True)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
