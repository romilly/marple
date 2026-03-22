# marple

Mini APL in Python Language Experiment. A first-generation APL interpreter with the rank operator, using APL arrays (shape + flat data) as the internal data model. Inspired by Rodrigo Girão Serrão's [RGSPL](https://github.com/rodrigogiraoserrano/RGSPL) and Iverson's [Dictionary of APL](https://www.jsoftware.com/papers/APLDictionary.htm).

## Features

- **40+ primitive functions** — arithmetic, comparison, boolean, structural, circular/trig
- **Operators** — reduce (`/`), scan (`\`), inner product (`f.g`), outer product (`∘.f`), **rank** (`⍤`)
- **Rank operator** — `(f⍤k)` applies any function along any axis: `(⌽⍤1) M` reverses rows, `(+/⍤1) M` sums rows
- **From function** (`⌷`) — leading-axis selection that composes with rank: `3(⌷⍤0 1) M` selects column 3
- **Direct functions (dfns)** — `{⍵}` syntax with guards, recursion via `∇`, default `⍺`
- **Matrices** — reshape, transpose, bracket indexing (`M[r;c]`), matrix inverse (`⌹`)
- **Numpy backend** — automatic vectorization (73x faster for large arrays), with pure-Python fallback
- **Interactive REPL** — live backtick→glyph input, workspace save/load, APL-style formatting
- **290 tests**, pyright strict, no external runtime dependencies

## Quick start

```bash
pip install -e .
marple
```

```
MARPLE v0.1.0 - Mini APL in Python
CLEAR WS

      ⍳5
1 2 3 4 5
      +/⍳100
5050
      fact←{⍵≤1:1⋄⍵×∇ ⍵-1}
      fact 10
3628800
      M←3 4⍴⍳12
      (⌽⍤1) M
 4  3  2  1
 8  7  6  5
12 11 10  9
      (+/⍤1) M
10 26 42
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
| `` `J `` | ⍤ | `` `I `` | ⌷ | `` `j `` | ∘ | `` `D `` | ⌹ |

### System commands

| Command | Action |
|---------|--------|
| `)off` | Exit |
| `)clear` | Clear workspace |
| `)wsid [name]` | Show or set workspace ID |
| `)save [name]` | Save workspace (sets WSID if name given) |
| `)load name` | Load workspace |
| `)lib` | List saved workspaces |
| `)fns` | List defined functions |
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
| `tokenizer.py` | Lexer for APL glyphs, numbers, strings, identifiers |
| `parser.py` | Right-to-left recursive descent parser |
| `interpreter.py` | Tree-walking evaluator with dfn closures |
| `functions.py` | Scalar functions with pervasion (numpy-accelerated) |
| `structural.py` | Shape-manipulating and indexing functions |
| `cells.py` | Cell decomposition and reassembly for the rank operator |
| `repl.py` | Interactive read-eval-print loop |
| `terminal.py` | Raw terminal input with live glyph translation |
| `glyphs.py` | Backtick → APL character mapping |
| `workspace.py` | Directory-based workspace persistence |

## References

- [RGSPL](https://github.com/rodrigogiraoserrano/RGSPL) — Rodrigo Girão Serrão's Python APL interpreter (design reference)
- [RGSPL blog series](https://mathspp.com/blog/lsbasi-apl-part1) — step-by-step interpreter build
- [Iverson's Dictionary of APL](https://www.jsoftware.com/papers/APLDictionary.htm) — the rank operator and leading-axis theory
- [Language spec](docs/MARPLE_Language_Reference.md) — full first-generation APL reference and roadmap
- [Rank operator spec](docs/MARPLE_Rank_Operator.md) — detailed rank operator design
- [Indexing spec](docs/MARPLE_Indexing.md) — From function and indexing approach
