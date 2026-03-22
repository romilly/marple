# How to wrap a Python library for MARPLE

To use any Python library from MARPLE, write thin wrapper functions that translate between `APLArray` and native Python types.

## Example: wrapping Python's `math` library

Create a file `mathwrap.py`:

```python
import math
from marple.arraymodel import APLArray, S

def sqrt(right: APLArray) -> APLArray:
    """Monadic: square root of each element."""
    data = [math.sqrt(x) for x in right.data]
    return APLArray(list(right.shape), data)

def atan2(left: APLArray, right: APLArray) -> APLArray:
    """Dyadic: atan2(y, x) element-wise."""
    results = [math.atan2(y, x) for y, x in zip(left.data, right.data)]
    return APLArray(list(left.shape), results)
```

Use from MARPLE:

```apl
      sqrt ← ⌶'mathwrap.sqrt'
      sqrt 4 9 16
2 3 4
```

## Steps

1. Write Python wrapper functions that accept/return `APLArray`
2. Place the module somewhere importable (on `PYTHONPATH` or installed as a package)
3. Call from APL via `⌶'module.function'`

## Tips

- Keep wrappers thin -- just convert types and delegate
- Use `APLArray(list(right.shape), data)` to preserve the input shape
- Use `S(value)` to return a scalar
- Raise clear exceptions for invalid inputs -- they become DOMAIN ERRORs

See also: [Write a Python function](write-python-function.md), [Using I-Beam](using-ibeam.md)
