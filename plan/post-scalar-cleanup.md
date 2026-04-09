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

## Helpers that could go away after the migration

- **`_dyadic` in `numpy_array.py`** — built around the list-of-1
  scalar idiom. Will be rewritten in the migration (Step 4 of the plan)
  but the rewrite may make it possible to drop the helper entirely in
  favour of `np.broadcast_to` + numpy native ops. Decide post-migration
  whether the abstraction still earns its keep.
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
