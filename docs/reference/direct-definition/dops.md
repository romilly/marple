# Dops (Direct Operators)

## Status

Direct operators are **not yet implemented** in MARPLE.

## Planned syntax

```apl
      name ← {body containing ⍺⍺ and/or ⍵⍵}
```

A dfn is detected as an operator by the presence of `⍺⍺` (left operand) or `⍵⍵` (right operand).

- **Monadic operator**: contains `⍺⍺` but not `⍵⍵`. Takes one operand.
- **Dyadic operator**: contains both `⍺⍺` and `⍵⍵`. Takes two operands.

The derived function uses `⍺` and `⍵` for its arguments as usual.

## Workaround

You can pass functions as arguments to dfns by assigning them to names and referencing those names inside the body.

## See also

- [Dfns](dfns.md) -- dfn basics
