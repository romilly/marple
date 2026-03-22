# How to work with character arrays

In MARPLE, a string is a character vector -- each element is a single character:

```apl
      greeting ← 'Hello, world!'
      ⍴greeting
13
```

You can index, reverse, and reshape character vectors just like numeric ones:

```apl
      greeting[1]
H
```

```apl
      ⌽greeting
!dlrow ,olleH
```

## Character matrices

A table of strings is a character matrix. Rows are padded with spaces to equal length:

```apl
      names ← 3 5⍴'AliceBob  Clara'
```

This creates a 3-by-5 matrix where each row is a 5-character name.

## Case conversion

```apl
      $::str::upper 'hello'
HELLO
```

```apl
      $::str::lower 'HELLO'
hello
```

See also: [Trim whitespace](trim.md), [Standard library -- strings](../../reference/standard-library/str.md)
