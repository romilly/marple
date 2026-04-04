try:
    from typing import Any
except ImportError:
    pass

try:
    import cupy as np  # type: ignore[no-redef]
except ImportError:
    try:
        import numpy as np  # type: ignore[no-redef]
    except ImportError:
        import ulab.numpy as np  # type: ignore[no-redef,import-not-found]
