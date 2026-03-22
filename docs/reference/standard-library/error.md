# `$::error` -- Error Handling

## `$::error::ea` -- Execute Alternate

Dyadic. Both arguments are character vectors containing APL expressions. Tries the right expression; if it raises an APL error, evaluates the left expression instead.

### Syntax

```apl
      'fallback' $::error::ea 'expression'
```

### Examples

```apl
      '0' $::error::ea '2+3'
5
      '0' $::error::ea '1÷0'
0
```

The error code from a caught error is stored for `$::error::en`:

```apl
      '¯1' $::error::ea '1÷0'
¯1
      $::error::en 0
3
```

### Notes

Both arguments are evaluated as strings, not as APL values. This is similar to Dyalog's `⎕EA`.

## `$::error::en` -- Error Number

Monadic. Returns the error code of the most recent caught error, or 0 if no error has occurred. The argument is ignored (pass any scalar).

### Syntax

```apl
      $::error::en 0
```

### Error codes

| Code | Error |
|------|-------|
| 1 | SYNTAX ERROR |
| 2 | VALUE ERROR |
| 3 | DOMAIN ERROR |
| 4 | LENGTH ERROR |
| 5 | RANK ERROR |
| 6 | INDEX ERROR |
| 7 | LIMIT ERROR |
| 8 | WS FULL |
| 9 | SECURITY ERROR |
| 10 | DEPENDENCY ERROR |
| 11 | CLASS ERROR |

## Implementation

```apl
      ea←{⍺ (⌶'marple.stdlib.error_impl.ea') ⍵}
      en←{(⌶'marple.stdlib.error_impl.en') ⍵}
```
