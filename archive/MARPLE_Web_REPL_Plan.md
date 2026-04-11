# MARPLE Web REPL: Incremental Development Plan

*A minimalist web interface for MARPLE, developed incrementally with TDD using Playwright, designed to also run on Pico W / Pico 2 W.*

---

## 1. The two-target constraint

The Pico W runs MicroPython (or CircuitPython) with ~264KB RAM and a single-core 133MHz RP2040 (Pico 2 W: dual-core 150MHz RP2350, 520KB RAM). This constrains the web server and frontend in important ways:

- **No frameworks.** No Flask, no FastAPI, no Jinja. The Pico needs a bare HTTP server — `asyncio` + raw socket handling, or MicroPython's `microdot` (a ~50KB Flask-alike that runs on MicroPython).
- **Minimal Pico frontend.** Every byte of HTML/CSS/JS served from the Pico's filesystem (or flash) counts. The Pico frontend (`index.html`) must be a single HTML file with inline CSS and JS, staying under 20KB through all phases. No React, no build step, no npm, no CDN dependencies.
- **Richer desktop frontend.** The desktop version (`desktop.html`) can afford external dependencies. It loads HTMX from a CDN for declarative partial-page updates — useful from Phase 3 onwards (language bar, workspace panel, autocomplete). In Phase 1 the two files are nearly identical; they diverge as features accumulate.
- **Same server, same API.** Both frontends hit the same HTTP endpoints. The desktop CPython server and the Pico MicroPython server both speak the same API. The server returns HTML fragments, not JSON, so both frontends insert responses directly into the DOM.
- **Stateful session.** The interpreter holds workspace state (variables, functions). The web server must maintain a single interpreter instance across requests — not spawn a new process per request.

The development strategy: **build and test on desktop first** (CPython, full MARPLE, Playwright tests against `desktop.html`), then port the server layer to MicroPython for the Pico. The API contract is shared; the Pico uses `index.html`.

---

## 2. API contract

The API is deliberately minimal — enough for a REPL, extensible later. **The server returns HTML fragments, not JSON.** Both frontends insert these fragments directly into the session log. This is simpler than JSON for both sides — the server builds the HTML once, the client just appends it.

### POST `/eval`

Execute an APL expression in the current session.

**Request:** form-encoded body: `expr=2%2B3`

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

The 6-space indent on input lines follows APL convention. The `<pre>` tags preserve whitespace — critical for matrix alignment. All user input and interpreter output is HTML-escaped to handle APL's `<`, `>`, and `&` functions safely.

### POST `/system`

Execute a system command (`)fns`, `)vars`, `)clear`, etc.).

**Request:** form-encoded body: `cmd=%29vars`

**Response** (same HTML fragment structure):

```html
<div class="entry">
  <pre class="input">      )vars</pre>
  <pre class="output">M  V  data</pre>
</div>
```

Separated from `/eval` because system commands are not APL expressions — they don't go through the parser. This also makes it easy to restrict or extend system commands independently.

### Why form-encoded, not JSON

HTMX sends form data by default (`hx-post` serialises inputs as `application/x-www-form-urlencoded`). Form-encoded is the path of least resistance and equally easy to parse server-side (`urllib.parse.parse_qs` in CPython, trivial in MicroPython). The Pico vanilla JS frontend can send form-encoded just as easily.

### Why HTML fragments, not JSON

Both frontends need to insert the result into the session log. With JSON, the client must parse the response, construct DOM elements, apply CSS classes, and append them. With HTML fragments, it's a single `insertAdjacentHTML('beforeend', response)` call — same on desktop and Pico. The server does the HTML construction once, using `html.escape()` for safety. This also sets up cleanly for HTMX in later phases, where `hx-swap="beforeend"` expects HTML.

### GET `/`

Serve `desktop.html` on CPython, `index.html` on the Pico. (Configurable or auto-detected.)

### GET `/health`

Returns `{"status": "ok"}` as JSON. This is the one JSON endpoint — it's for test fixtures and Pico health checks, not for the frontend.

### Future endpoints (not in initial phases)

- `GET /glyphs` — return the glyph mapping (as HTML fragment or JSON) for dynamic language bar generation
- `GET /workspace` — return workspace state as an HTML fragment for the workspace panel (HTMX `hx-get` with polling)
- `POST /complete` — autocomplete suggestions for a partial expression
- `WebSocket /ws` — upgrade to persistent connection for lower latency (important on Pico W where HTTP overhead per request is costly)

---

## 3. Incremental phases

Each phase produces a working, tested increment. Phases are ordered by value delivered — the earliest phases give the most important functionality.

### Phase 1: Bare REPL — execute and display

**What it does:** A text input box and a scrolling output area. Type an APL expression, press Enter, see the result. Errors display in red. That's it.

**Server:**
- `src/marple/web/server.py` using `http.server` (stdlib, no dependencies)
- Creates a single `Interpreter` instance on startup
- Implements `POST /eval`, `POST /system`, `GET /`, `GET /health`
- Returns HTML fragments for `/eval` and `/system`; JSON for `/health`
- Parses form-encoded request bodies

**Frontend (both files):**
- Dark background, monospace font, scrolling session log, input at bottom
- Enter submits; input cleared after submission
- Session log shows input (6-space indent) and output as `<pre>` elements
- Errors styled distinctly (red text)
- `desktop.html` includes HTMX `<script>` tag (for later phases); `index.html` is self-contained

**Playwright tests:**
- Server starts, `/health` returns 200
- Submit `2+3`, output area contains `5`
- Submit `1÷0`, output area contains `DOMAIN ERROR` in error styling
- Submit `M←3 4⍴⍳12` then `M`, output shows the formatted matrix
- State persists: define a variable, then reference it in the next expression
- Empty input does nothing
- System command `)vars` lists defined variables
- `)clear` resets the workspace

**Size budget:** Pico `index.html` < 5KB. Server module < 200 lines.

**Full implementation detail** is in the separate document `MARPLE_Web_REPL_Phase1_Brief.md`.

---

### Phase 2: Backtick glyph input

**What it does:** Typing `` `r `` in the input box produces `⍴`. Typing `` `` `` (double backtick) produces a literal backtick. This mirrors the terminal REPL's existing glyph input.

**Frontend changes:**
- A `keydown` handler on the input element
- After a backtick, the next character is looked up in a glyph map (a JS object: `{r: '⍴', o: '∘', ...}`)
- The glyph map is embedded in the HTML (extracted from MARPLE's `glyphs.py`)
- Visual feedback: after backtick, the input border or cursor changes colour briefly to indicate "prefix mode"

**Playwright tests:**
- Type `` `r `` → input contains `⍴`
- Type `` `i `` → input contains `⍳`
- Type `` `` `` → input contains `` ` ``
- Type `` `x `` (unmapped) → input contains `` `x `` (no transformation, or just `x` — match terminal REPL behaviour)
- Type a full expression using backtick input, submit, verify correct result
- Backtick mode is cancelled by Escape

**Size increment:** ~2KB of JS for the handler + glyph map.

---

### Phase 3: Language bar

**What it does:** A clickable bar of APL glyphs above (or below) the input area. Click a glyph to insert it at the cursor position. Hover to see the glyph name, keyboard shortcut, and brief description.

**Frontend changes:**
- A `<div>` containing one `<button>` or `<span>` per glyph, grouped logically (arithmetic, comparison, structural, operators)
- Click inserts the glyph into the input at the current cursor position
- Tooltip on hover: e.g. `⍴ — Rho — Shape/Reshape — `r`
- The glyph data can be served from `/glyphs` or embedded in the HTML
- **Desktop (HTMX opportunity):** the language bar could be loaded via `hx-get="/glyphs"` on page load, keeping the HTML file smaller and the glyph data server-authoritative

**Playwright tests:**
- Language bar is visible on page load
- Click `⍴` button → `⍴` appears in input
- Click multiple glyphs → they appear in sequence
- Hover over a glyph → tooltip appears with name and shortcut
- Click glyph when cursor is mid-expression → glyph inserted at cursor position

**Size increment:** ~3KB for the bar HTML/CSS + glyph metadata.

---

### Phase 4: Session history and recall

**What it does:** Up/Down arrow keys in the input box cycle through previously entered expressions (like the terminal REPL's history, or shell history). History persists within the browser session (not across page reloads — that's a later enhancement).

**Frontend changes:**
- A JS array storing submitted expressions
- Up arrow: replace input with the previous expression in history
- Down arrow: move forward in history
- History pointer resets when a new expression is submitted
- Optionally: Ctrl+R for reverse-search (later)

**Playwright tests:**
- Submit three expressions, press Up three times → see them in reverse order
- Down arrow moves forward
- Editing a recalled expression and submitting adds it as a new entry
- Up arrow at the oldest entry stays there (no wrap)
- Down arrow past the newest entry clears the input

**Size increment:** ~1KB of JS.

---

### Phase 5: Multi-line input and dfn editing

**What it does:** Shift+Enter inserts a newline in the input (instead of submitting). This allows entering multi-line dfns directly:

```
sort ← {⍵[⍋⍵]}
```

or multi-line expressions with diamonds:

```
A←3 4⍴⍳12 ⋄ (+/⍤1) A
```

**Frontend changes:**
- Input changes from `<input>` to `<textarea>` (or was already — just enable multiline)
- Enter submits; Shift+Enter adds a newline
- Auto-resize textarea height to fit content (up to a max)
- Display multi-line inputs in the transcript with proper formatting

**Playwright tests:**
- Shift+Enter adds a newline, does not submit
- Enter submits the full multi-line content
- Multi-line dfn definition works: define `sort ← {⍵[⍋⍵]}` across lines, then use it
- Textarea grows with content
- Multi-line input displays correctly in the session transcript

**Size increment:** ~1KB of JS/CSS.

---

### Phase 6: Output formatting — arrays as tables

**What it does:** When the result is a matrix or higher-rank array, display it as a formatted grid rather than plain text. This is a rendering enhancement — the server still returns `⍕`-formatted text in `<pre>` tags, but the frontend detects rectangular output and optionally renders it with enhanced alignment or subtle grid lines.

**Frontend changes:**
- Detect output that looks like a matrix (multiple lines, consistent column structure)
- Render as a `<table>` or CSS grid with monospace alignment
- Optionally: display shape information (`3 4` for a 3×4 matrix) in a subtle annotation

**Playwright tests:**
- Submit `3 4⍴⍳12` → output renders as a visually aligned grid
- Submit `⍳5` → output renders as a simple vector (no grid treatment)
- Submit a scalar expression → plain text output
- Large matrix scrolls horizontally rather than wrapping

**Size increment:** ~2KB of JS/CSS.

---

### Phase 7: Workspace panel

**What it does:** A sidebar (collapsible) showing the current workspace state: defined variables with their shapes, and defined functions. Clicking a variable name inserts it into the input. This is the first step toward IDE-like functionality.

**Server changes:**
- Add `GET /workspace` returning an HTML fragment listing variables and functions:
  ```html
  <div class="ws-section">
    <h3>Variables</h3>
    <div class="ws-var" data-name="M">M <span class="shape">3 4</span></div>
    <div class="ws-var" data-name="V">V <span class="shape">5</span></div>
  </div>
  <div class="ws-section">
    <h3>Functions</h3>
    <div class="ws-fn" data-name="sort">sort</div>
  </div>
  ```

**Frontend changes:**
- A `<div>` sidebar, toggleable
- Lists variables (with shape badges) and functions
- Click to insert name into input
- **Desktop (HTMX):** `hx-get="/workspace" hx-trigger="load, htmx:afterSwap from:#session"` — auto-refreshes the panel after each evaluation, no custom JS needed
- **Pico:** vanilla JS fetches `/workspace` after each submit and sets `innerHTML`

**Playwright tests:**
- Define a variable → it appears in the workspace panel
- Panel shows correct shape
- Click variable name → it appears in input
- `)clear` → panel empties
- Define a function → it appears in the functions section

**Size increment:** ~3KB of JS/CSS. Server endpoint ~50 lines.

---

### Phase 8: Pico W server port

**What it does:** A MicroPython-compatible server that implements the same API contract, serving `index.html`. MARPLE runs on the Pico under MicroPython/CircuitPython with the pure-Python backend.

**Implementation:**
- A new module `pico_server.py` using MicroPython's `asyncio` and socket API (or `microdot` if it fits in RAM)
- Same endpoints: `GET /`, `POST /eval`, `POST /system`, `GET /health`
- Same HTML fragment responses — the Pico frontend inserts them identically
- The `index.html` file is stored on the Pico's filesystem (LittleFS)
- WiFi setup: connect to a configured SSID, or create an AP (access point) so the user connects to the Pico directly
- mDNS: advertise as `marple.local` so the user navigates to `http://marple.local/`

**Testing:**
- Playwright tests run against the desktop server (same API contract)
- Pico-specific testing is manual or via a hardware-in-the-loop setup (a separate concern)
- The key guarantee: if it works against the desktop server, the same frontend works against the Pico server (because the API contract is identical)

**Constraints:**
- `index.html` must be ≤ 20KB total (all phases combined) to fit comfortably in the Pico's filesystem alongside the interpreter
- HTTP responses should be streamed where possible to avoid buffering large outputs in RAM
- Concurrent connections: probably just one at a time (the Pico isn't a multi-user server)

**Size:** Server module ~150 lines of MicroPython.

---

### Later phases (not yet planned in detail)

- **Syntax highlighting** in the input area (colouring numbers, strings, glyphs, comments). Requires a lightweight tokenizer in JS — or use the server to tokenize and return spans.
- **WebSocket upgrade** for lower-latency interaction (eliminates HTTP overhead per keystroke if we want live evaluation or completion).
- **Autocomplete** — tab-completion for variable and function names. Needs a `/complete` endpoint.
- **Persistent history** — save expression history to `localStorage` (desktop browser) or a file on the Pico's filesystem.
- **Workspace save/load** via the web UI — buttons that invoke `)save` and `)load`, with a workspace name dialog.
- **Mobile-friendly layout** — responsive CSS for phone/tablet use (particularly relevant for the Pico W scenario: you might be programming the Pico from a phone on the same WiFi).
- **File upload/download** — upload `.apl` files to the workspace, download workspace files.

---

## 4. Testing strategy: Playwright + pytest

### Test structure

```
tests/
  web/
    conftest.py          # pytest fixtures: start server, provide page
    test_phase1_repl.py  # Phase 1 tests
    test_phase2_glyphs.py
    test_phase3_langbar.py
    test_phase4_history.py
    test_phase5_multiline.py
    test_phase6_formatting.py
    test_phase7_workspace.py
```

### Server fixture

A pytest fixture starts the MARPLE web server on a random port in a background thread, yields the URL, and tears down on cleanup. Module-scoped for speed — each test file shares one server instance. Tests get function-scoped browser pages.

### What Playwright tests cover

- **Functional correctness:** expressions evaluate correctly, errors display properly, state persists across evaluations
- **UI interaction:** keyboard input, backtick sequences, button clicks, history navigation, cursor position
- **Responsive behaviour:** output scrolls, textarea resizes, sidebar toggles
- **Edge cases:** empty input, very long output, special characters in strings, rapid submissions

### What Playwright tests don't cover

- The interpreter itself — that's the existing pytest suite (290 tests)
- Pico-specific behaviour (WiFi, mDNS, memory limits) — manual or hardware-in-the-loop
- Performance — separate concern

### Running tests

```bash
pip install playwright pytest-playwright
playwright install chromium
pytest tests/web/ -v
```

---

## 5. File structure

```
src/marple/
  web/
    __init__.py
    server.py            # Desktop HTTP server (stdlib http.server)
    static/
      desktop.html       # Desktop frontend (includes HTMX from CDN)
      index.html         # Pico frontend (fully self-contained, <20KB)

pico/
  pico_server.py         # MicroPython HTTP server (same API)
  boot.py                # WiFi setup, mDNS
  index.html             # Copy of the Pico frontend

tests/
  web/
    conftest.py
    test_phase1_repl.py
    ...
```

The `web/` package is a new addition to the MARPLE source tree. It depends only on `marple.interpreter` and the standard library — no new pip dependencies for the server. Playwright is a test dependency only.

---

## 6. Design decisions

**Two frontends, one API.** The Pico frontend (`index.html`) is self-contained with inline CSS/JS and no external resources — a hard constraint driven by the Pico's tiny filesystem and lack of internet access. The desktop frontend (`desktop.html`) loads HTMX from a CDN, enabling declarative partial-page updates in later phases (workspace panel auto-refresh, language bar loading). Both hit the same endpoints and receive the same HTML fragment responses.

**HTML fragments, not JSON.** The server returns pre-built HTML fragments for `/eval` and `/system`. Both frontends insert them with `insertAdjacentHTML`. This is simpler than JSON on both sides: no client-side DOM construction, no response parsing, and it aligns naturally with HTMX's `hx-swap="beforeend"` model. The server handles HTML escaping to keep APL's `<`, `>`, `&` functions safe.

**Form-encoded requests, not JSON.** HTMX sends form data by default. Form-encoded is equally easy to parse on all platforms (`parse_qs` in CPython, trivial string splitting in MicroPython). No Content-Type negotiation needed.

**HTMX included but not yet used in Phase 1.** The desktop HTML includes the HTMX `<script>` tag from Phase 1, but the actual submission logic is vanilla JS (because the `/eval` vs `/system` routing decision needs JS anyway). HTMX's value emerges in Phase 3+ where declarative `hx-get`, `hx-trigger`, and `hx-swap` attributes replace what would otherwise be custom JS event wiring.

**HTTP, not WebSocket (initially).** HTTP request/response is simpler to implement, test, and debug. Each expression is one request/response cycle. WebSockets can be added later for lower latency, but HTTP is fine for a REPL where human typing speed is the bottleneck.

**Server-side formatting.** The server applies `⍕` (format) to produce the display string, wraps it in `<pre>` tags, and returns it. The frontend doesn't need to know anything about APL arrays — it just inserts HTML.

**Module-scoped server in tests.** Starting a fresh server per test is slow. Module-scoped means the server starts once per test file. Tests that need clean state use `)clear`. This mirrors how a real user interacts — the server stays running, the workspace accumulates state.

**No authentication.** The Pico W scenario is a single user on a local network (or direct AP connection). The desktop scenario is localhost. Authentication adds complexity with no benefit for either case. If MARPLE is ever exposed to a wider network, authentication can be added at the HTTP layer without changing the API contract.

---

## 7. Pico W / Pico 2 W considerations

The Pico W (RP2040, 264KB RAM) and Pico 2 W (RP2350, 520KB RAM) both have WiFi via the CYW43439 chip. Key considerations:

**RAM budget.** The MARPLE interpreter, workspace state, and web server must all fit in RAM simultaneously. On the RP2040, this is tight — the interpreter itself may consume 50–100KB, leaving ~150KB for workspace data and the server. The RP2350's 520KB gives much more headroom. The web frontend is served from flash (filesystem), not held in RAM.

**WiFi modes.** Two options: (1) station mode — the Pico connects to an existing WiFi network, gets an IP via DHCP, and is accessible at that IP or via mDNS (`marple.local`). (2) AP mode — the Pico creates its own network, the user connects to it, and navigates to a fixed IP (e.g. `192.168.4.1`). AP mode is simpler for demos and doesn't require an existing network.

**MicroPython HTTP server.** MicroPython's `asyncio` module supports cooperative multitasking. A minimal HTTP server parses request lines, reads headers, reads the body for POST requests, routes to handlers, and sends responses. This is ~100–150 lines. Libraries like `microdot` package this up but add ~50KB; worth evaluating whether the RAM cost is justified.

**Response streaming.** For large array outputs, the server should stream the response rather than buffering the entire HTML fragment in RAM. This may require chunked transfer encoding or simply writing the response in pieces.

**File serving.** The `index.html` file is read from the Pico's LittleFS filesystem and served with `Content-Type: text/html`. Staying under 20KB total for the frontend is a hard discipline.

---

## 8. Getting started: Phase 1

The detailed Phase 1 implementation brief lives in `MARPLE_Web_REPL_Phase1_Brief.md`. It specifies exactly what to build, the sequence of work, potential pitfalls, and a definition of done. That's the document to hand to Claude Code for the first session.
