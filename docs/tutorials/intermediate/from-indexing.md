# Indexing with From

From (`⌷`) is MARPLE's functional indexing primitive. It selects **major cells** — subarrays along the first axis — and it composes with the rank operator for arbitrary-axis selection.

## Why From?

Bracket indexing (`M[i;j]`) works, but it's special syntax — it can't be passed to operators, can't be used in dfns as a first-class value, and the number of semicolons is tied to the array's rank. From is a proper function that composes with everything.

## Basic usage: selecting major cells

```apl
      V ← 10 20 30 40 50
      3 ⌷ V
30
      1 3 5 ⌷ V
10 30 50
```

For a vector, major cells are individual elements. For a matrix, major cells are rows:

```apl
      M ← 4 5 ⍴ ⍳20
      2 ⌷ M                    ⍝ row 2
6 7 8 9 10
      1 3 ⌷ M                  ⍝ rows 1 and 3
 1  2  3  4  5
11 12 13 14 15
```

For a rank-3 array, major cells are matrices:

```apl
      A ← 2 3 4 ⍴ ⍳24
      1 ⌷ A                    ⍝ the first 3×4 matrix
 1  2  3  4
 5  6  7  8
 9 10 11 12
```

## Result shape

The result shape is always `(⍴i) , 1↓⍴Y` — the shape of the index, followed by the shape of a single major cell.

```apl
      ⍴ 1 3 ⌷ M               ⍝ 2 rows, each of 5 columns
2 5
      ⍴ (2 3⍴1 2 1 2 1 2) ⌷ V ⍝ 2×3 matrix of selections from V
2 3
```

## From + Rank: selecting along other axes

Since From selects along the first axis, and rank controls which cells the function sees, combining them reaches any axis.

### Column selection

Apply From at rank 1 to select within each row:

```apl
      M ← 3 4 ⍴ ⍳12
      3 (⌷⍤0 1) M              ⍝ column 3
3 7 11
```

Left rank 0 (each index is a scalar), right rank 1 (each row is a 1-cell). The scalar `3` is paired with each row, selecting the 3rd element.

For multiple columns:

```apl
      1 3 (⌷⍤1) M              ⍝ columns 1 and 3
 1  3
 5  7
 9 11
```

### Rectangular cross-sections

Select rows first, then columns:

```apl
      2 4 (⌷⍤1) 1 3 ⌷ M       ⍝ rows 1,3 × columns 2,4
 2  4
10 12
```

Compare with bracket indexing: `M[1 3; 2 4]` — same result, but From composes with operators.

## Equivalence with bracket indexing

| Bracket syntax | From + Rank | Meaning |
|---------------|-------------|---------|
| `V[i]` | `i ⌷ V` | Select from vector |
| `M[i;]` | `i ⌷ M` | Select rows |
| `M[;j]` | `j (⌷⍤1) M` | Select columns |
| `M[i;j]` | `j (⌷⍤1) i ⌷ M` | Rows then columns |

## When to use which

**Use From** when you want composability — passing indexing to operators, writing rank-independent code, or building reusable tools.

**Use bracket indexing** when you want a quick, readable cross-section and don't need to compose.

Both are available. Use whichever is clearer for the task at hand.

## Key points

- `i ⌷ Y` selects major cells of `Y` at indices `i`
- Result shape: `(⍴i) , 1↓⍴Y`
- Combine with rank to select along any axis: `j (⌷⍤1) M` for columns
- From is a proper function — it composes with operators and works in dfns
- Bracket indexing is retained for convenience

**Next:** [Direct Functions in Depth](dfns-in-depth.md)
