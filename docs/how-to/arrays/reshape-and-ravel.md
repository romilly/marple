# How to reshape and ravel arrays

## Reshape a vector into a matrix

```apl
      3 4 ⍴ ⍳12                 ⍝ 3 rows, 4 columns
```

## Create an array filled with a constant

```apl
      5 5 ⍴ 0                   ⍝ 5×5 matrix of zeros
      2 3 ⍴ 1                   ⍝ 2×3 matrix of ones
```

## Flatten any array to a vector

```apl
      , 3 4 ⍴ ⍳12               ⍝ ravel to a 12-element vector
```

## Reshape with recycling

```apl
      3 3 ⍴ 1 0                 ⍝ alternating 1s and 0s
```
