# Reading APL Right to Left

APL's evaluation rule is simpler than any other programming language: **every function takes everything to its right as its right argument**. There is no operator precedence. No exceptions.

## The rule

In an expression like:

```apl
      2 × 3 + 4
14
```

This is evaluated as `2 × (3 + 4)`, giving 14. The `+` takes `3` and `4`, producing `7`. Then `×` takes `2` and `7`, producing `14`.

In a language with precedence (like Python or C), `2 * 3 + 4` would be `(2 * 3) + 4 = 10`. APL doesn't do this. Every function is equal — `×` doesn't bind tighter than `+`.

## Reading longer expressions

Read from right to left, one function at a time:

```apl
      +/ 2 × ⍳5
30
```

1. `⍳5` → `1 2 3 4 5`
2. `2 × 1 2 3 4 5` → `2 4 6 8 10`
3. `+/ 2 4 6 8 10` → `30`

Another example:

```apl
      ⌈/ | ¯3 5 ¯7 2
7
```

1. `¯3 5 ¯7 2` — the data
2. `| ¯3 5 ¯7 2` → `3 5 7 2` — absolute values
3. `⌈/ 3 5 7 2` → `7` — maximum

## When you need parentheses

Sometimes right-to-left isn't what you want. Parentheses override, just as in mathematics:

```apl
      (2+3) × 4
20
      2 + 3 × 4
14
```

A common pattern: using the result of a monadic function as a left argument:

```apl
      (⍴M) ⍴ 0        ⍝ create a zero-filled array the same shape as M
```

Without parentheses, `⍴ M ⍴ 0` would try to reshape `0` into shape `M`, which isn't the intent.

## Functions are monadic or dyadic

A function with a left argument is **dyadic**. Without one, it's **monadic**. The same symbol often means different things:

```apl
      ⍴ 1 2 3          ⍝ monadic ⍴: shape → 3
      2 3 ⍴ 1 2 3      ⍝ dyadic ⍴: reshape → 2 3 matrix
```

How does APL know which? A function is dyadic if there's a value (or a closing parenthesis) immediately to its left. Otherwise it's monadic. This falls naturally out of right-to-left evaluation.

## Operators bind first

There's one thing that does have binding priority: **operators bind tighter than function application**. When you write `+/ V`, the `/` binds to `+` first (forming the derived function `+/`), and then `+/` is applied to `V`.

This matters with the rank operator:

```apl
      (⌽⍤1) M         ⍝ correct: ⍤ binds to 1, then (⌽⍤1) is applied to M
      ⌽⍤1 M           ⍝ wrong: ⍤ binds to the strand (1 M)
```

Always parenthesise when using rank. See [Common Mistakes](../../troubleshooting/common-mistakes.md) for more on this.

## The binding hierarchy

From tightest to loosest:

1. **Bracket indexing** — `M[i;j]`
2. **Operator binding** — `+/`, `⌽⍤1`, `∘.×`
3. **Strand formation** — `1 2 3` (numbers separated by spaces form a vector)
4. **Function application** — `f Y` or `X f Y`
5. **Assignment** — `name ← value`

In practice, you rarely think about this explicitly. The right-to-left rule, plus parentheses when needed, handles almost everything.

## Key points

- APL evaluates right to left, with no precedence among functions
- Every function takes everything to its right as its right argument
- Use parentheses when you need a different grouping
- Operators (`/`, `\`, `⍤`) bind to their operands before function application
- This rule is simpler than precedence — there's only one rule to learn

**Next:** [Writing Your First Dfn](first-dfn.md)
