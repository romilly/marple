# How to apply a function to each matrix in a 3D array

Use rank 2 to treat each matrix (2-cell) of a rank-3 array as an independent operand:

```apl
      A ← 2 3 4⍴⍳24
      (⌽⍤2) A
```

This reverses the rows within each of the two matrices.

```apl
      (+/⍤2) A
```

This sums each row of each matrix, reducing the last axis.

```apl
      (⍉⍤2) A
```

This transposes each matrix independently.

The frame shape is `2` (the leading axis) and the cell shape is `3 4` (each matrix).

See also: [Apply to rows](apply-to-rows.md), [Leading-axis theory](../../explanation/leading-axis.md)
