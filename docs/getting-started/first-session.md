# Your First Session

This page walks you through a first interactive session with MARPLE. Launch the REPL (`marple`) and follow along.

## MARPLE as a calculator

APL works right to left, like mathematics. Try some arithmetic:

```apl
      2 + 3
5
      10 - 4
6
      3 × 5
15
      20 ÷ 4
5
```

!!! note
    APL uses `×` for multiplication and `÷` for division, not `*` and `/`. The `*` symbol means *power* (exponentiation), and `/` means *reduce*.

Right-to-left evaluation means there's no precedence — every function takes everything to its right as its argument:

```apl
      2 × 3 + 4
14
```

This is `2 × (3 + 4)`, not `(2 × 3) + 4`. There's no precedence to memorise: just read right to left.

## Vectors

Type several numbers separated by spaces to create a **vector**:

```apl
      1 2 3 4 5
1 2 3 4 5
```

Arithmetic works element-wise on vectors:

```apl
      1 2 3 + 10 20 30
11 22 33
      2 × 1 2 3 4 5
2 4 6 8 10
```

When one argument is a scalar and the other is a vector, the scalar is paired with every element. This is called **scalar extension**:

```apl
      100 + 1 2 3
101 102 103
```

## Generating arrays with Iota

The `⍳` function (iota) generates a sequence of integers:

```apl
      ⍳5
1 2 3 4 5
      ⍳10
1 2 3 4 5 6 7 8 9 10
```

## Reduce

The `/` operator inserts a function between every element of a vector. `+/` sums a vector:

```apl
      +/ 1 2 3 4 5
15
      ×/ 1 2 3 4 5
120
```

`×/` computes a product — so `×/⍳5` gives you 5 factorial.

## Matrices

Use `⍴` (rho) to reshape a vector into a matrix. The left argument is the shape:

```apl
      3 4 ⍴ ⍳12
 1  2  3  4
 5  6  7  8
 9 10 11 12
```

This creates a 3-row, 4-column matrix filled with the numbers 1 to 12.

You can ask for an array's shape with monadic `⍴`:

```apl
      M ← 3 4 ⍴ ⍳12
      ⍴M
3 4
```

## Assigning names

The `←` arrow assigns a value to a name:

```apl
      prices ← 9.99 14.50 3.25 21.00
      prices
9.99 14.5 3.25 21
      +/prices
48.74
      total ← +/prices
      total
48.74
```

Names are case-sensitive. `M`, `m`, and `Matrix` are three different names.

## Defining functions

Curly braces `{}` define a **dfn** (direct function). Inside, `⍵` is the right argument and `⍺` is the optional left argument:

```apl
      double ← {2×⍵}
      double 5
10
      double 1 2 3
2 4 6
```

A dyadic dfn:

```apl
      avg ← {(+/⍵)÷⍴⍵}
      avg 3 5 7 9
6
```

## Saving your work

Give your workspace a name and save it:

```apl
      )wsid myfirst
      )save
```

Next time, load it back:

```apl
      )load myfirst
```

## What next?

- **New to APL?** Continue with the [beginner tutorials](../tutorials/beginners/index.md), starting with [Arrays](../tutorials/beginners/arrays.md)
- **Know APL already?** See [MARPLE for Dyalog Users](../tutorials/for-aplers/from-dyalog.md) or jump to the [Reference](../reference/index.md)
- **Want to see worked examples?** Try the [Worked Examples](../tutorials/worked-examples/index.md) section
