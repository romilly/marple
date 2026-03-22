# Reshape and Iota — Building Arrays

Two functions you'll use constantly: `⍳` (iota) to generate sequences and `⍴` (rho) to shape them.

## Iota: generating sequences

Monadic `⍳` generates integers from 1 to its argument:

```apl
      ⍳6
1 2 3 4 5 6
      ⍳1
1
```

!!! note
    MARPLE's default index origin is 1 (`⎕IO←1`), so `⍳5` starts at 1. Some APLs default to 0.

Iota is often the starting point for building data:

```apl
      2 × ⍳5
2 4 6 8 10
      (⍳5) * 2
1 4 9 16 25
```

## Reshape: `⍴`

Dyadic `⍴` reshapes data into a given shape:

```apl
      3 4 ⍴ ⍳12
 1  2  3  4
 5  6  7  8
 9 10 11 12
```

If you provide fewer elements than needed, they **recycle**:

```apl
      3 3 ⍴ 1 0
1 0 1
0 1 0
1 0 1
      2 5 ⍴ 0
0 0 0 0 0
0 0 0 0 0
```

This is useful for creating arrays filled with a constant, identity-like patterns, or repeating sequences.

## Shape: asking about dimensions

Monadic `⍴` returns the shape of an array:

```apl
      ⍴ 'Hello'
5
      ⍴ 3 4 ⍴ ⍳12
3 4
      ⍴ 2 3 4 ⍴ ⍳24
2 3 4
```

The number of elements in the shape tells you the rank:

```apl
      ⍴⍴ 3 4 ⍴ ⍳12
2
```

## Ravel: `,`

Monadic `,` (ravel) flattens any array into a vector:

```apl
      M ← 2 3 ⍴ ⍳6
      , M
1 2 3 4 5 6
```

## Catenate: `,`

Dyadic `,` joins arrays along the last axis:

```apl
      1 2 3 , 4 5 6
1 2 3 4 5 6
      (2 3⍴⍳6) , (2 2⍴10 20 30 40)
 1  2  3 10 20
 4  5  6 30 40
```

## Putting it together

These building blocks combine naturally:

```apl
      ⍝ A multiplication table
      (⍳5) ∘.× (⍳5)
 1  2  3  4  5
 2  4  6  8 10
 3  6  9 12 15
 4  8 12 16 20
 5 10 15 20 25

      ⍝ Count of elements
      ×/ ⍴ 3 4 5 ⍴ 0
60
```

## Key points

- `⍳N` generates the integers 1 through N
- `shape ⍴ data` reshapes data into the given dimensions (recycling if needed)
- `⍴ array` returns the shape; `⍴⍴ array` returns the rank
- `,` ravels (monadic) or catenates (dyadic)
- These functions are the basic toolkit for creating and exploring arrays

**Next:** [Reading APL Right to Left](right-to-left.md)
