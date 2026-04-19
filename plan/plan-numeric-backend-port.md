# Plan: Numeric-backend port (re-enabling the Pico path)

## Status

**Not scheduled yet.** The user wants to complete some long-deferred test
refactoring before starting on this experiment. This file records the agreed
design so we can pick it up cleanly when the test work is done.

## Context

MARPLE's `APLArray` currently holds data as `np.ndarray`, and several modules
reach directly into numpy for arithmetic, reductions, reshape, `np.dot`,
`np.errstate` overflow handling, and ufunc fast paths for inner/outer products.

The project ran on the Raspberry Pi Pico under MicroPython + ulab.numpy for a
period of time. It was abandoned at v0.8.0 (2026-04-11) because the char-data
migration to `uint32` (completed in `plan/archive/plan-char-uint32-migration.md`)
is incompatible with ulab, whose dtype set stops at `uint16`. The planned
`uint32 → uint16` workaround was deferred and never landed.
(See `plan/progress-2026-04-08.md`: "Pico e2e: still blocked on uint32"; and
`plan/progress-2026-04-11-pm.md`: "desktop-only after MicroPython abandonment".)

The intended outcome of this refactor is to isolate numpy behind a port so the
same APL semantics can run on top of either numpy (desktop) or ulab.numpy
(Pico). The char-dtype mismatch — the specific thing that killed Pico — is
absorbed by the port rather than leaking through the codebase. Ports are also
consistent with the existing pattern in `src/marple/ports/` (`filesystem`,
`console`, `config`, `timer`, `char_source`).

## Recommended approach: operation-level `NumericBackend` port

Evaluated against clarity, module/function length, composability, simplicity,
and ease of testing, an **operation-level** port wins over a glyph-level port on
every criterion except one-time churn:

- **Clarity** — port contract reads as "primitives APL needs from a numeric
  backend"; no APL surface syntax leaks into it.
- **Length** — ~15–20 primitive methods vs ~40 glyph entries per adapter.
- **Composability** — adapters can share helpers; primitives reuse across
  glyphs (e.g. `negate` serves `-`, `÷−`, conjugate).
- **Simplicity** — APL semantics (scalar extension, tolerant compare, char
  guards) stay in `APLArray` in one place instead of being duplicated across
  adapters.
- **Testing** — contract tests at the primitive level are small and exhaustive;
  no APL-rule entanglement.

**Storage stays ndarray-compatible.** ulab.numpy exposes an ndarray-like API,
so `APLArray.data` remains a concrete array type. An opaque `Buffer` protocol
would add indirection with no payoff for the two realistic backends.

## Char dtype must be abstract in the port

This is the Pico-unblocking piece. Today `backend_functions.is_char_array`
hardcodes `np.issubdtype(data.dtype, np.uint32)`. In the port design:

- `NumericBackend.is_char(buffer) -> bool` — backends classify their own
  storage.
- `NumericBackend.make_char_array(text: str)` — numpy adapter returns `uint32`;
  ulab adapter returns `uint16` (BMP-only).
- `NumericBackend.classify(buffer) -> Literal["int", "float", "bool", "char"]`
  — single dispatch hook for APL-semantic decisions in `APLArray`.

Calling code never inspects dtypes directly. Both `uint32` (numpy) and `uint16`
(ulab) are "char" to the same calling code.

## Overflow signalling belongs in the port

The "upcast when you must" pattern (commits `35c9e18` … `3ef3cd4`) wraps
arithmetic in `np.errstate(over='raise', invalid='raise')` and catches
`FloatingPointError`. That contract is numpy-specific; ulab raises different
exceptions. So the port owns overflow detection:

```python
backend.try_op(name, a, b) -> OpResult  # either a buffer, or an Overflow signal
```

Adapters translate native exceptions into the common `Overflow` signal.
`APLArray` decides what to do with it (retry in float64, raise `DomainError`).

## Walking-skeleton first slice

Prove the pattern on a small, low-risk surface before growing the port:

1. `NumericBackend` ABC in `src/marple/ports/numeric_backend.py` with:
   - `add`, `subtract`, `multiply`, `negate`, `reciprocal`
   - `make_char_array`, `make_numeric_array`, `is_char`, `classify`
   - `try_op` (overflow-aware wrapper)
2. `NumpyBackend` adapter in `src/marple/adapters/numpy_backend.py`
   replicating current behaviour (uint32 chars, `np.errstate` translation).
3. Contract tests in `tests/adapters/test_numeric_backend_contract.py` that any
   adapter must pass. Run them against `NumpyBackend` only for now; a
   ulab-adapter sketch is documented but not implemented.
4. Wire `APLArray.add / subtract / multiply / negate / reciprocal` and
   `backend_functions.is_char_array` to delegate through an injected
   `NumericBackend`. Default injection keeps current behaviour.
5. Full existing test suite must stay green throughout.

## Critical files

- `src/marple/numpy_array.py` — `APLArray` and its arithmetic methods; data
  ownership and APL semantics live here and stay here.
- `src/marple/backend_functions.py` — `is_char_array`, `chars_to_str`,
  `str_to_char_array`, `char_fill`, dtype coercion; char classification routes
  through the port.
- `src/marple/executor.py` — `_INNER_SCALAR_OPS`, `_OUTER_UFUNCS`, `np.dot`
  fast path, `np.errstate` usage; later slices will add `dot`, `pairwise`,
  `outer` port methods.
- `src/marple/monadic_functions.py`, `dyadic_functions.py` — glyph→method
  tables; **untouched** by this refactor.
- `src/marple/ports/` — new `numeric_backend.py` lives here alongside existing
  ports.
- `src/marple/adapters/` — new directory; `numpy_backend.py` goes here.

## Existing utilities to reuse

- Port/adapter pattern already established — `src/marple/ports/filesystem.py` is
  the closest shape precedent (small ABC, one abstract method per operation).
- Char helpers (`is_char_array`, `chars_to_str`, `str_to_char_array`,
  `char_fill`) — rewire them to delegate to the backend rather than reimplement.
- The dispatch tables in `MonadicFunctionBinding._SIMPLE` and
  `DyadicFunctionBinding._SIMPLE` already isolate scalar dispatch cleanly; no
  change needed there.
- `DomainError` raising pattern from the char-arithmetic guards (step 1 of
  `plan/archive/plan-char-uint32-migration.md`) — reuse as-is.

## Verification

- `pytest` — full fast suite green against `NumpyBackend`.
- `pytest -m slow` — PRIDE and WebSocket paths unaffected.
- Contract tests in `tests/adapters/test_numeric_backend_contract.py` — any
  adapter must satisfy the port's behavioural contract (arithmetic correctness,
  overflow signalling, char classification, dtype preservation).
- Manual REPL check of a handful of arithmetic expressions against Dyalog to
  confirm no regressions in observable behaviour.
- A ulab-adapter sketch (documented, not executed) that shows how `uint32` char
  storage is mapped to `uint16` — proof that the port's char-dtype abstraction
  actually absorbs the Pico blocker.

## Open questions (to resolve before starting)

- Exact shape of the `try_op` / `OpResult` contract — discuss when we pick this
  up. The least obvious piece and the one most likely to need iteration.
- Whether `make_char_array` and `make_numeric_array` return backend-native
  buffers or a thin wrapper — depends on what minimises call-site churn in
  `APLArray`.
- Whether `NumericBackend` is injected per-`APLArray`, per-`Executor`, or
  module-level — module-level is simplest but couples tests; per-`Executor` is
  closest to the existing port wiring.
