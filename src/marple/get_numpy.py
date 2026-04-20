"""Numpy import shim.

On desktop this resolves to CPython's numpy; on the Pico, to ulab.numpy,
which MARPLE accesses via the UlabAPLArray subclass (see
src/marple/ulab_aplarray.py). The cupy branch is for GPU experiments and
is ignored at runtime unless cupy is installed.
"""

try:
    import cupy as np  # type: ignore[no-redef]
except ImportError:
    try:
        import numpy as np  # type: ignore[no-redef]
    except ImportError:
        from ulab import numpy as np  # type: ignore[no-redef,import-not-found]
