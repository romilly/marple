# How to read a file into a matrix

!!! note
    `$::str::v2m` is not yet implemented. This page describes the planned approach and a manual workaround.

## Planned usage

Once `v2m` is available, you will be able to split a file into a character matrix with one row per line:

```apl
      #import $::io::nread
      #import $::str::v2m
      data ← v2m nread '/path/to/file.txt'
```

## Current workaround

You can read the file as a character vector and process it using the available primitives:

```apl
      #import $::io::nread
      text ← nread '/path/to/file.txt'
```

See also: [Read a text file](read-text-file.md)
