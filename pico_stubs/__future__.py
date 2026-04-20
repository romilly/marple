"""MicroPython stub for the __future__ module.

CPython uses `from __future__ import annotations` (PEP 563) to defer
annotation evaluation. MicroPython has no `__future__` module but
discards function/class annotations at runtime anyway, so the directive
is a no-op — this stub just lets the import succeed.
"""

annotations = None
