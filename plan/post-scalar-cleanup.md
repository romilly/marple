# Post-scalar-convention cleanup follow-ups

The scalar storage convention migration completed 2026-04-09 in
commits `46c269f` → `fe7499a` (`v0.7.26` → `v0.7.40`). See
`progress-2026-04-09.md` for the full timeline and
`project_scalar_convention_rot.md` (in memory) for the durable
record of what was wrong and why.

This file lists cleanup work that the migration touched but kept
out of scope, plus follow-ups discovered during the post-migration
sweep that completed the same day.

## Type C sites — `.flatten()[0]` / `to_list(...)[0]` idioms

These work today (and continue to work after the storage flip) because
`.flatten()` and `to_list()` both produce a 1-d sequence regardless of
input shape. They are not blockers, just verbose. Listed here so that a
future cleanup pass can simplify them to `.item()`:

| file:line | function | current pattern |
|---|---|---|
| structural.py:152 | `catenate` | `alpha.data.flatten()` (scalar+scalar branch) |
| structural.py:354-355 | `encode` | `omega.data.flatten()[0]` |
| structural.py:473 | `from_array` | `alpha.data.flatten()[0]` |
| formatting.py:71 | `format_result` | `result.data.flatten()[0]` |
| nodes.py:389 | bracket index | `[idx.data.flatten()[0]]` |
| cells.py:14-16 | `rank_spec` | `to_list(spec.data)` then `data[0]` |

## Pre-existing dead code surfaced by the audit

(All known dead-code sites resolved 2026-04-09.)

## Monadic methods with `to_list`+comprehension slow paths

The monadic methods on `APLArray` follow a "numeric fast path /
to_list slow path" pattern. The slow paths are migration-safe via the
`to_list` defensive fix (commit `e5adc1d`), but they are also dead or
dead-adjacent code in the post-char-migration world: the only data
that hits the slow path is non-numeric, non-char data, which after
the char migration may not exist at all.

Sites:

| line | method | fast path | slow path |
|---|---|---|---|
| numpy_array.py:391 | `signum` | none ⚠️ | `to_list` + comprehension |
| numpy_array.py:397 | `negate` | numpy negate | `to_list` + comprehension |
| numpy_array.py:405 | `reciprocal` | numpy 1/data | `to_list` + comprehension |
| numpy_array.py:433 | `logical_not` | numpy 1-data | `to_list` + comprehension |
| numpy_array.py:443 | `factorial` | none ⚠️ | `to_list` + comprehension |

Refactoring goals after the migration:
1. Add a numpy fast path to `signum` and `factorial` (the two with no
   fast path at all). For `signum`: `np.sign(data)`. For `factorial`:
   numpy doesn't have a vectorised gamma in core, but `scipy.special`
   does, or use `np.vectorize(math.gamma)` as a thin wrapper.
2. Once every monadic has a fast path, audit whether the slow paths
   are dead. If yes, delete them.
3. If a `_monadic` helper would centralise the pattern usefully,
   create one — but only if it actually reduces duplication. The
   current per-method shape is fine if the slow paths go away.

## Helpers that could go away after the migration

- **`_dyadic` in `numpy_array.py`** — built around the list-of-1
  scalar idiom. **Originally planned for rewrite as Step 4a of the
  migration, but reclassified as post-migration cleanup on
  2026-04-09**: the `to_list` defensive fix (commit `e5adc1d`) made
  `_dyadic` migration-safe via the list bridge, so the rewrite is no
  longer required for correctness — only for code quality and
  performance. Three regression-guard tests were committed in
  preparation for this refactoring:
    - `test_dyadic_handles_zero_d_scalars_both_sides`
    - `test_dyadic_handles_zero_d_left_vector_right`
    - `test_dyadic_handles_vector_left_zero_d_right`
  When the refactoring happens, use `np.broadcast_arrays` or
  `np.broadcast_to` to align operand shapes, then a single
  comprehension over the broadcast result. Test driver options:
  `circular` (○) and `binomial` (!) — both go through `_dyadic` with
  no fast path. Decide post-migration whether the helper still earns
  its keep at all, or whether each dyadic method should call numpy
  directly via `np.frompyfunc` or similar.
- **`to_list()`** — many call sites only use it to bridge the
  list/array gap created by the broken scalar convention. After the
  storage flip, audit whether `to_list()` is still needed, or whether
  `.tolist()` / direct numpy ops would do.

## Missing operators

A scan of the tokenizer against the standard ISO operator set
shows the following operators are NOT recognised by marple at all
(no token, no parse, no execute):

- **`⍥` (Over)** — `f⍥g ω` ≡ `f g ω`; dyadically `α f⍥g ω` ≡
  `(g α) f (g ω)`. Pre-processes both arguments through g before
  applying f.
- **`@` (At)** — `(new)@(idx) array` patches values from `new` into
  `array` at positions `idx`. Common idiom for "update these
  elements". Heavy use in modern APL.
- **`⌸` (Key)** — `f⌸ y` partitions y by unique keys and applies f
  to each group. Used for tabulation and groupby-style code.
- **`⌺` (Stencil)** — `f⌺ window y` applies f to sliding windows of
  y. Used for cellular automata, image filters, etc.

Marple tokenises but does not (yet) fully implement:

- **`⍤` (Rank)** — known major missing feature, planned as the next
  big piece of work post-migration. See `project_rank_operator.md`.

Captured 2026-04-09 by user request during the commute work.
The list above is what a casual scan turned up; a more thorough
ISO/Dyalog audit may find more.

(Commute (`⍨`) added 2026-04-09, removed from this list.)

## Test file organisation

Tests are currently scattered across files in arbitrary ways. Some
files are per-primitive (`test_decode.py`, `test_random.py`); others
are broad collections (`test_matrices.py`, `test_extended_functions.py`,
`test_structural.py`); some bundle unrelated concerns (`test_sysvar.py`
holds system variables, ⎕EA, ⎕WA, and ⎕CR). The boundary between
`test_structural.py` and `test_structural_higherrank.py` is not
obvious.

Sort this out as a refactoring step once the more urgent post-scalar
work (encode, transpose, rank operator, etc.) is complete. Likely
principle: one file per primitive family, with cross-cutting concerns
(numeric types, character handling) in their own files. The exact
mapping is a planning task in its own right when we get to it.

Captured 2026-04-09 during the decode resume.

## Idiom upgrades worth considering

- **`np.char.mod` + `np.char.rjust`** — numpy has vectorized string
  formatting. Used in `dyadic_format` already (during the migration);
  worth checking whether `format_result` and `format_num` could also
  benefit.
- **Scalar extension via numpy broadcasting** — many dyadic primitives
  hand-roll scalar extension via `is_scalar()` branches. After the
  storage flip, numpy broadcasting handles this for free in most cases.
