# The Rank Operator Step by Step

The rank operator (`⍤`) is MARPLE's most important extension to first-generation APL. It lets you apply *any* function — primitive or user-defined — at any level of an array's structure. Once you understand it, you'll use it constantly.

## The problem rank solves

In first-generation APL, `+/M` reduces along the last axis (sums each row). To reduce along the first axis, you need `+⌿M`. But what if you want to apply a *user-defined* function along a specific axis? Bracket-axis (`f[1]`) only works with certain primitives. There's no general mechanism.

Rank provides that mechanism. `(f⍤k)` means "apply `f` to each k-cell" — and it works with *any* function.

## Cells and frames

To use rank, you need two concepts.

A **k-cell** is a subarray formed by the last `k` axes. For a matrix `M` with shape `3 4`:

- **0-cells** are individual scalars (12 of them)
- **1-cells** are the rows — vectors of length 4 (3 of them)
- **2-cells** are the whole matrix (1 of it)

The remaining leading axes form the **frame** — the structure that organises the cells.

```apl
      M ← 3 4 ⍴ ⍳12
      ⍴M
3 4
      ⍝ 1-cells: 3 rows, each of length 4
      ⍝ Frame is 3 (three 1-cells)
```

For a rank-3 array with shape `2 3 4`:

- **1-cells** are 6 vectors of length 4 (frame `2 3`)
- **2-cells** are 2 matrices of shape `3 4` (frame `2`)
- **3-cells** are the whole array (frame is empty)

## Monadic rank: `(f⍤k) Y`

The expression `(f⍤k) Y` means: decompose `Y` into k-cells, apply `f` to each one, reassemble the results.

### Apply to each row (rank 1)

```apl
      M ← 3 4 ⍴ ⍳12

      (⌽⍤1) M           ⍝ reverse each row
 4  3  2  1
 8  7  6  5
12 11 10  9

      (+/⍤1) M          ⍝ sum each row
10 26 42
```

`⌽⍤1` applies reverse to each 1-cell (row). The frame is `3`, so the result has 3 reversed rows.

`+/⍤1` applies `+/` (sum) to each 1-cell. Each row reduces to a scalar, so the result is a 3-element vector.

### Apply to each matrix (rank 2)

```apl
      A ← 2 3 4 ⍴ ⍳24

      (+/⍤2) A           ⍝ sum each 3×4 matrix (column sums per layer)
12 15 18 21
48 51 54 57
```

The frame is `2` (two 2-cells). Each matrix is reduced along its last axis, giving a `4`-element vector per matrix. Result shape: `2 4`.

### User-defined functions work too

```apl
      sort ← {⍵[⍋⍵]}
      (sort⍤1) M         ⍝ sort each row independently
```

This is something bracket-axis cannot do. There's no `sort[1]` — but `sort⍤1` works perfectly.

## Negative rank (complementary)

Negative rank means "everything except the first `|k|` axes". For an array of rank `r`, `⍤¯1` means `(r−1)`-cells — the major cells.

```apl
      (+/⍤¯1) 2 3 4 ⍴ ⍳24
      ⍝ On a rank-3 array, ¯1 → 2-cells → same as (+/⍤2)
```

This is useful for writing rank-independent code: `(f⍤¯1)` always applies `f` to major cells, regardless of the array's actual rank.

## Dyadic rank: `X (f⍤b c) Y`

In the dyadic case, you specify separate cell ranks for left and right arguments:

```apl
      V ← 10 20 30 40
      M ← 3 4 ⍴ ⍳12

      V (+⍤1) M          ⍝ add vector V to each row of M
11 22 33 44
15 26 37 48
19 30 41 52
```

`V` is a single 1-cell (frame is empty). `M` has three 1-cells (frame is `3`). When one frame is empty, that argument is paired with *every* cell of the other — scalar extension at the frame level.

### Different ranks for each argument

```apl
      100 200 300 (+⍤0 1) M
101 102 103 104
205 206 207 208
309 310 311 312
```

Left rank 0: three scalars (frame `3`). Right rank 1: three rows (frame `3`). Frames match, so scalar 100 is added to row 1, 200 to row 2, 300 to row 3.

## The rank specification

The right operand to `⍤` is 1, 2, or 3 integers:

| You write | Interpreted as | Meaning |
|-----------|---------------|---------|
| `⍤c` | `c c c` | Same rank for monadic, left, and right |
| `⍤b c` | `c b c` | `b` for left arg, `c` for right arg and monadic |
| `⍤a b c` | `a b c` | `a` monadic, `b` left, `c` right |

!!! warning "Always parenthesise"
    Write `(f⍤1) Y`, not `f⍤1 Y`. Without parentheses, `⍤` tries to bind the strand `1 Y` as its right operand. See [Common Mistakes](../../troubleshooting/common-mistakes.md).

## The reassembly rule

After applying `f` to each cell, the results are reassembled. If all result cells have the same shape, they stack neatly. If shapes differ (rare in practice), shorter results are padded with fill elements (0 for numbers, space for characters) to make them uniform.

This is MARPLE's flat-array answer to what nested APLs handle with enclosure. See [The Reassembly Constraint](../../explanation/rank-history.md#the-reassembly-constraint) for the full story.

## Rank replaces bracket-axis

| Old style | With rank | Meaning |
|-----------|-----------|---------|
| `+/M` | `(+/⍤1) M` | Sum each row |
| `+⌿M` or `+/[1]M` | `(+/⍤¯1) M` | Sum down columns |
| `⌽[1]M` | `(⌽⍤¯1) M` | Reverse along first axis |

For primitives, the old style is fine. For user-defined functions, rank is the only option.

## Key points

- `(f⍤k) Y` applies `f` to each k-cell of `Y`
- A k-cell is formed by the last `k` axes; the leading axes are the frame
- Negative rank (`⍤¯1`) counts from the front — useful for rank-independent code
- Dyadic rank (`⍤b c`) specifies separate cell ranks for left and right arguments
- Frames must match, or one must be empty (scalar extension at the frame level)
- Always parenthesise: `(f⍤k) Y`, not `f⍤k Y`
- Rank works with any function, including user-defined dfns

**Next:** [Indexing with From](from-indexing.md)
