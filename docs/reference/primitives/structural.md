# Structural Functions

These functions operate on the shape and arrangement of arrays, not on individual elements.

## `⍴` Rho

### Monadic: Shape

Returns the dimensions of the array as a vector.

```apl
      ⍴1 2 3 4 5
5
      ⍴2 3⍴⍳6
2 3
```

A scalar has empty shape (the result is an empty vector).

### Dyadic: Reshape

Creates an array with the shape given by the left argument, filled cyclically from the right argument.

```apl
      3⍴42
42 42 42
      2 3⍴⍳6
1 2 3
4 5 6
      7⍴1 2 3
1 2 3 1 2 3 1
```

---

## `⍳` Iota

### Monadic: Index generator

Generates integers from `⎕IO` to `⍵`.

```apl
      ⍳5
1 2 3 4 5
      ⍳1
1
```

### Dyadic: Index of

Returns the position of each right-argument element in the left argument. Returns one past the end if not found. Respects `⎕CT`.

```apl
      1 2 3 4 5⍳3
3
      10 20 30⍳25
4
```

---

## `,` Comma

### Monadic: Ravel

Flattens an array to a vector.

```apl
      ,2 3⍴⍳6
1 2 3 4 5 6
      ,5
5
```

### Dyadic: Catenate

Joins two arrays.

```apl
      1 2 3,4 5 6
1 2 3 4 5 6
      0,1 2 3
0 1 2 3
```

---

## `⌽` Circle stile

### Monadic: Reverse

```apl
      ⌽1 2 3 4 5
5 4 3 2 1
      ⌽'HELLO'
OLLEH
```

### Dyadic: Rotate

Positive rotates left, negative rotates right.

```apl
      2⌽1 2 3 4 5
3 4 5 1 2
      ¯1⌽1 2 3 4 5
5 1 2 3 4
```

---

## `⍉` Circle backslash

### Monadic: Transpose

Swaps rows and columns of a matrix.

```apl
      ⍉2 3⍴⍳6
1 4
2 5
3 6
```

---

## `↑` Up arrow

### Dyadic: Take

Takes elements from the front (positive) or back (negative).

```apl
      3↑1 2 3 4 5
1 2 3
      ¯2↑1 2 3 4 5
4 5
```

---

## `↓` Down arrow

### Dyadic: Drop

Drops elements from the front (positive) or back (negative).

```apl
      2↓1 2 3 4 5
3 4 5
      ¯2↓1 2 3 4 5
1 2 3
```

---

## `∈` Epsilon

### Dyadic: Membership

Returns `1` for each left element found in the right argument, `0` otherwise. Respects `⎕CT`.

```apl
      3∈1 2 3 4 5
1
      6∈1 2 3 4 5
0
      1 3 5∈2 3 4
0 1 0
```

---

## `⍋` Grade up

### Monadic: Grade up

Returns indices that would sort ascending. Respects `⎕IO`.

```apl
      ⍋30 10 50 20 40
2 4 1 5 3
      v←30 10 50 20 40
      v[⍋v]
10 20 30 40 50
```

---

## `⍒` Grade down

### Monadic: Grade down

Returns indices that would sort descending. Respects `⎕IO`.

```apl
      ⍒30 10 50 20 40
3 5 1 4 2
```
