# Tips for writing fast MARPLE code

## Use scalar functions directly

Scalar functions (arithmetic, comparison, boolean) use the NumPy backend automatically. They are much faster than applying the same operation via rank:

```apl
      10 + M              ⍝ fast: built-in scalar extension with NumPy
      10 (+⍤0) M          ⍝ slow: per-element function call
```

## Prefer reduce over explicit recursion

Built-in reduce (`+/V`) uses NumPy's `ufunc.reduce` for commutative operations (add, multiply, maximum, minimum):

```apl
      +/⍳10000            ⍝ fast: single NumPy call
```

Writing the same reduction as a recursive dfn would be orders of magnitude slower.

## Minimise per-cell dfn calls

The rank operator calls your dfn once per cell. For large arrays with many cells, this can be slow. When possible, express your computation using built-in primitives and operators that map to vectorised NumPy operations.

## Operations with NumPy acceleration

These operations use NumPy when available:

- Arithmetic: `+`, `-`, `*`, `÷`, `*` (power)
- Comparison: `<`, `≤`, `=`, `≥`, `>`, `≠`
- Boolean: `∧`, `∨`, `~`
- Structural: `⍴` (reshape)
- Operators: `+/`, `*/`, `⌈/`, `⌊/` (commutative reduce)
- Inner product: `+.×` uses `numpy.dot`

See also: [NumPy backend](numpy-backend.md), [Performance issues](../../troubleshooting/performance-issues.md)
