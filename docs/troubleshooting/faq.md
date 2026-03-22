# Frequently Asked Questions

## Can I use nested arrays?

No. MARPLE implements flat arrays only. If arrays-of-arrays are added in the future, they'll follow Iverson's Dictionary boxing model, not APL2 nesting.

## Where are tradfns?

MARPLE doesn't have traditional function definitions (`∇`-headers, line numbers, `→`). Use dfns (`{⍺+⍵}`) instead. See [Direct Definition](../explanation/dfns-vs-tradfns.md) for the rationale.

## How do I enter APL characters?

Use backtick sequences in the REPL: `` `r `` for `⍴`, `` `i `` for `⍳`, etc. See the [Glyph Input](../reference/glyph-input.md) reference.

## Is MARPLE compatible with Dyalog/GNU APL?

Mostly, for first-generation features. Scalar functions, structural functions, reduce, scan, and bracket indexing work the same way. The main incompatibilities are: no nested arrays, no tradfns, no control structures. See [How MARPLE Differs](../explanation/comparison.md).

## Can I use MARPLE on a Raspberry Pi Pico?

That's a design goal. The interpreter is designed to run under CircuitPython with ulab. See [The Python Connection](../explanation/python-connection.md) for current status.

<!-- TODO: Romilly — update with actual Pico status -->

## How fast is MARPLE?

With NumPy, element-wise operations on large arrays are about 73× faster than pure Python. The interpreter itself is tree-walking Python, so it won't match compiled APLs like Dyalog for complex workloads. It's designed for correctness and portability, not raw speed.
