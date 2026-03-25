# marple

Mini APL in Python Language Experiment. A first-generation APL interpreter with the rank operator, namespaces, and Python FFI. Uses APL arrays (shape + flat data) as the internal data model. Inspired by Rodrigo Girão Serrão's [RGSPL](https://github.com/rodrigogiraoserrano/RGSPL) and Iverson's [Dictionary of APL](https://www.jsoftware.com/papers/APLDictionary.htm).

## Documentation

More extensive documentation is available [here](https://romilly.github.io/marple/)

## MARPLE on the Raspberry Pi Pico 2

MARPLE runs on the Raspberry Pi Pico 2 via MicroPython. See the [demo videos](https://romilly.github.io/marple/demos/) — primitives, dfns, the rank operator, namespaces, and file I/O, all running on the Pico.

## Features

- **40+ primitive functions** — arithmetic, comparison, boolean, structural, circular/trig, match/tally, membership
- **Operators** — reduce (`/`), scan (`\`), inner product (`f.g`), outer product (`∘.f`), **rank** (`⍤`)
- **Rank operator** — `(f⍤k)` applies any function along any axis: `(⌽⍤1) M` reverses rows, `(+/⍤1) M` sums rows
- **From function** (`⌷`) — leading-axis selection that composes with rank
- **Direct functions (dfns)** — `{⍵}` syntax with guards, recursion via `∇`, default `⍺`
- **Symbol table-aware parser** — named functions work without parens: `double ⍳5`
- **Namespaces** — `$::str::upper 'hello'`, `#import` directives, `::` separator
- **I-beam operator** (`⌶`) — Python FFI for extending MARPLE with Python code
- **Error handling** — `⎕EA` (execute alternate), `⎕EN` (error number), `⎕DM` (diagnostic message), `⎕SIGNAL`
- **System variables** — `⎕IO`, `⎕CT`, `⎕PP`, `⎕RL`, `⎕A`, `⎕D`, `⎕TS`, `⎕WSID`, `⎕UCS`, `⎕NC`, `⎕EX`, `⎕FR`
- **Data representation** — `⎕DR` queries/converts internal types; `⎕FR←1287` enables exact decimal arithmetic
- **Numeric type system** — automatic upcast/downcast prevents integer overflow; boolean uint8 for comparisons
- **Matrices** — reshape, transpose, bracket indexing (`M[r;c]` any rank, index shape preserved), matrix inverse (`⌹`)
- **Numpy backend** — automatic vectorization (73x faster for element-wise, 380x for outer product), with pure-Python fallback
- **Web REPL** — browser-based REPL over WebSocket with language bar, workspace panel, session history, multi-line input
- **Pico web bridge** — evaluate APL on a connected Pico from the browser (`--pico-port /dev/ttyACM0`)
- **Terminal REPL** — live backtick→glyph input, workspace save/load, APL-style formatting
- **Script runner** — `marple script.marple` with session transcript output
- **528 tests** (481 interpreter + 47 web), pyright strict

## Quick start

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if you don't have it, then:

```bash
uv venv
source .venv/bin/activate      # on Windows: .venv\Scripts\activate
uv pip install marple-lang
marple
```

```
MARPLE v0.3.0 - Mini APL in Python
CLEAR WS

      ⍳5
1 2 3 4 5
      +/⍳100
5050
      fact←{⍵≤1:1⋄⍵×∇ ⍵-1}
      fact 10
3628800
      double←{⍵+⍵}
      double ⍳5
2 4 6 8 10
      M←3 4⍴⍳12
      (⌽⍤1) M
 4  3  2  1
 8  7  6  5
12 11 10  9
      $::str::upper 'hello'
HELLO
```

### Web REPL

```bash
python -m marple.web.server
```

Open `http://localhost:8888/` in your browser. Communicates over WebSocket for real-time interaction. Features: clickable language bar, workspace panel, session history (up/down arrows), multi-line input (Shift+Enter).

To evaluate APL on a connected Raspberry Pi Pico 2 from the browser:

```bash
python -m marple.web.server --pico-port /dev/ttyACM0
```

A Local/Pico toggle appears in the header bar. Switch to Pico mode to send expressions to the Pico over USB serial.

### Running scripts

```bash
marple examples/01_primitives.marple          # run and display
marple examples/01_primitives.marple > out.txt  # capture session transcript
```

Six demo scripts are included in `examples/`:
- `01_primitives.marple` — arithmetic, vectors, matrices, reduce, products
- `02_dfns.marple` — user functions, guards, recursion, rank operator
- `03_namespaces.marple` — system library, imports, file I/O, i-beams
- `04_errors.marple` — ea/en error handling, error codes
- `05_pico_io.marple` — file I/O on Raspberry Pi Pico 2
- `06_numeric_types.marple` — ⎕DR, ⎕FR, boolean dtype, overflow protection, decimal arithmetic

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
| `` `J `` | ⍤ | `` `I `` | ⌷ | `` `j `` | ∘ | `` `D `` | ⌹ |
| `` `B `` | ⌶ | | | | | | |

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

| Module | Purpose |
|--------|---------|
| `arraymodel.py` | `APLArray(shape, data)` — the core data structure |
| `backend.py` | Numpy/CuPy/ulab detection with pure-Python fallback |
| `tokenizer.py` | Lexer for APL glyphs, numbers, strings, qualified names |
| `parser.py` | Right-to-left recursive descent with symbol table |
| `interpreter.py` | Tree-walking evaluator with dfn closures |
| `functions.py` | Scalar functions with pervasion (numpy-accelerated) |
| `structural.py` | Shape-manipulating and indexing functions |
| `cells.py` | Cell decomposition and reassembly for the rank operator |
| `namespace.py` | Hierarchical namespace resolution and system workspace |
| `errors.py` | APL error classes with numeric codes |
| `repl.py` | Interactive read-eval-print loop |
| `script.py` | Script runner with session transcript output |
| `terminal.py` | Raw terminal input with live glyph translation |
| `glyphs.py` | Backtick → APL character mapping |
| `workspace.py` | Directory-based workspace persistence |
| `stdlib/` | Standard library: string, I/O, and error handling |

## References

- [RGSPL](https://github.com/rodrigogiraoserrano/RGSPL) — Rodrigo Girão Serrão's Python APL interpreter (design reference)
- [RGSPL blog series](https://mathspp.com/blog/lsbasi-apl-part1) — step-by-step interpreter build
- [Iverson's Dictionary of APL](https://www.jsoftware.com/papers/APLDictionary.htm) — the rank operator and leading-axis theory
- [Language spec](docs/MARPLE_Language_Reference.md) — full first-generation APL reference and roadmap
- [Rank operator spec](docs/MARPLE_Rank_Operator.md) — detailed rank operator design
- [Indexing spec](docs/MARPLE_Indexing.md) — From function and indexing approach
- [Namespaces spec](docs/MARPLE_Namespaces_And_IBeams.md) — namespaces, i-beams, and standard library
