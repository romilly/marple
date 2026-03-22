# How to apply a function to each column

## Select a column with From

Use `⌷` (From) with rank `0 1` to select a column by index:

```apl
      M ← 3 4⍴⍳12
      2(⌷⍤0 1)M
2 6 10
```

This selects column 2 from each row (1-cell) of M.

## Transpose, operate, transpose back

For arbitrary functions, transpose the matrix, operate on rows, then transpose back:

```apl
      ⍉(⌽⍤1)⍉M
 9 10 11 12
 5  6  7  8
 1  2  3  4
```

See also: [Apply to rows](apply-to-rows.md), [Replace bracket-axis](replace-bracket-axis.md)
