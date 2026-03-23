# Changelog

All notable changes to MARPLE are documented here.

## [Unreleased]

### Added
- Numpy fast path for outer product using `ufunc.outer()` (~380x faster)
- Fixed inner product to use `np.tensordot` (correct for rank > 2)
- Fixed outer product scalar handling

### Changed
- Dispatch tables for monadic/dyadic functions (replacing if/elif chains)
- `default_env()` replaces per-variable initialization
- Random seeding: seed once at startup, re-seed only on `⎕RL←`

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
