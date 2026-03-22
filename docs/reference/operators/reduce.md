# Reduce (`f/`)

## Syntax

```
f/ Y
```

`f` is a dyadic scalar function. `Y` is the argument array.

## Description

Inserts `f` between consecutive elements of `Y`, evaluated **right to left**.

For a vector `a b c d`, `f/ a b c d` computes `a f (b f (c f d))`.

## Examples

```apl
      +/ 1 2 3 4 5
15
      ×/ ⍳5
120
      ⌈/ 3 1 4 1 5
5
      ⌊/ 3 1 4 1 5
1
```

Right-to-left evaluation matters for non-commutative functions:

```apl
      -/ 1 2 3 4 5
3
```

This computes `1-(2-(3-(4-5)))` = `1-2+3-4+5` = `3`.

## Higher-rank arrays

On matrices and higher-rank arrays, reduce works along the **last axis**. The result drops the last dimension.

```apl
      +/ 3 4⍴⍳12
10 26 42
```

Each row is summed independently.

## Empty arrays

Reducing an empty array raises DOMAIN ERROR.

## See also

- [Scan](scan.md) (`f\`) -- running reduction
- [First-axis variants](first-axis.md) -- use `(f/⍤¯1)` for first-axis reduce
