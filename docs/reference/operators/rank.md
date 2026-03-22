# Rank Operator (`f⍤k`)

## Syntax

```
  (f⍤k) Y           ⍝ monadic: apply f to each k-cell of Y
X (f⍤k) Y           ⍝ dyadic: decompose X and Y, apply f to paired cells
```

## Right operand (rank specification)

| Form | Expansion | Meaning |
|------|-----------|---------|
| `⍤c` | `c c c` | Same rank for monadic, left-dyadic, and right-dyadic |
| `⍤b c` | `c b c` | `b` = left rank, `c` = right and monadic rank |
| `⍤a b c` | as-is | `a` = monadic, `b` = left, `c` = right |

## Negative rank

Negative values are complementary: `⍤¯1` means cells of rank `(array rank - 1)`. For a matrix, `⍤¯1` gives 1-cells (rows).

## Cell decomposition

Given array rank `r` and cell rank `k` (after clamping to `[0, r]`):

- **Cell shape**: the last `k` axes of the array.
- **Frame shape**: the leading `r-k` axes.

The array is split into cells in row-major order of the frame.

## Monadic use

```apl
      (⌽⍤1) 3 3⍴⍳9
3 2 1
6 5 4
9 8 7
```

Reverses each row (1-cell) of the matrix.

## Dyadic use

```apl
      10 20 30 (+⍤0 1) 3 3⍴⍳9
11 12 13
24 25 26
37 38 39
```

Adds each scalar (0-cell) of the left argument to each row (1-cell) of the right argument.

## Frame agreement

The frames of the left and right arguments must be identical, or one frame must be empty (scalar extension at the frame level).

## Reassembly

Result cells are assembled back into a single array with shape `frame_shape , max_cell_shape`. If result cells differ in shape, shorter ones are padded with fill elements (0 for numeric, space for character).

## Composing with reduce and scan

You can combine reduce or scan with rank:

```apl
      (+/⍤1) 3 3⍴⍳9
6 15 24
```

Row sums via `+/` applied to each 1-cell.

```apl
      (+/⍤¯1) 3 3⍴⍳9
6 15 24
```

Equivalent using complementary rank.

## First-axis reduce and scan

MARPLE does not implement `⌿` or `⍀`. Use the rank operator instead:

- `f⌿` becomes `(f/⍤¯1)`
- `f⍀` becomes `(f\⍤¯1)`

## See also

- [First-axis variants](first-axis.md)
- [Reduce](reduce.md) (`f/`)
- [Scan](scan.md) (`f\`)
