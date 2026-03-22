# Scan (`f\`)

## Syntax

```
f\ Y
```

`f` is a dyadic scalar function. `Y` is the argument array.

## Description

Like reduce, but keeps all intermediate results. Element `i` of the result is `f/` applied to the first `i+1` elements. The result has the same shape as the input.

Scan is left-to-right: for `+\ a b c d`, the result is `a`, `a+b`, `(a+b)+c`, `((a+b)+c)+d`.

## Examples

```apl
      +\ 1 2 3 4 5
1 3 6 10 15
      ×\ 1 2 3 4 5
1 2 6 24 120
      ⌈\ 3 1 4 1 5
3 3 4 4 5
```

## Higher-rank arrays

On matrices, scan works along the **last axis**. The result has the same shape as the input.

```apl
      +\ 3 3⍴⍳9
1 3  6
4 9 15
7 16 27
```

## Empty arrays

Scanning an empty array returns an empty array.

## See also

- [Reduce](reduce.md) (`f/`) -- full reduction
- [First-axis variants](first-axis.md) -- use `(f\⍤¯1)` for first-axis scan
