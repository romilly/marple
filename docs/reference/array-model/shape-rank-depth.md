# Shape, Rank, and Depth

## Shape (`⍴`)

The shape of an array is a vector of non-negative integers giving the length along each axis. You get it with monadic `⍴`.

```apl
      ⍴ 42
⍝ (empty — scalar has no axes)
      ⍴ 1 2 3
3
      ⍴ 3 4⍴⍳12
3 4
```

## Rank

The rank is the number of axes -- the length of the shape vector. You get it with `≢⍴` or `⍴⍴`.

```apl
      ⍴⍴ 42
0
      ⍴⍴ 1 2 3
1
      ⍴⍴ 3 4⍴⍳12
2
```

| Array type | Rank | Example shape |
|-----------|------|---------------|
| Scalar | 0 | (empty) |
| Vector | 1 | `5` |
| Matrix | 2 | `3 4` |
| 3D array | 3 | `2 3 4` |

## Depth

MARPLE arrays are flat -- all elements are simple scalars (numbers or characters). There is no nesting. Depth is always 0 for a scalar or 1 for an array of scalars.

## Tally (`≢`)

Monadic `≢` returns the length of the first axis. For a scalar it returns 1.

```apl
      ≢ 1 2 3
3
      ≢ 3 4⍴⍳12
3
      ≢ 42
1
```

## See also

- [Empty Arrays](empty-arrays.md)
- [Fill Elements](fill-elements.md)
