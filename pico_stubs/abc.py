"""MicroPython stub for abc module.

ulab MicroPython has no abc, so deploy.sh copies this as /abc.py on the
Pico filesystem. ABCs become plain classes; abstractmethod raises
NotImplementedError when called on an un-overridden subclass.
"""


class ABC:
    pass


def abstractmethod(f):
    def _not_implemented(*args, **kwargs):
        raise NotImplementedError(
            f"Subclass must implement {f.__name__}"
        )
    return _not_implemented
