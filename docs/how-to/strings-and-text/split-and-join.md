# How to split and join strings

!!! note
    `$::str::split` and `$::str::join` are not yet implemented. This page documents what is currently available for string manipulation.

## Available string operations

You can work with character vectors using the implemented primitives:

**Select a substring with take and drop:**

```apl
      5↑'Hello, world!'
Hello
```

```apl
      7↓'Hello, world!'
world!
```

**Concatenate strings:**

```apl
      'Hello',', ','world!'
Hello, world!
```

**Find a character in a string:**

```apl
      'Hello, world!'⍳'o'
5
```

See also: [Character arrays](character-arrays.md), [Trim whitespace](trim.md)
