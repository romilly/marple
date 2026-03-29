# Installation

## Requirements

MARPLE requires Python 3.10 or later. It runs on **Linux**, **macOS**, and **Windows**.

- **All platforms**: interpreter, PRIDE web IDE, Jupyter kernel, script runner
- **Linux/macOS**: terminal REPL with live backtick-to-glyph input
- **Windows**: terminal REPL works but without live glyph translation — use PRIDE or Jupyter for glyph input

NumPy is optional but recommended for performance on large arrays.

We recommend using [uv](https://docs.astral.sh/uv/getting-started/installation/) for fast, reliable Python package management.

## Install from PyPI

```bash
uv venv
source .venv/bin/activate      # on Windows: .venv\Scripts\activate
uv pip install marple-lang
```

## Install from source

For the latest development version:

```bash
git clone https://github.com/romilly/marple.git
cd marple
uv venv
source .venv/bin/activate      # on Windows: .venv\Scripts\activate
uv pip install -e .
```

This installs MARPLE in development mode, so changes to the source take effect immediately.

## Verify the installation

```bash
marple
```

You should see the MARPLE banner and a six-space prompt:

```
MARPLE v0.3.0 - Mini APL in Python
CLEAR WS


```

Type `1+1` and press ++enter++. You should see `2`. Type `)off` to exit.

## Optional: NumPy for performance

If NumPy is installed, MARPLE uses it automatically for element-wise operations on large arrays (roughly 73× faster than pure Python). Install it with:

```bash
uv pip install numpy
```

MARPLE detects NumPy at startup — no configuration needed. To force pure-Python mode (useful for testing or on platforms without NumPy):

```bash
MARPLE_BACKEND=none marple
```

## Jupyter Notebook

To use MARPLE in Jupyter Notebook or JupyterLab:

```bash
uv pip install marple-lang[jupyter]
marple-jupyter-install
jupyter notebook
```

Select **MARPLE (APL)** as the kernel when creating a new notebook. See the [Jupyter guide](../how-to/jupyter.md) for details.

## For development

To install with test dependencies:

```bash
uv pip install -e ".[test]"
pytest           # run the test suite
pyright src/     # type checking (strict mode)
```
