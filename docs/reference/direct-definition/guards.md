# Guards

## Syntax

```apl
      {condition : result}
      {c1 : r1 ⋄ c2 : r2 ⋄ default}
```

## Description

A guard is `condition : expression` inside a dfn. If `condition` evaluates to 1 (true), `expression` is returned immediately and no further statements execute.

Multiple guards are checked top to bottom. The first true guard wins. If no guard fires, the last expression in the body is the result.

## Examples

```apl
      sign ← {⍵>0 : 1 ⋄ ⍵<0 : ¯1 ⋄ 0}
      sign 5
1
      sign ¯3
¯1
      sign 0
0
```

Absolute value:

```apl
      abs ← {⍵<0 : -⍵ ⋄ ⍵}
      abs ¯7
7
      abs 3
3
```

## Condition requirements

The condition must produce a scalar boolean (0 or 1).

## Evaluation order

Guards are evaluated in order from top to bottom. Once a guard fires, execution stops. Statements before a guard execute normally and can set local variables.

```apl
      {x←⍵×⍵ ⋄ x>100 : 'big' ⋄ 'small'} 5
small
      {x←⍵×⍵ ⋄ x>100 : 'big' ⋄ 'small'} 15
big
```

## See also

- [Dfns](dfns.md) -- dfn basics
- [Recursion](recursion.md) -- combining guards with `∇`
