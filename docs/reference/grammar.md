# Grammar

This page documents the grammar implemented by MARPLE's parser (`src/marple/parser.py`).

## Evaluation order

APL evaluates **right to left**. Every function takes everything to its right as its right argument. There is no operator precedence among functions.

```apl
      2×3+4
14
```

This is `2×(3+4)`, not `(2×3)+4`.

## Binding hierarchy (tightest first)

1. **Bracket indexing** -- `M[i;j]`
2. **Operator binding** -- `+/`, `⌽⍤1`, `∘.×`, `f.g`
3. **Strand formation** -- `1 2 3` (adjacent numbers form a vector)
4. **Function application** -- `f Y` (monadic) or `X f Y` (dyadic)
5. **Assignment** -- `name ← value`

## Valence

A function is **dyadic** if a value appears to its left; otherwise it is **monadic**. The parser determines valence from context: if the token immediately left of a function glyph is a value (number, variable, or closing paren/bracket), the function is dyadic.

## Tokens

| Token type | Examples |
|-----------|---------|
| Number | `42`, `3.14`, `¯5`, `1e3` |
| String | `'hello'`, `'it''s'` |
| Function glyph | `+ - × ÷ ⌈ ⌊ * ⍟ \| < ≤ = ≥ > ≠ ∧ ∨ ~ ⍴ ⍳ , ↑ ↓ ⌽ ⍉ ⍋ ⍒ ⊤ ⊥ ⍎ ⍕ ⌹ ○ ⌷ ≡ ≢ ∈` |
| Operator | `/ ⌿ \ ⍀ . ∘ ⍤ ⌶` |
| Identifier | `x`, `myFunc`, `total` |
| Qualified name | `$::str::upper`, `ns::func` |
| System variable | `⎕IO`, `⎕CT`, `⎕PP`, `⎕FR` |
| System function | `⎕NREAD`, `⎕NWRITE`, `⎕DR`, `⎕EA` |
| Dfn delimiters | `{ }` |
| Dfn special names | `⍵` `⍺` `∇` |
| Guard | `:` (inside dfns) |
| Diamond | `⋄` (statement separator) |
| Assignment | `←` |
| Brackets | `[ ] ;` (indexing) |
| Parentheses | `( )` (grouping) |

## Statements

Multiple expressions on one line are separated by `⋄` (diamond). Each statement is parsed independently.

```apl
      a←3 ⋄ b←4 ⋄ a+b
7
```

## Assignment

```
name ← expression
⎕SYSVAR ← expression
```

Assigns the result of `expression` to `name` or a system variable. The assigned value is the result (but the REPL suppresses display for bare assignments).

## Dfn syntax

```
{ statement (⋄ statement)* }
```

Inside a dfn:

- `⍵` -- right argument
- `⍺` -- left argument
- `∇` -- self-reference (recursion)
- `⍺←expr` -- default left argument
- `condition : expr` -- guard

## Derived functions

| Syntax | Meaning |
|--------|---------|
| `f/ Y` | Reduce `Y` with `f` |
| `f\ Y` | Scan `Y` with `f` |
| `X ∘.f Y` | Outer product |
| `X f.g Y` | Inner product |
| `(f⍤k) Y` | Rank operator (monadic) |
| `X (f⍤k) Y` | Rank operator (dyadic) |
| `(⌶'path') Y` | I-beam (monadic) |
| `X (⌶'path') Y` | I-beam (dyadic) |

## Operator-function composition

Reduce and scan can be composed with rank:

```
(f/⍤k) Y
(f\⍤k) Y
```

## Bracket indexing

```
array[index]
array[row;col]
array[;col]
array[row;]
```

Bracket indexing binds tighter than function application. Empty indices select all elements along that axis.

## Dyadic use of `/` and `\`

When `/` or `\` appears between two values (not after a function glyph), they act as dyadic functions:

- `X / Y` -- replicate/compress
- `X \ Y` -- expand

## Parentheses

Parentheses override the default right-to-left evaluation:

```apl
      (2+3)×4
20
```
