# The Python Connection

## Backend abstraction

MARPLE detects NumPy (or CuPy, or ulab) at import time and uses it for vectorised operations. When no array library is available, it falls back to pure Python loops.

This makes the same codebase portable from desktop (NumPy, ~73× faster) to CircuitPython on a Pico (ulab) to bare MicroPython (pure Python).

## I-Beam FFI

The `⌶` operator calls Python functions from APL. This keeps the interpreter core small — system facilities live in Python modules called through thin APL wrappers.

## The Pico target

MARPLE is designed to run on a Raspberry Pi Pico under CircuitPython with ulab. The flat-array model, pure-Python fallback, and backend abstraction all support this goal.

<!-- TODO: Romilly — add status of Pico work and what's been tested -->
