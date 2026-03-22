# Outer Product (`∘.f`)

## Syntax

```
X ∘.f Y
```

`f` is a dyadic scalar function. `X` and `Y` are arrays.

## Description

Applies `f` to every pair of elements, one from `X` and one from `Y`. The result shape is `(⍴X),(⍴Y)`, with element `[i;j]` equal to `X[i] f Y[j]`.

## Examples

Multiplication table:

```apl
      1 2 3 ∘.× 1 2 3 4
1 2  3  4
2 4  6  8
3 6  9 12
```

Addition table:

```apl
      1 2 3 ∘.+ 10 20 30 40
11 21 31 41
12 22 32 42
13 23 33 43
```

Equality table (character example):

```apl
      'abc' ∘.= 'abba'
1 0 0 1
0 1 1 0
0 0 0 0
```

## See also

- [Inner Product](inner-product.md) (`f.g`)
