# How to pair cells from two arrays

Dyadic rank specifies separate cell ranks for the left and right arguments:

## Add a different scalar to each row

```apl
      100 200 300 (+⍤0 1) 3 4⍴⍳12
101 102 103 104
205 206 207 208
309 310 311 312
```

The left argument has rank-0 cells (scalars), the right has rank-1 cells (rows). The frames both have shape `3`, so they pair up: `100` with row 1, `200` with row 2, `300` with row 3.

## Add a vector to each row

```apl
      10 20 30 40 (+⍤1) 3 4⍴⍳12
11 22 33 44
15 26 37 48
19 30 41 52
```

Both sides use rank-1 cells. The left has an empty frame (one cell), so it pairs with every right cell (scalar extension at the frame level).

## Frame agreement

Frames must either match or one must be empty (scalar-extended). A mismatch gives a LENGTH ERROR.

See also: [Leading-axis theory](../../explanation/leading-axis.md)
