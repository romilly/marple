# Writing Your First Dfn

A **dfn** (direct function, pronounced "dee-fun") is how you define your own functions in MARPLE. It's a block of APL code in curly braces, with `⍵` for the right argument and `⍺` for the optional left argument.

## A simple dfn

```apl
      double ← {2 × ⍵}
      double 7
14
      double 1 2 3 4 5
2 4 6 8 10
```

The braces `{}` define the function. Inside, `⍵` (omega) refers to whatever argument you pass. The result of the last expression is the function's return value.

## Dyadic dfns

If you call a dfn with a left argument, it's available as `⍺` (alpha):

```apl
      add ← {⍺ + ⍵}
      3 add 4
7
```

A more useful example — a function to scale a vector to a given range:

```apl
      pct ← {100 × ⍵ ÷ ⍺}
      500 pct 50 100 250
10 20 50
```

## Default left argument

You can make a dfn work both monadically and dyadically by providing a default for `⍺`:

```apl
      avg ← {⍺ ← 1 ⋄ (+/⍵) ÷ ⍺ × ⍴⍵}
```

<!-- TODO: find a cleaner example for default ⍺ — perhaps a simpler one
     that shows the concept without overcomplicating the maths -->

The `⍺←1` line sets the default. If the function is called monadically, `⍺` is 1.

!!! note
    The `⋄` (diamond) separates expressions on the same line, like a semicolon in C or Python's newline.

## Guards: conditional logic

A **guard** is a condition followed by `:` and a result. If the condition is true (1), the result is returned and the function stops:

```apl
      abs ← {⍵ ≥ 0 : ⍵ ⋄ -⍵}
      abs 5
5
      abs ¯3
3
```

Read this as: "if `⍵ ≥ 0`, return `⍵`; otherwise, return `-⍵`".

Multiple guards chain naturally:

```apl
      sign ← {⍵ > 0 : 1 ⋄ ⍵ < 0 : ¯1 ⋄ 0}
      sign 42
1
      sign ¯7
¯1
      sign 0
0
```

## Local variables

Assignments inside a dfn are **local** — they don't affect the workspace:

```apl
      stats ← {
          total ← +/⍵
          n ← ⍴⍵
          total ÷ n
      }
      stats 10 20 30 40
25
      total
VALUE ERROR
```

`total` and `n` exist only inside the function. After the call, they're gone.

## Recursion with `∇`

Inside a dfn, `∇` (del) refers to the function itself, enabling recursion:

```apl
      fact ← {⍵ ≤ 1 : 1 ⋄ ⍵ × ∇ ⍵ - 1}
      fact 5
120
      fact 10
3628800
```

This reads: "if `⍵ ≤ 1`, return 1; otherwise, return `⍵` times the factorial of `⍵ - 1`".

## Dfns are values

A dfn is a value, just like a number or an array. You can assign it to a name, pass it to an operator, or use it inline:

```apl
      {⍵ × ⍵} 5
25
      {⍺ + ⍵}/ 1 2 3 4 5
15
```

The second example uses an anonymous dfn as the operand to reduce.

## No tradfns

If you've used other APLs, you may know **traditional function definition** using `∇`-headers, line numbers, and the Del editor. MARPLE doesn't have these. Dfns are the only way to define functions. They're simpler, composable, and lexically scoped.

## Key points

- Dfns are defined with `{}`, using `⍵` for the right argument and `⍺` for the left
- Guards (`condition : result`) provide conditional logic
- `⍺←value` provides a default left argument for optional dyadic use
- Variables assigned inside `{}` are local
- `∇` inside a dfn is the function itself (for recursion)
- Dfns are values — use them inline or pass them to operators
- MARPLE uses dfns exclusively; there are no traditional function definitions

**Next:** Ready for more? Continue to the [Intermediate Tutorials](../intermediate/index.md) for the rank operator, From indexing, and direct operators.
