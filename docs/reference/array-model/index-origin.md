# Index Origin (`⎕IO`)

`⎕IO` controls whether indexing starts at 0 or 1. MARPLE defaults to `⎕IO←1`.

## Setting index origin

```apl
      ⎕IO←1
      ⍳5
1 2 3 4 5
      ⎕IO←0
      ⍳5
0 1 2 3 4
```

## Affected functions

`⎕IO` affects all index-producing and index-consuming operations:

| Function | Effect |
|----------|--------|
| `⍳` (iota) | Generated indices start at `⎕IO` |
| `⌷` (from) | Index values interpreted relative to `⎕IO` |
| `V[i]` (bracket indexing) | Index values interpreted relative to `⎕IO` |
| `⍋` (grade up) | Returned indices start at `⎕IO` |
| `⍒` (grade down) | Returned indices start at `⎕IO` |
| `⍳` (index-of, dyadic) | Returned indices start at `⎕IO`; not-found value is `(≢⍺)+⎕IO` |

## Permitted values

Only 0 and 1 are meaningful values for `⎕IO`.
