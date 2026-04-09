# Post-scalar-convention cleanup follow-ups

When the scalar storage convention migration is complete (Steps 1-9 of
`plan-scalar-convention-fix.md`), there are a number of further cleanups
worth a dedicated sweep. The migration itself stays narrowly focused on
"make storage and APL shape agree" — these notes capture work that
*could* be done in the same area but is out of scope for the migration
itself.

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

- **`workspace.py:25`** — `if isinstance(v, str): return f"'{v}'"`. After
  the char-uint32 migration completed on 2026-04-07, `value.data[0]` for
  a char scalar is a `uint32` codepoint, never a Python `str`. This
  branch is unreachable. Safe to remove (and the surrounding logic
  needs to render char scalars via `chr(int(...))` instead).

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

## Idiom upgrades worth considering

- **`np.char.mod` + `np.char.rjust`** — numpy has vectorized string
  formatting. Used in `dyadic_format` already (during the migration);
  worth checking whether `format_result` and `format_num` could also
  benefit.
- **Scalar extension via numpy broadcasting** — many dyadic primitives
  hand-roll scalar extension via `is_scalar()` branches. After the
  storage flip, numpy broadcasting handles this for free in most cases.
