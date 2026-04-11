# Plan: Fix the scalar APLArray storage convention

## Context

`APLArray.scalar(value)` stores its data as a **1-element 1-d
ndarray** (shape `(1,)`) while the APL `shape` attribute is `[]`
(rank 0). The two layers disagree about rank. This is a vestige of
the list-backed era preserved through the numpy migration. See the
memory `project_scalar_convention_rot.md` for the full discovery
narrative; see `progress-2026-04-08.md` for how it surfaced.

The bug stayed hidden because (1) numpy length-1 broadcasting
accidentally mimics APL scalar extension, (2) primitives use
`is_scalar()` (which checks APL shape) rather than `data.ndim`, and
(3) no primitive in the new engine had a result-shape rule that
distinguished a scalar from a 1-element vector — until decode
(`(¯1↓⍴⍺),(1↓⍴⍵)`), exposed by spec-driven testing on 2026-04-08.

The fix is a **precondition** for:
- The decode/encode/transpose post-char-migration sweep (paused mid-decode)
- The rank operator (`⍤`) — the next major feature
- From (`⌷`) — also next
- Any future primitive whose result shape depends on input rank

## Goal

After this work, **`APLArray.scalar(7).data` is a 0-d ndarray**
(`np.array(7)`, `data.ndim == 0`, `data.shape == ()`). APL `shape`
and numpy `data.shape` agree everywhere. Numpy idioms like
`broadcast_to`, `cumprod` along an axis, and the `@` operator can
be used naturally on APLArray data without compensating reshapes.

## Approach

Strict TDD per `CLAUDE.md`. Multi-commit migration similar in shape
to the char-uint32 one (16 commits, 2026-04-07). Sequenced so each
commit leaves the suite green.

### Step 0 — Stage the dirty tree

The working tree at the start of 2026-04-09 contains uncommitted
work from 2026-04-08:

```
modified:   src/marple/__init__.py            (version → 0.7.26)
modified:   src/marple/structural.py          (partial decode rewrite)
modified:   tests/new_engine/test_matrices.py (+11 spec-driven decode tests)
```

**Decisions to make first thing:**

- The 11 spec-driven decode tests are spec-correct and should be kept
  as a target for after the convention fix lands. Recommendation:
  keep in working tree, do not commit yet (they have failures), use
  them to verify decode after the fix.
- The partial decode rewrite in `structural.py` will be redone after
  the fix. Recommendation: **revert** so the fix lands against the
  current decode (which has known matrix-`α` and float-`ω` bugs that
  the spec tests will catch post-fix).
- The version bump to 0.7.26 in `__init__.py` had no corresponding
  commit. Recommendation: **revert** and let the first real commit
  of the migration bump it.

### Step 1 — Failing canary tests

Write tests in a new `tests/new_engine/test_scalar_convention.py`
that assert the *desired* state:

```python
def test_scalar_data_is_zero_dimensional():
    assert S(7).data.ndim == 0
    assert S(7).data.shape == ()

def test_scalar_apl_shape_matches_data_shape():
    s = S(7)
    assert len(s.shape) == s.data.ndim

def test_scalar_equality_works_after_fix():
    assert S(7) == S(7)
    assert S(7) != S(8)
```

These will **fail** against the current code. They are the canary
that drives the rest of the migration. **Commit:** failing tests
under an `xfail` marker, OR commit them as failing in a single
"start of migration" commit alongside Step 2's first edit so the
suite stays green.

### Step 2 — Make `__eq__` shape-tolerant for the migration window

Before changing `S()` itself, fix `APLArray.__eq__` so that
`np.array_equal` is replaced with a comparison that treats 0-d and
1-d (1,) as equal **when both APLArrays have `shape == []`**. This
is the bridge that lets the rest of the migration proceed without
every test breaking on the first commit.

```python
def __eq__(self, other):
    if not isinstance(other, APLArray):
        return NotImplemented
    if self.shape != other.shape:
        return False
    if is_char_array(self.data) != is_char_array(other.data):
        return False
    # Bridge: scalar APLArrays may have 0-d or 1-d (1,) data
    # during the migration. Compare flat values.
    if self.shape == []:
        return self.data.flat[0] == other.data.flat[0]
    return bool(np.array_equal(self.data, other.data))
```

**Commit:** test that the bridge works (an explicit test that
constructs a scalar APLArray with 0-d data and compares it equal to
`S(value)`). Run full suite, must stay green.

### Step 3 — Flip the factory

Change `APLArray.scalar` to use 0-d storage:

```python
@classmethod
def scalar(cls, value):
    return APLArray([], np.asarray(value))
```

Run full suite. Expect failures: every site that does
`scalar.data[0]` will fail with `IndexError: too many indices for
array`. The `__eq__` bridge from Step 2 keeps tests working.

**Commit:** the factory flip, with a list of failing sites in the
commit message.

### Step 4 — Fix `data[0]` extraction sites

The 41 src sites identified by
`rg '\.data\[0\]|\.data\.flatten\(\)\[0\]' src/marple/`. For each,
the right replacement depends on context:

- If extracting a scalar value: `data.item()` (works for 0-d and 1-d)
- If iterating: use `to_list(data)` or `data.flat`
- If the access is "first element of a vector": leave as `data[0]`,
  it's not a scalar-extraction site at all

Group these by file and commit one or two files per commit. After
each commit, run full suite, must stay green.

Files to touch (from 2026-04-08 grep):

| file | hits |
|---|---|
| `numpy_array.py` | 9 |
| `executor.py` | 13 |
| `structural.py` | 8 |
| `environment.py` | 4 |
| `formatting.py` | 2 |
| `dfn_binding.py` | 1 |
| `fmt.py` | 1 |
| `jupyter/html_render.py` | 1 |
| `nodes.py` | 1 |
| `workspace.py` | 1 |

### Step 5 — Fix `__repr__` and `_dyadic`

`numpy_array.py:47` (`__repr__`) and `numpy_array.py:53–75` (`_dyadic`)
both compensate for the convention. Update them to use `.item()` for
scalar extraction.

### Step 6 — Audit `is_scalar()` call sites

The 29 src `is_scalar()` calls are mostly correct (they check APL
shape, not data shape). But verify each one is doing the right thing
post-fix — particularly anywhere a scalar branch builds an APL result
using `data[0]` indexing.

### Step 7 — Test fallout

The 36 test-side `data[0]` patterns are slightly different. Most
will be tests that explicitly probe data internals; some may need
updating to `.item()`.

**Some tests in `test_matrices.py` (the 11 spec-driven decode tests
from 2026-04-08) will start passing for the right reason** as
`weights @ o_view` produces correct results without compensating
reshapes. Verify each one still passes for the right reason after
the fix.

### Step 8 — Remove the bridge from `__eq__`

Once no APLArray anywhere stores scalars as 1-d (1,) data, remove
the bridge from Step 2 and restore `np.array_equal` as the sole
comparison. This proves the migration is complete.

**Commit:** "End of scalar convention migration."

### Step 9 — Resume the decode sweep

With the convention fixed, redo the decode rewrite using the clean
numpy idiom that prompted the discovery:

```python
def decode(alpha, omega):
    if is_char_array(alpha.data) or is_char_array(omega.data):
        raise DomainError("⊥ does not accept character arguments")
    a, o = alpha.data, omega.data
    a_n = a.shape[-1] if a.ndim >= 1 else 1
    o_n = o.shape[0]  if o.ndim >= 1 else 1
    if a_n != o_n and a_n != 1 and o_n != 1:
        raise LengthError(f"⊥ length mismatch: {a_n} vs {o_n}")
    n = max(a_n, o_n)
    a2 = np.atleast_1d(a)
    a_view = np.broadcast_to(a2, a2.shape[:-1] + (n,))
    o2 = np.atleast_1d(o)
    o_view = np.broadcast_to(o2, (n,) + o2.shape[1:])
    ones_tail = np.ones(a_view.shape[:-1] + (1,), dtype=a_view.dtype)
    shifted = np.concatenate([a_view[..., 1:], ones_tail], axis=-1)
    weights = np.flip(np.cumprod(np.flip(shifted, axis=-1), axis=-1), axis=-1)
    result = weights @ o_view
    result_shape = list(a.shape[:-1]) + list(o.shape[1:])
    return APLArray(result_shape, np.asarray(result).reshape(tuple(result_shape)))
```

The reshape no longer needs an `or (1,)` fallback because scalar
APLArrays now hold 0-d data, and `result.reshape(())` produces a
0-d array that equals `S(value)` directly.

Run the 11 spec tests. Should be 11/11. Bump version. Commit.

## Verification at every commit

```bash
pytest                                       # full fast suite, must pass
pyright src/                                 # strict, no NEW errors (the
                                             # 31 pre-existing ones documented
                                             # 2026-04-08 are not in scope)
```

## Out of scope

- The Pico ulab `uint32 → uint16` migration (deferred since 2026-04-07)
- Encode and transpose sweeps (resume after decode is re-landed)
- Any change to `is_char_array`, `chars_to_str`, etc. — these were
  already migrated in the char-uint32 work and are not affected
- Removing `is_scalar()` as an API — keep it; it's a valid abstraction
  even with correct storage

## Open questions

To discuss before starting:

1. Step 0: revert the partial decode rewrite, or keep it as a
   reference for Step 9?
2. Step 1: `xfail` the canary tests, or commit them alongside Step 2's
   bridge so the very first commit is green?
3. Is there anywhere outside `numpy_array.py` that explicitly
   constructs `APLArray([], ...)` with non-list data we should know
   about? (grep found 2 src sites — verify they're not affected)
