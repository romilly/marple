# Glyph Input

MARPLE provides two methods for entering APL glyphs.

## Backtick sequences

In the REPL, press `` ` `` (backtick) followed by a key. The APL glyph appears immediately — no Enter needed.

Type ` `` ` `` ` (two backticks) for a literal backtick.

### Complete backtick table

| Key | Glyph | Name | Key | Glyph | Name |
|-----|-------|------|-----|-------|------|
| `` `r `` | `⍴` | Rho (shape/reshape) | `` `i `` | `⍳` | Iota |
| `` `e `` | `∈` | Epsilon (membership) | `` `t `` | `↑` | Take |
| `` `y `` | `↓` | Drop | `` `q `` | `⌽` | Reverse/rotate |
| `` `Q `` | `⍉` | Transpose | `` `g `` | `⍋` | Grade up |
| `` `G `` | `⍒` | Grade down | `` `- `` | `×` | Times |
| `` `= `` | `÷` | Divide | `` `< `` | `≤` | Less or equal |
| `` `> `` | `≥` | Greater or equal | `` `/ `` | `≠` | Not equal |
| `` `^ `` | `∧` | And | `` `v `` | `∨` | Or |
| `` `~ `` | `⍲` | Nand | `` `T `` | `⍱` | Nor |
| `` `* `` | `⍟` | Log | `` `o `` | `○` | Circle |
| `` `! `` | `⌈` | Ceiling | `` `d `` | `⌊` | Floor |
| `` `p `` | `⌈` | Ceiling (alt) | `` `b `` | `⌊` | Floor (alt) |
| `` `D `` | `⌹` | Domino (matrix) | `` `n `` | `⊤` | Encode |
| `` `N `` | `⊥` | Decode | `` `w `` | `⍵` | Omega (right arg) |
| `` `a `` | `⍺` | Alpha (left arg) | `` `V `` | `∇` | Del (self-ref) |
| `` `l `` | `←` | Assignment | `` `x `` | `⋄` | Diamond |
| `` `z `` | `⍎` | Execute | `` `Z `` | `⍕` | Format |
| `` `j `` | `∘` | Jot (compose) | `` `J `` | `⍤` | Rank |
| `` `I `` | `⌷` | From (squad) | `` `B `` | `⌶` | I-beam |
| `` `2 `` | `¯` | High minus | `` `c `` | `⍝` | Comment |
| `` `[ `` | `{` | Left brace | `` `] `` | `}` | Right brace |

### Example

To type `double←{⍵+⍵}`, you would type:

```
double`l`[`w+`w`]
```

## Keyboard layout

If you have a Dyalog APL keyboard layout installed (e.g. via `setxkbmap` with `grp:win_switch`), you can use the Win key to type APL glyphs directly. The REPL handles both methods — use whichever you prefer.
