# MARPLE Language Extension: Indexing

## From (`⌷`), leading-axis selection, and the future of bracket indexing

*This document specifies MARPLE's approach to array indexing: a new From function for leading-axis selection that composes with the Rank operator, retained bracket indexing for multi-axis cross-sections, and a roadmap for full functional indexing when boxing arrives.*

---

## 1. The problem with bracket indexing

Bracket indexing `M[i;j]` has been in APL since APL\360. It works, everyone knows it, and for simple cases it's fine. But it has well-known deficiencies that Iverson, Whitney, and the SHARP APL team identified in the early 1980s:

**It's not a function.** Bracket indexing is special syntax — it doesn't participate in normal right-to-left evaluation, can't be passed as an operand to operators, can't be used in direct definitions as a first-class value, and can't be composed. You can't write `⌷/` to reduce by indexing, or `⌷⍤1` to index at a specific rank.

**Each axis must be specified.** To select from a matrix, you write `M[rows;cols]`. To select from a rank-3 array, `A[planes;rows;cols]`. The number of semicolons is tied to the rank. A function that should work on arrays of any rank must know the rank in advance or use `⍎` (execute) to build the indexing expression as a string.

**It conflicts with other bracket uses.** Square brackets are also used for bracket-axis notation `f[k]` and, in MARPLE, for array notation `[⋄]`. This overloading is manageable but inelegant.

**Indexed assignment is ad-hoc.** `M[i;j] ← value` is another piece of special syntax, not derivable from the indexing function.

The Dictionary of APL and SHARP APL addressed these problems through two mechanisms: a proper indexing function (From), and the Rank operator to extend it to arbitrary axes. J carried this further, making From (`{`) the sole indexing mechanism and eliminating bracket indexing entirely.

---

## 2. Leading-axis theory in brief

The key insight behind the Dictionary's approach to indexing is **leading-axis theory**: all operations should, by default, apply to the *first* axis (the leading axis). The Rank operator then generalises to any axis.

In a matrix with shape `3 4`:
- The **major cells** are the 3 rows (the items along the first axis)
- Each major cell is a vector of length 4

In a rank-3 array with shape `2 3 4`:
- The major cells are the 2 matrices (each of shape `3 4`)
- The 1-cells are the 6 rows (vectors of length 4)

**From selects major cells.** Everything else follows from combining From with Rank.

---

## 3. Specification: From (`⌷`)

### 3.1 Glyph and syntax

The glyph is `⌷` (quad-jot, Unicode U+2337), called **From** or **Squad** (squished quad). In ASCII fallback, MARPLE accepts `#:` as an alternative.

```
i ⌷ Y        ⍝ select major cells i from array Y
```

From is a **dyadic function** with no monadic definition in MARPLE (Dyalog uses monadic `⌷` for Materialise, which we don't need).

### 3.2 Dyadic From: `i ⌷ Y`

The left argument `i` is a simple integer scalar or vector of indices. The right argument `Y` is any array. From selects **major cells** of `Y` — the sub-arrays along the first axis.

**Result shape:** `(⍴i) , 1↓⍴Y`

That is: the shape of the index expression, followed by the shape of a single major cell.

**Examples with vectors:**

```apl
V ← 10 20 30 40 50

3 ⌷ V              ⍝ → 30        (scalar: one element from vector)
1 3 5 ⌷ V          ⍝ → 10 30 50  (vector: three elements)
3 3 1 ⌷ V          ⍝ → 30 30 10  (repeats allowed)
(2 3⍴1 2 3 4 5 1) ⌷ V
                    ⍝ → 2 3⍴10 20 30 40 50 10  (matrix of selections)
```

**Examples with matrices:**

```apl
M ← 3 4⍴⍳12
⍝  1  2  3  4
⍝  5  6  7  8
⍝  9 10 11 12

2 ⌷ M              ⍝ → 5 6 7 8      (row 2: a vector)
1 3 ⌷ M            ⍝ → 2 4⍴1 2 3 4 9 10 11 12  (rows 1 and 3: a matrix)
```

**Examples with rank-3 arrays:**

```apl
A ← 2 3 4⍴⍳24

1 ⌷ A              ⍝ → 3 4 matrix (the first "plane")
2 ⌷ A              ⍝ → 3 4 matrix (the second "plane")
```

### 3.3 Index origin

From respects `⎕IO`. With `⎕IO←1` (MARPLE's default), the first major cell is at index 1. With `⎕IO←0`, it's at index 0. Out-of-range indices produce an INDEX ERROR.

### 3.4 Empty selections

An empty index vector selects zero major cells:

```apl
⍬ ⌷ M              ⍝ → 0 4⍴0  (empty matrix with 4 columns)
```

The result shape is `0 , 1↓⍴Y` — zero rows, preserving the trailing shape. This is consistent with first-gen APL's handling of empty arrays.

---

## 4. From + Rank: replacing bracket indexing

The power of From becomes apparent when combined with the Rank operator. Since From selects along the leading axis, and Rank controls which cells the function sees, the combination addresses any axis.

### 4.1 Column selection

To select columns from a matrix (the *second* axis), apply From at rank 1 — i.e., apply From to each row independently:

```apl
M ← 3 4⍴⍳12
⍝  1  2  3  4
⍝  5  6  7  8
⍝  9 10 11 12

2 (⌷⍤0 1) M        ⍝ → 2 6 10   (column 2)
```

Here `⌷⍤0 1` means: left argument at rank 0 (each index is a scalar), right argument at rank 1 (each row is a 1-cell). The scalar 2 is paired with each row, selecting the 2nd element from each.

For multiple columns:

```apl
1 3 (⌷⍤1) M        ⍝ → 3 2⍴1 3 5 7 9 11  (columns 1 and 3)
```

Wait — this needs care. `⌷⍤1` with a vector left argument applies the vector index `1 3` to each row, selecting elements 1 and 3 from each row. The left frame is empty (single cell), the right frame is `3`. Scalar extension at the frame level pairs the single index vector with each row. Result: 3 rows of 2 elements = `3 2` matrix. This is exactly `M[;1 3]`.

### 4.2 Equivalence table

| Bracket syntax | From + Rank | Meaning |
|---------------|-------------|---------|
| `V[i]` | `i ⌷ V` | Select from vector |
| `M[i;]` | `i ⌷ M` | Select rows from matrix |
| `M[;j]` | `j (⌷⍤1) M` | Select columns from matrix |
| `M[i;j]` | `j (⌷⍤1) i ⌷ M` | Select rows then columns |
| `A[i;;]` | `i ⌷ A` | Select planes from 3D array |
| `A[;j;]` | `j (⌷⍤1 2) A` | Select rows within each plane |
| `A[;;k]` | `k (⌷⍤0 1) A` or `k (⌷⍤1) A` | Select columns within each row |

### 4.3 Rectangular cross-sections

The one case where bracket indexing is more concise is the **rectangular cross-section**: `M[1 3; 2 4]` selects a 2×2 submatrix in one expression. With From + Rank, this becomes two steps:

```apl
2 4 (⌷⍤1) 1 3 ⌷ M
```

First select rows 1 and 3 (yielding a 2×4 matrix), then select columns 2 and 4 from each row (yielding a 2×2 matrix). This is two operations, but they compose naturally in right-to-left evaluation and the intermediate result is a well-defined array.

For the common case of selecting a single element from a matrix, From at rank 0 works:

```apl
⍝ M[2;3] — element at row 2, column 3
3 ⌷ 2 ⌷ M          ⍝ → 7
```

### 4.4 Comparison: what we gain, what we lose

**Gains:**
- From is a proper function — it composes with operators, works in dfns, and participates in right-to-left evaluation
- Rank-parametric code: a function can index into arrays of any rank without knowing the rank in advance
- From + Rank can express patterns that bracket indexing cannot, such as selecting different indices from different major cells (via dyadic rank pairing)
- Indexed replacement via the Merge adverb (future extension) will compose naturally

**Losses:**
- Multi-axis rectangular cross-sections require two operations instead of one
- Bracket indexing is more immediately readable for APL programmers accustomed to `M[i;j]`
- Until boxing arrives, there's no single-expression equivalent of `M[i;j]` for arbitrary `i` and `j`

---

## 5. MARPLE's pragmatic decision: both

MARPLE retains bracket indexing **and** adds From. This is not indecisiveness — it's the right call for a language that starts with flat arrays and plans to add boxing later.

### 5.1 What MARPLE implements now

**From (`⌷`):** dyadic function, selects major cells, composes with Rank. This is the preferred style for new code and is required for rank-parametric programming.

**Bracket indexing (`M[i;j]`):** retained from first-gen APL for multi-axis rectangular selection and indexed assignment. This remains special syntax, not a function.

**Bracket-axis notation (`f[k]`):** deprecated in favour of Rank. MARPLE may support it for backward compatibility but new code should use `f⍤k`.

### 5.2 When boxing arrives (future)

Once MARPLE adds the Dictionary's boxed-array model, From can be extended to handle multi-axis selection in a single call, by accepting a boxed left argument where each box specifies indices for one axis:

```apl
⍝ Future syntax (requires boxing):
(⊂1 3)(⊂2 4) ⌷ M      ⍝ → rows 1,3 × columns 2,4 = 2×2 submatrix
```

At that point, bracket indexing becomes entirely redundant and can be relegated to sugar or deprecated. Indexed assignment can be handled via Merge (`}`) or the At operator (`@`).

### 5.3 Indexed assignment

For now, MARPLE retains bracket-indexed assignment:

```apl
M[2;3] ← 99        ⍝ replace element at row 2, column 3
M[1;] ← 0          ⍝ zero out row 1
```

A functional alternative using At (`@`) is planned for a future extension:

```apl
99 (⊢@(2 3)) M     ⍝ future: replace element at index 2,3
```

---

## 6. Formal specification

### 6.1 From: `i ⌷ Y`

**Domain:** `i` is a simple integer array. `Y` is any array.

**Result:** An array whose major cells are the major cells of `Y` selected by the scalar elements of `i` (in ravel order).

**Shape:** `(⍴i) , 1↓⍴Y`

**Rank:** From has inherent function rank `∞ ∞` (operates on entire arguments). When used with the Rank operator, cell decomposition happens before From is applied.

**Errors:**
- INDEX ERROR if any element of `i` is outside the range `⎕IO` to `(⎕IO + (⊃⍴Y) - 1)`
- RANK ERROR if `Y` is a scalar (scalars have no major cells)

### 6.2 Grammar addition

From is added as a primitive dyadic function:

```ebnf
(* Addition to MARPLE primitive functions *)
function := ... | '⌷' | ... ;
```

No new parsing rules are needed — `⌷` is an ordinary dyadic function.

---

## 7. Complete example session

```apl
⎕IO ← 1

⍝ ── Vector indexing ──
V ← 'ABCDEFGH'
3 ⌷ V                       ⍝ → 'C'
1 3 5 7 ⌷ V                 ⍝ → 'ACEG'

⍝ ── Row selection from matrix ──
M ← 4 5⍴⍳20
⍝  1  2  3  4  5
⍝  6  7  8  9 10
⍝ 11 12 13 14 15
⍝ 16 17 18 19 20

2 ⌷ M                       ⍝ → 6 7 8 9 10  (row 2)
2 4 ⌷ M                     ⍝ → 2 5⍴6 7 8 9 10 16 17 18 19 20

⍝ ── Column selection via Rank ──
3 (⌷⍤0 1) M                 ⍝ → 3 8 13 18  (column 3)
2 4 (⌷⍤1) M                 ⍝ → 4 2⍴2 4 7 9 12 14 17 19  (columns 2,4)

⍝ ── Rectangular cross-section ──
2 4 (⌷⍤1) 1 3 ⌷ M           ⍝ → 2 2⍴2 4 12 14  (rows 1,3 × cols 2,4)
⍝ Compare: M[1 3; 2 4]      ⍝ same result

⍝ ── Rank-3 array ──
A ← 2 3 4⍴⍳24

1 ⌷ A                       ⍝ → first 3×4 matrix
2 (⌷⍤1 2) A                 ⍝ → row 2 from each matrix: 2 4 matrix
3 (⌷⍤0 1) A                 ⍝ → column 3 from each row: 2 3 matrix

⍝ ── From in a dfn ──
firstAndLast ← {(1,(⊃⍴⍵)) ⌷ ⍵}
firstAndLast M               ⍝ → 2 5⍴1 2 3 4 5 16 17 18 19 20

⍝ ── From as operand (composable!) ──
⍝ Select row 2 from each matrix in a 3D array:
(2∘⌷⍤2) A                   ⍝ → 2 4 matrix (row 2 from each plane)

⍝ ── Where bracket indexing remains convenient ──
M[2;3]                       ⍝ → 8  (single element)
M[2 4; 1 3 5]               ⍝ → 2 3⍴6 8 10 16 18 20 (cross-section)
```

---

## 8. Comparison with J and Dyalog

| Feature | J | Dyalog APL | MARPLE |
|---------|---|-----------|--------|
| Indexing function | `{` (From) | `⌷` (Squad) | `⌷` (From) |
| Bracket indexing | Not supported | Supported | Supported (retained) |
| Leading-axis select | `i { Y` | `i⌷Y` (short left arg) | `i ⌷ Y` |
| Multi-axis select | Boxed left arg to `{` | `⌷[k]` axis or nested left | Two-step via Rank |
| Indexed assignment | `x i} Y` (Amend) | `Y[i] ← x` | `Y[i] ← x` (bracket) |
| Rank interaction | `{"k` | `⌷⍤k` | `⌷⍤k` |
| Requires boxing | Yes (for multi-axis) | Yes (for Choose indexing) | No (uses Rank instead) |

J defines all one-dimensional functions to work on the first axis, unifying APL's pairs of first- and last-axis functions. J also extends Rotate so that it can work on multiple leading axes rather than a single axis. MARPLE follows this principle for From but, lacking boxing, cannot yet achieve J's single-expression multi-axis selection.

---

## 9. Implementation notes

The MARPLE interpreter is Python, using NumPy when available and falling back to pure Python otherwise.

**With NumPy**: `i ⌷ Y` maps directly to NumPy fancy indexing along axis 0: `Y[i - ⎕IO]` (adjusting for index origin, since NumPy is always 0-origin). For scalar `i`, this returns a view (no copy). For vector `i`, NumPy's advanced indexing handles the gather efficiently.

**Pure Python fallback**: given the flat data buffer and shape, compute the offset of each major cell (`index × product(1↓shape)`), slice the data list accordingly. Straightforward and allocation-light.

**Performance**: From is very cache-friendly for row selection (major cells are contiguous in row-major storage). Column selection via `⌷⍤1` is less cache-friendly (strided access), but no worse than bracket indexing `M[;j]` — the data layout is the same either way. On constrained platforms (CircuitPython with ulab), the NumPy path via ulab should handle From efficiently since ulab supports basic array indexing along axis 0.

---

## 10. References

- Ken Iverson. *A Dictionary of APL*. APL Quote Quad 18(1), September 1987. Section on indexing and the From verb.
- Ken Iverson. *Rationalized APL*. IPSA, 1983. Introduction of leading-axis approach.
- Arthur Whitney. Rank operator and leading-axis theory, 1982.
- J. A. Gerth and D. L. Orth. "Indexing and Merging in APL." APL Quote Quad, 1987.
- APL Wiki — Bracket indexing: https://aplwiki.com/wiki/Bracket_indexing
- APL Wiki — Index (function): https://aplwiki.com/wiki/Index_(function)
- APL Wiki — Indexing: https://aplwiki.com/wiki/Indexing
- APL Wiki — Leading axis theory: https://aplwiki.com/wiki/Leading_axis_theory
- Dyalog APL — Squad indexing: https://docs.dyalog.com/20.0/language-reference-guide/primitive-functions/index-function/
- J Wiki — Essays/Rank: https://code.jsoftware.com/wiki/Essays/Rank
- J Software — Indexing phrases: https://www.jsoftware.com/help/phrases/indexing.htm
- Stefan Kruger. "Indexing" (Learning APL): https://xpqz.github.io/learnapl/indexing.html
