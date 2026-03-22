# From (`⌷`)

## Syntax

```
i ⌷ Y
```

Selects major cells (first-axis slices) of `Y` at the indices given by `i`.

## Result shape

`(⍴i) , 1↓⍴Y`

When `i` is a scalar, the result has the shape of a single major cell (`1↓⍴Y`).

## Examples

Vector selection:

```apl
      2 ⌷ 10 20 30 40 50
20
      2 4 ⌷ 10 20 30 40 50
20 40
```

Matrix row selection:

```apl
      2 ⌷ 3 4⍴⍳12
5 6 7 8
      1 3 ⌷ 3 4⍴⍳12
1 2  3  4
9 10 11 12
```

## Index origin

Respects `⎕IO`. With `⎕IO←0`, the first major cell has index 0.

```apl
      ⎕IO←0
      0 ⌷ 10 20 30
10
```

## Errors

- **RANK ERROR** if `Y` is a scalar (scalars have no major cells).
- **INDEX ERROR** if any index is out of range.

## See also

- [Bracket Indexing](bracket-indexing.md) -- `V[i]`, `M[r;c]`
