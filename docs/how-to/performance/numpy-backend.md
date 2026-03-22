# How to enable or disable the NumPy backend

MARPLE auto-detects array backends at startup in this order: CuPy, NumPy, ulab. If none are found, it falls back to pure Python.

## Use NumPy (recommended for desktop)

```bash
pip install numpy
marple
```

NumPy provides significant speedups for element-wise arithmetic, reduce, and inner product on large arrays.

## Force pure Python

```bash
MARPLE_BACKEND=none marple
```

Set the `MARPLE_BACKEND` environment variable to `none` to disable all backends. This is useful for testing or when you want predictable Python-only behaviour.

## Auto-detection (default)

When `MARPLE_BACKEND` is unset or set to `auto`, MARPLE tries CuPy first (for GPU acceleration), then NumPy, then ulab (for CircuitPython/MicroPython), and finally falls back to pure Python lists.

See also: [Check which backend is active](check-backend.md), [Writing fast code](writing-fast-code.md)
