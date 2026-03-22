# MARPLE Language Extension: The Rank Operator

## Adding `⍤` to first-generation flat APL

*This document specifies the rank operator for MARPLE. It is a separate extension to the core first-generation APL primitives, added because rank is orthogonal, general, and — crucially — was designed for flat arrays before nested arrays complicated matters.*

---

## 1. Historical context and rationale

The rank operator was invented by Arthur Whitney in 1982 while he and Ken Iverson were building an APL model at I.P. Sharp Associates. It was first implemented in SHARP APL in 1983, a full year before IBM released APL2 with nested arrays. It appeared in Iverson's "Rationalized APL" (1983) and was formalized in "A Dictionary of APL" (1987), where it became a cornerstone of the leading-axis approach that later defined J.

Robert Bernecky's 1988 paper described rank as "a microcosm of APL history" — a progression from scalar extension (APL\360, 1966) through leading-axis theory to a single construct that generalizes scalar extension, inner product, outer product, LISP's maplist, functional programming's map, and NumPy's broadcasting.

**Why add it to MARPLE**: rank replaces the ad-hoc bracket-axis mechanism (`f[k]`) that first-generation APL used to control which axis a function operates along. Bracket-axis is specified differently for each primitive and cannot be applied to user-defined functions. Rank provides a single, uniform, composable mechanism that works with *any* function — primitive or user-defined. It is the single most important operator missing from first-generation APL.

**Why it fits flat arrays**: rank decomposes arrays into cells and reassembles results. With flat arrays, the only constraint is that results must form a regular (rectangular) array. This is naturally satisfied by the vast majority of use cases and gracefully handled by padding in the remainder. No nesting, no enclosing, no depth — just cells in, cells out.

---

## 2. Concepts: cells and frames

Understanding rank requires two concepts that are implicit in first-generation APL but were not named until the leading-axis work of the 1980s.

### 2.1 k-cells

Given an array of rank `r`, a **k-cell** is a subarray formed by the last `k` axes. The leading `r-k` axes form the **frame** that organizes the cells.

For a matrix `M` with shape `3 4` (rank 2):

```
0-cells: individual elements (scalars)      — there are 12, frame is 3 4
1-cells: rows (vectors of length 4)         — there are 3,  frame is 3
2-cells: the entire matrix                  — there is 1,   frame is ⍬ (empty)
```

For a rank-3 array `A` with shape `2 3 4`:

```
0-cells: scalars                            — 24 of them, frame 2 3 4
1-cells: vectors of length 4                — 6 of them,  frame 2 3
2-cells: 3×4 matrices                       — 2 of them,  frame 2
3-cells: the whole array                    — 1 of it,    frame ⍬
```

**Negative rank** specifies cells relative to the array's rank. For an array of rank `r`, a cell specification of `¯1` means `(r-1)`-cells, i.e. "everything except the first axis" — or equivalently, the major cells. `¯2` means `(r-2)`-cells, and so on. This is called **complementary rank**: you're specifying how many leading axes to exclude rather than how many trailing axes to include.

### 2.2 The frame–cell decomposition

Every application of rank decomposes an argument into:

```
argument shape = frame , cell-shape
                 ─────   ──────────
                 leading  trailing k axes
                 r-k axes
```

The rank operator iterates over cells according to the frame, applies the function to each cell, and reassembles the results.

---

## 3. Specification

### 3.1 Syntax

```
f ⍤ B        ⍝ derived function: f applied at rank B
```

`⍤` is a **dyadic operator**. Its left operand `f` is a function (primitive, named, or dfn). Its right operand `B` is a numeric array specifying cell ranks.

The glyph `⍤` (jot-diaeresis, Unicode U+2364) is used. In ASCII fallback mode, MARPLE accepts `@:` as an alternative spelling.

### 3.2 Right operand: rank specification

`B` is a simple integer scalar or vector of 1, 2, or 3 elements:

| Form | Meaning | Extension |
|------|---------|-----------|
| `⍤ c` | Single value | Extended to `c c c` |
| `⍤ b c` | Two values | Extended to `c b c` |
| `⍤ a b c` | Three values | Used as-is |

Where:
- `a` = cell rank for the monadic case
- `b` = cell rank for the left argument (dyadic case)
- `c` = cell rank for the right argument (dyadic case)

**Note the extension rule for 2 elements**: `b c` becomes `c b c`. This means the first element in a 2-vector specifies the *left* argument rank and the second specifies the *right* argument rank. The monadic cell rank is taken from the right-argument rank. This follows SHARP APL, the Dictionary, Dyalog, and J conventions.

Each rank value `k`:
- If `k ≥ 0`: use the last `k` axes of the argument (k-cells)
- If `k < 0`: use the last `(r + k)` axes, where `r` is the argument's rank (complementary rank)
- If `k ≥ r` (or `k + r ≤ 0` for negative): use the entire argument (the function sees the whole array)

Rank values are clamped to `[0, r]` after resolving negatives, where `r` is the actual rank of the argument. There is no error for out-of-range values; they simply saturate.

### 3.3 Monadic case: `(f⍤k) Y`

Given monadic function `f`, right operand resolving to cell rank `a` for the monadic case, and argument `Y` of shape `s`:

1. **Decompose**: Let `a' = min(a, ⍴⍴Y)` (clamp to argument rank). The cell shape is `(a'↑⊖s)` — the last `a'` elements of `s`. The frame is `((-a')↓s)` — the remaining leading elements.

2. **Iterate**: For each cell `C` in `Y` (enumerated in row-major order over the frame), compute `R ← f C`.

3. **Reassemble**: Collect all result cells `R`. If all have the same shape, the result has shape `frame , (⍴R)`. If shapes differ, pad shorter results with fill elements (0 for numeric, `' '` for character) to match the largest shape in each axis, then assemble. The result shape is `frame , max-cell-shape`.

**Example**: Reverse each row of a matrix.

```apl
M ← 3 4⍴⍳12
⍝ M is:
⍝  1  2  3  4
⍝  5  6  7  8
⍝  9 10 11 12

(⌽⍤1) M
⍝  4  3  2  1
⍝  8  7  6  5
⍝ 12 11 10  9
```

Here `⌽⍤1` means "apply reverse to 1-cells (rows)". The frame is `3` (the first axis). Each row is reversed independently.

**Example**: Sum each row.

```apl
(+/⍤1) M
⍝ 10 26 42
```

The function `+/` reduces a vector to a scalar. Applied at rank 1, each row (a 1-cell) is summed. The frame is `3`, each result is a scalar (shape `⍬`), so the overall result is a 3-element vector.

**Example**: Negative rank — sum along the first axis of each matrix in a 3D array.

```apl
A ← 2 3 4⍴⍳24
(+/⍤¯1) A
⍝ Equivalent to: (+/⍤2) A
⍝ Applies +/ to each 2-cell (matrix), giving two 4-vectors
```

### 3.4 Dyadic case: `X (f⍤b c) Y`

Given dyadic function `f`, left argument `X`, right argument `Y`, left cell rank `b`, and right cell rank `c`:

1. **Decompose**: Clamp `b` and `c` to the ranks of `X` and `Y` respectively. Extract frames for both arguments.

2. **Frame agreement**: The frames must be compatible:
   - If both frames are non-empty, they must be identical (same shape), OR
   - One frame may be a scalar (empty frame, i.e., the entire argument is a single cell), in which case that argument is replicated to match the other frame (scalar extension at the frame level).
   - If frames have different lengths but one is a prefix of the other, this is **not** valid in MARPLE's flat model. (J and nested APLs allow this via "agreement"; MARPLE requires exact frame match or scalar extension. This may be relaxed in a future version.)

3. **Iterate**: Pair up cells from `X` and `Y` according to the frame. If one frame is empty (scalar extension), pair that single cell with every cell of the other argument. Apply `f` dyadically to each pair.

4. **Reassemble**: Same padding rules as the monadic case. Result shape is `common-frame , max-result-cell-shape`.

**Example**: Add a vector to each row of a matrix.

```apl
V ← 10 20 30 40
M ← 3 4⍴⍳12

V (+⍤1) M        ⍝ left rank 1, right rank 1
⍝ 11 22 33 44
⍝ 15 26 37 48
⍝ 19 30 41 52
```

Here `V` has frame `⍬` (it's a single 1-cell), `M` has frame `3` (three 1-cells). Scalar extension at the frame level: `V` is paired with each row of `M`.

**Example**: Pair elements of a vector with rows of a matrix.

```apl
100 200 300 (+⍤0 1) M
⍝ 101 102 103 104
⍝ 205 206 207 208
⍝ 309 310 311 312
```

Left rank 0 gives frame `3` (three scalars). Right rank 1 gives frame `3` (three rows). Frames match, so scalar 100 is added to row 1, scalar 200 to row 2, scalar 300 to row 3.

### 3.5 Interaction with existing operators

Rank is a dyadic operator and follows normal operator binding: `f⍤k` binds tighter than function application but the derived function `(f⍤k)` then behaves as an ordinary function.

**Critical parsing note**: the right operand `k` must not be confused with the right argument. Parentheses or the right-tack function `⊢` disambiguate:

```apl
(⌽⍤1) M       ⍝ parentheses: ⍤ takes 1 as operand, derived fn takes M
⌽⍤1 ⊢ M       ⍝ ⊢ separates: ⍤ binds 1, ⊢ passes M through
```

Without either, `⌽⍤1 M` would attempt to bind the strand `1 M` as the right operand, which is not the intent. MARPLE follows the standard convention: **operators bind tighter than functions to their right operand**, so `⌽⍤1 M` actually parses as `⌽⍤(1 M)` — a rank specification of the vector `1 M`, which is almost certainly wrong. Always parenthesise.

Rank composes naturally with reduce, scan, and other operators:

```apl
(+/⍤1) M         ⍝ sum each row
(+\⍤1) M         ⍝ running sum along each row
(⌽⍤1) M          ⍝ reverse each row
({⍵[⍋⍵]}⍤1) M    ⍝ sort each row (using a dfn)
```

---

## 4. The reassembly constraint in flat APL

This is the one genuine restriction compared to nested APL implementations.

### 4.1 The problem

When `f⍤k` is applied and the function `f` produces result cells of different shapes, the results cannot form a regular rectangular array. In nested APL, each result cell would be enclosed and gathered into a nested vector. In flat APL, we have no enclosure.

**Example of the problem**:

```apl
names ← [
    'Alice   '
    'Bob     '
    'Clarence'
]
⍝ Shape: 3 8

⍝ Suppose we want to trim trailing spaces from each row:
⍝ Row 1 → 'Alice'    (length 5)
⍝ Row 2 → 'Bob'      (length 3)
⍝ Row 3 → 'Clarence' (length 8)
⍝ These have different lengths! Can't form a matrix.
```

### 4.2 MARPLE's solution: padding

When result cells have different shapes, MARPLE **pads** shorter results with fill elements to match the maximum shape along each axis:

- Numeric fill: `0`
- Character fill: `' '` (space)
- Boolean fill: `0`

The result is always a regular array. In the example above, if a trim function were applied at rank 1, the result would be a 3×8 character matrix — which is the same as the input, because padding restores the trailing spaces. This is admittedly not very useful for that particular case, but it's *correct* and *predictable*.

### 4.3 When it matters and when it doesn't

**It almost never matters in practice.** The vast majority of rank-operator uses fall into categories where result shapes are uniform:

| Use case | Result shape | Uniform? |
|----------|-------------|----------|
| Scalar function at any rank | Same as cell | Always ✓ |
| Reduce (`+/⍤k`) | One rank lower | Always ✓ |
| Scan (`+\⍤k`) | Same as cell | Always ✓ |
| Reverse/rotate (`⌽⍤k`) | Same as cell | Always ✓ |
| Transpose (`⍉⍤2`) | Transposed cell shape | Always ✓ |
| Reshape to fixed shape | Fixed | Always ✓ |
| Grade (`⍋⍤1`) | Same length vector | Always ✓ |
| User dfn returning fixed shape | Fixed | ✓ if designed so |
| Take/drop with constant `⍺` | Fixed | Always ✓ |
| Take/drop with varying `⍺` | Varies | ✗ — padding needed |
| Compress with varying mask | Varies | ✗ — padding needed |

The problematic cases are those where the function selects a data-dependent subset of its argument. These are exactly the cases that motivate nested arrays in the first place. MARPLE's answer is: for now, use padding; when boxing arrives (Dictionary APL model), you'll have an explicit way to collect non-uniform results.

### 4.4 Signalling non-uniform results

MARPLE provides a system variable `⎕RANK` (read-only, set automatically) that, when non-uniform padding occurs during a rank operation, is set to `1`. User code can check this after a rank application to detect whether padding occurred. This is optional and may be deferred to a later implementation phase.

---

## 5. Rank subsumes existing mechanisms

One of rank's great virtues is that it replaces and generalizes several first-generation APL features:

### 5.1 Rank replaces bracket-axis

First-generation APL uses bracket-axis notation like `+/[1]` to reduce along a specific axis. This is ad-hoc — each primitive defines its own axis behavior. Rank provides a uniform alternative:

| First-gen syntax | Rank equivalent | Meaning |
|-----------------|----------------|---------|
| `+/M` | `+/M` | Reduce along last axis (unchanged) |
| `+/[1]M` | `(+/⍤¯1) M` | Reduce along first axis |
| `⌽[1]M` | `(⌽⍤¯1) M` | Reverse along first axis |
| `,[1]M` | N/A (ravel along axis — keep `,[k]` for this) |

Bracket-axis can be retained for backward compatibility but is no longer necessary for user-defined functions — rank works with any function.

### 5.2 Rank generalizes scalar extension

Scalar functions in APL already apply element-wise with scalar extension (a scalar paired with each element of an array). This is exactly rank-0 application:

```apl
10 + M          ⍝ scalar extension (built into scalar functions)
10 (+⍤0) M      ⍝ same thing, via rank (but slower — use scalar extension)
```

### 5.3 Rank can express reduce-first and scan-first

```apl
+⌿M             ⍝ reduce along first axis (first-gen primitive)
(+/⍤¯1) M       ⍝ same via rank: reduce each major cell (¯1 = rank minus 1)
```

### 5.4 Rank can express Each (when we don't have it)

In nested APL, `f¨` applies `f` to each element. For flat arrays, `f⍤0` applies `f` to each scalar — achieving the same effect without requiring the Each operator or nested arrays.

---

## 6. Implementation notes

The MARPLE interpreter is Python, using NumPy when available and falling back to pure Python otherwise. The core rank implementation is the same in both cases:

1. Parse the right operand to extract `a b c` (with extension rules)
2. Determine the appropriate cell rank based on valence (monadic → `a`, dyadic → `b c`)
3. Clamp cell ranks to argument ranks
4. Compute frame and cell shapes
5. Iterate over cells in row-major order
6. Apply the operand function to each cell (or pair of cells)
7. Collect results, determine max result shape, pad if necessary
8. Assemble into output array with shape `frame , max-result-shape`

When NumPy is available, cells can be extracted efficiently via `reshape` and slicing (views into the original array, avoiding copies), and `np.ndindex(frame_shape)` provides the frame iteration. Padding uses `np.full`. In pure-Python mode, the same logic operates on lists with manual offset arithmetic.

**Performance consideration**: the rank operator introduces a function-call-per-cell overhead. For scalar functions this is much slower than built-in element-wise application. MARPLE should optimize the case where the operand is a scalar primitive at rank 0 — bypass the rank machinery and use direct element-wise operations. On constrained platforms (e.g. CircuitPython on a Pico with ulab), this optimization matters considerably.

---

## 7. Grammar addition

Add `⍤` to the set of dyadic operators in MARPLE's parser:

```ebnf
(* Extension to MARPLE grammar *)

dop     := '.' | '⍤' ;

(* ⍤ takes a function left operand and numeric right operand *)
(* The derived function is monadic or dyadic *)
```

The `⍤` operator has the same binding strength as other dyadic operators (`.`), binding tighter than function application. This is consistent with the existing binding hierarchy: bracket indexing → operator binding → strand formation → function application → assignment.

---

## 8. Complete example session

```apl
⍝ Create a 3D array: 2 layers, each a 3×4 matrix
A ← 2 3 4⍴⍳24

⍝ Sum each row (1-cells)
(+/⍤1) A
⍝ Shape: 2 3
⍝  6 22 38
⍝ 54 70 86

⍝ Sum each matrix (2-cells) — column sums per layer
(+/⍤2) A
⍝ Shape: 2 4
⍝ 12 15 18 21
⍝ 48 51 54 57

⍝ Reverse each row
(⌽⍤1) A
⍝ Each row reversed in place, shape unchanged: 2 3 4

⍝ Sort each row using a dfn
sort ← {⍵[⍋⍵]}
(sort⍤1) A
⍝ Each row sorted independently

⍝ Add a different scalar to each layer
10 20 (+⍤0 2) A
⍝ 10 added to entire first 3×4 matrix
⍝ 20 added to entire second 3×4 matrix
⍝ Shape: 2 3 4

⍝ Rank with negative specification
(+/⍤¯1) 2 3 4⍴⍳24
⍝ ¯1 on a rank-3 array → 2-cells → sum each 3×4 matrix
⍝ Same as (+/⍤2)

⍝ Matrix multiply each pair of matrices from two 3D arrays
X ← 2 3 4⍴⍳24
Y ← 2 4 2⍴⍳16
X (+.×⍤2) Y
⍝ Two 3×2 result matrices, shape: 2 3 2
```

---

## 9. References

- Arthur Whitney. Rank operator invention, 1982. First implemented in SHARP APL, 1983.
- Ken Iverson. *Rationalized APL*. IPSA, 1983. Includes rank operator.
- Ken Iverson. *A Dictionary of APL*. APL Quote Quad 18(1), September 1987.
- Robert Bernecky. "An Introduction to Function Rank." APL88 conference proceedings, ACM SIGAPL, 1988.
- Dyalog APL rank operator documentation: https://docs.dyalog.com/20.0/language-reference-guide/primitive-operators/rank/
- APL Wiki — Rank (operator): https://aplwiki.com/wiki/Rank_(operator)
- APL Wiki — Cells and subarrays: https://aplwiki.com/wiki/Cell
- Dyalog APL course — Cells and Axes: https://course.dyalog.com/cells-and-axes/
- Stefan Kruger, "The Rank Operator and Dyadic Transpose" (Learning APL): https://xpqz.github.io/learnapl/rank.html
