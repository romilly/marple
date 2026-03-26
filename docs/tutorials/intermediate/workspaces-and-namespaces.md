# Workspaces and Namespaces

As your MARPLE code grows, you need ways to organise it. Workspaces save and load your session. Namespaces group functions into directories. The standard library (`$:`) provides built-in utilities.

## Workspaces

A workspace is a snapshot of your defined functions and variables.

### Saving and loading

```apl
      )wsid myproject          ⍝ name the workspace
      )save                    ⍝ save to disk
      )load myproject          ⍝ load it back
      )lib                     ⍝ list available workspaces
```

Workspaces are saved as directories containing `.apl` files — one per function. This means they're plain text, version-controllable, and easy to inspect.

### Managing the workspace

```apl
      )fns                     ⍝ list all functions
      )vars                    ⍝ list all variables
      )clear                   ⍝ remove everything
```

## Namespaces

A namespace is a subdirectory within a workspace. Functions in the `utils/` subdirectory belong to the `utils` namespace.

### Directory structure

```
myproject/
  main.apl              ⍝ top-level function
  utils/
    trim.apl            ⍝ utils:trim
    pad.apl             ⍝ utils:pad
  math/
    stats/
      mean.apl          ⍝ math:stats:mean
```

### Calling namespaced functions

Use colon-separated qualified names:

```apl
      utils:trim '  hello  '
      math:stats:mean data
```

!!! note "Why colon, not dot?"
    The dot (`.`) is APL's inner-product operator. `foo.bar` where `foo` and `bar` are functions is a legitimate inner product. The colon is unambiguous — it has no other infix meaning in APL.

### Listing namespace contents

```apl
      )fns utils             ⍝ functions in the utils namespace
      )fns math:stats        ⍝ functions in math:stats
```

## The standard library (`$:`)

MARPLE provides a built-in system workspace referenced by `$`. It contains utility functions organised into namespaces:

```apl
      $::str::trim '  hello  '          ⍝ trim whitespace
      ⎕NREAD '/tmp/data.txt'            ⍝ read a file (system function)
```

`$` is always available, regardless of your current workspace. File I/O uses system functions (`⎕NREAD`, `⎕NWRITE`, `⎕NEXISTS`, `⎕NDELETE`) rather than the standard library.

### Available standard library namespaces

| Namespace | Purpose |
|-----------|---------|
| `$::str` | String utilities — `trim`, `upper`, `lower` |
| `$::error` | Error handling — `ea`, `en` |

See the [Standard Library Reference](../../reference/standard-library/index.md) for full details.

## Importing

To avoid typing full qualified names, use `#import`:

```apl
      #import $::str::trim as strip    ⍝ import with alias
      #import $::str                   ⍝ import namespace — use as str::trim
```

Import directives work in the REPL and in `.apl` source files. They are not valid inside dfns — use qualified names there.

## Key points

- Workspaces save as directories of `.apl` files — one function per file
- Namespaces map to subdirectories; use `ns:fn` to call
- The standard library is at `$:` and is always available
- `#import` brings names into scope with optional aliases
- Colon (`:`) separates namespace levels, not dot

**This concludes the intermediate tutorials.** For task-specific guidance, see the [How-To Guides](../../how-to/index.md). For complete specifications, see the [Reference](../../reference/index.md).
