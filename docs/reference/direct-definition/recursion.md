# Recursion (`∇`)

## Syntax

Inside a dfn, `∇` refers to the dfn itself.

## Monadic recursion

```apl
      fact ← {⍵≤1 : 1 ⋄ ⍵×∇ ⍵-1}
      fact 5
120
```

## Dyadic recursion

For dyadic recursive calls, `∇` is called with a left argument:

```apl
      gcd ← {⍵=0 : ⍺ ⋄ ⍵ ∇ ⍵|⍺}
      12 gcd 8
4
```

## Fibonacci

```apl
      fib ← {⍵≤1 : ⍵ ⋄ (∇ ⍵-1)+∇ ⍵-2}
      fib 10
55
```

## Notes

`∇` refers to the current dfn, enabling anonymous recursion. Named dfns can also call themselves by name.

## See also

- [Dfns](dfns.md) -- dfn basics
- [Guards](guards.md) -- conditional returns
