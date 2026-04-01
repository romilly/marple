# Pico Memory and ⎕WA

## Overview

On the Pimoroni Presto (Pico 2 with 8MB PSRAM), MARPLE reports approximately 7.5MB of workspace available via `⎕WA`. This memory is backed by PSRAM through MicroPython's garbage-collected heap.

## Key findings (2026-04-01)

- **ulab/numpy arrays allocate from the GC heap**, which is placed in PSRAM by the Pimoroni firmware. Arrays consume PSRAM and `⎕WA` decreases accordingly.
- **Maximum contiguous allocation is approximately 2MB.** A 400,000-element integer array (~1.6MB) succeeds, but 500,000 elements (~2MB) fails with a memory allocation error, even with ~6.7MB total free.
- This limit is due to GC heap fragmentation or a maximum block size in the allocator, not total memory.
- **`⎕WA` triggers `gc.collect()`** before reporting, so the value reflects reclaimable memory.

## Practical limits

| Array size | Memory | Result |
|-----------|--------|--------|
| 100,000 elements | ~400KB | OK |
| 200,000 elements | ~800KB | OK |
| 400,000 elements | ~1.6MB | OK |
| 500,000 elements | ~2MB | Fails |

## CPython

On CPython, `⎕WA` returns 2^31 - 1 (a sentinel value). There is no practical memory limit beyond system RAM.
