# The Rank Operator -- History and Significance

## Origins

The rank operator was invented by Arthur Whitney in 1982 while he and Ken Iverson were working at I.P. Sharp Associates on an APL model. It was first implemented in SHARP APL in 1983 -- a full year before IBM released APL2 with nested arrays.

Whitney's insight was that you could replace the proliferating collection of per-axis function variants with a single operator that specifies *at what rank* a function should operate. Instead of needing separate "reduce along first axis" and "reduce along last axis" primitives, you write `(+/⍤1)` to reduce rows or `(+/⍤2)` to reduce matrices.

## Iverson's formalisation

The rank operator appeared in Iverson's *Rationalized APL* (1983) and was formalised in *A Dictionary of APL* (1987), where it became a cornerstone of the leading-axis approach. The Dictionary described a clean, regular APL built on cells, frames, and rank -- the theoretical foundation that MARPLE follows.

Iverson and Roger Hui later carried this design into J, where rank is pervasive. Every verb in J has an inherent rank, and the rank conjunction (`"`) is the primary mechanism for controlling how functions interact with array structure.

## Why rank matters

Robert Bernecky's 1988 paper described rank as "a microcosm of APL history." It unifies several concepts that had been treated as separate mechanisms:

- **Scalar extension** -- a scalar paired with each element is just rank-0 cell pairing
- **Each (`¨`)** -- applying a function to each element of a nested array is rank applied to major cells
- **Inner product** -- expressible through rank and reduce
- **Outer product** -- expressible through rank with scalar cells
- **NumPy broadcasting** -- a special case of frame agreement

One operator replaces many.

## Rank in MARPLE

MARPLE adopts rank as a foundational operator, not an afterthought. With flat arrays and no Each operator, rank is the primary way to control how functions interact with multi-dimensional data. The decompose-apply-reassemble cycle works naturally with flat arrays: cells are always regular subarrays, and results are reassembled (with padding if necessary) into regular arrays.
