# MARPLE Features

## Language

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
- **Factorial and binomial** — `!n` (factorial), `k!n` (binomial coefficient)
- **Numeric type system** — automatic upcast/downcast prevents integer overflow; boolean uint8 for comparisons
- **Matrices** — reshape, transpose, bracket indexing (`M[r;c]` any rank, index shape preserved), matrix inverse (`⌹`)

## I/O

- **⎕← value** — output with newline (tee: returns value)
- **⍞← prompt** — display prompt, read character input, return response (Dyalog style)
- **⎕ read** — display `⎕:` prompt, read and evaluate input as APL
- **⍞ read** — read raw character input, return character vector
- **Error handling** — `⎕EA` (execute alternate), `⎕EN` (error number), `⎕DM` (diagnostic message), `⎕SIGNAL`
- **Format function** (`⎕FMT`) — Dyalog-compatible formatting with I/F/E/A/G codes, text insertion, G pattern, character matrices
- **CSV import** — `⎕CSV 'data.csv'` reads columns into named variables
- **File I/O** — `⎕NREAD`, `⎕NWRITE`, `⎕NEXISTS`, `⎕NDELETE`
- **System variables** — `⎕IO`, `⎕CT`, `⎕PP`, `⎕RL`, `⎕A`, `⎕D`, `⎕TS`, `⎕WSID`, `⎕UCS`, `⎕NC`, `⎕EX`, `⎕FR`, `⎕AI`
- **Data representation** — `⎕DR` queries/converts internal types; `⎕FR←1287` enables exact decimal arithmetic

## Extensions

- **Namespaces** — `$::str::upper 'hello'`, `#import` directives, `::` separator
- **I-beam operator** (`⌶`) — Python FFI for extending MARPLE with Python code

## Platforms

- **Terminal REPL** — workspace save/load, APL-style formatting
- **PRIDE web IDE** — browser-based IDE over WebSocket with language bar, workspace panel, click-to-re-edit, session save/load, interactive ⎕/⍞ input
- **Jupyter kernel** — HTML tables, tab completion, backtick glyph input
- **Pico web bridge** — evaluate APL on a connected Pimoroni Presto from the browser
- **Presto LCD mirror** — scrolling REPL display on the Pimoroni Presto's 480x480 touchscreen
- **Script runner** — `marple script.marple` with multi-line dfn support

## Implementation

- **Numpy backend** — automatic vectorization, with pure-Python fallback for MicroPython
- **Hexagonal architecture** — Console and FileSystem ports with real and test adapters
- **890+ fast tests** in ~1.2s, pyright strict
