"""MicroPython stub for contextlib.

Provides contextmanager() (decorator that wraps a generator function as
a context manager) and AbstractContextManager (base class used only in
type annotations).
"""


class AbstractContextManager:
    """Base for context managers — used only in type annotations."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


def contextmanager(func):
    """Wrap a generator function as a context manager."""

    class _CM:
        def __init__(self, *args, **kwargs):
            self._gen = func(*args, **kwargs)

        def __enter__(self):
            return next(self._gen)

        def __exit__(self, exc_type, exc_val, exc_tb):
            try:
                next(self._gen)
            except StopIteration:
                pass
            return False

    return _CM
