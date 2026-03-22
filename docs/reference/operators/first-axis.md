# First-Axis Reduce (`⌿`) and Scan (`⍀`)

## Status

`⌿` and `⍀` are **not implemented** in MARPLE.

## Replacement

Use the rank operator to achieve the same effect:

| Traditional | MARPLE equivalent |
|------------|-------------------|
| `f⌿ M` | `(f/⍤¯1) M` |
| `f⍀ M` | `(f\⍤¯1) M` |

## Example

Column sums of a matrix:

```apl
      (+/⍤¯1) 3 4⍴⍳12
15 18 21 24
```

This applies `+/` to each `¯1`-cell (each column slice) of the matrix.

## See also

- [Rank Operator](rank.md) (`f⍤k`)
- [Reduce](reduce.md) (`f/`)
- [Scan](scan.md) (`f\`)
