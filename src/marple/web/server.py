"""MARPLE Web REPL server.

Usage:
    python -m marple.web.server [--port PORT]
"""

import html
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
try:
    from typing import Any
except ImportError:
    pass
from urllib.parse import parse_qs

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


class MARPLEHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the MARPLE web REPL."""

    def do_GET(self) -> None:
        if self.path == "/":
            self._serve_file("desktop.html", "text/html")
        elif self.path == "/health":
            self._send_json({"status": "ok"})
        elif self.path == "/workspace":
            fragment = self.server.session.workspace_fragment()  # type: ignore[attr-defined]
            self._send_html(fragment)
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        body = self._read_form_body()
        if body is None:
            return
        if self.path == "/eval":
            expr = body.get("expr", [""])[0]
            if not expr:
                self.send_error(400, "Empty expression")
                return
            fragment = self.server.session.evaluate(expr)  # type: ignore[attr-defined]
            self._send_html(fragment)
        elif self.path == "/system":
            cmd = body.get("cmd", [""])[0]
            if not cmd:
                self.send_error(400, "Empty command")
                return
            fragment = self.server.session.system_command(cmd)  # type: ignore[attr-defined]
            self._send_html(fragment)
        else:
            self.send_error(404)

    def _read_form_body(self) -> dict[str, list[str]] | None:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            self.send_error(400, "Empty body")
            return None
        raw = self.rfile.read(length).decode("utf-8")
        return parse_qs(raw, keep_blank_values=True)

    def _send_html(self, fragment: str) -> None:
        data = fragment.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, obj: object) -> None:
        data = json.dumps(obj).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _serve_file(self, filename: str, content_type: str) -> None:
        path = STATIC_DIR / filename
        if not path.is_file():
            self.send_error(404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: object) -> None:
        pass  # suppress per-request logging


def create_server(port: int = 8888) -> HTTPServer:
    server = HTTPServer(("", port), MARPLEHandler)
    server.session = WebSession()  # type: ignore[attr-defined]
    return server


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8888)
    args = parser.parse_args()
    server = create_server(args.port)
    print(f"MARPLE Web REPL: http://localhost:{args.port}/")
    server.serve_forever()
