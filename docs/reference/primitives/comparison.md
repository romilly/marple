# Comparison Functions

All comparison functions are dyadic and scalar. They return `1` (true) or `0` (false) for each element pair. They apply element-wise with scalar extension.

## Summary

| Glyph | Name | `3 f 4` | `4 f 4` |
|-------|------|---------|---------|
| `<` | Less than | 1 | 0 |
| `≤` | Less than or equal | 1 | 1 |
| `=` | Equal | 0 | 1 |
| `≥` | Greater than or equal | 0 | 1 |
| `>` | Greater than | 0 | 0 |
| `≠` | Not equal | 1 | 0 |

## Examples

```apl
      3<5
1
      5<3
0
      1 2 3 4 5≥3
0 0 1 1 1
      3=3
1
      3≠3
0
```

## Comparison tolerance (`⎕CT`)

Comparisons use tolerant comparison for floating-point values. Two numbers `a` and `b` are considered equal if:

```
|a-b| ≤ ⎕CT × (|a| ⌈ |b|)
```

The default `⎕CT` is `1E¯14`. This means very small floating-point differences (from rounding) are ignored:

```apl
      1=(1÷3)×3          ⍝ tolerant: 0.999... equals 1
1
```

Set `⎕CT←0` for exact comparison:

```apl
      ⎕CT←0
      1=1.001
0
```

!!! note
    Match (`≡`) and not-match (`≢`) always use exact comparison, regardless of `⎕CT`.
