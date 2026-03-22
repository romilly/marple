# MARPLE for J Users

If you know J, MARPLE will feel familiar — both languages descend from Iverson's *Dictionary of APL* and share the leading-axis philosophy. But MARPLE uses APL glyphs rather than ASCII spellings.

## What's the same (conceptually)

- **Rank operator** — J's `"` is MARPLE's `⍤`. Same semantics: cell decomposition, frame agreement, scalar extension at the frame level.
- **Leading-axis theory** — From (`⌷`) selects major cells, just as `{` does in J. Everything defaults to the first axis; rank generalises to any axis.
- **No nested arrays** — MARPLE is flat, like J's boxed-but-not-nested model (though MARPLE doesn't yet have boxing).
- **Direct definition** — MARPLE's dfns (`{⍺+⍵}`) correspond to J's explicit definitions. `⍵` is `y.`, `⍺` is `x.`.
- **Flat arrays with cells and frames** — the conceptual model is identical.

## Key differences

<!-- TODO: fill in with detailed comparison table covering:
     - Glyph differences (J ASCII vs MARPLE APL symbols)
     - Rank specification syntax (J "0 1 vs MARPLE ⍤0 1)
     - Valence detection (J uses separate mono/dyadic definition; MARPLE uses ⍺←default)
     - J's forks and hooks vs MARPLE's lack thereof
     - J's boxing ({) vs MARPLE's planned boxing
     - Tacit programming: J is heavily tacit; MARPLE is dfn-based
     - Inner/outer product notation differences
     - J's gerunds vs MARPLE's dops
-->

| J | MARPLE | Notes |
|---|--------|-------|
| `+/ y` | `+/ Y` | Reduce — same semantics |
| `x + y` | `X + Y` | Scalar functions — same |
| `i. 5` | `⍳ 5` | Iota — J is 0-origin by default |
| `5 3 $ i.15` | `5 3 ⍴ ⍳15` | Reshape |
| `f"1 y` | `(f⍤1) Y` | Rank operator |
| `{` | `⌷` | From / indexing |
| `3 : 'x+y'` | `{⍺+⍵}` | Explicit function definition |
| Fork: `(+/ % #)` | `{(+/⍵)÷⍴⍵}` | Tacit vs dfn |

<!-- TODO: expand with more examples and discussion of the philosophical similarities
     (both languages are "Dictionary APL" descendants) -->
