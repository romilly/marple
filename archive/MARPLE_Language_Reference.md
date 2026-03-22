# First-generation APL syntax: a builder's reference for MARPLE

**APL's core is deceptively small: roughly 60 glyph-functions, 6 operators, right-to-left evaluation with no precedence rules, and a uniform array data model.** This makes it an ideal target for a minimal interpreter. What follows is a complete reference covering the language definition of first-generation APL (APL\360 through APL.SV), direct definition for user-defined functions and operators, the I-APL educational implementation, the ISO standards, formal grammar approaches, and a phased implementation roadmap for MARPLE — a Mini APL in Python using APL arrays as the internal data model.

**Design decisions for MARPLE:** No nested arrays (avoiding the APL2/Dyalog complexity). User-defined functions and operators via direct definition (dfns), not the `∇` tradfn editor. The internal data model uses APL arrays (`shape` + flat `data` list), inspired by Rodrigo Girão Serrão's RGSPL interpreter. The door remains open for Iverson's "Dictionary of APL" approach to arrays of arrays, which offers a cleaner model than Jim Brown's APL2 nested arrays.

---

## How APL evaluation actually works

APL's syntax is radically simpler than most languages because it has **no operator precedence**. Every function has equal priority. The entire evaluation model rests on four rules:

1. **Functions have long right scope** — a function consumes *everything* to its right as its right argument (up to an unmatched parenthesis or end of expression).
2. **Functions have short left scope** — a dyadic function takes only the *single data item* immediately to its left as its left argument.
3. **Operators bind tighter than functions** — an operator grabs its operand(s) first, producing a derived function, before function application occurs.
4. **Parentheses override** all default scoping.

The practical effect: `1 ÷ 2 ⌊ 3 × 4 - 5` evaluates as `1 ÷ (2 ⌊ (3 × (4 - 5)))`, yielding `¯0.333...`. There is no multiplication-before-addition rule. This uniformity eliminates an entire class of parsing complexity.

**Binding strength hierarchy** (tightest to loosest): bracket indexing `[]` → operator binding → strand formation (adjacent arrays) → function application → assignment `←` → statement separation `⋄`. The critical parser challenge is distinguishing monadic from dyadic function calls, which depends on whether data or a function appears to the left of a glyph.

---

## Complete primitive function catalog

Every APL glyph carries **two meanings**: one when used monadically (prefix, one argument) and one dyadically (infix, two arguments). The high minus `¯` distinguishes negative literals from the negate function: `¯3` is the number negative-three, while `-3` is the function negate applied to three.

### Scalar functions (apply element-wise, with scalar extension)

| Glyph | Monadic | Dyadic |
|-------|---------|--------|
| `+` | Conjugate (identity for reals) | **Add** |
| `-` | **Negate** | **Subtract** |
| `×` | Signum (¯1, 0, or 1) | **Multiply** |
| `÷` | Reciprocal (1÷B) | **Divide** |
| `⌈` | Ceiling | **Maximum** |
| `⌊` | Floor | **Minimum** |
| `*` | Exponential (e*B) | **Power** (A*B) |
| `⍟` | Natural log | Logarithm base A |
| `|` | Absolute value | **Residue** (modulo) |
| `!` | Factorial / Gamma | Binomial coefficient |
| `○` | Pi times (π×B) | Circular/trig (A selects function) |
| `?` | Roll (random 1..B) | Deal (A distinct randoms from 1..B) |
| `< ≤ = ≥ > ≠` | *(none in first-gen)* | **Comparison** (returns 0 or 1) |
| `∧ ∨` | *(none)* | **And / Or** (Boolean; later extended to GCD/LCM) |
| `⍲ ⍱` | *(none)* | **Nand / Nor** |
| `~` | **Not** (Boolean) | Without (set difference — mixed, not scalar) |

The circular function `○` deserves special note: the left argument selects which trig function to apply. `1○B` is sin(B), `2○B` is cos(B), `3○B` is tan(B), with negative left arguments giving inverse functions (`¯1○B` is arcsin). Values 5–7 give hyperbolic functions.

### Structural and mixed functions

| Glyph | Monadic | Dyadic |
|-------|---------|--------|
| `⍴` | **Shape** (returns dimensions) | **Reshape** (A⍴B creates array with shape A) |
| `⍳` | **Iota** (index generator: ⍳N → 1 2...N) | **Index of** (position of B in A) |
| `,` | **Ravel** (flatten to vector) | **Catenate** (join along last axis) |
| `⌽` | **Reverse** (last axis) | **Rotate** by A positions |
| `⊖` | Reverse (first axis) | Rotate along first axis |
| `⍉` | **Transpose** (reverse axis order) | Generalized transpose |
| `↑` | First element | **Take** (A elements from B) |
| `↓` | *(later: Split)* | **Drop** (remove A elements from B) |
| `∈` | *(later: Enlist)* | **Membership** (A∈B → Boolean) |
| `⍋` | **Grade up** (sort indices, ascending) | Grade with collation |
| `⍒` | **Grade down** (sort indices, descending) | Grade with collation |
| `⊤` | — | **Encode** (convert to base-A representation) |
| `⊥` | — | **Decode** (evaluate as base-A polynomial) |
| `⌹` | Matrix inverse | Matrix divide (solve linear system) |
| `⍎` | **Execute** (evaluate APL string) | — |
| `⍕` | **Format** (convert to string) | Format with width/precision |
| `/` | *(operator)* | **Replicate/Compress** (select where 1) |
| `\` | *(operator)* | **Expand** (insert fill where 0) |

Bracket indexing is the original mechanism: `V[3]` for vectors, `M[2;3]` for matrices, `M[;3]` for entire columns. **Index origin** `⎕IO` controls whether indexing starts at 0 or 1 (default 1 in classic APL).

---

## The six first-generation operators

Operators are higher-order: they take functions (or data) as operands and produce **derived functions**. First-generation APL had remarkably few:

**APL\360 (1966)** shipped with only reduce and inner/outer product. **APL.SV (1973)** added scan. The `¨` (each) operator arrived with nested arrays in APL2 (1984) — MARPLE will not include it. For a first-gen target, the essential operators are:

| Symbol | Name | Behavior |
|--------|------|----------|
| `f/` | **Reduce** | Insert f between vector elements: `+/1 2 3 4` → 10 |
| `f⌿` | **Reduce-first** | Reduce along first axis |
| `f\` | **Scan** | Running reduce: `+\1 2 3` → `1 3 6` |
| `f⍀` | **Scan-first** | Scan along first axis |
| `f.g` | **Inner product** | Generalized matrix multiply: `A +.× B` |
| `∘.f` | **Outer product** | Apply f to all element pairs: `A ∘.× B` gives multiplication table |

Reduce evaluates right-to-left: `f/ b1 b2 b3` becomes `b1 f (b2 f b3)`. This matters for non-associative functions like subtract: `-/1 2 3` → `1-(2-3)` → `2`, not `(1-2)-3` → `¯4`.

---

## Direct definition: user-defined functions and operators for MARPLE

MARPLE will use **direct definition (dfns)** rather than the traditional `∇` editor for user-defined functions and operators. This is both cleaner to implement and closer to modern APL practice.

### Historical lineage

The concept has two distinct historical phases. **Iverson's original "direct definition"** (1974, described in SATN 36, 1980) used a named form with colon separators:

```
mean : (+/⍵) ÷ ⍴⍵
abs  : (⍵<0) : -⍵ : ⍵
```

The three-part form `name : expr0 : proposition : expr1` returned `expr0` if the proposition was 0, or `expr1` if it was 1. `⍺` and `⍵` denoted the left and right arguments respectively (alpha and omega, the first and last letters of the Greek alphabet — a typically Iversonian mnemonic).

**John Scholes' dfns** (1996, Dyalog APL) evolved this into an anonymous, curly-brace syntax that is now the dominant style. Scholes was inspired by functional programming — he read a special issue of *The Computer Journal* on the topic in 1989. The key innovations were: anonymous definition via `{}`, guards using `:`, lexical (not dynamic) scoping, and self-reference via `∇` for recursion.

### Dfn syntax for MARPLE

A dfn is enclosed in curly braces and uses fixed argument names:

```
{⍺ and ⍵ in body}
```

The core rules are:

**Arguments:** `⍵` is the right argument (always present). `⍺` is the optional left argument. If only `⍵` appears in the body, the function is monadic; if `⍺` also appears, it's ambivalent (usable both ways).

**Return value:** A dfn returns the result of the first expression that does not end in assignment. There is no explicit "return" — the first non-assigned value is the result.

**Guards:** A colon separates a boolean test from its consequent expression: `condition : expression`. Guards are evaluated in sequence; the first whose condition yields 1 has its expression evaluated as the result.

**Statement separation:** Multiple expressions are separated by `⋄` (diamond) or newlines.

**Local variables:** All names assigned within a dfn are local, with lexical scope. A dfn cannot see locals of its caller, but can see locals of its enclosing definition.

**Default left argument:** `⍺ ← value` sets a default for the left argument, making a dfn usable both monadically and dyadically.

**Self-reference:** `∇` refers to the function itself, enabling anonymous recursion. `∇∇` in a dop refers to the operator itself.

**Examples for MARPLE:**

```apl
⍝ Named function via assignment
mean ← {(+/⍵) ÷ ⍴⍵}

⍝ Factorial via recursion with guard
fact ← {⍵≤1 : 1 ⋄ ⍵ × ∇ ⍵-1}

⍝ Ambivalent function with default left argument
pad ← {⍺←' ' ⋄ ⍺,⍵}

⍝ Fibonacci (two guards)
fib ← {⍵=0 : 0 ⋄ ⍵=1 : 1 ⋄ (∇ ⍵-1) + ∇ ⍵-2}
```

### Direct operators (dops)

If `⍺⍺` appears in the body, the dfn is a **monadic operator** (takes one operand). If `⍵⍵` also appears, it's a **dyadic operator** (takes two operands).

```apl
⍝ Monadic operator: apply function twice
twice ← {⍺⍺ ⍺⍺ ⍵}
+twice 3

⍝ Dyadic operator example
compose ← {⍺⍺ ⍵⍵ ⍵}
```

For MARPLE, implementing dops is optional in early phases but the parser should reserve `⍺⍺` and `⍵⍵` from the start to keep the door open.

### Why dfns over tradfns

For an interpreter project, dfns are dramatically simpler to implement: no line editor, no line numbers, no `→` branching, no state indicator management. The function body is a single expression (or sequence of guarded expressions), parsed exactly like any other APL expression. The only new parser requirements are: recognizing `{}` as delimiters, binding `⍺`/`⍵`/`⍺⍺`/`⍵⍵`/`∇` as special names within the scope, and handling guard syntax.

---

## Iverson's "Dictionary of APL" — the future path for arrays of arrays

Rather than Jim Brown's APL2 nested arrays (which Dyalog adopted and which greatly complicate the language with enclosed arrays, depth, match vs. equal, and numerous edge cases), MARPLE's future direction for handling arrays of arrays should draw on Iverson's 1987 paper **"A Dictionary of APL"**.

The Dictionary defines a simplified language aligned with **leading axis theory** — the idea that primitive operations should naturally apply along the first (leading) axis rather than requiring explicit axis specification. It introduces new primitives such as Nub Sieve and Raze, and uses English grammar terminology (nouns, verbs, adverbs, conjunctions) that later became central to J.

The key advantage for MARPLE: the Dictionary approach keeps the array model relatively flat while still enabling structured data. Much of this functionality was eventually implemented in SHARP APL and then in J, but it was generally *not* adopted by other APL implementations. This means MARPLE could occupy an interesting design space — a first-gen APL core with Dictionary-style extensions rather than APL2-style nesting.

The full text of the Dictionary is freely available at:
**https://www.jsoftware.com/papers/APLDictionary.htm**

---

## I-APL: Paul Chapman's portable, free, ISO-conformant interpreter

I-APL (International APL) was born at the **APL86 conference in Manchester** when programmer Paul Chapman offered to build a portable APL for school microcomputers. Incorporated as **I-APL Limited on 30 September 1986**, the project delivered version 1.0 in **January 1988** — an interpreter fitting in **under 25 kilobytes** of program space.

Chapman wrote I-APL in a **custom Forth-based language called "DE"** (Development Environment), producing platform-neutral pseudocode that was then compiled via APL*PLUS/PC programs and optimized in C. This architecture enabled ports to **BBC Micro (6502), IBM PC (8086), Apple II, Macintosh (68000), CP/M (Z80), Sinclair Spectrum, and ARM-based Acorn machines**.

**I-APL targeted full conformance with ISO 8485** (the flat APL standard). It implemented the complete ISO-mandated primitive set. It deliberately omitted file systems (not required by the standard) and shared variables (optional). A critical design decision: I-APL used **configurable character tables** rather than requiring APL-specific character ROMs — essential for 1980s school computers. The software was **distributed free of charge**.

---

## Anthony Camacho: the organizational force behind I-APL

Anthony Camacho served as **secretary and later chairman of the British APL Association (BAA)** across multiple decades. At APL86, he was among the founding group — alongside Chapman, Ken Iverson, Sylvia Camacho, Ed Cherlin, Howard Peelle, and Linda Alvord — who conceived the I-APL project. Camacho and Ed Cherlin were elected **co-chairmen** of the I-APL project committee.

His contributions were primarily organizational and evangelistic rather than technical. He handled fundraising, assembled the mailing list, and represented the BAA at British Computer Society technical board meetings. Anthony remained active in the BAA through at least **2010**, authoring AGM reports in **Vector**, the BAA's journal.

---

## Two ISO standards define APL formally

**ISO 8485:1989** ("Programming languages — APL") is the foundational standard, covering **flat (non-nested) APL** in 259 pages. It defines the character set, primitive functions, operators, syntax, semantics, and conformance requirements for an APL.SV-era dialect. **This is the relevant target for MARPLE.**

**ISO/IEC 13751:2001** ("Programming language Extended APL") supersedes 8485 for nested-array APL (the APL2 model that MARPLE is deliberately avoiding). A **near-final draft PDF** is hosted at the University of Waterloo (`math.uwaterloo.ca/~ljdickey/apl-rep/docs/is13751.pdf`). **GNU APL** implements this standard.

Neither standard is freely available in final form; ISO charges approximately CHF 221–227 for the official documents.

---

## Parsing APL: why it defies conventional grammars

**APL does not have a context-free grammar** in the general case. The syntactic role of a name — array, function, or operator — depends on its runtime value, not its lexical form.

Three practical approaches exist:

**The Bunda-Gerth pairwise reduction parser** (1984) is the most widely adopted. Tokens are classified as A (array), F (function), MOP (monadic operator), or DOP (dyadic operator). The parser scans right-to-left, identifies the rightmost "peak" in a binding-strength table, reduces that pair, and repeats. Dyalog's `dfns` workspace contains a working implementation.

**Girardot's LR(1) approach** (1987) demonstrated that APL can be described with an LR(1) grammar plus limited backtracking.

**For MARPLE specifically**, the simplest practical grammar (adapted from Rodrigo Girão Serrão's RGSPL Python interpreter) reads right-to-left:

```
program     := statement_list EOF
statement_list := statement ( '⋄' statement )*
statement   := ( ID '←' | array function | function )* array
function    := f | function mop | f dop function | dfn
dfn         := '{' guard_expr ( '⋄' guard_expr )* '}'
guard_expr  := ( expr ':' )? expr
f           := '+' | '-' | '×' | '÷' | '⌈' | '⌊' | '⍴' | '⍳' | ...
mop         := '/' | '\' | '⌿' | '⍀'
dop         := '.'
array       := atom+
atom        := NUMBER | STRING | ID | '(' statement ')' | dfn
```

Note the addition of `dfn` as both a function and an atom production — dfns are first-class values that can appear anywhere a function or data value is expected.

---

## Rodrigo Girão Serrão's RGSPL: a Python APL interpreter

Rodrigo Girão Serrão (who later interned and worked at Dyalog) built **RGSPL** — a Python interpreter for APL — as a learning project. It is an excellent reference for MARPLE because it implements the core APL array model, scalar functions, operators, and parsing in clear, readable Python.

- **GitHub repository:** https://github.com/rodrigogiraoserrano/RGSPL
- **Blog series (step-by-step build):** https://mathspp.com/blog/lsbasi-apl-part1

The blog series walks through tokenization, parsing, the array model (shape and rank), scalar function implementation, and operator handling — all closely matching what MARPLE needs to build.

---

## A phased roadmap for MARPLE

Given MARPLE's design — pure Python, APL arrays as the internal data model, dfns for user definitions, flat arrays only — here is a concrete implementation sequence.

**Phase 1: Calculator.** Numeric scalars and vectors via strand notation (`1 2 3`), the six essential scalar functions (`+ - × ÷ ⌈ ⌊`) in both monadic and dyadic forms, right-to-left evaluation, parentheses, high minus (`¯`), assignment (`←`), comments (`⍝`). Internal representation: `APLArray(shape, data)` where `shape` is a list of dimensions and `data` is a flat list of values. Scalars have shape `[]`, vectors have shape `[n]`.

**Phase 2: Useful subset.** Statement separator (`⋄`). Extend scalar functions with `* ⍟ | < ≤ = ≥ > ≠ ∧ ∨ ~`. Add structural functions: `⍴` (shape/reshape), `⍳` (iota/index-of), `,` (ravel/catenate), `↑ ↓` (take/drop), `⌽` (reverse/rotate). Introduce the reduce operator `/` and scan `\`.

**Phase 3: Direct definition.** Implement dfns with `{⍺ ⍵}` syntax, guards (`condition : expr`), lexical scoping, `∇` self-reference for recursion, and `⍺ ← default` for ambivalent functions. This is the critical phase that turns MARPLE from a calculator into a programming language. Named functions via `name ← {body}`.

**Phase 4: Full first-gen APL.** Inner product `f.g` and outer product `∘.f`. Matrices and higher-rank arrays with bracket indexing `M[i;j]`. Add `⍉` (transpose), `⍋ ⍒` (grade), `⊤ ⊥` (encode/decode), `⍎ ⍕` (execute/format), `⌹` (matrix operations), replicate/expand as functions. System variables `⎕IO` and `⎕CT`. Optionally, direct operators (dops) with `⍺⍺` and `⍵⍵`.

**Future: Dictionary APL extensions.** Following Iverson's "Dictionary of APL" rather than APL2, add leading-axis operations, Nub Sieve, and a clean boxed-array model that avoids the complexity explosion of nested arrays.

---

## Key references

| Resource | URL |
|----------|-----|
| **RGSPL** (Python APL interpreter) | https://github.com/rodrigogiraoserrano/RGSPL |
| RGSPL blog series | https://mathspp.com/blog/lsbasi-apl-part1 |
| Iverson's "Dictionary of APL" (1987) | https://www.jsoftware.com/papers/APLDictionary.htm |
| John Scholes' dfns paper | https://www.dyalog.com/uploads/documents/Papers/dfns.pdf |
| Dfn — APL Wiki | https://aplwiki.com/wiki/Dfn |
| Direct definition (notation) — APL Wiki | https://aplwiki.com/wiki/Direct_definition_(notation) |
| I-APL — APL Wiki | https://aplwiki.com/wiki/I-APL |
| History of I-APL — J Wiki | https://code.jsoftware.com/wiki/Essays/History_of_I-APL |
| ISO 8485:1989 — APL Wiki | https://aplwiki.com/wiki/ISO_8485:1989 |
| ISO/IEC 13751 draft (Waterloo) | https://math.uwaterloo.ca/~ljdickey/apl-rep/docs/is13751.pdf |
| APL syntax and symbols — Wikipedia | https://en.wikipedia.org/wiki/APL_syntax_and_symbols |
| Bunda-Gerth parser (Dyalog dfns) | https://dfns.dyalog.com/n_parse.htm |
| GNU APL | https://www.gnu.org/software/apl/ |
| APL syntax — APL Wiki | https://aplwiki.com/wiki/APL_syntax |
