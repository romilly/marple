---
hide:
  - navigation
  - toc
---

# MARPLE on the Raspberry Pi Pico 2

These videos show MARPLE running on a Raspberry Pi Pico 2 via MicroPython.
The workstation sends APL expressions over USB serial; the Pico evaluates
them and returns results.

## Demo 1: Primitive Functions and Operators

Arithmetic, vectors, matrices, reduce, scan, outer product, grade, encode/decode,
and trig — all running on the Pico.

<video src="picoapl-2026-03-23_16.35.35.mp4" controls style="width:100%; max-width:1200px;"></video>

## Demo 2: Direct Functions (Dfns) and the Rank Operator

Named dfns, guards, recursion (factorial, Fibonacci), default left arguments,
and the rank operator applied to matrices and 3D arrays.

<video src="picoapl-2026-03-23_16.46.54.mp4" controls style="width:100%; max-width:1200px;"></video>

## Demo 3: Namespaces and Standard Library

Qualified names (`$::str::upper`), `#import` directives, aliases, file I/O
(`⎕NWRITE`/`⎕NREAD`), and the i-beam operator for direct Python FFI.

<video src="picoapl-2026-03-23_17.25.09.mp4" controls style="width:100%; max-width:1200px;"></video>
