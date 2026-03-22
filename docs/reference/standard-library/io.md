# `$::io` -- File I/O

## `$::io::nread`

Monadic. Reads a text file and returns its contents as a character vector.

### Syntax

```apl
      $::io::nread 'path/to/file.txt'
```

### Arguments

- `⍵` -- character vector containing the file path.

### Result

A character vector with the file contents, including embedded newlines. Returns an empty vector if the file is empty.

### Example

```apl
      text ← $::io::nread '/tmp/hello.txt'
      ⍴text
13
```

## `$::io::nwrite`

Dyadic. Writes a character vector to a file.

### Syntax

```apl
      data $::io::nwrite 'path/to/file.txt'
```

### Arguments

- `⍺` -- character vector containing the data to write.
- `⍵` -- character vector containing the file path.

### Result

Empty vector (shape `0`).

### Example

```apl
      'Hello, world!' $::io::nwrite '/tmp/hello.txt'
```

Overwrites the file if it exists, creates it if it does not.

## Implementation

Both functions are thin wrappers around Python file I/O, exposed via i-beam:

```apl
      nread←{(⌶'marple.stdlib.io_impl.nread') ⍵}
      nwrite←{⍺ (⌶'marple.stdlib.io_impl.nwrite') ⍵}
```
