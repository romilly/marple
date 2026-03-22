# How to concatenate arrays

## Join two vectors

```apl
      1 2 3,4 5 6
1 2 3 4 5 6
```

## Append a scalar to a vector

```apl
      1 2 3,4
1 2 3 4
```

```apl
      0,1 2 3
0 1 2 3
```

## Ravel a matrix into a vector

Monadic `,` (ravel) flattens any array into a vector:

```apl
      ,2 3⍴⍳6
1 2 3 4 5 6
```

See also: [Reshape and ravel](reshape-and-ravel.md)
