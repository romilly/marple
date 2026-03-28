# Plan: Convert 223 Missing Tests to New Engine

## Context

The old interpreter was deleted but 223 tests were not converted first.
The old tests can be recovered from git: `git show 3879a34^:tests/test_*.py`

Currently 498 tests pass. We need ~720 (498 + 223 missing).

## Rules

- Recover each old test file from git history
- Convert every test to use `Interpreter` from `marple.engine`
- Add to the appropriate file in `tests/new_engine/`
- Run tests after each file, fix any failures (these reveal real bugs)
- Commit after each file
- Run pyright before each commit

## Files to convert (in order of size)

### 1. test_sysvar.py (71 missing)
FMT (all variants including G-pattern, text insertion, A format, matrix,
cycling, error cases), NL, CR (simple, multi-line, round-trip, errors),
FX (simple, multi-statement, round-trip, dop, errors), DR (all types,
dyadic), FR (set, decimal mode), EN/DM (after error, readonly),
EA (with expression alternate), CSV (numeric, text, row count),
DL (elapsed, zero), file I/O (read, write, exists, delete, errors)

### 2. test_dfns.py (25 missing)
Dop tests (with negate, reciprocal, reduce, scan, iota, guard, compose,
array operand, dyadic dop), multi-statement (CR, FX round-trip),
named dyadic with variable/parens, alpha_alpha outside dop error

### 3. test_structural.py (18 missing)
Basic: iota, shape (scalar/vector), reshape, ravel (scalar/vector),
reverse, rotate (left/right), take (front/end), drop (front/end),
catenate (vectors, scalar+vector), index_of

### 4. test_operators.py (14 missing)
Matrix reduce/scan (columns via ⌿/⍀), replicate rows, reduce
right-to-left (subtract), single element reduce, large sum,
running max, rank3 reduce, vector scan same as backslash

### 5. test_ct.py (14 missing)
Default CT, near equal/not-equal/less-equal/greater-equal, far not
equal, CT zero exact, iota tolerant (including ÷3), match exact,
membership (found/not found/tolerant/vector)

### 6. test_numeric_types.py (13 missing)
Backend downcast/upcast tests — these test `maybe_downcast` and
`maybe_upcast` directly, not via interpreter. Check if they need
converting or if they're infrastructure tests.

### 7. test_random.py (13 missing)
RL seed (default, set), deterministic roll/deal, roll in range,
roll pervades, roll respects IO, roll zero gives float, deal
distinct/in range/length/error/respects IO

### 8. test_matrices.py (11 missing)
Encode, decode (mixed base), grade up/down, negate matrix,
ravel matrix, scalar+matrix, shape of matrix, transpose
(matrix and vector)

### 9. test_indexing.py (10 missing)
IO=0 tests (indexing, grade up/down, index-of, not-found),
rank3/rank4 index preservation, outer product index,
default index origin, string index with matrix

### 10. test_ea.py (10 missing)
Success/failure returns, divide by zero raises, EN via EA,
failure with expression alternate, fresh session EN,
error codes (index, length), not reset by success

### 11. test_name_table.py (9 missing)
Array/function assignment NC, class change errors (both directions),
call outer fn in dfn (with/without iota), define and call in dfn
(monadic/dyadic), imported fn with alias no parens

### 12. test_namespaces.py (6 missing)
Tokenizer tests (simple, triple, system workspace qualified names),
guard not affected, qualified in expression, str::trim

### 13. test_extended_functions.py (3 missing)
tan(0), sqrt_via_circle (0○0.6), pi_times_two (○2)

### 14. test_workspace.py (3 missing)
load_restores_wsid, load_system_vars_first, save_system_variable

### 15. test_workspace_chars.py (2 missing)
save_and_load_char_vector, save_and_load_char_matrix

### 16. test_interpreter.py (1 missing)
comment_only_no_space

## After all tests converted

- Run full suite, verify ~720 tests pass
- Move `tests/new_engine/` contents up to `tests/`
- Review `_sysvar_ts` implementation
- Implement FunctionRef wrapping in parser (now that old interpreter is gone)
- Add ⎕CSV to new engine
- Bump version and push
