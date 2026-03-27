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

Dfns (direct functions), were first proposed by Ken Iverson. John Scholes introduced them in Dyalog APL in 1996.
Here's the mean declares as a dfn.

```apl
      mean ← {(+/⍵)÷⍴⍵}
```

Key differences:

- **Dynamic lookup** -- a dfn looks up names in the calling environment at runtime. Local assignments shadow outer names.
- **Guards instead of branching** -- `condition : result` replaces `→label`. No line numbers, no labels, no branch targets.
- **First-class values** -- dfns are values that can be assigned, passed to operators, and returned from other dfns.

## Why MARPLE uses dfns exclusively

MARPLE does not support traditional `∇`-header definitions. The reasons are both practical and philosophical:

**Simplicity.** One way to define functions means one set of scoping rules, one mental model, and less to learn.

**Composability.** Dfns work naturally with the rank operator and other higher-order constructs. A dfn is a value; a tradfn is a named procedure. Values compose; procedures don't.

**No branch.** The `→` primitive is the source of many bugs in traditional APL. Guards (`condition : result`) are clearer and less error-prone.

**Modern expectations.** First-class functions and clean scoping are standard in modern programming. Line-number-based flow control is not.

## What you lose

Tradfns can be easier to read for long, step-by-step procedures. They support local variables declared in the header and multi-line editing in the Del editor. If you're coming from Dyalog or GNU APL and rely heavily on tradfns, you'll need to restructure your code as dfns -- though most APL programmers who try dfns prefer them.
