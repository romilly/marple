# Direct Functions in Depth

The [beginner tutorial](../beginners/first-dfn.md) introduced dfns. This tutorial covers the details: scoping rules, guard patterns, recursion techniques, and common idioms.

## Scoping rules

Dfns use **lexical scope**. A variable assigned inside a dfn is local. An unassigned name looks outward through enclosing dfns to the workspace:

```apl
      x ← 100
      f ← {y ← 10 ⋄ x + y + ⍵}
      f 1
111
```

`y` is local to `f`. `x` is found in the workspace.

Nested dfns see their enclosing scope:

```apl
      outer ← {
          scale ← ⍵
          {scale × ⍵}
      }
      double ← outer 2
      double 5
10
```

The inner dfn looks up `scale` from the calling environment via dynamic lookup.

## Guard patterns

### Multiple conditions

Guards are checked top to bottom. The first true guard returns:

```apl
      classify ← {
          ⍵ < 0   : 'negative'
          ⍵ = 0   : 'zero'
          'positive'
      }
```

The last expression (no guard) is the default — reached only if all guards are false.

### Guards with scalar arguments only

<!-- TODO: discuss behaviour of guards with array arguments — does the guard
     require a scalar boolean? What happens with a vector condition? -->

Guards expect a scalar boolean (0 or 1). If the condition produces an array, this is an error.

## Recursion patterns

### Simple recursion

```apl
      fact ← {⍵ ≤ 1 : 1 ⋄ ⍵ × ∇ ⍵ - 1}
```

### Accumulator pattern

```apl
      fact ← {⍺ ← 1 ⋄ ⍵ ≤ 1 : ⍺ ⋄ (⍺×⍵) ∇ ⍵-1}
```

The default `⍺←1` lets it be called monadically. The left argument accumulates the result.

### Recursion on arrays

```apl
      ⍝ Quicksort
      qsort ← {1≥⍴⍵ : ⍵ ⋄ (∇ ⍵/⍨⍵<p) , (⍵/⍨⍵=p) , ∇ ⍵/⍨⍵>p←⍵[1]}
```

<!-- TODO: verify this quicksort works in MARPLE — test with actual REPL -->

## Common idioms

### Identity / default

```apl
      {⍵}               ⍝ identity (right tack equivalent)
      {⍺ ← 0 ⋄ ⍺ + ⍵}  ⍝ add with default left arg of 0
```

### Pipeline style

```apl
      process ← {
          data ← clean ⍵
          data ← transform data
          summarise data
      }
```

Each step assigns to `data`, threading the computation through.

### Anonymous dfns

Dfns don't have to be named:

```apl
      {⍵ × ⍵} 5         ⍝ square, inline
25
      {⍺ + ⍵}/ ⍳10      ⍝ anonymous dfn as operand to reduce
55
```

## Key points

- Dfns use dynamic lookup — inner dfns look up names in the calling environment
- Guards are checked top to bottom; the last unguarded expression is the default
- `∇` enables recursion; use an accumulator pattern for tail-style recursion
- Dfns are values: assign them, pass them to operators, use them inline

**Next:** [Direct Operators](dops.md)
