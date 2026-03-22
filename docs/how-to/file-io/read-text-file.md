# How to read a text file

Use `$::io::nread` with the file path as a character vector:

```apl
      #import $::io::nread
      text ← nread '/path/to/file.txt'
```

The result is a character vector containing the entire file contents, including any newline characters.

You can also call it without importing:

```apl
      text ← $::io::nread '/path/to/file.txt'
```

## Check the length

```apl
      ⍴nread '/path/to/file.txt'
```

This returns the number of characters in the file.

See also: [Write a text file](write-text-file.md), [Standard library -- I/O](../../reference/standard-library/io.md)
