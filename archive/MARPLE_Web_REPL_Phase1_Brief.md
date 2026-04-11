# MARPLE Web REPL — Phase 1 Implementation Brief

*This document is a detailed brief for a Claude Code session. It specifies exactly what to build, how to test it, and what pitfalls to watch for. Read the whole thing before writing any code.*

---

## Goal

Build a minimal web REPL for MARPLE: a browser page with a text input and a scrolling session log. Type an APL expression, press Enter, see the result. Errors display distinctly. Workspace state persists across evaluations. System commands (`)vars`, `)fns`, `)clear`) work. No glyph input, no language bar, no syntax highlighting — those come later.

The server uses only the Python standard library (`http.server`). There are **two frontend HTML files** sharing the same server and API:

- **`index.html`** — the Pico-compatible version. Inline everything, vanilla JS, stays under 20KB through all phases. No external resources.
- **`desktop.html`** — the desktop version. Uses HTMX (loaded via `<script>` tag from a CDN or inlined). Cleaner, more declarative, benefits from HTMX in later phases (workspace panel, language bar, autocomplete).

Both frontends hit the same endpoints. The server returns **HTML fragments**, not JSON — both HTMX and vanilla JS insert them directly into the DOM. The only exception is `/health`, which returns JSON.

Playwright tests run against the desktop (HTMX) version. No npm, no build step. Playwright is a test-only dependency.

---

## Prerequisites

Before starting, confirm you can run the existing test suite:

```bash
cd /path/to/marple
pip install -e .[test]
pytest
```

All 290 existing tests should pass. If they don't, fix that first.

Then install Playwright:

```bash
pip install pytest-playwright
playwright install chromium
```

---

## The HTML fragment API

This is the key design decision: **the server returns HTML fragments, not JSON.** Both frontends insert these fragments directly into the session log. This is simpler than JSON for both sides — the server builds the HTML once, the client just appends it.

### POST `/eval`

Execute an APL expression.

**Request body:** form-encoded: `expr=2%2B3`

**Success response** (Content-Type: `text/html; charset=utf-8`):

```html
<div class="entry">
  <pre class="input">      2+3</pre>
  <pre class="output">5</pre>
</div>
```

**Error response:**

```html
<div class="entry">
  <pre class="input">      1÷0</pre>
  <pre class="error">DOMAIN ERROR</pre>
</div>
```

**Assignment (no visible output):**

```html
<div class="entry">
  <pre class="input">      M←3 4⍴⍳12</pre>
</div>
```

The 6-space indent on input lines follows APL convention. The `<pre>` tags preserve whitespace — critical for matrix alignment.

### POST `/system`

Execute a system command.

**Request body:** `cmd=%29vars` (URL-encoded `)vars`)

**Response** (same HTML fragment structure):

```html
<div class="entry">
  <pre class="input">      )vars</pre>
  <pre class="output">M  V  data</pre>
</div>
```

For `)clear`:

```html
<div class="entry">
  <pre class="input">      )clear</pre>
  <pre class="output">CLEAR WS</pre>
</div>
```

### GET `/`

Serve `desktop.html` (or `index.html` — configurable, defaulting to desktop on CPython).

### GET `/health`

Returns `{"status": "ok"}` as JSON. This is the one JSON endpoint — it's for test fixtures and Pico health checks, not for the frontend.

### Why form-encoded, not JSON

HTMX sends form data by default (`hx-post` serialises the nearest `<form>` or specified inputs as `application/x-www-form-urlencoded`). Form-encoded is the path of least resistance and equally easy to parse on the server (`urllib.parse.parse_qs`). The Pico vanilla JS frontend can send form-encoded just as trivially.

---

## What to create

### 1. `src/marple/web/__init__.py`

Empty file. Makes `web` a package.

### 2. `src/marple/web/server.py`

A self-contained HTTP server module. Key design points:

**Interpreter integration.** The server needs a single `Interpreter` instance that persists across requests. Look at how `repl.py` creates and uses the interpreter — it instantiates `Interpreter()` and calls methods on it. The web server does the same thing, just over HTTP instead of stdin/stdout.

**Important: study the existing code first.** Before writing the server, read these files carefully:

- `src/marple/interpreter.py` — find the `Interpreter` class, its constructor, and how to evaluate an expression. Look for a method like `evaluate()` or `execute()` that takes a string and returns a result. Check what exceptions it raises on errors (e.g. `APLError`, `SyntaxError`, or similar).
- `src/marple/repl.py` — see how the REPL formats output. The REPL calls the interpreter, gets a result (an `APLArray`), and formats it for display. Find where `⍕` (format) is applied, or where the result is converted to a string. The web server needs to do the same formatting.
- `src/marple/workspace.py` — see how system commands like `)vars`, `)fns`, `)clear` are handled. The REPL dispatches these before they reach the interpreter. The web server needs the same dispatch logic.

**The `/eval` endpoint** receives form-encoded `expr=...`, evaluates the expression, and returns an HTML fragment (see API section above).

**The `/system` endpoint** receives form-encoded `cmd=...` and returns an HTML fragment.

System commands start with `)`. The frontend decides which endpoint to call based on whether the input starts with `)`.

**The `/` endpoint** serves `desktop.html` from the `static/` subdirectory (or `index.html` — make this configurable or auto-detect based on platform).

**The `/health` endpoint** returns `{"status": "ok"}` as JSON.

**CORS:** Not needed — the frontend is served from the same origin.

**Threading:** `http.server.HTTPServer` is single-threaded by default. That's fine for Phase 1. The interpreter is not thread-safe anyway.

**Skeleton structure:**

```python
"""MARPLE Web REPL server.

Usage:
    python -m marple.web.server [--port PORT]
"""

import html
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs

# Import the interpreter — adjust these imports based on what you find
# in the actual codebase. The names below are my best guesses.
from marple.interpreter import Interpreter

STATIC_DIR = Path(__file__).parent / 'static'
INPUT_INDENT = '      '  # 6 spaces — APL convention


class WebSession:
    """Wraps an Interpreter instance for web use."""
    
    def __init__(self):
        self.interpreter = Interpreter()
    
    def evaluate(self, expr: str) -> str:
        """Evaluate an APL expression. Return an HTML fragment."""
        input_html = html.escape(INPUT_INDENT + expr)
        try:
            # Study repl.py to see how it:
            # 1. Passes the expression to the interpreter
            # 2. Catches APL errors
            # 3. Formats the result as a string
            result_str = ...  # get formatted result string
            
            if result_str:  # non-empty = expression with visible output
                output_html = html.escape(result_str)
                return (f'<div class="entry">'
                        f'<pre class="input">{input_html}</pre>'
                        f'<pre class="output">{output_html}</pre>'
                        f'</div>')
            else:  # assignment — no visible output
                return (f'<div class="entry">'
                        f'<pre class="input">{input_html}</pre>'
                        f'</div>')
        except Exception as e:
            # Catch APL errors — adjust exception type based on codebase
            error_html = html.escape(str(e))
            return (f'<div class="entry">'
                    f'<pre class="input">{input_html}</pre>'
                    f'<pre class="error">{error_html}</pre>'
                    f'</div>')
    
    def system_command(self, cmd: str) -> str:
        """Execute a system command. Return an HTML fragment."""
        input_html = html.escape(INPUT_INDENT + cmd)
        try:
            result_str = ...  # execute system command, capture output
            output_html = html.escape(result_str) if result_str else ''
            parts = [f'<pre class="input">{input_html}</pre>']
            if output_html:
                parts.append(f'<pre class="output">{output_html}</pre>')
            return f'<div class="entry">{"".join(parts)}</div>'
        except Exception as e:
            error_html = html.escape(str(e))
            return (f'<div class="entry">'
                    f'<pre class="input">{input_html}</pre>'
                    f'<pre class="error">{error_html}</pre>'
                    f'</div>')


class MARPLEHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the MARPLE web REPL."""
    
    def do_GET(self):
        if self.path == '/':
            self.serve_file('desktop.html', 'text/html')
        elif self.path == '/health':
            self.send_json({"status": "ok"})
        else:
            self.send_error(404)
    
    def do_POST(self):
        body = self.read_form_body()
        if body is None:
            return
        
        if self.path == '/eval':
            expr = body.get('expr', [''])[0]
            fragment = self.server.session.evaluate(expr)
            self.send_html(fragment)
        elif self.path == '/system':
            cmd = body.get('cmd', [''])[0]
            fragment = self.server.session.system_command(cmd)
            self.send_html(fragment)
        else:
            self.send_error(404)
    
    def read_form_body(self):
        """Read and parse a form-encoded POST body."""
        length = int(self.headers.get('Content-Length', 0))
        if length == 0:
            self.send_error(400, 'Empty body')
            return None
        raw = self.rfile.read(length).decode('utf-8')
        return parse_qs(raw, keep_blank_values=True)
    
    def send_html(self, fragment: str):
        """Send an HTML fragment response."""
        data = fragment.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    
    def send_json(self, obj):
        """Send a JSON response."""
        data = json.dumps(obj).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    
    def serve_file(self, filename, content_type):
        """Serve a static file."""
        path = STATIC_DIR / filename
        if not path.is_file():
            self.send_error(404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', f'{content_type}; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    
    def log_message(self, format, *args):
        pass  # suppress per-request logging (noisy during tests)


def create_server(port=8888):
    server = HTTPServer(('', port), MARPLEHandler)
    server.session = WebSession()  # type: ignore
    return server


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8888)
    args = parser.parse_args()
    
    server = create_server(args.port)
    print(f'MARPLE Web REPL: http://localhost:{args.port}/')
    server.serve_forever()
```

**Critical things to discover from the codebase:**

1. What is the exact import path for the Interpreter class?
2. What method evaluates an expression? What does it return?
3. What exception types are raised on APL errors? (DOMAIN ERROR, INDEX ERROR, LENGTH ERROR, RANK ERROR, SYNTAX ERROR, VALUE ERROR)
4. How does `repl.py` format an `APLArray` result as a string for display?
5. How does `repl.py` handle system commands? Is there a method or class for this?
6. Does the interpreter need any setup beyond `Interpreter()`?

The answers to these questions determine the implementation of `WebSession`. **Do not guess — read the code.**

**HTML escaping is essential.** The server builds HTML fragments containing user input and interpreter output. Both must be escaped via `html.escape()` to prevent XSS and to correctly display characters like `<`, `>`, `&` that appear in APL output (e.g. `<` is the Less Than function). The skeleton above shows where escaping goes.

### 3. `src/marple/web/static/desktop.html`

The desktop frontend using HTMX. The HTMX library is loaded from a CDN (`<script src="https://unpkg.com/htmx.org@2.0.4"></script>` or similar — pin the version).

**Layout:**

```
┌──────────────────────────────────────┐
│            MARPLE Web REPL           │  ← header (small)
├──────────────────────────────────────┤
│                                      │
│  [scrolling session log area]        │  ← grows, shows input/output pairs
│                                      │
│      2+3                             │  ← user input (indented 6 spaces)
│  5                                   │  ← output
│      1÷0                             │
│  DOMAIN ERROR                        │  ← error in distinct colour
│      M←3 4⍴⍳12                       │
│      M                               │
│   1  2  3  4                         │  ← matrix output, pre-formatted
│   5  6  7  8                         │
│   9 10 11 12                         │
│                                      │
├──────────────────────────────────────┤
│ [input field                    ] ⏎  │  ← text input + submit
└──────────────────────────────────────┘
```

**Styling:**
- Dark background (`#1a1a2e` or similar), light text (`#e0e0e0`)
- Monospace font: `'APL385 Unicode', 'DejaVu Sans Mono', 'Courier New', monospace`
- Session log area: scrollable, auto-scrolls to bottom on new output
- Error lines (`pre.error`): red text or red left border — visually distinct
- Input field at bottom, full width, same monospace font, dark themed

**The HTMX approach — and why Phase 1 uses plain JS alongside it:**

Include the HTMX `<script>` tag now (it costs nothing on desktop and is needed for later phases), but the Phase 1 submission logic is plain JS using `fetch`. This is because the HTMX model (`hx-post`, `hx-target`, `hx-swap="beforeend"`) doesn't natively handle the routing decision (should the input go to `/eval` or `/system`?), or the "clear input on submit" behaviour, without extra JS anyway. HTMX earns its keep in later phases where it handles the workspace panel refresh and the language bar — declarative partial updates that would otherwise need custom JS event wiring.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MARPLE</title>
    <script src="https://unpkg.com/htmx.org@2.0.4"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #1a1a2e;
            color: #e0e0e0;
            font-family: 'APL385 Unicode', 'DejaVu Sans Mono',
                         'Courier New', monospace;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        h1 {
            padding: 0.5em;
            font-size: 1em;
            color: #8888aa;
            text-align: center;
        }
        #session {
            flex: 1;
            overflow-y: auto;
            padding: 0.5em 1em;
        }
        pre {
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        pre.input { color: #c0c0c0; }
        pre.output { color: #e0e0e0; }
        pre.error { color: #ff6b6b; }
        #input-bar {
            display: flex;
            padding: 0.5em;
            border-top: 1px solid #333;
            background: #16213e;
        }
        #input {
            flex: 1;
            background: #0f3460;
            color: #e0e0e0;
            border: 1px solid #444;
            padding: 0.5em;
            font-family: inherit;
            font-size: 1em;
            outline: none;
        }
        #input:focus { border-color: #6b8afd; }
    </style>
</head>
<body>
    <h1>MARPLE</h1>
    <div id="session"></div>
    <div id="input-bar">
        <input type="text" id="input"
               autocomplete="off" autocorrect="off"
               autocapitalize="off" spellcheck="false"
               placeholder="APL expression">
    </div>

    <script>
    const input = document.getElementById('input');
    const session = document.getElementById('session');

    input.addEventListener('keydown', async function(e) {
        if (e.key !== 'Enter') return;
        e.preventDefault();

        const text = input.value.trim();
        if (!text) return;
        input.value = '';

        const url = text.startsWith(')') ? '/system' : '/eval';
        const param = text.startsWith(')') ? 'cmd' : 'expr';
        const body = new URLSearchParams();
        body.set(param, text);

        try {
            const resp = await fetch(url, {
                method: 'POST',
                headers: {'Content-Type':
                    'application/x-www-form-urlencoded'},
                body: body.toString()
            });
            const fragment = await resp.text();
            session.insertAdjacentHTML('beforeend', fragment);
            session.scrollTop = session.scrollHeight;
        } catch (err) {
            session.insertAdjacentHTML('beforeend',
                '<div class="entry">' +
                '<pre class="error">Connection error</pre>' +
                '</div>');
        }

        input.focus();
    });

    input.focus();
    </script>
</body>
</html>
```

**Important HTML details:**
- `autocomplete="off"`, `autocorrect="off"`, `autocapitalize="off"`, `spellcheck="false"` on the input — browser auto-correction mangles APL
- `<pre>` tags for all output — preserves whitespace alignment for matrices
- `pre { white-space: pre-wrap; }` — allows long lines to wrap rather than overflow

### 4. `src/marple/web/static/index.html`

The Pico-compatible version. Identical layout and styling, but with all CSS and JS inline (no CDN `<script>` tags, no external resources). This is a copy of `desktop.html` with the HTMX `<script>` tag removed. In Phase 1 the two files are nearly identical. They diverge in later phases when the desktop version adds HTMX-driven features.

**Size budget:** < 5KB for Phase 1, < 20KB through all phases.

### 5. `tests/web/__init__.py`

Empty file.

### 6. `tests/web/conftest.py`

Pytest fixtures for starting the server and providing Playwright pages.

```python
import pytest
import threading
import time
import urllib.request
from marple.web.server import create_server


@pytest.fixture(scope="module")
def server_url():
    """Start a MARPLE web server on a free port, yield its URL."""
    server = create_server(port=0)
    port = server.server_address[1]
    url = f'http://localhost:{port}'
    
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    
    # Wait for server to be ready
    for _ in range(50):
        try:
            urllib.request.urlopen(f'{url}/health', timeout=1)
            break
        except Exception:
            time.sleep(0.1)
    else:
        raise RuntimeError('Server did not start')
    
    yield url
    
    server.shutdown()


@pytest.fixture
def page(server_url):
    """Provide a fresh Playwright browser page pointed at the server."""
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page()
        pg.goto(server_url)
        yield pg
        browser.close()
```

**Notes on the fixture design:**

- `server_url` is module-scoped: the server starts once per test file, not per test. Much faster.
- `page` is function-scoped: each test gets a fresh browser page. Tests that need clean interpreter state should submit `)clear` as their first action.
- The `daemon=True` thread means the server dies when the test process exits.
- `port=0` lets the OS pick a free port, avoiding conflicts.

### 7. `tests/web/test_phase1_repl.py`

The Playwright tests. Each test interacts with the browser page as a user would.

**Helper functions:**

```python
def submit_expr(page, text):
    """Type an expression and press Enter, wait for response."""
    input_el = page.locator('#input')
    input_el.fill(text)
    count_before = page.locator('.entry').count()
    input_el.press('Enter')
    # Wait for a new .entry to appear (the server responded)
    page.locator(f'.entry:nth-child({count_before + 1})').wait_for(
        timeout=3000)


def get_session_text(page):
    """Get all text from the session log."""
    return page.locator('#session').inner_text()
```

The key improvement over `wait_for_timeout(500)`: count `.entry` divs before submission and wait for one more to appear. This is deterministic — the test proceeds as soon as the server responds.

**Tests:**

```python
def test_health_endpoint(server_url):
    """The /health endpoint returns ok."""
    import urllib.request, json
    resp = urllib.request.urlopen(f'{server_url}/health')
    data = json.loads(resp.read())
    assert data == {"status": "ok"}


def test_page_loads(page):
    """The frontend loads and shows an input field."""
    assert page.locator('#input').is_visible()


def test_simple_arithmetic(page):
    """Submit 2+3, expect 5 in the output."""
    submit_expr(page, '2+3')
    assert '5' in get_session_text(page)


def test_iota(page):
    """Submit ⍳5, expect 1 2 3 4 5."""
    submit_expr(page, '⍳5')
    text = get_session_text(page)
    assert '1 2 3 4 5' in text


def test_domain_error(page):
    """Submit 1÷0, expect a DOMAIN ERROR."""
    submit_expr(page, '1÷0')
    text = get_session_text(page)
    assert 'DOMAIN ERROR' in text
    assert page.locator('pre.error').count() > 0


def test_state_persists(page):
    """Define a variable, then use it in the next expression."""
    submit_expr(page, 'X←42')
    submit_expr(page, 'X+1')
    assert '43' in get_session_text(page)


def test_matrix_output(page):
    """Define and display a matrix. Check output is pre-formatted."""
    submit_expr(page, 'M←3 4⍴⍳12')
    submit_expr(page, 'M')
    text = get_session_text(page)
    assert '1' in text and '12' in text
    assert page.locator('pre.output').count() > 0


def test_empty_input_does_nothing(page):
    """Pressing Enter with empty input should not add anything."""
    count_before = page.locator('.entry').count()
    page.locator('#input').press('Enter')
    page.wait_for_timeout(300)
    count_after = page.locator('.entry').count()
    assert count_before == count_after


def test_system_command_vars(page):
    """Define variables, then )vars should list them."""
    submit_expr(page, 'A←1')
    submit_expr(page, 'B←2')
    submit_expr(page, ')vars')
    text = get_session_text(page)
    assert 'A' in text and 'B' in text


def test_system_command_clear(page):
    """After )clear, the response should confirm clearing."""
    submit_expr(page, 'X←99')
    submit_expr(page, ')clear')
    text = get_session_text(page)
    assert 'CLEAR' in text.upper()


def test_assignment_no_visible_output(page):
    """An assignment like X←5 should show the input but no output."""
    submit_expr(page, 'X←5')
    entry = page.locator('.entry').last
    assert entry.locator('pre.input').count() == 1
    assert entry.locator('pre.output').count() == 0
    assert entry.locator('pre.error').count() == 0


def test_dfn_definition_and_use(page):
    """Define a dfn and then call it."""
    submit_expr(page, 'double←{⍵+⍵}')
    submit_expr(page, 'double 21')
    assert '42' in get_session_text(page)


def test_input_clears_after_submit(page):
    """The input field should be empty after submission."""
    page.locator('#input').fill('2+3')
    count_before = page.locator('.entry').count()
    page.locator('#input').press('Enter')
    page.locator(f'.entry:nth-child({count_before + 1})').wait_for(
        timeout=3000)
    assert page.locator('#input').input_value() == ''


def test_multiple_expressions_accumulate(page):
    """Multiple submissions should all appear in the session log."""
    submit_expr(page, '1+1')
    submit_expr(page, '2+2')
    submit_expr(page, '3+3')
    assert page.locator('.entry').count() == 3
    text = get_session_text(page)
    assert '2' in text and '4' in text and '6' in text
```

**Important testing considerations:**

- **Waiting strategy:** `submit_expr` counts `.entry` divs before and after, waiting for the new one. Robust and doesn't depend on fixed timeouts.
- **Unicode in tests:** The test strings contain APL characters (`⍴`, `⍳`, `⍵`, `←`). Playwright handles Unicode `fill()` correctly.
- **Test isolation:** Tests share a server (module-scoped) but get fresh browser pages (function-scoped). The interpreter accumulates state across tests in the same module. If a test needs a clean workspace, submit `)clear` first.

---

## What NOT to build in Phase 1

- No backtick glyph input (Phase 2)
- No language bar (Phase 3)
- No history/recall with arrow keys (Phase 4)
- No multi-line input / Shift+Enter (Phase 5)
- No table formatting for arrays (Phase 6)
- No workspace panel (Phase 7)
- No WebSocket — plain HTTP only

---

## File structure when done

```
src/marple/
  web/
    __init__.py
    server.py              # ~150-200 lines
    static/
      desktop.html         # ~120 lines (includes HTMX <script> tag)
      index.html           # ~110 lines (no external resources, Pico-ready)
tests/
  web/
    __init__.py
    conftest.py            # ~40 lines
    test_phase1_repl.py    # ~120 lines
```

---

## Potential pitfalls

### The interpreter API might not be what I've assumed

I've inferred the API from the status doc and README, but I haven't seen the actual source. The interpreter might:
- Have a different class name than `Interpreter`
- Return something other than an `APLArray` from evaluation
- Need an environment or workspace object passed to its constructor
- Handle system commands internally rather than in `repl.py`

**Action:** read `interpreter.py` and `repl.py` first. Adjust the `WebSession` class to match what you find.

### System command handling

The REPL probably checks for `)` prefix and dispatches to workspace commands before reaching the expression evaluator. The web server needs to replicate this dispatch. Look for how `)vars` returns a space-separated list of variable names, how `)fns` lists functions, and how `)clear` resets the workspace. The command output may be printed to stdout in the REPL — for the web server, it needs to be captured as a string.

**If system commands print to stdout:** you may need to capture stdout during command execution using `io.StringIO` and `contextlib.redirect_stdout`.

### Assignment vs expression

In APL, `X←5` is an assignment and produces no display output. `X+1` is an expression and does. The interpreter may distinguish these (returning `None` for assignments) or it may return the assigned value. Check what the REPL does — it probably suppresses output for assignments. The web server should match: if the result is None or empty, the HTML fragment should contain the input `<pre>` but no output `<pre>`.

### HTML escaping

The server builds HTML fragments containing user input and interpreter output. **Both must be escaped via `html.escape()`** to prevent XSS and to correctly display characters like `<`, `>`, `&` that appear in APL (e.g. `<` is the Less Than function, `>` is Greater Than). Without escaping, `3<5` would produce `1` but the input line would contain a broken HTML tag.

### Matrix formatting and `<pre>` tags

The `⍕` function (or whatever formatting the REPL uses) produces correctly aligned columns for matrix output. The `<pre>` tags in the HTML fragment preserve this whitespace. Make sure the server returns the formatted string with spaces/newlines intact.

### Form-encoded parsing

`parse_qs` returns **lists** for each key (because query strings can have repeated keys). So `parse_qs('expr=2%2B3')` returns `{'expr': ['2+3']}`, and you need `body.get('expr', [''])[0]` to get the string. This is a common gotcha.

### Port 0 for tests

`HTTPServer(('', 0), handler)` binds to a random free port. After construction, `server.server_address[1]` gives the actual port. Essential for tests to avoid port conflicts.

### HTMX CDN availability

The desktop HTML loads HTMX from `unpkg.com`. If the network is unavailable, the page still works — the Phase 1 JS doesn't use any HTMX features yet. For offline desktop use, consider inlining the HTMX source (14KB minified) later. For now, CDN is fine.

---

## Definition of done

Phase 1 is complete when:

1. `python -m marple.web.server` starts a web server on port 8888
2. Opening `http://localhost:8888/` in a browser shows the REPL interface
3. Typing `2+3` and pressing Enter shows `5`
4. Typing `1÷0` shows `DOMAIN ERROR` in red
5. Typing `M←3 4⍴⍳12` then `M` shows a formatted matrix
6. Typing `)vars` after defining variables lists them
7. Typing `)clear` resets the workspace
8. All Playwright tests pass: `pytest tests/web/ -v`
9. All existing MARPLE tests still pass: `pytest tests/ -v`
10. No new pip dependencies except Playwright (test only)
11. `index.html` (Pico version) is under 5KB
12. `pyright src/` still passes (or at least the web module does)
13. Both `desktop.html` and `index.html` exist and work with the same server

---

## Sequence of work

1. **Read** `interpreter.py`, `repl.py`, `workspace.py` to understand the actual API
2. **Write** `tests/web/conftest.py` — the server fixture
3. **Write** a minimal `server.py` — just `/health` and `GET /` serving a placeholder HTML
4. **Write** a minimal `desktop.html` — just the layout and styling, no JS yet
5. **Write** `test_phase1_repl.py` — start with `test_health_endpoint` and `test_page_loads`
6. **Run tests** — get the first two passing
7. **Add** the `/eval` endpoint to the server, returning HTML fragments
8. **Add** the JS submission logic to `desktop.html`
9. **Write and pass** `test_simple_arithmetic`
10. **Add** error handling — pass `test_domain_error`
11. **Add** the `/system` endpoint — pass `test_system_command_vars` and `test_system_command_clear`
12. **Pass** remaining tests one by one
13. **Copy** `desktop.html` → `index.html`, remove the HTMX `<script>` tag
14. **Clean up**, check size budget, run `pyright`
