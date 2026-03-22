# Performance Issues

## Large arrays are slow

Check which backend is active. Without NumPy, all operations use pure Python loops, which can be orders of magnitude slower for large arrays.

**Fix:** install NumPy:

```bash
pip install numpy
```

Verify it is being used (see [Check which backend is active](../how-to/performance/check-backend.md)).

If you have set `MARPLE_BACKEND=none`, remove or change that setting:

```bash
unset MARPLE_BACKEND
marple
```

## Rank operator is slow on many cells

`(f⍤k)` calls `f` once per cell. For scalar functions, this is much slower than the built-in element-wise operations:

```apl
      10 + M            ⍝ fast: built-in scalar extension with NumPy
      10 (+⍤0) M        ⍝ slow: per-element dfn call overhead
```

**Fix:** use scalar primitives directly when possible. Reserve the rank operator for operations that genuinely need per-cell application (sorting rows, custom reductions, etc.).

## Inner product is slow

The fast path for `+.×` uses `numpy.dot`. Other inner products (e.g., `⌈.+`) fall back to per-element Python loops.

**Fix:** if you need fast matrix multiplication, use `+.×` which is accelerated. For other inner products, consider whether you can restructure the computation.

## Memory usage

MARPLE stores flat arrays. When NumPy is active, numeric arrays are stored as NumPy ndarrays (typically 8 bytes per element). Without NumPy, they are Python lists (roughly 28+ bytes per element).

**Fix:** install NumPy to reduce memory usage for large numeric arrays.
