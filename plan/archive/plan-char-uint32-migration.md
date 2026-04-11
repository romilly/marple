# Plan: Character data uint32 migration

## Background

MARPLE currently stores character arrays as Python `list[str]`. The goal is to store them as `numpy.ndarray` of `uint32` (Unicode codepoints) so they live in the same representation as numeric arrays.

Yesterday (2026-04-06) we completed preparation: helper functions (`is_char_array`, `chars_to_str`, `str_to_char_array`, `char_fill`), 24 character safety-net tests, and migration of all detection sites to use the helpers. The actual representation flip got stuck on two problems:

1. **Chicken-and-egg.** Flipping `to_array` to produce uint32 breaks ~76 tests at once because creation sites and consumers are coupled.
2. **Empty character arrays.** `to_array([])` cannot distinguish empty-char from empty-numeric — type information is lost before `to_array` sees the data.

This plan unblocks both problems by sequencing changes that are individually safe to commit.

## Steps

### Step 1 — Arithmetic domain guards

Add `DomainError` guards to all arithmetic methods in `src/marple/numpy_array.py`: `add`, `subtract`, `multiply`, `divide`, `power`, `residue`, `min`, `max`, and any other numeric-only dyadic operations. They currently fall through from the `is_numeric_array` fast path to `_dyadic`, which silently applies operations to character data.

**Do NOT guard** comparison and equality operators (`<`, `>`, `≤`, `≥`, `=`, `≠`). These are legitimately defined for character data and must continue to work, with comparison tolerance forced to zero (already fixed yesterday in v0.7.7).

**TDD:** for each guarded method, write a failing test that asserts `DomainError` is raised when a character array is passed, then add the guard.

This step adds behaviour without changing representation, so it cannot break existing tests. Decouples arithmetic from the upcoming representation change.

**Commit.**

### Step 2 — `dtype_hint` parameter on `to_array`

Add an optional `dtype_hint` parameter to `to_array` with values `'char'` or `None` (default). When `dtype_hint='char'` and the input is empty, produce `np.array([], dtype=np.uint32)` instead of the default float64 empty array. For non-empty inputs the existing detection logic (via the helpers) is unchanged — the hint only matters for the empty case.

Update the known character-producing creation sites to pass the hint:
- `Str.execute` (handles `''`)
- `trim` (whitespace-only input)
- `_fill_element` (character fill)
- `quad-DM`, `quad-LX` (environment defaults)
- any other site discovered while editing

**TDD:** failing test that `to_array([], dtype_hint='char')` returns a uint32 array; failing test that `Str.execute('')` produces a character (not numeric) empty array.

**Commit.**

### Step 3 — Dual-representation phase

Make `is_char_array()` and the other helpers in `backend_functions.py` accept **both** `list[str]` and `numpy.ndarray` of `uint32`. `chars_to_str` and `char_fill` already need to handle both forms; verify and extend as needed.

This is the transitional bridge: it lets creation sites be flipped one at a time without breaking consumers, because consumers will accept either form during the transition.

**TDD:** for each helper, add tests that exercise both representations.

**Commit.**

### Step 4 — Flip creation sites one at a time

Start with `Str.execute` — it is the single entry point for character literals and has the clearest blast radius. Change it to produce `np.ndarray[uint32]` (via `str_to_char_array`), run the full test suite, fix fallout, commit.

Then flip the next creation site. Suggested order (smallest blast radius first, refine as we learn):
1. `Str.execute`
2. `_fill_element` for character fills
3. `trim`
4. `quad-DM`, `quad-LX`
5. Any remaining sites surfaced by failing tests

**Rule:** one creation site per commit. After each flip the test suite must be green before moving on. If a flip breaks more than ~10 tests, stop and discuss before fixing — that is a signal that a consumer needs attention before the next flip.

### Step 5 — Remove the list[str] branch

Once no creation site produces `list[str]` and the full suite is green, remove the list[str] branch from `is_char_array`, `chars_to_str`, `char_fill`, and any other helper that still carries dual-representation code. Search for any remaining `isinstance(x, str)` or `isinstance(x, list)` character checks and remove them.

**Commit.**

## Out of scope

- Performance optimisation of uint32 character operations — measure first, optimise later if needed.
- Changes to the parser, formatter, or display layer beyond what is required to keep tests green.
- MicroPython deployment testing of the migrated code — do that as a separate verification pass after Step 5.

## Open questions

None at plan time. Record any that arise during execution here.
