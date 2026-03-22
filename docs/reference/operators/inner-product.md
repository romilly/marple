# Inner Product (`f.g`)

## Syntax

```
X f.g Y
```

`f` and `g` are dyadic scalar functions. `X` and `Y` are arrays.

## Description

Generalised inner product. Applies `g` to corresponding pairs along the last axis of `X` and the first axis of `Y`, then reduces the results with `f`.

The classic case is `+.×` (matrix multiply / dot product).

## Vector dot product

```apl
      1 2 3 +.× 4 5 6
32
```

Computes `(1×4)+(2×5)+(3×6)`.

## Matrix multiply

```apl
      (2 3⍴⍳6) +.× 3 2⍴⍳6
22 28
49 64
```

The left array has shape 2 3, the right has shape 3 2, and the result has shape 2 2.

## Other inner products

You can use any pair of dyadic functions. For example, `∧.=` tests whether two vectors are identical element-wise:

```apl
      1 2 3 ∧.= 1 2 3
1
      1 2 3 ∧.= 1 2 4
0
```

## Shape rules

| Left shape | Right shape | Result shape |
|-----------|------------|-------------|
| `n` | `n` | scalar |
| `m n` | `n p` | `m p` |
| `n` | `n p` | `p` |

The last axis of the left argument must equal the first axis of the right argument (LENGTH ERROR otherwise).

## See also

- [Outer Product](outer-product.md) (`∘.f`)
