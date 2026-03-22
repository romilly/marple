# Leading-Axis Theory

## The key insight

All operations should, by default, apply along the **leading** (first) axis. The rank operator generalises to any axis.

In a matrix with shape `3 4`, the major cells are the 3 rows (each a 4-element vector). In a rank-3 array with shape `2 3 4`, the major cells are the 2 matrices (each with shape `3 4`).

This convention is consistent and composable. You always know that the first axis organises the "items" of a collection, regardless of what those items look like.

## Cells and frames

An array can be decomposed into **cells** of any rank. For an array with shape `2 3 4`:

| Cell rank | Cell shape | Frame shape | Number of cells |
|-----------|-----------|-------------|-----------------|
| 0 | (scalar) | 2 3 4 | 24 |
| 1 | 4 | 2 3 | 6 |
| 2 | 3 4 | 2 | 2 |
| 3 | 2 3 4 | (empty) | 1 |

The **frame** is the leading axes that organise the cells. The **cell** is the trailing axes that the function operates on.

## Why From works

The `⌷` (From) function selects major cells -- subarrays along the leading axis. For a matrix, `2⌷M` gives you row 2. For a rank-3 array, `1⌷A` gives you the first matrix.

This is natural because the leading axis always represents the "collection" dimension. From doesn't need an axis argument -- it always works on the first axis, and the rank operator handles the rest.

## Comparison to trailing-axis conventions

Traditional APL often defaults to the last axis: reduce operates along the trailing axis, rotate rotates along the trailing axis, and so on. This creates a mismatch: some operations default to the first axis, others to the last.

The leading-axis approach resolves this inconsistency. Every operation has one default behaviour (leading axis), and rank provides uniform access to any other axis. The result is fewer special cases and more predictable composition.

## Leading-axis in MARPLE

MARPLE follows the leading-axis convention from Iverson's *Dictionary of APL*. From (`⌷`) selects major cells. The rank operator decomposes arrays into cells of any rank. Together they replace the ad-hoc axis mechanisms of first-generation APL with a uniform, composable system.
