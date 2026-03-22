# How to write tests that expect errors

Define a helper that catches an error and returns its code:

```apl
      #import $::error::ea
      #import $::error::en
      expect ← {'en 0' ea ⍵}
```

Then test that specific expressions produce specific errors:

```apl
      3 = expect '1÷0'
1
```

```apl
      6 = expect '10⌷⍳5'
1
```

```apl
      4 = expect '1 2+1 2 3'
1
```

The pattern works because `ea` catches the error and `en 0` returns its code. The comparison then checks for the expected error type.

See also: [Catch errors](catch-errors.md), [Check error codes](check-error-codes.md)
