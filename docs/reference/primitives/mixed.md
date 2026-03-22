# Mixed Functions

Mixed functions have non-scalar behaviour — their result shape depends on the operation, not just the argument shapes.

## `⊤` Encode

### Dyadic only

Represents the right argument in the number system given by the left argument.

```apl
      2 2 2 2⊤13        ⍝ binary: 1101
1 1 0 1
      10 10 10⊤256
2 5 6
```

---

## `⊥` Decode

### Dyadic only

Evaluates the right argument as a polynomial with the left argument as base.

```apl
      2⊥1 1 0 1         ⍝ binary 1101 = 13
13
      10⊥2 5 6           ⍝ 256
256
      24 60 60⊥1 2 3     ⍝ 1h 2m 3s = 3723 seconds
3723
```

---

## `⌹` Domino

### Monadic: Matrix inverse

Inverts a square matrix using Gauss-Jordan elimination.

```apl
      ⌹2 2⍴2 0 0 2
0.5 0
  0 0.5
```

### Dyadic: Matrix divide

Solves the linear system `b⌹A` (finds x where Ax = b).

---

## `⍎` Execute

### Monadic only

Evaluates a character vector as an APL expression.

```apl
      ⍎'2+3'
5
      ⍎'+/⍳10'
55
```

---

## `⍕` Format

### Monadic: Format

Converts an array to a character vector.

```apl
      ⍕42
42
      ⍕1 2 3
1 2 3
```

### Dyadic: Format with width

Left argument specifies field width (scalar) or width and decimal places (2-element vector).

```apl
      6⍕42
    42
      8 2⍕3.14159
    3.14
```

---

## `≡` Match

### Dyadic only

Returns `1` if both arguments have the same shape and data, `0` otherwise. Uses exact comparison (ignores `⎕CT`).

```apl
      3≡3
1
      1 2 3≡1 2 3
1
      3≡4
0
      1 2 3≡1 2           ⍝ different shapes
0
```

---

## `≢` Not match / Tally

### Monadic: Tally

Returns the number of major cells (first dimension).

```apl
      ≢1 2 3 4 5
5
      ≢2 3⍴⍳6
2
      ≢5                  ⍝ scalar tally is 1
1
```

### Dyadic: Not match

Returns `1` if arguments differ, `0` if identical. Exact comparison.

```apl
      3≢4
1
      3≢3
0
```
