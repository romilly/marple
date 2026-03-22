# Scalar Functions and Scalar Extension

Scalar functions are the workhorses of APL. They operate element-by-element on arrays of any shape, and they handle mismatched sizes gracefully through scalar extension.

## Scalar functions apply element-wise

When you add two vectors of the same length, the function is applied to each pair of corresponding elements:

```apl
      1 2 3 + 10 20 30
11 22 33
      5 10 15 × 2 3 4
10 30 60
```

This works for all scalar functions — arithmetic, comparison, boolean, and more:

```apl
      3 5 7 > 4 4 4
0 1 1
      1 0 1 ∧ 1 1 0
1 0 0
```

## Scalar extension

When one argument is a scalar and the other is an array, the scalar is **extended** — paired with every element:

```apl
      100 + 1 2 3 4 5
101 102 103 104 105
      1 2 3 4 5 × 10
10 20 30 40 50
      0 = 3 0 5 0 7
0 1 0 1 0
```

This works with arrays of any rank:

```apl
      M ← 2 3 ⍴ 1 2 3 4 5 6
      10 × M
10 20 30
40 50 60
```

## Matching shapes

If both arguments are arrays (not scalars), they must have the **same shape**. Mismatched shapes cause a LENGTH ERROR:

```apl
      1 2 3 + 10 20
LENGTH ERROR
```

## Monadic scalar functions

Most scalar functions also have a **monadic** form (one argument, on the right). The function is applied to each element:

| Dyadic | Monadic | Meaning |
|--------|---------|---------|
| `X + Y` (add) | `+ Y` (conjugate/identity) | Returns `Y` unchanged for real numbers |
| `X - Y` (subtract) | `- Y` (negate) | Flips sign |
| `X × Y` (multiply) | `× Y` (signum) | Returns ¯1, 0, or 1 |
| `X ÷ Y` (divide) | `÷ Y` (reciprocal) | `1÷Y` |
| `X * Y` (power) | `* Y` (exponential) | `e*Y` |
| `X ⍟ Y` (logarithm) | `⍟ Y` (natural log) | `ln Y` |
| `X ⌈ Y` (maximum) | `⌈ Y` (ceiling) | Round up |
| `X ⌊ Y` (minimum) | `⌊ Y` (floor) | Round down |
| `X \| Y` (residue) | `\| Y` (magnitude) | Absolute value |

```apl
      - 3 ¯5 0 7
¯3 5 0 ¯7
      ⌈ 2.3 4.7 ¯1.2
3 5 ¯1
      | ¯3 5 ¯7 0
3 5 7 0
```

!!! note "Negative numbers"
    APL uses `¯` (high minus) for negative numbers, not `-`. So negative three is `¯3`, not `-3`. The `-` symbol is the *subtract* function.

## The complete list

MARPLE implements these scalar functions. Each applies element-wise and supports scalar extension.

**Arithmetic:** `+` `−` `×` `÷` `⌈` `⌊` `*` `⍟` `|` `!` `○`

**Comparison:** `<` `≤` `=` `≥` `>` `≠`

**Boolean:** `∧` `∨` `⍲` `⍱` `~`

Comparison functions return 1 (true) or 0 (false). Boolean functions operate on 0s and 1s.

See the [Primitive Functions Reference](../../reference/primitives/index.md) for full details on each one.

## Key points

- Scalar functions work element-by-element on arrays of any shape
- If both arguments are arrays, their shapes must match
- If one argument is a scalar, it's extended to match the other
- Most scalar functions have both monadic and dyadic forms
- Comparison functions return 0 or 1

**Next:** [Reduce and Scan](reduce-and-scan.md)
