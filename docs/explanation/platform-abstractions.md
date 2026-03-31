# Platform Abstractions for MARPLE

## The Problem

MARPLE runs on CPython (Linux desktop) and MicroPython (Pimoroni Presto / Pico 2). Platform differences are currently handled ad-hoc: try/except imports, hasattr checks, and deploy-time stripping. This makes the code fragile and means some features silently degrade or disappear on the Pico rather than being properly implemented for that platform.

The same problem will recur as we add more backends (CuPy for GPU, specialised hardware accelerators).

## Proposed Architecture

At startup, MARPLE selects a **platform backend** based on available hardware and software. Each backend provides concrete implementations of abstract interfaces. The interpreter works entirely through these interfaces.

```
Interpreter
    │
    ├── APLArray (abstract) ──► PythonArray / NumpyArray / CuPyArray / UlabArray
    │
    ├── Config (abstract) ────► PythonConfig / PicoConfig
    │
    ├── Console (abstract) ───► TerminalConsole / PrideConsole / PicoConsole
    │
    └── FileSystem (abstract) ► OsFileSystem  (already exists)
```

## Abstraction 1: APLArray — Computation

**Current state:** `APLArray` is a single class holding `shape` (list) and `data` (list or numpy array). Every function checks `is_numeric_array(data)` to decide whether to use numpy or Python loops. This check happens on every operation, and the numpy/Python logic is duplicated across `functions.py`, `structural.py`, and `operator_binding.py`.

**Proposed:** `APLArray` becomes an abstract base class. Each subclass implements all primitive operations as methods.

| Subclass | data storage | available when |
|----------|-------------|----------------|
| `PythonArray` | Python list | always |
| `NumpyArray` | numpy ndarray (numeric) or list (character) | numpy installed |
| `CuPyArray` | cupy ndarray | cupy installed |
| `UlabArray` | ulab array (numeric) or list (character) | MicroPython with ulab |

**What moves into array methods:**

| Current location | Method | Example |
|-----------------|--------|---------|
| `functions.py` | `negate()`, `add()`, `multiply()`, etc. | `omega.negate()`, `alpha.add(omega)` |
| `structural.py` | `reshape()`, `take()`, `drop()`, `reverse()`, `transpose()`, `iota()`, `index_of()`, `membership()` | `alpha.reshape(omega)`, `omega.iota(io)` |
| `operator_binding.py` | `reduce()`, `scan()` | `omega.reduce(fn)` |
| `backend.py` | `to_list()`, `to_array()`, `is_numeric_array()`, `maybe_upcast()`, `maybe_downcast()` | internal to each subclass |

**What this eliminates:**
- `is_numeric_array()` checks on every operation
- `to_list()` / `to_array()` conversions
- The `_pervade_monadic()` / `_pervade_dyadic()` wrappers with ufunc fallback
- `MonadicFunctionBinding` and `DyadicFunctionBinding` dispatch classes
- Most of `functions.py`, `structural.py`, and `backend.py`

**Dyadic convention:** `alpha.add(omega)` — the left operand's class determines the implementation. Both operands will always be the same subclass since the platform is selected once at startup.

**Character arrays:** Numpy and CuPy support character data (`dtype='U1'`) for searching (`⍳`, `∊`), comparison (`=`, `≠`), and all structural operations (reshape, transpose, indexing, take, drop, reverse, etc.). Only arithmetic is inapplicable to characters. The `NumpyArray` and `CuPyArray` subclasses should store character data as numpy/cupy arrays and use vectorised operations on them — not fall back to Python lists.

**Factory:** A module-level function `make_array(shape, data)` creates arrays of the selected subclass. Called by the parser (for literals), structural operations (for results), and anywhere else arrays are constructed.

### Issues addressed
- Runtime overhead of backend detection on every operation
- Duplicated numpy/Python code paths
- Difficulty adding new backends (currently requires changes across 5+ files)
- No GPU acceleration path without touching core logic

### Risks
- Large refactoring touching most files
- Tests that test implementation (e.g. checking `APLArray` directly) will break
- Character array handling adds complexity to each subclass

---

## Abstraction 2: Config — Platform Configuration

**Current state:** `config.py` uses `configparser.ConfigParser` and `os.path.expanduser()` to read `~/.marple/config.ini`. On MicroPython, ConfigParser doesn't exist, so `_config = None` and all settings return hardcoded defaults. The Pico cannot be configured.

**Proposed:** Abstract `Config` class with platform-specific implementations.

| Implementation | Storage | Available when |
|---------------|---------|----------------|
| `DesktopConfig` | `~/.marple/config.ini` via ConfigParser | CPython |
| `PicoConfig` | `/config.py` as a Python dict (importable) | MicroPython |

**Interface:**
```
get_default_io() -> int
get_workspaces_dir() -> str
get_sessions_dir() -> str
```

**What this eliminates:**
- `os.path.expanduser()` in config.py
- `os.path.join()` in config.py
- `os.path.exists()` in config.py
- The try/except around ConfigParser import
- The `_config is None` checks in every getter

### Issues addressed
- Pico has no way to configure `⎕IO`, workspace paths, etc.
- `os.path` usage is a MicroPython incompatibility
- Adding new config sources (environment variables, command-line args) requires modifying config.py

### Risks
- Minor — small interface, easy to implement

---

## Abstraction 3: Console — I/O

**Current state:** Already abstracted with `Console` ABC, `TerminalConsole`, `BufferedConsole`, `PrideConsole`, and `FakeConsole` adapters. This is the most mature abstraction.

**Gap:** No `PicoConsole` adapter. The Pico currently uses raw `input()` / `print()` in `pico_eval.py` outside the Console abstraction. If we want `⎕` and `⍞` to work on the Pico, we need a `PicoConsole` that wraps serial I/O. Future: `I2CConsole` for I2C keyboard input.

| Implementation | I/O mechanism | Available when |
|---------------|--------------|----------------|
| `TerminalConsole` | stdin/stdout with tty | Linux terminal |
| `PrideConsole` | WebSocket with threading | PRIDE web IDE |
| `BufferedConsole` | In-memory capture | Scripts, Jupyter |
| `FakeConsole` | Scripted inputs | Tests |
| `PicoConsole` (new) | USB serial `input()`/`print()` | Pico |
| `I2CConsole` (future) | I2C keyboard + display | Pico with I2C hardware |

### Issues addressed
- `⎕` and `⍞` don't work on the Pico
- `pico_eval.py` duplicates REPL logic instead of using Console abstraction
- Future I2C keyboard support needs a clean extension point

### Risks
- Minor — Console ABC already exists, just needs new adapters

---

## Abstraction 4: FileSystem — File I/O

**Current state:** Already abstracted with `FileSystem` ABC and `OsFileSystem` / `FakeFileSystem` adapters. `OsFileSystem` was recently fixed to use `os.stat()` instead of `os.path` for MicroPython compatibility.

**Gap:** `system_commands.py` still uses `os.path.join()` and `os.path.isdir()` directly (lines 97, 111-112) instead of going through the FileSystem port. `config.py` also uses `os.path` directly.

### Issues addressed
- Inconsistent use of the abstraction (some code bypasses it)
- `system_commands.py` would break on MicroPython if workspace save/load were used

### Risks
- Minimal — mostly wiring fixes

---

## Abstraction 5: Time — Timing and Profiling

**Current state:** `executor.py` has scattered platform checks for timing:
- `time.time()` vs `time.ticks_ms()` (line 270)
- `resource.getrusage()` with try/except (line 264)
- `os.getuid()` with try/except (line 258)

These are used by `⎕AI` (account information) and `⎕DL` (delay).

**Proposed:** A simple `Timer` abstraction or platform-aware utility functions.

| Implementation | Time source | CPU measurement |
|---------------|-------------|-----------------|
| `DesktopTimer` | `time.time()` | `resource.getrusage()` |
| `PicoTimer` | `time.ticks_ms()` | not available (return 0) |

### Issues addressed
- Scattered hasattr/try/except checks in executor.py
- `⎕AI` reporting is inconsistent across platforms

### Risks
- Very minor — small interface, few callers

---

## Abstraction 6: Module Loader — Dynamic Import

**Current state:** The i-beam operator (`⌶`) uses `__import__()` with `getattr` to walk dotted paths. This was changed from `importlib.import_module()` for MicroPython compatibility. The namespace system also uses `__import__` indirectly.

**Not proposed as a separate abstraction.** The `__import__()` + getattr approach already works on both platforms. No further abstraction needed unless we add platforms where `__import__` doesn't exist.

---

## Abstraction 7: Terminal — Raw Character Input

**Current state:** `terminal.py` uses `tty` and `termios` (Unix-only) to read individual keystrokes and perform live backtick-to-glyph translation. The `TerminalConsole` adapter tries to import it and falls back to plain `input()` if it fails. This means:

- **Windows/Mac:** No backtick glyph input in the terminal REPL. Users must use PRIDE or Jupyter.
- **Pico with I2C keyboard:** No way to get character-by-character input. The I2C keyboard sends raw keystrokes, but there's no abstraction to receive them.

**The logic in `terminal.py` has two distinct layers:**

1. **Raw character source** — reading one character at a time. This is platform-specific.
2. **Line editing and glyph translation** — backtick detection, glyph substitution, cursor movement, echo. This is platform-independent.

**Proposed:** Split into an abstract `CharSource` (raw input) and a shared `GlyphLineEditor` (editing logic).

| CharSource implementation | Mechanism | Available when |
|--------------------------|-----------|----------------|
| `UnixCharSource` | `tty.setraw()` + `os.read()` | Linux, macOS |
| `WindowsCharSource` | `msvcrt.getwch()` | Windows |
| `I2CCharSource` | I2C keyboard read | Pico with I2C hardware |

`GlyphLineEditor` takes any `CharSource` and provides `read_line()` with full backtick translation and line editing. `TerminalConsole` uses `GlyphLineEditor` instead of importing `terminal.py` directly.

**What this enables:**
- Backtick glyph input on Windows and Mac
- Backtick glyph input on Pico with I2C keyboard
- Dyalog keyboard input on any platform that supports it (the `CharSource` just passes through non-backtick keys)
- The PRIDE language bar remains an alternative for platforms without keyboard setup

### Issues addressed
- Terminal REPL is Linux-only for glyph input
- I2C keyboard has no integration path
- Glyph translation logic is tangled with Unix terminal control

### Risks
- `msvcrt` on Windows needs testing (character encoding, special keys)
- I2C keyboard protocol needs defining (depends on hardware choice)
- Line editing edge cases (multi-byte UTF-8, escape sequences) need care

---

## What Doesn't Need Abstracting

| Area | Why not |
|------|---------|
| `web/server.py` (asyncio, aiohttp) | Never deployed to Pico |
| `jupyter/` (ipykernel) | Never deployed to Pico |
| `adapters/pride_console.py` (threading) | Never deployed to Pico |
| `pathlib` | Only used in web/jupyter, never deployed to Pico |
| `deploy.sh` stripping | Build-time concern, not runtime |

---

## Implementation Order

The abstractions have dependencies. Suggested order:

1. **Config** — smallest, no dependencies, immediate benefit (Pico can be configured)
2. **FileSystem fixes** — wire `system_commands.py` through existing port
3. **Console: PicoConsole** — enables `⎕`/`⍞` on Pico, small addition to existing ABC
4. **Time** — small, self-contained
5. **Terminal: CharSource + GlyphLineEditor** — enables glyph input on Windows, Mac, and Pico I2C
6. **APLArray** — largest, most impactful, depends on all the above being stable

APLArray is deliberately last because it's the biggest change and touches the most code. The smaller abstractions serve as practice runs and reduce the number of platform-specific workarounds that the APLArray refactoring needs to handle.

---

## Test Impact

The APLArray refactoring will break tests that:
- Construct `APLArray(shape, data)` directly (most tests do this)
- Compare against `APLArray` instances
- Check `.data` or `.shape` attributes
- Import from `functions.py`, `structural.py`, or `backend.py`

Tests that test **behaviour** (input expression → output value) will survive unchanged. Tests that test **implementation** (specific class, specific data representation) will need updating.

Before starting the APLArray refactoring, we should audit the test suite and convert implementation-focused tests to behaviour-focused tests. This is a prerequisite, not part of the refactoring itself.

---

## Conformance and Benchmark Scripts

Before refactoring, we need to establish a ground truth for correctness and a baseline for performance. Two sets of APL scripts will be created:

### Conformance scripts

For each primitive that MARPLE plans to implement (excluding those that require nested arrays), a script exercises the function across:

- **Ranks:** scalar, vector, matrix, rank-3
- **Data types:** integer, float, character (where applicable)
- **Edge cases:** empty arrays, scalar extension, shape mismatches

Each script prints its inputs and outputs in a standard format. Running the same script against Dyalog APL gives the expected results. Differences reveal bugs or missing features in MARPLE.

Scripts should set `⎕IO`, `⎕CT`, and `⎕FR` explicitly at the top so both interpreters are in the same state.

### Benchmark scripts

For each primitive, a script times the operation on data large enough to show performance differences but small enough to fit on the Pico (520KB RAM). Suggested sizes:

- **Numeric vectors:** 1000 elements
- **Numeric matrices:** 100x100
- **Character vectors:** 500 elements
- **Character matrices:** 50x50

Each script reports wall-clock time for each operation. Running against Dyalog, MARPLE (current), and MARPLE (after refactoring) shows the impact of changes.

### Nested array boundary

A separate document will list all Dyalog APL features and classify each as:

- **Implemented in MARPLE** — covered by conformance scripts
- **Requires nested arrays** — future work, not tested yet
- **Not planned** — out of scope (e.g. GUI, OLE, .NET integration)

This draws a clear line around MARPLE's current scope and makes the feature gap visible.

### Workflow

1. Claude (project) analyses Dyalog features and generates the scripts
2. Claude Code runs them against Dyalog and MARPLE, compares outputs
3. Differences are filed as bugs or documented as known limitations
4. Benchmark results become the baseline for measuring refactoring improvements
