"""MARPLE Web REPL server.

Usage:
    python -m marple.web.server [--port PORT]
"""

import html
import json
from pathlib import Path
try:
    from typing import Any
except ImportError:
    pass

from aiohttp import web

from marple.arraymodel import APLArray
from marple.errors import APLError
from marple.interpreter import default_env, interpret, _DfnClosure
from marple.repl import format_result, _is_silent

STATIC_DIR = Path(__file__).parent / "static"
INPUT_INDENT = "      "


class WebSession:
    """Wraps an interpreter environment for web use."""

    def __init__(self) -> None:
        self.env: dict[str, Any] = default_env()

    def evaluate(self, expr: str) -> str:
        """Evaluate an APL expression. Return an HTML fragment."""
        input_html = html.escape(INPUT_INDENT + expr)
        try:
            result = interpret(expr, self.env)
            if _is_silent(expr):
                return (
                    f'<div class="entry">'
                    f'<pre class="input">{input_html}</pre>'
                    f"</div>"
                )
            output_html = html.escape(format_result(result, self.env))
            return (
                f'<div class="entry">'
                f'<pre class="input">{input_html}</pre>'
                f'<pre class="output">{output_html}</pre>'
                f"</div>"
            )
        except APLError as e:
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

    def _run_system_command(self, cmd: str) -> str:
        """Execute a system command and return the output string."""
        if cmd == ")clear":
            self.env.clear()
            self.env.update(default_env())
            return "CLEAR WS"
        if cmd == ")vars":
            names = sorted(
                n for n in self.env
                if not n.startswith("⎕") and not n.startswith("__")
                and n not in ("⍵", "⍺", "∇")
                and isinstance(self.env[n], APLArray)
            )
            return "  ".join(names)
        if cmd == ")fns":
            names = sorted(
                n for n in self.env
                if not n.startswith("⎕") and not n.startswith("__")
                and n not in ("⍵", "⍺", "∇")
                and isinstance(self.env[n], _DfnClosure)
            )
            return "  ".join(names)
        if cmd.startswith(")wsid"):
            parts = cmd.split(None, 1)
            if len(parts) > 1:
                self.env["⎕WSID"] = APLArray([len(parts[1])], list(parts[1]))
                return parts[1]
            wsid = self.env.get("⎕WSID")
            if isinstance(wsid, APLArray):
                return "".join(str(c) for c in wsid.data)
            return "CLEAR WS"
        return f"Unknown command: {cmd}"

    def workspace_fragment(self) -> str:
        """Return an HTML fragment listing variables and functions."""
        vars_list = []
        fns_list = []
        for name in sorted(self.env):
            if name.startswith("⎕") or name.startswith("__"):
                continue
            if name in ("⍵", "⍺", "∇"):
                continue
            val = self.env[name]
            if isinstance(val, APLArray):
                shape_str = " ".join(str(s) for s in val.shape) if val.shape else "scalar"
                vars_list.append(
                    f'<div class="ws-item" data-name="{html.escape(name)}">'
                    f'{html.escape(name)} '
                    f'<span class="ws-shape">{shape_str}</span></div>'
                )
            elif isinstance(val, _DfnClosure):
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


async def handle_index(request: web.Request) -> web.Response:
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


async def handle_ws(request: web.Request) -> web.WebSocketResponse:
    import asyncio

    ws = web.WebSocketResponse()
    await ws.prepare(request)
    session: WebSession = request.app["session"]
    pico = request.app.get("pico")
    mode = "local"

    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            try:
                data = json.loads(msg.data)
            except (json.JSONDecodeError, ValueError):
                await ws.send_json({"type": "error", "message": "Invalid JSON"})
                continue
            msg_type = data.get("type")
            if msg_type == "mode":
                new_mode = data.get("mode", "")
                if new_mode == "pico" and pico is None:
                    await ws.send_json({"type": "error", "message": "No Pico connected"})
                elif new_mode in ("local", "pico"):
                    mode = new_mode
                    await ws.send_json({"type": "mode_changed", "mode": mode})
                else:
                    await ws.send_json({"type": "error", "message": "Invalid mode: " + str(new_mode)})
            elif msg_type == "eval":
                expr = data.get("expr", "")
                if mode == "pico" and pico is not None:
                    try:
                        result_text = await asyncio.get_event_loop().run_in_executor(
                            None, pico.eval, expr
                        )
                    except Exception as e:
                        result_text = "ERROR: " + str(e)
                    fragment = _pico_eval_html(expr, result_text)
                    await ws.send_json({"type": "result", "html": fragment})
                else:
                    fragment = session.evaluate(expr)
                    await ws.send_json({"type": "result", "html": fragment})
                    await ws.send_json({"type": "workspace", "html": session.workspace_fragment()})
            elif msg_type == "system":
                cmd = data.get("cmd", "")
                fragment = session.system_command(cmd)
                await ws.send_json({"type": "result", "html": fragment})
                await ws.send_json({"type": "workspace", "html": session.workspace_fragment()})
            else:
                await ws.send_json({"type": "error", "message": "Unknown message type: " + str(msg_type)})
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
    web.run_app(app, port=args.port, print=None)
