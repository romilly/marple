# How to read a text file

Use `⎕NREAD` with the file path as a character vector:

```apl
      text ← ⎕NREAD '/path/to/file.txt'
```

The result is a character vector containing the entire file contents, including any newline characters.

## Check the length

```apl
      ⍴ ⎕NREAD '/path/to/file.txt'
```

This returns the number of characters in the file.

## Check if a file exists first

```apl
      ⎕NEXISTS '/path/to/file.txt'
1
```

See also: [Write a text file](write-text-file.md), [System Functions](../../reference/system/system-variables.md)
