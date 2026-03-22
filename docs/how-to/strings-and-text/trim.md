# How to trim whitespace

Use `$::str::trim` to remove leading and trailing whitespace from a character vector:

```apl
      $::str::trim '  hello  '
hello
```

You can also import it for shorter syntax:

```apl
      #import $::str::trim
      trim '  hello  '
hello
```

The result is a character vector with the whitespace stripped from both ends.

See also: [Character arrays](character-arrays.md), [Standard library -- strings](../../reference/standard-library/str.md)
