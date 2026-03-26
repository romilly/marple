# How to write a text file

Use `⎕NWRITE` with the data on the left and the file path on the right:

```apl
      'Hello, world!' ⎕NWRITE '/path/to/output.txt'
```

The left argument is a character vector to write. The right argument is the file path.

## Write computed results

Format a numeric array with `⍕` before writing:

```apl
      (⍕ 1 2 3 4 5) ⎕NWRITE '/path/to/numbers.txt'
```

## Delete a file

```apl
      ⎕NDELETE '/path/to/output.txt'
```

See also: [Read a text file](read-text-file.md), [System Functions](../../reference/system/system-variables.md)
