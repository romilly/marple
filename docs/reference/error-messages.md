# Error Messages

## Error codes

| Code | Name | Common causes |
|------|------|---------------|
| 1 | SYNTAX ERROR | Malformed expression, unmatched brackets or braces, unexpected token |
| 2 | VALUE ERROR | Undefined name, use of `⍵` or `⍺` outside a dfn |
| 3 | DOMAIN ERROR | Invalid argument (division by zero, wrong type, unknown function) |
| 4 | LENGTH ERROR | Mismatched shapes in dyadic operation, inner product length mismatch |
| 5 | RANK ERROR | Wrong rank for the operation (e.g. From on a scalar, transpose of rank >2) |
| 6 | INDEX ERROR | Index out of range for `⌷` or bracket indexing |
| 7 | LIMIT ERROR | Implementation limit exceeded |
| 8 | WS FULL | Out of memory |
| 9 | SECURITY ERROR | I-beam path not allowed by `MARPLE_IBEAM_ALLOW` |
| 10 | DEPENDENCY ERROR | Circular import detected |
| 11 | CLASS ERROR | Attempting to change the type of a name (e.g. array to function) |

## Using error codes

Error codes are accessible via `$::error::en` after catching an error with `$::error::ea`:

```apl
      #import $::error::ea as ea
      #import $::error::en as en
      '0' ea '1÷0'
0
      en 0                ⍝ 3 = DOMAIN ERROR
3
```

See [Error Handling](../how-to/error-handling/catch-errors.md) for more details.

See [Common Errors](../troubleshooting/common-errors.md) for diagnosis and solutions.
