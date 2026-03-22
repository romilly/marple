# How to catch errors with ea

`$::error::ea` (Execute Alternate) tries an expression and falls back to an alternative if it fails. Both arguments are character vectors containing APL expressions:

```apl
      #import $::error::ea
      '0' ea '2+3'
5
```

```apl
      '0' ea '1÷0'
0
```

The right argument is evaluated first. If it succeeds, its result is returned. If it raises an error, the left argument is evaluated instead.

## Return the error code on failure

```apl
      'en 0' ea '1÷0'
3
```

Here `en 0` returns the error number of the most recent error (DOMAIN ERROR = 3).

See also: [Check error codes](check-error-codes.md), [Test for errors](test-for-errors.md)
