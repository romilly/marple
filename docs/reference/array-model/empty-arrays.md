# Empty Arrays

An empty array has at least one axis of length 0.

## Creating empty arrays

```apl
      ⍴ ⍳0
0
      ⍴ 0⍴0
0
      ⍴ 0 4⍴0
0 4
```

`⍳0` produces an empty numeric vector. `0⍴0` reshapes to length 0. `0 4⍴0` creates an empty matrix with 4 columns.

## Character vs numeric

Empty character and numeric vectors are distinct by element type but both have shape `0`.

```apl
      ⍴ ''
0
      ⍴ ⍳0
0
```

## Behaviour with functions

Most scalar functions apply element-wise and produce empty results from empty inputs. Reduce (`f/`) on an empty array raises DOMAIN ERROR. Scan (`f\`) on an empty array returns an empty array.
