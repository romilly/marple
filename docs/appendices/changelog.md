# Changelog

## Unreleased

### Added

- APL array model with scalar and vector support
- Scalar functions: arithmetic (`+`, `-`, `×`, `÷`), comparison (`<`, `≤`, `=`, `≥`, `>`, `≠`), boolean (`∧`, `∨`, `~`), extended (`*`, `⍟`, `|`, `○`)
- Structural functions: `⍴` (shape/reshape), `⍳` (iota/index-of), `,` (ravel/catenate), `⌽` (reverse/rotate), `⍉` (transpose), `↑` (take), `↓` (drop), `⍋` (grade up), `⍒` (grade down), `⊤` (encode), `⊥` (decode), `/` (replicate), `\` (expand), `⌹` (matrix inverse/divide), `⌷` (From), `∈` (membership), `⍕` (format), `⍎` (execute), `≢` (tally/not-match), `≡` (match)
- Operators: `/` (reduce), `\` (scan), `⍤` (rank), `∘.f` (outer product), `f.g` (inner product), `⌶` (I-Beam)
- Direct functions (dfns) with guards, alpha defaults, and recursion via `∇`
- Direct operators (dops)
- Bracket indexing for vectors and matrices
- Auto-detecting backend: CuPy, NumPy, ulab, or pure Python
- REPL with backtick glyph input
- Workspace save/load system
- Standard library: `$::str` (trim, upper, lower), `$::io` (nread, nwrite), `$::error` (ea, en)
- `#import` directive with optional aliasing
- Script execution mode
- Initial documentation site
