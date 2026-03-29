# marple

Mini APL in Python Language Experiment. An APL interpreter with the rank and power operators, tail call optimization, namespaces, hexagonal architecture, Jupyter kernel, and MicroPython support. Uses APL arrays (shape + flat data) as the internal data model. Inspired by Rodrigo Girão Serrão's [RGSPL](https://github.com/rodrigogiraoserrao/RGSPL) and Iverson's [Dictionary of APL](https://www.jsoftware.com/papers/APLDictionary.htm).

## Documentation

More extensive documentation is available [here](https://romilly.github.io/marple/)

## Conway's Game of Life

MARPLE can run Conway's Game of Life in a single dfn — no nested arrays needed:

```apl
life←{⎕IO←0
  s←{(1↑⍺)⊖(1↓⍺)⌽⍵}
  P←(⍉3 3⊤⍳9)-1
  N←(+⌿P(s⍤1 2)⍵)-⍵
  (N=3)∨⍵∧N=2}

G←6 6⍴0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 1 0 0 0 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0
(life⍣4) G
```

Uses the rank operator to apply 9 shift pairs, reduce-first to sum neighbours, and the power operator to iterate. Runs on CPython and the Raspberry Pi Pico 2.

## MARPLE on the Raspberry Pi Pico 2

MARPLE runs on the Raspberry Pi Pico 2 via MicroPython, with tail call optimization for constant-stack recursion on the Pico's 8KB stack. On the Pimoroni Presto, the REPL session mirrors to the 480x480 touchscreen LCD with a custom APL bitmap font. See the [demo videos](https://romilly.github.io/marple/demos/).

## Features

- **40+ primitive functions** — arithmetic, comparison, boolean, structural, circular/trig, match/tally, membership
- **Operators** — reduce (`/`), scan (`\`), inner product (`f.g`), outer product (`∘.f`), **rank** (`⍤`), **power** (`⍣`)
- **Rank operator** — `(f⍤k)` applies any function along any axis: `(⌽⍤1) M` reverses rows, `(+/⍤1) M` sums rows
- **Power operator** — `(f⍣n)` iterates n times, `(f⍣≡)` iterates to fixed point (convergence)
- **Tail call optimization** — `∇` self-calls in tail position run in constant stack space; essential for MicroPython
- **From function** (`⌷`) — leading-axis selection that composes with rank
- **First-axis functions** — `⊖` (reverse/rotate first axis), `⌿` (reduce first), `⍀` (scan first)
- **Direct functions (dfns)** — `{⍵}` syntax with guards, recursion via `∇`, default `⍺`, multi-line definitions
- **Direct operators (dops)** — `{⍺⍺ ⍵}` adverbs and `{⍺⍺ ⍵⍵ ⍵}` conjunctions with function or array operands
- **Localised system variables** — `⎕IO←0` inside a dfn does not leak to the caller
- **Iverson stack-based parser** — correct operator binding precedence following the Dictionary of APL
- **Namespaces** — `$::str::upper 'hello'`, `#import` directives, `::` separator
- **I-beam operator** (`⌶`) — Python FFI for extending MARPLE with Python code
- **Error handling** — `⎕EA` (execute alternate), `⎕EN` (error number), `⎕DM` (diagnostic message), `⎕SIGNAL`
- **Format function** (`⎕FMT`) — Dyalog-compatible formatting with I/F/E/A/G codes, text insertion, G pattern, character matrices
- **CSV import** — `⎕CSV 'data.csv'` reads columns into named variables
- **System variables** — `⎕IO`, `⎕CT`, `⎕PP`, `⎕RL`, `⎕A`, `⎕D`, `⎕TS`, `⎕WSID`, `⎕UCS`, `⎕NC`, `⎕EX`, `⎕FR`
- **Data representation** — `⎕DR` queries/converts internal types; `⎕FR←1287` enables exact decimal arithmetic
- **Numeric type system** — automatic upcast/downcast prevents integer overflow; boolean uint8 for comparisons
- **Matrices** — reshape, transpose, bracket indexing (`M[r;c]` any rank, index shape preserved), matrix inverse (`⌹`)
- **Numpy backend** — automatic vectorization, with pure-Python fallback for MicroPython
- **Factorial and binomial** — `!n` (factorial), `k!n` (binomial coefficient)
- **⎕AI** — account information: user ID, CPU time, connect time, keying time
- **Hexagonal architecture** — Console and FileSystem ports with real and test adapters
- **Jupyter kernel** — `pip install marple-lang[jupyter]` for Notebook/Lab/Console with HTML tables, tab completion, and backtick glyph input
- **PRIDE web IDE** — browser-based IDE over WebSocket with language bar, workspace panel, click-to-re-edit, session save/load, workspace save/load
- **Pico web bridge** — evaluate APL on a connected Pico from the browser (`--pico-port /dev/ttyACM0`)
- **Presto LCD mirror** — scrolling REPL display on the Pimoroni Presto's 480x480 touchscreen
- **Terminal REPL** — live backtick→glyph input, workspace save/load, APL-style formatting
- **Script runner** — `marple script.marple` with multi-line dfn support
- **825 tests**, pyright strict, 0 errors

## Quick start

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if you don't have it, then:

```bash
uv venv
source .venv/bin/activate      # on Windows: .venv\Scripts\activate
uv pip install marple-lang
marple
```

```
MARPLE v0.5.8 - Mini APL in Python
CLEAR WS

      ⍳5
1 2 3 4 5
      +/⍳100
5050
      fact←{⍺←1 ⋄ ⍵=0:⍺ ⋄ (⍺×⍵)∇ ⍵-1}
      fact 20
2432902008176640000
      double←{⍵×2}
      (double⍣10) 1
1024
      M←3 4⍴⍳12
      (⌽⍤1) M
 4  3  2  1
 8  7  6  5
12 11 10  9
      $::str::upper 'hello'
HELLO
```

### PRIDE Web IDE

```bash
python -m marple.web.server
```

Open `http://localhost:8888/` in your browser. PRIDE (the MARPLE web IDE) communicates over WebSocket. Features:

- Clickable language bar for APL glyph input (including `⍣` power operator)
- Click any previous input line to re-edit and re-submit
- Session save/load as markdown (Session menu)
- Workspace save/load (`)SAVE`, `)LOAD`, `)LIB`)
- Workspace panel showing variables and functions
- Session history (up/down arrows), multi-line input (Shift+Enter)
- Link to MARPLE documentation

To evaluate APL on a connected Raspberry Pi Pico 2 from the browser:

```bash
python -m marple.web.server --pico-port /dev/ttyACM0
```

A Local/Pico toggle appears in the header bar. Switch to Pico mode to send expressions to the Pico over USB serial.

### Jupyter Notebook

```bash
pip install marple-lang[jupyter]
marple-jupyter-install
jupyter notebook
```

Select **MARPLE (APL)** as the kernel. Features:
- HTML table output for arrays (vectors, matrices, rank-3+ slices)
- Backtick-to-glyph translation (`` `r `` → `⍴`)
- Tab completion for workspace names
- Shift+Tab introspection (shape, source)
- System commands (`)vars`, `)load`, etc.) in cells
- Multi-line dfn support
- Language bar in classic Notebook (via `lb.js`)

### Running scripts

```bash
marple examples/01_primitives.marple          # run and display
marple examples/01_primitives.marple > out.txt  # capture session transcript
```

Demo scripts are included in `examples/`:
- `01_primitives.marple` — arithmetic, vectors, matrices, reduce, products
- `02_dfns.marple` — user functions, guards, recursion, rank operator
- `03_namespaces.marple` — system library, imports, file I/O, i-beams
- `04_errors.marple` — ea/en error handling, error codes
- `05_pico_io.marple` — file I/O on Raspberry Pi Pico 2
- `06_numeric_types.marple` — ⎕DR, ⎕FR, boolean dtype, overflow protection, decimal arithmetic
- `07_cr_fx.marple` — ⎕CR, ⎕FX, ⎕NC, dynamic function definition
- `08_operators.marple` — operators, dops, reduce/scan with dfns, replicate
- `09_fmt.marple` — ⎕FMT formatting with I/F/E/A/G codes, text insertion, patterns
- `11_power_and_tco.marple` — power operator and tail call optimization
- `12_life.marple` — Conway's Game of Life step-by-step

### Pico deployment

```bash
./scripts/deploy.sh                                        # deploy to Pico 2
python scripts/pico_client.py                              # interactive REPL
python scripts/pico_client.py --script examples/12_life.marple  # run a script
```

### APL character input

If you have a Dyalog APL keyboard layout installed (e.g. via `setxkbmap` with `grp:win_switch`), you can use the Win key to type APL glyphs directly.

Alternatively, type APL glyphs using backtick prefixes — they appear immediately as you type:

| Key | Glyph | Key | Glyph | Key | Glyph | Key | Glyph |
|-----|-------|-----|-------|-----|-------|-----|-------|
| `` `r `` | ⍴ | `` `i `` | ⍳ | `` `l `` | ← | `` `w `` | ⍵ |
| `` `a `` | ⍺ | `` `V `` | ∇ | `` `x `` | ⋄ | `` `c `` | ⍝ |
| `` `- `` | × | `` `= `` | ÷ | `` `< `` | ≤ | `` `> `` | ≥ |
| `` `/ `` | ≠ | `` `o `` | ○ | `` `* `` | ⍟ | `` `2 `` | ¯ |
| `` `q `` | ⌽ | `` `Q `` | ⍉ | `` `g `` | ⍋ | `` `G `` | ⍒ |
| `` `t `` | ↑ | `` `y `` | ↓ | `` `n `` | ⊤ | `` `N `` | ⊥ |
| `` `J `` | ⍤ | `` `P `` | ⍣ | `` `I `` | ⌷ | `` `j `` | ∘ |
| `` `D `` | ⌹ | `` `B `` | ⌶ | | | | |

### System commands

| Command | Action |
|---------|--------|
| `)off` | Exit |
| `)clear` | Clear workspace |
| `)wsid [name]` | Show or set workspace ID |
| `)save [name]` | Save workspace (sets WSID if name given) |
| `)load name` | Load workspace |
| `)lib` | List saved workspaces |
| `)fns [ns]` | List defined functions (optionally in namespace) |
| `)vars` | List defined variables |

## Development

```bash
pip install -e .[test]
pytest
pyright src/
```

To run without numpy (pure-Python mode):
```bash
MARPLE_BACKEND=none pytest
```

## Architecture

MARPLE uses hexagonal architecture with ports and adapters for testable I/O:

| Module | Purpose |
|--------|---------|
| `arraymodel.py` | `APLArray(shape, data)` — the core data structure |
| `backend.py` | Numpy/ulab detection with pure-Python fallback |
| `tokenizer.py` | Lexer for APL glyphs, numbers, strings, qualified names |
| `parser.py` | Iverson stack-based parser with operator binding precedence |
| `nodes.py` | AST node classes with execute methods |
| `executor.py` | Base evaluator with system function dispatch |
| `engine.py` | `Interpreter` class — parse and evaluate APL source |
| `dfn_binding.py` | Dfn/dop evaluation with tail call optimization |
| `environment.py` | Workspace state — variables, system settings, name table |
| `symbol_table.py` | Name class tracking (array/function/operator) |
| `functions.py` | Scalar functions with pervasion (numpy-accelerated) |
| `monadic_functions.py` | Monadic function dispatch |
| `dyadic_functions.py` | Dyadic function dispatch |
| `structural.py` | Shape-manipulating and indexing functions |
| `operator_binding.py` | Reduce, scan, replicate operators |
| `cells.py` | Cell decomposition and reassembly for the rank operator |
| `fmt.py` | Dyadic ⎕FMT format specification parser |
| `namespace.py` | Hierarchical namespace resolution and system workspace |
| `errors.py` | APL error classes with numeric codes |
| `ports/console.py` | Console port — abstract REPL I/O interface |
| `ports/filesystem.py` | FileSystem port — abstract file I/O interface |
| `adapters/terminal_console.py` | Real Console adapter (terminal + stdout) |
| `adapters/os_filesystem.py` | Real FileSystem adapter (os module) |
| `repl.py` | Interactive read-eval-print loop (uses Console port) |
| `script.py` | Script runner with multi-line dfn support |
| `terminal.py` | Raw terminal input with live glyph translation |
| `glyphs.py` | Backtick → APL character mapping |
| `workspace.py` | Directory-based workspace persistence |
| `config.py` | User configuration (~/.marple/config.ini) |
| `stdlib/` | Standard library: string functions |
| `system_commands.py` | Shared system command dispatcher |
| `web/server.py` | PRIDE web IDE server (aiohttp + WebSocket) |
| `jupyter/kernel.py` | Jupyter kernel (wraps Interpreter.execute) |
| `jupyter/html_render.py` | APLArray → HTML table conversion |
| `pico_stubs/` | MicroPython stub modules for abc and typing |

## References

- [RGSPL](https://github.com/rodrigogiraoserrao/RGSPL) — Rodrigo Girão Serrão's Python APL interpreter (design reference)
- [RGSPL blog series](https://mathspp.com/blog/lsbasi-apl-part1) — step-by-step interpreter build
- [Iverson's Dictionary of APL](https://www.jsoftware.com/papers/APLDictionary.htm) — the rank operator and leading-axis theory
- [Language spec](docs/MARPLE_Language_Reference.md) — full APL reference and roadmap
- [Rank operator spec](docs/MARPLE_Rank_Operator.md) — detailed rank operator design
- [Indexing spec](docs/MARPLE_Indexing.md) — From function and indexing approach
- [Namespaces spec](docs/MARPLE_Namespaces_And_IBeams.md) — namespaces, i-beams, and standard library
