# How to write a text file

Use `$::io::nwrite` with the data on the left and the file path on the right:

```apl
      #import $::io::nwrite
      'Hello, world!' nwrite '/path/to/output.txt'
```

The left argument is a character vector to write. The right argument is the file path.

You can also use the fully qualified name:

```apl
      'Hello, world!' $::io::nwrite '/path/to/output.txt'
```

## Write computed results

Format a numeric array with `⍕` before writing:

```apl
      (⍕ 1 2 3 4 5) nwrite '/path/to/numbers.txt'
```

See also: [Read a text file](read-text-file.md), [Standard library -- I/O](../../reference/standard-library/io.md)
