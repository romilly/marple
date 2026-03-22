# Bracket Indexing

## Syntax

```
V[i]            ⍝ select from vector
M[r;c]          ⍝ select from matrix
M[r;]           ⍝ all columns of selected rows
M[;c]           ⍝ all rows of selected columns
```

Semicolons separate axis specifications. An empty axis (nothing before or after a semicolon) selects all indices along that axis.

## Vector indexing

```apl
      V ← 10 20 30 40 50
      V[3]
30
      V[2 4]
20 40
```

## Matrix indexing

```apl
      M ← 3 4⍴⍳12
      M[2;3]
7
      M[1;]
1 2 3 4
      M[;2]
2 6 10
      M[1 3;2 4]
 2  4
10 12
```

## Result shape

- Scalar index on each axis: scalar result.
- Vector index on one axis, scalar on others: vector result.
- Vector indices on both axes: matrix result (cross-section).

## Index origin

Bracket indexing respects `⎕IO`.

```apl
      ⎕IO←0
      V ← 10 20 30
      V[0]
10
```

## Limitations

Bracket indexing is special syntax, not a function. You cannot pass it to operators or compose it. For composable indexing, use [From](from.md) (`⌷`).

Currently supports vectors and matrices (up to rank 2). Higher-rank arrays raise RANK ERROR.

## See also

- [From](from.md) (`⌷`) -- function-based major-cell selection
- [Indexed Assignment](indexed-assignment.md) -- not yet implemented
