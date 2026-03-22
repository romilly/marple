# I-Beam (`⌶`)

## Syntax

```
  (⌶'module.function') Y        ⍝ monadic call
X (⌶'module.function') Y        ⍝ dyadic call
```

The operand is a string naming a Python callable in `module.function` form.

## Description

`⌶` is a monadic operator that derives a function from a Python callable. The derived function passes its APL arguments directly to the Python function.

## Contract

The Python function must:

1. Accept one `APLArray` argument (monadic) or two `APLArray` arguments (dyadic, left then right).
2. Return an `APLArray`.

If the Python function raises an exception, MARPLE wraps it as a DOMAIN ERROR. If it returns something other than `APLArray`, MARPLE raises DOMAIN ERROR.

## Examples

Given a Python file `mylib.py`:

```python
from marple.arraymodel import APLArray, S

def double(right: APLArray) -> APLArray:
    return APLArray(list(right.shape), [x * 2 for x in right.data])
```

You can call it from MARPLE:

```apl
      (⌶'mylib.double') 1 2 3
2 4 6
```

The standard library uses i-beam internally:

```apl
      (⌶'marple.stdlib.str_impl.upper') 'hello'
HELLO
```

## Security

By default, any importable Python module can be called via `⌶`.

To restrict access, set the `MARPLE_IBEAM_ALLOW` environment variable to a comma-separated list of allowed module prefixes:

```
MARPLE_IBEAM_ALLOW=marple.stdlib,myproject
```

With this setting, only paths starting with `marple.stdlib` or `myproject` are allowed. All other paths raise SECURITY ERROR.

## See also

- [Standard Library](../standard-library/index.md) -- built on i-beam
