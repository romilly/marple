# How to check which backend is active

From Python, inspect the backend module:

```python
from marple.backend import HAS_BACKEND, np

if HAS_BACKEND:
    print(f"Backend: {np.__name__}")
else:
    print("No backend (pure Python)")
```

From the MARPLE REPL, you can check via I-Beam. Create a small helper:

```python
# checkbackend.py
from marple.arraymodel import APLArray
from marple.backend import HAS_BACKEND, np

def check(right: APLArray) -> APLArray:
    if HAS_BACKEND:
        name = np.__name__
    else:
        name = "none"
    return APLArray([len(name)], list(name))
```

```apl
      (⌶'checkbackend.check') 0
numpy
```

See also: [NumPy backend](numpy-backend.md), [Writing fast code](writing-fast-code.md)
