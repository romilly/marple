# MARPLE for GNU APL Users

GNU APL implements the ISO 13751 standard, which includes nested arrays. MARPLE is closer to the earlier ISO 8485 flat-array standard, extended with the rank operator and From indexing. If you use GNU APL, the scalar functions and basic structural operations will be very familiar.

## What's the same

- All scalar functions with standard APL glyphs
- Structural functions: `⍴`, `⍳`, `,`, `⌽`, `⊖`, `⍉`, `↑`, `↓`, `∈`, `⍋`, `⍒`
- Reduce, scan, outer product, inner product
- Bracket indexing `M[i;j]`
- System commands `)save`, `)load`, `)fns`, `)vars`

## Key differences

<!-- TODO: fill in with detailed comparison covering:
     - No nested arrays (no ⊂, ⊃, ≡, ¨)
     - No tradfns — dfns only (GNU APL primarily uses tradfns)
     - No control structures
     - Rank operator (not in GNU APL)
     - From indexing (not standard in GNU APL)
     - Namespaces and i-beams
     - Workspace format differences
-->

| GNU APL | MARPLE | Notes |
|---------|--------|-------|
| Nested arrays | Flat arrays only | No `⊂`, `⊃`, `≡`, `¨` |
| `∇ fn` tradfns | `fn ← {⍵}` dfns | No traditional definitions |
| `:If` / `:For` | Guards + recursion | No control structures |
| No rank operator | `⍤` (rank) | MARPLE's key extension |
| No From function | `⌷` (From) | Leading-axis indexing |
| `⎕FX` | Not available | Functions defined via dfn syntax only |
