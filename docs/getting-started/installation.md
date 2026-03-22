# Installation

## Requirements

MARPLE requires Python 3.10 or later. It has no mandatory external dependencies — NumPy is optional but recommended for performance on large arrays.

## Install from source

MARPLE is not yet published on PyPI. Install it from GitHub:

```bash
git clone https://github.com/romilly/marple.git
cd marple
python -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
pip install -e .
```

This installs MARPLE in development mode, so changes to the source take effect immediately.

## Verify the installation

```bash
marple
```

You should see the MARPLE banner and a six-space prompt:

```
MARPLE v0.2.13 - Mini APL in Python
CLEAR WS


```

Type `1+1` and press ++enter++. You should see `2`. Type `)off` to exit.

## Optional: NumPy for performance

If NumPy is installed, MARPLE uses it automatically for element-wise operations on large arrays (roughly 73× faster than pure Python). Install it with:

```bash
pip install numpy
```

MARPLE detects NumPy at startup — no configuration needed. To force pure-Python mode (useful for testing or on platforms without NumPy):

```bash
MARPLE_BACKEND=none marple
```

## For development

To install with test dependencies:

```bash
pip install -e ".[test]"
pytest           # run the test suite
pyright src/     # type checking (strict mode)
```
