# How to use I-Beam

The `⌶` operator calls Python functions from APL. Its operand is a string naming a Python callable using dotted module path notation:

```apl
      (⌶'marple.stdlib.str_impl.upper') 'hello'
HELLO
```

## Assign to a name for reuse

```apl
      up ← ⌶'marple.stdlib.str_impl.upper'
      up 'hello world'
HELLO WORLD
```

The derived function is first-class -- you can assign it, pass it to operators, and call it monadically or dyadically.

## Dyadic usage

If the Python function accepts two `APLArray` arguments:

```apl
      'hello' (⌶'mymodule.myfunc') 'world'
```

## Security

If the `MARPLE_IBEAM_ALLOW` environment variable is set, only module paths matching one of its comma-separated prefixes are permitted. Paths not on the allowlist raise a SECURITY ERROR.

```bash
MARPLE_IBEAM_ALLOW=marple.stdlib,myproject marple
```

See also: [Write a Python function](write-python-function.md), [Wrap a Python library](wrap-python-library.md)
