# Installation

## Requirements

MARPLE requires Python 3.10 or later. It has no mandatory external dependencies — NumPy is optional but recommended for performance on large arrays.

## Install from PyPI

```bash
pip install marple
```

## Install from source

```bash
git clone https://github.com/romilly/marple.git
cd marple
pip install -e .
```

This installs MARPLE in development mode, so changes to the source take effect immediately.

## Verify the installation

```bash
marple
```

You should see the MARPLE banner and a six-space prompt:

```
MARPLE v0.x.x
      
```

Type `1+1` and press ++enter++. You should see `2`. Type `)off` to exit.

## Optional: NumPy for performance

If NumPy is installed, MARPLE uses it automatically for element-wise operations on large arrays (roughly 73× faster than pure Python for big arrays). Install it with:

```bash
pip install numpy
```

To verify which backend MARPLE is using, check `⎕BE` in the REPL:

<!-- TODO: confirm the system variable or mechanism for checking backend status -->

```apl
      ⎕BE
numpy
```

To force pure-Python mode (useful for testing or on platforms without NumPy):

```bash
MARPLE_BACKEND=none marple
```

## For development

To install with test dependencies:

```bash
pip install -e .[test]
pytest           # run the test suite
pyright src/     # type checking (strict mode)
```

<!-- TODO: Romilly — confirm the exact install commands match the current setup,
     especially the package name on PyPI (if published) vs install-from-source -->
