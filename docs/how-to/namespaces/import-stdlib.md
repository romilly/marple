# How to import standard library functions

## Fully qualified access

Call any standard library function directly using its full path:

```apl
      $::str::trim '  hello  '
hello
```

## Import by name

Use `#import` to bind a function to a local name:

```apl
      #import $::str::trim
      trim '  hello  '
hello
```

## Import with an alias

```apl
      #import $::str::trim as strip
      strip '  hello  '
hello
```

## List functions in a namespace

```apl
      )fns $::str
lower  trim  upper
```

## Available namespaces

- `$::str` -- string utilities (trim, upper, lower)
- `$::error` -- error handling (ea, en)

File I/O uses system functions: `⎕NREAD`, `⎕NWRITE`, `⎕NEXISTS`, `⎕NDELETE`.

See also: [Standard library reference](../../reference/standard-library/index.md)
