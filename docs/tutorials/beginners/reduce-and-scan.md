# Reduce and Scan

Reduce and scan are your first **operators**. An operator takes a function and produces a new, derived function. They're one of APL's most powerful ideas.

## Reduce: `/`

Reduce inserts its operand function between every element of a vector. `+/` inserts `+` between every element, giving a sum:

```apl
      +/ 1 2 3 4 5
15
```

This is equivalent to `1 + 2 + 3 + 4 + 5`. But because APL evaluates right to left, the reduction actually computes `1 + (2 + (3 + (4 + 5)))`.

Any dyadic function can be the operand:

```apl
      ×/ 1 2 3 4 5
120
      ⌈/ 3 1 4 1 5 9
9
      ⌊/ 3 1 4 1 5 9
1
```

`×/` gives the product. `⌈/` gives the maximum. `⌊/` gives the minimum.

## Reduce on matrices

When applied to a matrix, `/` reduces along the **last axis** — that is, across each row:

```apl
      M ← 3 4 ⍴ ⍳12
      M
 1  2  3  4
 5  6  7  8
 9 10 11 12
      +/ M
10 26 42
```

Each row is summed independently, giving a 3-element vector.

To reduce along the **first axis** (down the columns), use `⌿`:

```apl
      +⌿ M
15 18 21 24
```

!!! tip "Rank operator alternative"
    You can also use the rank operator: `(+/⍤1) M` sums each row, `(+/⍤2) M` sums each column of a matrix. The [rank operator tutorial](../intermediate/rank-operator.md) covers this in detail.

## Scan: `\`

Scan is like reduce, but it keeps all the intermediate results. `+\` gives a running sum:

```apl
      +\ 1 2 3 4 5
1 3 6 10 15
```

This produces: `1`, `1+2`, `1+2+3`, `1+2+3+4`, `1+2+3+4+5`.

```apl
      ×\ 1 2 3 4 5
1 2 6 24 120
      ⌈\ 3 1 4 1 5 9
3 3 4 4 5 9
```

`×\` gives running products. `⌈\` gives running maximums.

## Scan on matrices

Like reduce, `\` works along the last axis (across rows), and `⍀` works along the first axis (down columns):

```apl
      +\ 3 3 ⍴ ⍳9
1  3  6
4  9 15
7 17 24

      +⍀ 3 3 ⍴ ⍳9
 1  2  3
 5  7  9
12 15 18
```

## The key idea: operators transform functions

The important thing isn't the specific examples — it's the concept. `/` and `\` are **operators**: they take a function (like `+` or `⌈`) and produce a new function (`+/`, `⌈\`). This is APL's version of higher-order functions.

MARPLE has several operators:

| Operator | Name | What it does |
|----------|------|--------------|
| `/` | Reduce | Insert function between elements (last axis) |
| `\` | Scan | Running reduce (last axis) |
| `⌿` | First-axis reduce | Reduce along first axis |
| `⍀` | First-axis scan | Scan along first axis |
| `∘.` | Outer product | Apply function to all pairs |
| `.` | Inner product | Generalised matrix multiply |
| `⍤` | Rank | Apply function at a specific cell rank |

You'll meet the others in later tutorials.

## Key points

- `/` (reduce) inserts a function between elements: `+/` sums, `×/` multiplies, `⌈/` finds the max
- `\` (scan) keeps intermediate results: `+\` gives running sums
- On matrices, `/` and `\` work across rows (last axis); `⌿` and `⍀` work down columns (first axis)
- Operators take functions and produce new functions — this is one of APL's core ideas

**Next:** [Reshape and Iota — Building Arrays](reshape-and-iota.md)
