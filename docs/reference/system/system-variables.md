# System Variables

System variables are names beginning with `⎕` (quad). They control interpreter behaviour.

## `⎕IO` — Index Origin

| | |
|---|---|
| **Default** | `1` |
| **Valid values** | `0` or `1` |

Controls where counting starts. Affects `⍳` (iota), `⍋` `⍒` (grade), `⌷` (From), bracket indexing, and dyadic `⍳` (index-of).

```apl
      ⎕IO
1
      ⍳5
1 2 3 4 5
      ⎕IO←0
      ⍳5
0 1 2 3 4
```

## `⎕CT` — Comparison Tolerance

| | |
|---|---|
| **Default** | `1E¯14` |
| **Valid values** | Any non-negative number |

Controls tolerant comparison for floating-point numbers. Two values `a` and `b` are considered equal if `|a-b| ≤ ⎕CT × (|a| ⌈ |b|)`.

Affects: `= ≠ < ≤ ≥ >`, dyadic `⍳` (index-of), `∈` (membership).

Does **not** affect: `≡` (match) and `≢` (not-match), which always use exact comparison.

```apl
      1=(1÷3)×3          ⍝ tolerant: floating-point 0.999... equals 1
1
      ⎕CT←0              ⍝ exact comparison
      1=1.001
0
```

Set `⎕CT←0` when you need exact floating-point comparison.

!!! note
    `⎕PP` (print precision) is not a settable system variable. Display precision is fixed at 10 significant digits.
