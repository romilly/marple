# Dfns (Direct Functions)

## Syntax

```apl
      {body}             ⍝ anonymous dfn
      name ← {body}      ⍝ named dfn
```

## Arguments

- `⍵` -- right argument (always available)
- `⍺` -- left argument (available in dyadic calls)

## Default left argument

Use `⍺←value` to provide a default for `⍺`. If the dfn is called monadically, `⍺` takes the default value. If called dyadically, the default is ignored.

```apl
      f ← {⍺←10 ⋄ ⍺+⍵}
      f 3
13
      5 f 3
8
```

## Body

The body is a sequence of statements separated by `⋄` (diamond). The value of the last evaluated expression is the result.

```apl
      {⍵×⍵} 5
25
      3 {⍺+⍵} 4
7
```

## Assignment inside dfns

You can assign local variables inside a dfn body. These are scoped to the dfn.

```apl
      {x←⍵×⍵ ⋄ x+1} 5
26
```

## Scoping

Dfns use **lexical scope**. Assignments inside `{}` create local bindings. Unresolved names look outward through enclosing dfns to the workspace.

```apl
      scale ← 10
      {scale × ⍵} 3
30
```

## Multiple statements

Separate statements with `⋄`. The last expression's value is returned.

```apl
      {a←⍵+1 ⋄ b←⍵×2 ⋄ a+b} 5
16
```

## See also

- [Guards](guards.md) -- conditional returns
- [Recursion](recursion.md) -- self-reference with `∇`
- [Dops](dops.md) -- direct operators
