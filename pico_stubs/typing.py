"""MicroPython stub for typing module.

Typing constructs collapse to bare objects at runtime on the Pico; we
only need them importable, not functional. deploy.sh copies this as
/typing.py on the Pico filesystem.
"""

Any = object
Callable = object
Generator = object
Iterator = object
Protocol = type('Protocol', (), {})
TYPE_CHECKING = False
