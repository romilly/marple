# MARPLE for Dyalog Users

If you know Dyalog APL, you already know most of MARPLE. This page highlights the differences.

## What's the same

Most of what you type daily works identically:

- All scalar functions with the same glyphs and semantics
- `⍴`, `⍳`, `,`, `⌽`, `⊖`, `⍉`, `↑`, `↓`, `∈`, `⍋`, `⍒` — same behaviour
- Reduce `/`, scan `\`, first-axis `⌿` `⍀`
- Outer product `∘.f`, inner product `f.g`
- Bracket indexing `M[i;j]` (including indexed assignment)
- Dfn syntax `{⍺ + ⍵}` with guards, recursion (`∇`), default `⍺`
- Dop syntax `{⍺⍺/⍵}` with `⍺⍺` and `⍵⍵`
- System commands `)save`, `)load`, `)fns`, `)vars`, `)off`

## What's different

### No nested arrays

This is the big one. MARPLE arrays are flat — every element is a scalar (number or character). There is no `⊂` (enclose), no `⊃` (disclose/first), no `≡` (depth), no `¨` (each), no `⍤` as "atop", and no arrays of arrays.

If MARPLE eventually adds arrays-of-arrays, it will follow Iverson's Dictionary boxing model (explicit `<` and `>`), not APL2's implicit nesting. This is the model used by J.

### No tradfns or tradops

There are no `∇`-header function definitions, no line numbers, no labels, no `→` (branch), no Del editor. Dfns and dops are the only way to define functions and operators.

### No control structures

No `:If`, `:For`, `:While`, `:Select`. Use guards in dfns and recursion instead.

### Bracket-axis is deprecated

Instead of `+/[1]M`, use `(+/⍤¯1)M` or `+⌿M`. The rank operator replaces bracket-axis for user-defined functions, which bracket-axis can't handle.

### Index origin defaults to 1

Same as Dyalog's default, but worth noting. `⎕IO` is supported.

## What's new

### Rank operator (`⍤`)

MARPLE includes the rank operator, which Dyalog also has (since version 14.0). If you already use it in Dyalog, it works identically. If you've been avoiding it, now's a good time to learn — see the [rank operator tutorial](../intermediate/rank-operator.md).

### From function (`⌷`)

Dyalog has `⌷` (squad indexing), and MARPLE's From works similarly for simple leading-axis selection. The difference: in MARPLE, `⌷` is the *preferred* indexing mechanism, designed to compose with rank. See [Indexing with From](../intermediate/from-indexing.md).

### Namespaces via directories

Instead of Dyalog's `⎕NS` objects, MARPLE maps namespaces to subdirectories in the workspace. `utils:trim` calls the `trim` function in the `utils/` subdirectory. The system workspace `$:` provides the standard library.

### I-beam as Python FFI

`⌶` in MARPLE is an operator that calls Python functions, not a system service dispatcher. `(⌶'module.function') Y` calls Python code from APL.

## Quick equivalence table

| Dyalog | MARPLE | Notes |
|--------|--------|-------|
| `+/[1]M` | `(+/⍤¯1)M` or `+⌿M` | Rank replaces bracket-axis |
| `f¨ V` | `f⍤0 ⊢ V` | Rank-0 replaces Each for flat arrays |
| `⊂ X` | (not available) | No enclosure; boxing planned |
| `⊃ X` | (not available) | No disclosure |
| `X ≡ Y` | (not available) | No depth; flat arrays only |
| `:If` / `:For` | Guards + recursion | No control structures |
| `∇ fn` header | `fn ← {⍵}` | Dfns only |
| `⎕NS` | Directory namespaces | `utils:fn` syntax |
| `85⌶` | `(⌶'mod.fn')` | I-beam is a Python FFI operator |

<!-- TODO: Romilly — review this table for accuracy and add any missing equivalences
     that Dyalog users commonly ask about -->
