# System Variables and Functions

System variables are names beginning with `⎕` (quad). They control interpreter behaviour, provide system information, or act as built-in functions.

## Settable System Variables

### `⎕IO` — Index Origin

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

### `⎕CT` — Comparison Tolerance

| | |
|---|---|
| **Default** | `1E¯14` |
| **Valid values** | Any non-negative number |

Controls tolerant comparison for floating-point numbers. Two values `a` and `b` are considered equal if `|a-b| ≤ ⎕CT × (|a| ⌈ |b|)`.

Affects: `= ≠ < ≤ ≥ >`, dyadic `⍳` (index-of), `∈` (membership), and numeric downcast (integer results from float arithmetic).

Does **not** affect: `≡` (match) and `≢` (not-match), which always use exact comparison.

```apl
      1=(1÷3)×3          ⍝ tolerant: floating-point 0.999... equals 1
1
      ⎕CT←0              ⍝ exact comparison
      1=1.001
0
```

### `⎕PP` — Print Precision

| | |
|---|---|
| **Default** | `10` |
| **Valid values** | Positive integer |

Controls the number of significant digits used when displaying floating-point numbers.

```apl
      ○1
3.141592654
      ⎕PP←4
      ○1
3.142
      ⎕PP←17
      0.1+0.2
0.30000000000000004
```

### `⎕RL` — Random Link

| | |
|---|---|
| **Default** | `1` |
| **Valid values** | Any integer |

Seed for the random number generator. Setting `⎕RL` makes `?` (roll/deal) produce reproducible sequences.

```apl
      ⎕RL←42
      ?10
4
```

### `⎕WSID` — Workspace ID

| | |
|---|---|
| **Default** | `CLEAR WS` |
| **Valid values** | Character vector |

The name of the current workspace. Used by `)save` and `)load`.

### `⎕FR` — Floating-point Representation

| | |
|---|---|
| **Default** | `645` |
| **Valid values** | `645` or `1287` |

Controls the arithmetic mode, following Dyalog APL conventions:

- `645` — IEEE binary float64 (default). Standard floating-point arithmetic.
- `1287` — Decimal arithmetic using Python's `decimal.Decimal`. Provides exact results for addition, subtraction, and multiplication of decimal values.

```apl
      ⎕CT←0
      (0.1+0.2)=0.3      ⍝ float: not exactly equal
0
      ⎕FR←1287
      (0.1+0.2)=0.3      ⍝ decimal: exactly equal
1
      0.1×0.1
0.01
```

## Read-only System Variables

These variables can be queried but not assigned.

### `⎕A` — Alphabet

The 26 uppercase Latin letters: `ABCDEFGHIJKLMNOPQRSTUVWXYZ`

### `⎕D` — Digits

The 10 decimal digits: `0123456789`

### `⎕TS` — Timestamp

A 7-element integer vector: `year month day hour minute second millisecond`.

```apl
      ⎕TS
2026 3 25 14 30 0 0
```

### `⎕EN` — Error Number

The numeric code of the most recent caught error (via `⎕EA`). `0` if no error has been caught.

### `⎕DM` — Diagnostic Message

The text of the most recent caught error. Empty character vector if no error has been caught.

### `⎕VER` — Version

A character vector identifying the MARPLE version and platform, e.g. `MARPLE v0.4.3 on linux`.

## System Functions

These quad-names behave as functions (monadic or dyadic).

### `⎕DR` — Data Representation

**Monadic:** `⎕DR x` returns an integer code for the internal data type of `x`:

| Code | Type |
|------|------|
| `11` | Boolean (uint8) |
| `80` | Character |
| `163` | 16-bit integer (int16, ulab) |
| `323` | 32-bit integer (int32, numpy) |
| `645` | 64-bit float (float64) |

```apl
      ⎕DR 42
323
      ⎕DR 3.14
645
      ⎕DR 'hello'
80
      ⎕DR 1 2 3=1 3 3
11
```

**Dyadic:** `code ⎕DR x` converts `x` to the specified type.

```apl
      645 ⎕DR 42        ⍝ int to float
42
      ⎕DR 645 ⎕DR 42
645
```

### `⎕EA` — Execute Alternate

`alternate ⎕EA expression` — evaluates `expression` (a character vector). If it errors, evaluates `alternate` instead.

```apl
      '0' ⎕EA '2+3'     ⍝ succeeds: returns 5
5
      '0' ⎕EA '1÷0'     ⍝ fails: returns 0
0
```

### `⎕UCS` — Universal Character Set

Converts between characters and Unicode code points.

```apl
      ⎕UCS 65 66 67
ABC
      ⎕UCS 'A'
65
```

### `⎕NC` — Name Class

`⎕NC 'name'` returns the name class: 0 (undefined), 2 (array), 3 (function), 4 (operator).

### `⎕EX` — Expunge

`⎕EX 'name'` removes a name from the workspace. Returns 1 if successful, 0 if the name was not defined.

### `⎕SIGNAL` — Signal Error

`⎕SIGNAL code` raises an APL error with the given numeric code.

```apl
      ⎕SIGNAL 3          ⍝ raises DOMAIN ERROR
```

### `⎕NREAD` — Read File

Monadic. Reads a text file and returns a character vector.

```apl
      ⎕NREAD '/tmp/data.txt'
hello world
```

### `⎕NWRITE` — Write File

Dyadic. Writes a character vector to a file. Left argument is the data, right argument is the path.

```apl
      'hello world' ⎕NWRITE '/tmp/data.txt'
```

### `⎕NEXISTS` — File Exists

Monadic. Returns `1` if the file exists, `0` otherwise.

```apl
      ⎕NEXISTS '/tmp/data.txt'
1
      ⎕NEXISTS '/tmp/no_such_file.txt'
0
```

### `⎕NDELETE` — Delete File

Monadic. Deletes a file. Raises DOMAIN ERROR if the file does not exist.

```apl
      ⎕NDELETE '/tmp/data.txt'
```

### `⎕CR` — Canonical Representation

Monadic. Returns the source text of a named function as a character vector.

```apl
      double←{⍵+⍵}
      ⎕CR 'double'
double←{⍵+⍵}
```

Raises DOMAIN ERROR if the name is not a defined function.

### `⎕FX` — Fix

Monadic. Defines a function from its text representation. Returns the function name as a character vector.

```apl
      ⎕FX 'triple←{⍵×3}'
triple
      triple 5
15
```

Works with multi-statement dfns:

```apl
      ⎕FX 'abs←{⍵<0:-⍵ ⋄ ⍵}'
      abs ¯7
7
```

Round-trip with `⎕CR`:

```apl
      src ← ⎕CR 'double'
      ⎕FX src           ⍝ re-define from source
```

### `⎕FMT` — Format

**Monadic:** `⎕FMT x` — default formatting as a character vector.

**Dyadic:** `fmt ⎕FMT (val1;val2;...)` — format values according to specification. Returns a character matrix.

The right argument uses semicolon-separated values in parentheses. Each value is a column; vectors produce multiple rows.

#### Format codes

| Code | Meaning | Example |
|------|---------|---------|
| `Iw` | Integer, w wide, right-justified | `I5` → `   42` |
| `Fw.d` | Fixed-point, w wide, d decimals | `F8.2` → `    3.14` |
| `Ew.d` | Scientific notation | `E12.4` → `  1.2346E+05` |
| `Aw` | Character, w wide, left-justified | `A10` → `hello     ` |
| `G⊂pattern⊃` | Pattern: `9` filled with digits | `G⊂99/99⊃` → `12/34` |
| `⊂text⊃` or `<text>` | Literal text insertion | `⊂ => ⊃` |

Comma separates format codes. An optional repetition prefix applies: `3I5` = three I5 columns, `5A1` = five characters from one column.

#### Examples

```apl
      'I3,⊂: ⊃,F7.2' ⎕FMT (⍳3;100×⍳3)
  1:  100.00
  2:  200.00
  3:  300.00

      MEN←3 5⍴'FRED BILL JAMES'
      WOMEN←2 5⍴'MARY JUNE '
      '5A1,⊂|⊃' ⎕FMT (MEN;WOMEN)
FRED |MARY |
BILL |JUNE |
JAMES|     |

      'G⊂99/99/99⊃' ⎕FMT (0 100 100⊥8 7 89)
08/07/89
```

#### Errors

- Numeric data matched against A format
- Character data matched against non-A format
- F format: d > w-2
- E format: d > w-2
