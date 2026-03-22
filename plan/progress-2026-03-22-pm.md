# MARPLE Progress Report — 22 March 2026 (afternoon session)

## Summary

Third session. Major parser overhaul to support symbol table-aware parsing,
plus namespaces, i-beams, error handling, comparison tolerance, membership,
script runner, and four demo scripts.

## What was built this session

### Symbol table-aware parser
- Parser consults a name table to distinguish function names from array names
- Named dfns work without parens: `double ⍳5` parses correctly
- Name classes (ARRAY=2, FUNCTION=3) tracked on assignment
- Class changes raise CLASS ERROR (type of an identifier is immutable)
- 28 tests covering all parse categories: simple calls, dfn bodies, diamonds,
  functions defined in dfns, products, rank operator, imports

### Namespaces (`::` separator)
- Qualified names: `$::str::upper 'hello'` → `HELLO`
- `#import $::str::upper` brings names into scope
- `#import $::str::upper as up` with aliases
- `)fns $::str` lists namespace contents
- System workspace `$` loaded eagerly from `stdlib/` APL wrappers
- Double colon `::` chosen over single `:` to avoid conflict with dfn guards

### I-beam operator (`⌶`)
- `⌶'module.function'` calls Python, returns derived APL function
- Composes with operators and assignment
- Optional `MARPLE_IBEAM_ALLOW` security allowlist
- Initial stdlib: `str_impl` (upper, lower, trim), `io_impl` (nread, nwrite)

### Error handling (`ea` and `en`)
- `'0' ea '1÷0'` — catches error, evaluates alternate
- `en 0` — returns error code of most recent error
- Error codes: DomainError=3, LengthError=4, RankError=5, IndexError_=6
- Division by zero now raises proper DomainError
- `$::error` namespace with APL wrappers over Python i-beam implementations

### Comparison tolerance (`⎕CT`)
- Default `1E¯14`, affects `= ≠ < ≤ ≥ >`, dyadic `⍳`, and `∈`
- Match (`≡≢`) remains exact (not affected by `⎕CT`)
- Tolerant equality: `|a-b| ≤ ⎕CT × (|a| ⌈ |b|)`

### Membership (`∈`)
- `3∈1 2 3 4 5` → `1`
- Vector left arg: `1 3 5∈2 3 4` → `0 1 0`
- Respects `⎕CT`

### Match and tally (`≡ ≢`)
- Dyadic `≡` exact comparison (ignores `⎕CT`)
- Dyadic `≢` complement
- Monadic `≢` tally (number of major cells)

### Script runner
- `marple script.marple` executes each line
- Session transcript output (prompted input + output)
- Errors stop execution with line number
- `#import` directives silenced in output

### Display improvements
- Negative numbers shown with high minus (`¯`)
- Float precision: 10 significant digits
- Whole-number floats shown as integers
- Numpy bool values shown as `0`/`1`
- Right-aligned matrix columns

### Demo scripts (in `examples/`)
- `01_primitives.marple` — arithmetic, vectors, matrices, reduce, products
- `02_dfns.marple` — user functions, guards, recursion, rank
- `03_namespaces.marple` — system library, imports, file I/O, i-beams
- `04_errors.marple` — ea/en error handling, error codes

### Other
- Scientific notation in tokenizer (`1e-14`, `2.5E3`)
- `ClassError` (code 11) for name class violations
- Terminal UTF-8 fix for multi-byte characters

## Metrics

- **379 tests**, all passing
- **0 pyright errors** (strict mode)
- ~3,500 lines of implementation code (16 modules + stdlib)
- ~1,850 lines of test code (24 test files)
- 62 commits total
- 4 demo scripts with captured output

## Next steps

- Standard library expansion (`$::str::u`, `$::str::v2m`, `$::sys`)
- MicroPython port for Raspberry Pi Pico/Pico 2
- First-axis operators (`⌿ ⍀`)
- Line editing with history in the REPL
- Dictionary APL extensions (boxing)
- Performance: special-case scalar primitives at rank 0
- Error handling brief integration (numeric codes for scripted testing)
