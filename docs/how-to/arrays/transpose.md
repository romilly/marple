# How to transpose a matrix

Monadic `⍉` swaps rows and columns:

```apl
      M ← 3 4⍴⍳12
      ⍉M
1 5  9
2 6 10
3 7 11
4 8 12
```

The shape changes from `3 4` to `4 3`:

```apl
      ⍴⍉M
4 3
```

Transposing a vector returns it unchanged:

```apl
      ⍉ 1 2 3
1 2 3
```

## Transpose each matrix in a 3D array

Use the rank operator to transpose at rank 2:

```apl
      (⍉⍤2) 2 3 4⍴⍳24
```

See also: [Apply a function to matrices](../rank-operator/apply-to-matrices.md)
