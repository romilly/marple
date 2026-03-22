# `$::str` -- String Utilities

## `$::str::upper`

Monadic. Converts each character to uppercase.

```apl
      $::str::upper 'hello'
HELLO
```

Preserves shape. Non-letter characters are unchanged.

## `$::str::lower`

Monadic. Converts each character to lowercase.

```apl
      $::str::lower 'HELLO'
hello
```

Preserves shape. Non-letter characters are unchanged.

## `$::str::trim`

Monadic. Removes leading and trailing whitespace from a character vector.

```apl
      $::str::trim '  hello  '
hello
```

The result length matches the trimmed string.

## Implementation

All three are i-beam wrappers around Python string methods:

```apl
      upper←{(⌶'marple.stdlib.str_impl.upper') ⍵}
      lower←{(⌶'marple.stdlib.str_impl.lower') ⍵}
      trim←{(⌶'marple.stdlib.str_impl.trim') ⍵}
```
