# How to select rows, columns, and elements

## Select rows from a matrix

```apl
      M ← 4 5⍴⍳20
      2 ⌷ M                     ⍝ row 2
      1 3 ⌷ M                   ⍝ rows 1 and 3
      M[2;]                     ⍝ bracket indexing equivalent
```

## Select columns from a matrix

```apl
      3 (⌷⍤0 1) M               ⍝ column 3
      2 4 (⌷⍤1) M               ⍝ columns 2 and 4
      M[;3]                      ⍝ bracket indexing equivalent
```

## Select a single element

```apl
      3 ⌷ 2 ⌷ M                 ⍝ row 2, column 3 using From
      M[2;3]                     ⍝ bracket indexing equivalent
```

## Select a rectangular cross-section

```apl
      2 4 (⌷⍤1) 1 3 ⌷ M        ⍝ rows 1,3 × columns 2,4
      M[1 3; 2 4]               ⍝ bracket indexing equivalent
```

See also: [Indexing with From](../../tutorials/intermediate/from-indexing.md) for a full explanation.
