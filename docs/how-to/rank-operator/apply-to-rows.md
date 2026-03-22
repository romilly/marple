# How to apply a function to each row

Use rank 1 to apply a function to each row (1-cell) of a matrix:

```apl
      M ← 3 4⍴⍳12
      (⌽⍤1) M
 4  3  2  1
 8  7  6  5
12 11 10  9
```

```apl
      (+/⍤1) M
10 26 42
```

```apl
      ({⍵[⍋⍵]}⍤1) M
1  2  3  4
5  6  7  8
9 10 11 12
```

!!! warning
    Always parenthesise the derived function: `(f⍤1) M`, not `f⍤1 M`. Without parentheses, `1 M` forms a strand that becomes the rank operand.

See also: [Apply to columns](apply-to-columns.md), [Replace bracket-axis](replace-bracket-axis.md)
