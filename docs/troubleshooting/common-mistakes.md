# Common Mistakes

## Forgetting parentheses with rank

```apl
      ⌽⍤1 M           ⍝ WRONG: 1 and M form a strand used as the rank operand
      (⌽⍤1) M          ⍝ RIGHT: parentheses group the derived function
```

This is the most common mistake when using the rank operator. Always parenthesise `(f⍤k)`.

## Confusing reduce and compress

`/` has two meanings depending on context:

- **Operator** (after a function glyph): `+/V` -- reduce
- **Function** (with a left argument): `1 0 1/V` -- compress (replicate)

```apl
      +/1 2 3          ⍝ reduce: 6
      1 0 1/1 2 3      ⍝ compress: 1 3
```

## Shape mismatch in dyadic functions

Dyadic scalar functions require matching shapes (or one argument must be a scalar):

```apl
      1 2 3 + 1 2
LENGTH ERROR
```

```apl
      1 2 3 + 10
11 12 13
```

## Expecting nested arrays

MARPLE has flat arrays only. You cannot put an array inside an array:

```apl
      ⊂ 1 2 3          ⍝ ERROR: no ⊂ function
```

Use the rank operator instead of Each (`¨`):

```apl
      (f⍤1) M          ⍝ apply f to each row -- replaces f¨
```

## Index origin confusion

MARPLE defaults to `⎕IO←1`. If you are used to 0-origin:

```apl
      V ← 10 20 30
      V[0]             ⍝ INDEX ERROR with ⎕IO←1
      V[1]             ⍝ 10
```

## Right-to-left evaluation

APL evaluates right to left. This catches many newcomers:

```apl
      2×3+4            ⍝ 14, not 10 -- (3+4) is evaluated first
```

## Confusing assignment with comparison

`←` is assignment, `=` is comparison:

```apl
      x ← 5            ⍝ assigns 5 to x
      x = 5            ⍝ returns 1 (true)
```

## Name class conflicts

You cannot reuse a name that holds a function to store an array, or vice versa:

```apl
      f ← {⍵+1}
      f ← 42           ⍝ CLASS ERROR
```
