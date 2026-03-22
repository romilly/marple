# How to write a Python function for MARPLE

Every function called through `⌶` must follow this contract:

1. Accept one `APLArray` argument (monadic) or two (dyadic, left then right)
2. Return an `APLArray`

## Monadic example

```python
from marple.arraymodel import APLArray

def double(right: APLArray) -> APLArray:
    data = [x * 2 for x in right.data]
    return APLArray(list(right.shape), data)
```

Save this as `mymodule.py` somewhere on your Python path, then call it:

```apl
      (⌶'mymodule.double') 1 2 3
2 4 6
```

## Dyadic example

```python
from marple.arraymodel import APLArray, S

def power(left: APLArray, right: APLArray) -> APLArray:
    base = left.data[0]
    exp = right.data[0]
    return S(base ** exp)
```

```apl
      2 (⌶'mymodule.power') 10
1024
```

## Error handling

If your function raises an exception, MARPLE wraps it in a DOMAIN ERROR. Return meaningful error messages in your exceptions to help users debug.

See also: [Using I-Beam](using-ibeam.md), [Wrap a Python library](wrap-python-library.md)
