# marple

Mini APL in Python Language Experiment. A first-generation APL interpreter using APL arrays (shape + flat data) as the internal data model, inspired by Rodrigo Girão Serrão's [RGSPL](https://github.com/rodrigogiraoserrao/RGSPL).

## Features

- **40+ primitive functions** — arithmetic, comparison, boolean, structural, circular/trig
- **6 operators** — reduce (`/`), scan (`\`), inner product (`f.g`), outer product (`∘.f`)
- **Direct functions (dfns)** — `{⍵}` syntax with guards, recursion via `∇`, default `⍺`
- **Matrices** — reshape, transpose, bracket indexing (`M[r;c]`), matrix inverse (`⌹`)
- **Interactive REPL** — live backtick→glyph input, workspace save/load, APL-style formatting
- **229 tests**, pyright strict, no external runtime dependencies

## Quick start

```bash
pip install -e .
marple
```

```
MARPLE v0.1.0 - Mini APL in Python

      ⍳5
1 2 3 4 5
      +/⍳100
5050
      fact←{⍵≤1:1⋄⍵×∇ ⍵-1}
      fact 10
3628800
      2 3∘.×⍳4
2 4 6 8
3 6 9 12
```

### Backtick input

Type APL glyphs using backtick prefixes — they appear immediately as you type:

| Key | Glyph | Key | Glyph | Key | Glyph | Key | Glyph |
|-----|-------|-----|-------|-----|-------|-----|-------|
| `` `r `` | ⍴ | `` `i `` | ⍳ | `` `l `` | ← | `` `w `` | ⍵ |
| `` `a `` | ⍺ | `` `V `` | ∇ | `` `x `` | ⋄ | `` `c `` | ⍝ |
| `` `- `` | × | `` `= `` | ÷ | `` `< `` | ≤ | `` `> `` | ≥ |
| `` `/ `` | ≠ | `` `o `` | ○ | `` `* `` | ⍟ | `` `2 `` | ¯ |
| `` `q `` | ⌽ | `` `Q `` | ⍉ | `` `g `` | ⍋ | `` `G `` | ⍒ |
| `` `t `` | ↑ | `` `y `` | ↓ | `` `n `` | ⊤ | `` `N `` | ⊥ |

### System commands

| Command | Action |
|---------|--------|
| `)off` | Exit |
| `)clear` | Clear workspace |
| `)save [file]` | Save workspace (default: `workspace.apl`) |
| `)load [file]` | Load workspace |
| `)fns` | List defined functions |
| `)vars` | List defined variables |

## Development

```bash
pip install -e .[test]
pytest
pyright src/
```

## Architecture

| Module | Purpose |
|--------|---------|
| `arraymodel.py` | `APLArray(shape, data)` — the core data structure |
| `tokenizer.py` | Lexer for APL glyphs, numbers, strings, identifiers |
| `parser.py` | Right-to-left recursive descent parser |
| `interpreter.py` | Tree-walking evaluator with dfn closures |
| `functions.py` | Scalar functions with pervasion |
| `structural.py` | Shape-manipulating functions |
| `repl.py` | Interactive read-eval-print loop |
| `terminal.py` | Raw terminal input with live glyph translation |
| `glyphs.py` | Backtick → APL character mapping |
| `workspace.py` | Save/load workspace as APL text |

## References

- [RGSPL](https://github.com/rodrigogiraoserrano/RGSPL) — Rodrigo Girão Serrão's Python APL interpreter (design reference)
- [RGSPL blog series](https://mathspp.com/blog/lsbasi-apl-part1) — step-by-step interpreter build
- [Language spec](docs/MARPLE_Language_Reference.md) — full first-generation APL reference and roadmap
