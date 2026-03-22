# Direct Operators

A **dop** (direct operator) is a dfn that defines an operator rather than a function. It takes one or two function operands and produces a derived function.

## Recognising a dop

MARPLE detects a dop by the presence of `⍺⍺` (left operand) or `⍵⍵` (right operand) in the body. If the body contains `⍺⍺` or `⍵⍵`, it's a dop. Otherwise, it's a dfn.

## Monadic operators (one operand)

A monadic operator takes one operand (`⍺⍺`) and produces a derived function:

```apl
      twice ← {(⍺⍺ ⍺⍺ ⍵)}
      -twice 5
5
      ⌽twice 1 2 3 4
1 2 3 4
```

`twice` applies its operand function two times. `-twice 5` negates twice (identity). `⌽twice` reverses twice (identity for vectors).

A more practical example — apply a function and return both the argument and result:

```apl
      show ← {⍵ , ⍺⍺ ⍵}
      (×/)show ⍳5
1 2 3 4 5 120
```

<!-- TODO: verify these examples in the REPL — the show example may need
     adjustment depending on how MARPLE handles shape mismatches in catenation -->

## Dyadic operators (two operands)

A dyadic operator uses both `⍺⍺` and `⍵⍵`:

```apl
      between ← {(⍵⍵ ⍵) - ⍺⍺ ⍵}
      (⌊ between ⌈) 3.7
1
```

<!-- TODO: better examples of dyadic dops — perhaps a compose or a pipe operator -->

## The derived function

The result of applying an operator to its operands is a **derived function**. This derived function is called with `⍺` (left argument) and `⍵` (right argument), just like any dfn:

```apl
      apply_to_rows ← {(⍺⍺⍤1) ⍵}
      ⌽ apply_to_rows 3 4⍴⍳12
 4  3  2  1
 8  7  6  5
12 11 10  9
```

`apply_to_rows` is a monadic operator. `⌽ apply_to_rows` is the derived function (equivalent to `⌽⍤1`). It's applied to the matrix as `⍵`.

## Practical example: timing

```apl
      ⍝ An operator that times its operand function
      timed ← {
          ⍝ Placeholder — would need i-beam for actual timing
          result ← ⍺⍺ ⍵
          result
      }
```

<!-- TODO: flesh out with actual timing using i-beam once that's available -->

## Key points

- A dop is detected by the presence of `⍺⍺` or `⍵⍵` in the body
- `⍺⍺` is the left operand (always present); `⍵⍵` is the right operand (makes it dyadic)
- The derived function uses `⍺` and `⍵` for its own arguments
- Dops let you write reusable higher-order tools that work with any function

**Next:** [Workspaces and Namespaces](workspaces-and-namespaces.md)
