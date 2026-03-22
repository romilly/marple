# How to use escape sequences

!!! note
    `$::str::u` is not yet implemented. This page will be expanded when escape sequence support is added.

Currently, MARPLE string literals are plain character vectors. What you type between quotes is exactly what you get -- there are no escape sequences like `\n` or `\t` within string literals.

To include a quote character within a string, double it:

```apl
      'it''s'
it's
```

See also: [Character arrays](character-arrays.md)
