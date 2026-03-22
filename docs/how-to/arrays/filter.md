# How to filter (compress) an array

Use a boolean mask with compress (`/`) to select elements:

```apl
      V ← 3 1 4 1 5 9 2 6
      (V>3)/V
4 5 9 6
```

The comparison `V>3` produces the boolean vector `0 0 1 0 1 1 0 1`. Compress keeps elements where the mask is 1.

## Combine conditions

```apl
      V ← 3 1 4 1 5 9 2 6
      ((V>2)∧(V<6))/V
3 4 5
```

## Remove specific values

```apl
      V ← 3 1 4 1 5 9 2 6
      (V≠1)/V
3 4 5 9 2 6
```

See also: [Scalar functions and scalar extension](../../tutorials/beginners/scalar-functions.md)
