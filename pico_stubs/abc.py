"""MicroPython stub for abc module."""


class ABC:
    pass


def abstractmethod(f):
    def _not_implemented(*args, **kwargs):
        raise NotImplementedError(
            f"Subclass must implement {f.__name__}"
        )
    return _not_implemented
