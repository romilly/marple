# First-Axis Reduce (`⌿`) and Scan (`⍀`)

## Monadic: reduce and scan along the first axis

`f⌿` reduces along the first axis (columns of a matrix). `f⍀` scans along the first axis.

```apl
      M ← 3 4⍴⍳12
      +⌿M               ⍝ sum down columns
15 18 21 24
      +⍀M               ⍝ running sum down columns
 1  2  3  4
 6  8 10 12
15 18 21 24
```

For vectors, `f⌿` and `f⍀` behave the same as `f/` and `f\`.

These work on arrays of any rank — they always reduce or scan along the first axis.

## Dyadic: first-axis replicate/compress

`⌿` used dyadically replicates or compresses along the first axis (selecting or repeating major cells):

```apl
      1 0 1⌿3 4⍴⍳12     ⍝ select rows 1 and 3
1  2  3  4
9 10 11 12
```

## Rank operator alternative

The rank operator can also express first-axis operations:

| Traditional | Rank equivalent |
|------------|-----------------|
| `f⌿ M` | `(f/⍤¯1) M` |
| `f⍀ M` | `(f\⍤¯1) M` |

## See also

- [Rank Operator](rank.md) (`f⍤k`)
- [Reduce](reduce.md) (`f/`)
- [Scan](scan.md) (`f\`)
