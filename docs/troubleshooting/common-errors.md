# Common Errors

## SYNTAX ERROR (code 1)

The expression could not be parsed.

**Common causes:** unmatched braces or brackets, missing argument, invalid token, misplaced operator.

```apl
      1 + + 2
SYNTAX ERROR
```

## VALUE ERROR (code 2)

A name has no assigned value.

**Common causes:** typo in a function or variable name, using a name before assigning it.

```apl
      x + 1
VALUE ERROR: Undefined variable: x
```

## DOMAIN ERROR (code 3)

The function received an argument outside its domain.

**Common causes:** division by zero (`1÷0`), logarithm of zero or negative number, singular matrix in `⌹`.

```apl
      1÷0
DOMAIN ERROR: Division by zero
```

## LENGTH ERROR (code 4)

Array shapes do not match for a dyadic operation.

**Common causes:** `1 2 3 + 1 2` (different lengths), mismatched matrix dimensions in inner product.

```apl
      1 2 3 + 1 2
LENGTH ERROR: Shape mismatch: [3] vs [2]
```

## RANK ERROR (code 5)

The operation is not valid for the array's rank.

**Common causes:** applying `⌷` (From) to a scalar, transpose of rank > 2, monadic `⍳` on a non-scalar.

```apl
      1⌷5
RANK ERROR: requires non-scalar right argument
```

## INDEX ERROR (code 6)

An index is out of range.

**Common causes:** index larger than axis length, index less than or equal to 0 with `⎕IO←1`.

```apl
      V ← 1 2 3
      V[4]
INDEX ERROR
```

## SECURITY ERROR (code 9)

An I-Beam call was blocked by the allowlist.

**Cause:** the `MARPLE_IBEAM_ALLOW` environment variable is set and the requested module path is not on the allowlist.

## CLASS ERROR (code 11)

Attempt to change the name class of an existing binding (e.g., assigning an array to a name that currently holds a function).

```apl
      f ← {⍵+1}
      f ← 5
CLASS ERROR
```
