# Scalar Extension

When a scalar function is applied dyadically and one argument is a scalar while the other is an array, the scalar is **extended** to match the array's shape:

```apl
      10 + 1 2 3           ⍝ → 11 12 13
      (2 3⍴⍳6) × 10       ⍝ each element multiplied by 10
```

If both arguments are arrays, their shapes must match exactly. Mismatched non-scalar shapes cause a LENGTH ERROR.

Scalar extension applies to all scalar functions: arithmetic, comparison, and boolean.
