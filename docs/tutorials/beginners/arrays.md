# Arrays — Scalars, Vectors, Matrices

In APL, **everything is an array**. There are no separate types for single numbers, lists, and tables — they're all arrays of different **rank** (number of dimensions).

## Scalars

A scalar is a single value — a number or a character. It has rank 0.

```apl
      42
42
      'A'
A
```

## Vectors

A vector is a one-dimensional sequence of values. Type numbers separated by spaces:

```apl
      1 2 3 4 5
1 2 3 4 5
```

A character vector (string) is written with single quotes:

```apl
      'Hello'
Hello
```

You can find the number of elements in a vector with `⍴` (rho — shape):

```apl
      ⍴ 1 2 3 4 5
5
      ⍴ 'Hello'
5
```

## Matrices

A matrix is a two-dimensional array with rows and columns. You create one by **reshaping** a vector:

```apl
      2 3 ⍴ 1 2 3 4 5 6
1 2 3
4 5 6
```

The left argument to `⍴` is the desired shape (2 rows, 3 columns). The right argument provides the data.

```apl
      ⍴ 2 3 ⍴ 1 2 3 4 5 6
2 3
```

The shape of a matrix is a 2-element vector: rows and columns.

## Higher-rank arrays

Arrays can have three or more dimensions. A rank-3 array has planes, rows, and columns:

```apl
      2 3 4 ⍴ ⍳24
 1  2  3  4
 5  6  7  8
 9 10 11 12

13 14 15 16
17 18 19 20
21 22 23 24
```

!!! note
    MARPLE displays planes separated by a blank line.

## Rank: the number of dimensions

The **rank** of an array is how many dimensions it has:

| Array | Rank | Shape example |
|-------|------|---------------|
| Scalar | 0 | (empty) |
| Vector | 1 | `5` |
| Matrix | 2 | `3 4` |
| Cube | 3 | `2 3 4` |

You can find the rank of an array with `⍴⍴` (shape of the shape):

```apl
      ⍴⍴ 42
0
      ⍴⍴ 1 2 3
1
      ⍴⍴ 2 3 ⍴ ⍳6
2
```

<!-- TODO: verify that ⍴⍴ of a scalar returns 0 (empty numeric vector displayed as blank line?
     or does MARPLE display it differently?) — confirm with actual REPL output -->

## Flat arrays

MARPLE uses **flat arrays**: every element is a simple scalar (a number or a character). There are no arrays inside arrays (no nesting). This is different from Dyalog APL and APL2, which allow nested arrays.

If you're coming from another APL, see [How MARPLE Differs](../../explanation/comparison.md) for details on what this means in practice.

## Key points

- Everything in APL is an array
- Arrays have a **shape** (found with `⍴`) and a **rank** (number of dimensions)
- Vectors are rank 1, matrices are rank 2, and so on
- MARPLE arrays are **flat** — elements are always simple scalars
- Data is stored in **row-major order** (last axis varies fastest)

**Next:** [Scalar Functions and Scalar Extension](scalar-functions.md)
