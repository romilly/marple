# How MARPLE Differs from Other APLs

## Feature comparison

| Feature | MARPLE | Dyalog APL | GNU APL | J |
|---------|--------|-----------|---------|---|
| Array model | Flat | Nested | Nested | Boxed |
| Function definition | Dfns only | Dfns + tradfns | Tradfns + dfns | Explicit + tacit |
| Rank operator | Yes | Yes (v14+) | No | Yes |
| From indexing (`⌷`) | Yes | Yes | No | Yes (`{`) |
| Bracket indexing | Yes | Yes | Yes | No |
| Control structures | No | Yes | Yes | No |
| Namespaces | Directory-based | Object-based | No | Locale-based |
| Python FFI | Yes (`⌶`) | Yes (`⎕PY`) | No | No |
| Implementation | Python | C/C++ | C++ | C |

## Flat arrays, not nested

This is MARPLE's most significant departure from modern APLs. Every element is a simple scalar -- a number or a character. There is no `⊂` (enclose), no `⊃` (disclose), no depth, and no `¨` (each).

This means some idioms from nested APL don't translate directly. The rank operator covers most of the use cases that Each handles in nested APL. For cases where non-uniform results are needed, MARPLE pads to the largest shape with fill elements (0 for numbers, space for characters).

## Dfns only, no traditional definitions

MARPLE has no `∇`-header function definitions, no line numbers, no labels, and no `→` (branch). All functions are dfns; all operators are dops. This is a deliberate simplification -- dfns are lexically scoped, composable, and easier to reason about than their traditional counterparts.

## Leading-axis orientation

Like J and modern Dyalog, MARPLE follows the leading-axis convention. Reduce and scan operate along the last axis by default. The rank operator provides access to any axis. There is no bracket-axis notation (`f[k]`).

## The rank operator as a foundation

Where Dyalog has rank as one of many operators and GNU APL lacks it entirely, MARPLE treats rank as a foundational construct. It replaces Each, bracket-axis, and many ad-hoc per-axis variants found in other APLs.

## Python integration

MARPLE's `⌶` (I-Beam) operator provides direct access to Python functions. Any Python callable that accepts and returns `APLArray` objects can be called from APL. This keeps the interpreter core small while enabling access to the full Python ecosystem.

## Backend portability

The same MARPLE code runs on desktop Python (with NumPy acceleration), on CircuitPython with ulab, or on bare MicroPython with pure Python fallback. No code changes are needed -- the backend is detected at import time.
