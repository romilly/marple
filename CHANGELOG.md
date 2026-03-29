# Changelog

All notable changes to MARPLE are documented here.

## [0.5.8] — 2026-03-29

### Added
- **Jupyter kernel** — `pip install marple-lang[jupyter]`, HTML table output, tab completion, Shift+Tab inspection, backtick translation, system commands, multi-line dfns, language bar (classic Notebook)
- **`Interpreter.execute()`** — returns `EvalResult(value, silent, display_text)`, unified entry point for all interfaces
- **`system_commands.py`** — shared dispatcher returning strings, used by REPL, web server, and Jupyter
- **`Environment.list_variables()` / `list_functions()`** — workspace introspection without magic constants
- **`parser.is_balanced()`** — brace-balance check for multi-line input detection
- **Factorial (`!`)** — monadic `!n` (factorial via gamma), dyadic `k!n` (binomial coefficient)
- **⎕AI** — account information: user ID, CPU time (ms), connect time (ms), keying time
- **Multi-axis take/drop** — `2 3↑M` takes 2 rows and 3 cols, with space fill for character arrays

### Changed
- `format_result` moved from `repl.py` to `formatting.py` (proper home)
- `format_result` handles rank-3+ arrays (2D slices separated by blank lines)
- REPL and web server use shared system command dispatcher (no duplication)
- `pyproject.toml`: requires-python bumped to >=3.10, `[jupyter]` optional dependency added

### Fixed
- Take/drop on matrices: operate along first axis (was operating on flat data)
- Catenate on matrices: joins along last axis (was joining flat data)
- Error message for system function without argument (e.g. `⎕CR` alone)
- ⎕TS milliseconds: honest 0 on MicroPython instead of misleading ticks_ms value

## [0.5.2] — 2026-03-29

### Added
- **Power operator** (`⍣`) — `(f⍣n)` iterates n times, `(f⍣≡)` iterates to fixed point, custom convergence functions
- **Tail call optimization** — `∇` self-calls in tail position run in constant stack space; essential for Pico's 8KB stack
- **First-axis rotate/reverse** (`⊖`) — monadic reverse and dyadic rotate along first axis, any rank
- **⎕CSV** — `⎕CSV 'file.csv'` reads columns into named variables
- **Console port** — hexagonal architecture: `Console` ABC with `TerminalConsole` and `FakeConsole` adapters
- **FileSystem port** — `FileSystem` ABC with `OsFileSystem` and `FakeFileSystem` adapters
- **Localised system variables** — `⎕IO←0` inside a dfn does not leak to the caller
- **Multi-line dfns** in script runner and pico_client (lines accumulated until braces balance)
- **Conway's Game of Life** — single self-contained dfn using rank, reduce, encode
- **`life` workspace** — `life`, `shift`, `show`, `glider` ready to `)LOAD`
- **⍣ in PRIDE language bar** — backtick `P` mapping
- **)SAVE, )LOAD, )LIB** in PRIDE web IDE
- **Pico stubs** — `pico_stubs/abc.py` and `pico_stubs/typing.py` for MicroPython compatibility
- **pico_client --script** — run .marple files on the Pico from the workstation
- 185 recovered tests from old interpreter, 759 total

### Fixed
- **⌽ on matrices** — now operates along last axis (was reversing flat data)
- **⊖ and ⌽ for rank 3+** — chunk size uses product of trailing axes, not just last
- **Encode (⊤)** — supports vector right argument (produces matrix)
- **⎕RL assignment** re-seeds the RNG for deterministic roll/deal
- **⎕FX** classifies dops as NC=4 operators
- **⎕FR** validation — rejects values other than 645 or 1287
- **⎕CR** splits multi-line sources into matrix rows
- **ClassError** on name class change (function→array, array→function)
- **Infinity** in downcast — no longer crashes on overflow
- **Presto display** scrolls instead of clearing when full
- **Presto display** truncates long lines to fit 480px
- **Error message** when system function (⎕CR, ⎕FX etc.) used without argument
- **All pyright errors** resolved (was 7, now 0)
- **Pico deploy** updated for new engine architecture
- **Environment.copy()** copies quad vars (was sharing reference)

### Changed
- Hexagonal architecture: REPL uses Console port, file I/O uses FileSystem port
- Deploy script strips `from __future__ import annotations` for MicroPython
- pico_eval.py uses `Interpreter` class instead of deleted `interpret()`
- pico_client substitutes unsupported Unicode chars (em dash, box drawings) for Pico font
- README fully rewritten for v0.5.2

## [0.5.0] — 2026-03-28

### Changed
- **Class-based engine** replaces monolithic `interpreter.py`:
  - `engine.py` — `Interpreter(Executor)` with `run()` method
  - `executor.py` — base AST evaluator
  - `nodes.py` — AST nodes with `execute(ctx)` methods
  - `dfn_binding.py` — dfn/dop evaluation
  - `environment.py` — workspace state with `SymbolTable`
  - `monadic_functions.py`, `dyadic_functions.py` — function dispatch
  - `operator_binding.py` — reduce, scan operators
- Old `interpreter.py` deleted

## [0.3.6] — 2026-03-23

### Added
- **Web REPL** — browser-based REPL at `http://localhost:8888/`
  - Bootstrap layout with session area + workspace sidebar panel
  - Clickable language bar with tooltips for all APL glyphs
  - Session history with up/down arrow keys
  - Multi-line input with Shift+Enter (newlines converted to `⋄`)
  - Workspace panel: shows variables (with shapes) and functions, click to insert
  - `POST /eval`, `POST /system`, `GET /workspace`, `GET /health` endpoints
  - Server returns HTML fragments, form-encoded requests
  - Two frontends: `desktop.html` (Bootstrap + HTMX) and `index.html` (self-contained)
  - 36 Playwright tests
- Published to PyPI as `marple-lang`
- Numpy fast path for outer product using `ufunc.outer()` (~380x faster)
- `CHANGELOG.md`

### Fixed
- Inner product uses `np.tensordot` (correct for rank > 2, was using `np.dot`)
- Outer product: scalar args produce scalar result (not 1×1 matrix)
- Numpy multiply reduce uses float64 to avoid int64 overflow (`×/⍳30`)
- REPL uses `default_env()` (was missing system variables)
- Version display uses `marple-lang` package name

### Changed
- Package renamed to `marple-lang` for PyPI
- Desktop frontend uses Bootstrap 5 for layout
- Dispatch tables for monadic/dyadic functions (replacing if/elif chains)
- `default_env()` replaces per-variable initialization
- Bracket indexing generalised to any rank (was limited to rank 2)
- Random seeding: seed once at startup, re-seed only on `⎕RL←`
- Install instructions use `uv` with virtual environments

## [0.2.16] — 2026-03-23

### Added
- `?` (roll/deal) — monadic roll and dyadic deal
- `⎕RL` (random link) — seed for deterministic random results

## [0.2.15] — 2026-03-23

### Added
- **Tier 1 system variables and functions:**
  - `⎕PP` — print precision
  - `⎕A` — uppercase alphabet constant
  - `⎕D` — digit characters constant
  - `⎕TS` — timestamp
  - `⎕WSID` — workspace ID
  - `⎕EN` — error number (last error code)
  - `⎕DM` — diagnostic message (last error text)
  - `⎕EA` — execute alternate (error trapping)
  - `⎕UCS` — Unicode codepoint conversion
  - `⎕NC` — name class query
  - `⎕EX` — expunge names from workspace
  - `⎕SIGNAL` — raise errors programmatically

### Removed
- `$::error::ea` and `$::error::en` stdlib — replaced by `⎕EA`, `⎕EN`, `⎕DM`

## [0.2.13] — 2026-03-22

### Added
- MkDocs documentation — 119 pages covering tutorials, reference, how-to guides, explanation, troubleshooting, and appendices

## [0.2.12] — 2026-03-22

### Added
- Four demo scripts in `examples/` with captured output
- Negative numbers displayed with high minus (`¯`)
- `#import` directives silenced in script output

## [0.2.11] — 2026-03-22

### Added
- Symbol table-aware parser — named functions work without parentheses (`double ⍳5`)
- Name class tracking (ARRAY=2, FUNCTION=3) with CLASS ERROR on type change
- Script runner echoes input lines with REPL prompt for session transcripts

### Fixed
- Float display: 10 significant digits, whole-number floats shown as integers
- Numpy bool values displayed as `0`/`1` not `True`/`False`
- Author corrected in `pyproject.toml`

## [0.2.8] — 2026-03-22

### Added
- `⎕CT` (comparison tolerance) — default `1E¯14`, affects `= ≠ < ≤ ≥ >`, dyadic `⍳`, `∈`
- `∈` (membership) — `3∈1 2 3 4 5` → `1`
- Scientific notation in tokenizer (`1e-14`, `2.5E3`)

## [0.2.5] — 2026-03-22

### Added
- Namespaces with `::` separator — `$::str::upper 'hello'`
- System workspace `$` loaded from `stdlib/` APL wrappers
- `#import` directives — `#import $::str::upper as up`
- `)fns $::str` lists namespace contents

## [0.2.3] — 2026-03-22

### Added
- I-beam operator (`⌶`) — Python FFI: `(⌶'module.function') arg`
- Initial stdlib: `$::str` (upper, lower, trim), `$::io` (nread, nwrite)
- Optional `MARPLE_IBEAM_ALLOW` security allowlist

## [0.2.2] — 2026-03-22

### Added
- `≡` (match) and `≢` (not-match/tally) — exact comparison, monadic tally
- APL error classes with numeric codes (SYNTAX=1 through CLASS=11)

## [0.2.1] — 2026-03-22

### Added
- Script runner — `marple script.marple` executes files line by line
- Error handling: `$::error::ea` (execute alternate), `$::error::en` (error number)
- Division by zero raises proper DOMAIN ERROR

## [0.2.0] — 2026-03-22

### Added
- **Numpy backend** — auto-detects numpy/cupy/ulab, ~73x faster for element-wise ops
- `np.add.reduce` fast path for commutative reduce operations
- `np.dot` fast path for `+.×` inner product
- `MARPLE_BACKEND=none` environment variable for pure-Python mode

### Changed
- `APLArray.data` now stores numpy arrays for numeric data

## [0.1.0] — 2026-03-22

### Added
- **Rank operator** (`⍤`) — cell-wise function application at any rank
- **From function** (`⌷`) — leading-axis selection composing with rank
- Directory-based workspace management with `)WSID`, `)SAVE`, `)LOAD`, `)LIB`, `)CLEAR`
- `⎕IO` consistency — grade and dyadic iota respect index origin
- Live backtick→glyph terminal input
- REPL with silent assignment, right-aligned matrix display

### Phase 4 — Full first-gen APL
- Matrices, transpose (`⍉`), grade (`⍋ ⍒`), encode/decode (`⊤ ⊥`)
- Inner product (`f.g`), outer product (`∘.f`)
- Execute (`⍎`), format (`⍕`), replicate/compress (`/`), expand (`\`)
- Matrix inverse/divide (`⌹`), circular functions (`○`)
- Bracket indexing (`M[r;c]`), `⎕IO`
- String literals, character arrays

### Phase 3 — Direct definition
- Dfns with `{⍵}` syntax, `⍺` left argument
- Guards (`condition:expr`), `∇` recursion, `⍺←default`
- Named functions via assignment

### Phase 2 — Useful subset
- Statement separator (`⋄`)
- Extended scalar functions (`* ⍟ | < ≤ = ≥ > ≠ ∧ ∨ ~`)
- Structural functions (`⍴ ⍳ , ↑ ↓ ⌽`)
- Reduce (`/`) and scan (`\`) operators

### Phase 1 — Calculator
- APL array model (`shape` + flat `data`)
- Scalars, vectors, `+ - × ÷ ⌈ ⌊`
- Right-to-left evaluation, parentheses
- Assignment (`←`), comments (`⍝`), high minus (`¯`)
- Tokenizer, recursive descent parser, tree-walking interpreter
