# Arithmetic Functions

## `+` Plus

### Monadic: Conjugate

For real numbers, returns the argument unchanged (identity).

```apl
      +5
5
      +¯3
¯3
```

### Dyadic: Add

```apl
      3+4
7
      1 2 3+10 20 30
11 22 33
      100+⍳5
101 102 103 104 105
```

---

## `-` Minus

### Monadic: Negate

```apl
      -5
¯5
      -¯3
3
      -1 2 3
¯1 ¯2 ¯3
```

### Dyadic: Subtract

```apl
      10-3
7
      10 20 30-1 2 3
9 18 27
```

---

## `×` Times

### Monadic: Signum

Returns `¯1`, `0`, or `1` depending on the sign of the argument.

```apl
      ×¯3
¯1
      ×0
0
      ×42
1
```

### Dyadic: Multiply

```apl
      3×4
12
      2×⍳5
2 4 6 8 10
```

---

## `÷` Divide

### Monadic: Reciprocal

Returns `1÷⍵`. Raises DOMAIN ERROR for zero.

```apl
      ÷4
0.25
      ÷2 4 5
0.5 0.25 0.2
```

### Dyadic: Divide

Raises DOMAIN ERROR for division by zero.

```apl
      10÷4
2.5
      12÷1 2 3 4 6
12 6 4 3 2
```

---

## `⌈` Upstile

### Monadic: Ceiling

Returns the smallest integer greater than or equal to the argument.

```apl
      ⌈3.7
4
      ⌈¯2.3
¯2
      ⌈5
5
```

### Dyadic: Maximum

```apl
      3⌈5
5
      1 5 3⌈4 2 6
4 5 6
```

---

## `⌊` Downstile

### Monadic: Floor

Returns the largest integer less than or equal to the argument.

```apl
      ⌊3.7
3
      ⌊¯2.3
¯3
```

### Dyadic: Minimum

```apl
      3⌊5
3
      1 5 3⌊4 2 6
1 2 3
```

---

## `*` Star

### Monadic: Exponential

Returns e raised to the power of the argument.

```apl
      *1
2.718281828
      *0
1
```

### Dyadic: Power

```apl
      2*8
256
      2*0 1 2 3 4
1 2 4 8 16
```

---

## `⍟` Log

### Monadic: Natural logarithm

```apl
      ⍟1
0
      ⍟*1
1
```

### Dyadic: Logarithm

Left argument is the base.

```apl
      10⍟100
2
      2⍟8
3
```

---

## `|` Stile

### Monadic: Magnitude (absolute value)

```apl
      |¯5
5
      |3
3
      |¯1 2 ¯3
1 2 3
```

### Dyadic: Residue

The remainder when dividing the right argument by the left. Note: APL residue has the left argument as the divisor (opposite to most languages).

```apl
      3|7
1
      5|12
2
      2|⍳6
1 0 1 0 1 0
```

---

## `○` Circle

### Monadic: Pi times

Multiplies the argument by π.

```apl
      ○1
3.141592654
      ○0.5
1.570796327
```

### Dyadic: Circular functions

The left argument selects a trigonometric or hyperbolic function:

| Left | Function | Left | Function |
|------|----------|------|----------|
| `0` | `√(1-⍵²)` | | |
| `1` | sin | `¯1` | arcsin |
| `2` | cos | `¯2` | arccos |
| `3` | tan | `¯3` | arctan |
| `4` | `√(1+⍵²)` | `¯4` | `√(⍵²-1)` |
| `5` | sinh | `¯5` | arcsinh |
| `6` | cosh | `¯6` | arccosh |
| `7` | tanh | `¯7` | arctanh |

```apl
      1○○0.5           ⍝ sin(π/2) = 1
1
      2○0               ⍝ cos(0) = 1
1
      3○0               ⍝ tan(0) = 0
0
```
