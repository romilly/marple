# How to check error codes with en

`$::error::en` returns the error code of the most recent error caught by `ea`, or 0 if no error has occurred:

```apl
      #import $::error::ea
      #import $::error::en
      en 0
0
```

After catching an error:

```apl
      '0' ea '1÷0'
0
      en 0
3
```

## Error code reference

| Code | Error |
|------|-------|
| 1 | SYNTAX ERROR |
| 2 | VALUE ERROR |
| 3 | DOMAIN ERROR |
| 4 | LENGTH ERROR |
| 5 | RANK ERROR |
| 6 | INDEX ERROR |
| 7 | LIMIT ERROR |
| 9 | SECURITY ERROR |
| 11 | CLASS ERROR |

!!! note
    `en` requires a dummy right argument (any value). Use `en 0`.

See also: [Catch errors](catch-errors.md), [Common errors](../../troubleshooting/common-errors.md)
