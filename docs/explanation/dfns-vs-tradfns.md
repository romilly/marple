# Direct Definition -- Why Not Tradfns

## Traditional function definition

Traditional APL function definition uses `∇`-headers, line numbers, and the Del editor:

```
∇ R←MEAN X
[1] R←(+/X)÷⍴X
∇
```

This style dates from the 1960s when APL ran on line-oriented terminals. It relies on dynamic scope, mutable line numbers, and `→` (branch) for flow control.

## Dfns: the modern alternative

Dfns (direct functions), introduced by John Scholes for Dyalog APL in 1996, replace all of that:

```apl
      mean ← {(+/⍵)÷⍴⍵}
```

Key differences:

- **Lexical scope** -- a dfn sees the variables that existed where it was defined, not where it's called. This makes code easier to reason about and eliminates accidental name collisions.
- **Closures** -- dfns capture their defining environment, so they compose naturally with operators.
- **Guards instead of branching** -- `condition : result` replaces `→label`. No line numbers, no labels, no branch targets.
- **First-class values** -- dfns are values that can be assigned, passed to operators, and returned from other dfns.

## Why MARPLE uses dfns exclusively

MARPLE does not support traditional `∇`-header definitions. The reasons are both practical and philosophical:

**Simplicity.** One way to define functions means one set of scoping rules, one mental model, and less to learn.

**Composability.** Dfns work naturally with the rank operator and other higher-order constructs. A dfn is a value; a tradfn is a named procedure. Values compose; procedures don't.

**No branch.** The `→` primitive is the source of many bugs in traditional APL. Guards (`condition : result`) are clearer and less error-prone.

**Modern expectations.** Lexical scope, closures, and first-class functions are standard in modern programming. Dynamic scope and line-number-based flow control are not.

## What you lose

Tradfns can be easier to read for long, step-by-step procedures. They support local variables declared in the header and multi-line editing in the Del editor. If you're coming from Dyalog or GNU APL and rely heavily on tradfns, you'll need to restructure your code as dfns -- though most APL programmers who try dfns prefer them.
