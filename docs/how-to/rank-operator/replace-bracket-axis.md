# How to replace bracket-axis with rank

MARPLE does not have bracket-axis notation (`f[k]`). Use the rank operator instead:

| Traditional bracket-axis | Rank equivalent | Meaning |
|-------------------------|----------------|---------|
| `+/V` | `+/V` | Reduce along last axis (same) |
| `+/[1]M` | `(+/⍤¯1) M` | Reduce along first axis |
| `⌽[1]M` | `(⌽⍤¯1) M` | Reverse along first axis |

Negative rank means "complementary rank" -- the cell rank is computed as `array_rank + k`. So `⍤¯1` on a matrix (rank 2) gives cell rank 1, which means the frame is the first axis.

For user-defined functions, rank is the only option:

```apl
      myFn ← {⍵[⍋⍵]}
      (myFn⍤1) M
```

There is no bracket-axis equivalent for user dfns.

See also: [Apply to rows](apply-to-rows.md), [Rank operator reference](../../reference/operators/rank.md)
