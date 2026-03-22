# Glossary

**Array**
: The fundamental data structure in APL. A rectangular collection of scalars with a shape.

**Axis**
: One dimension of an array. A matrix has two axes (rows and columns).

**Cell**
: A subarray formed by trailing axes. A k-cell uses the last k axes. See [Leading-Axis Theory](../explanation/leading-axis.md).

**Catenate**
: The `,` function used dyadically. Joins two arrays along the last axis.

**Compress**
: Dyadic `/` with a boolean left argument. Selects elements where the mask is 1.

**Dfn**
: Direct function. A function defined with `{body}` syntax, using `⍵` and `⍺` for arguments.

**Dop**
: Direct operator. Like a dfn but takes function operands (`⍺⍺`, `⍵⍵`).

**Dyadic**
: A function called with two arguments (left and right).

**Fill element**
: The value used for padding: 0 for numbers, space for characters.

**Frame**
: The leading axes that organise cells. If cells are k-cells, the frame is the first `rank-k` axes.

**From**
: The `⌷` function. Selects major cells along the leading axis.

**Grade**
: `⍋` (grade up) and `⍒` (grade down). Return the indices that would sort an array.

**Guard**
: Conditional expression in a dfn: `condition : result`.

**I-Beam**
: The `⌶` operator. Calls a Python function from APL.

**Index origin**
: The starting index for arrays, controlled by `⎕IO`. MARPLE defaults to 1.

**Inner product**
: `f.g` applied to two arrays. Generalises matrix multiplication (`+.×`).

**Iota**
: `⍳n`. Generates the integers from `⎕IO` to `n`.

**Major cell**
: The largest cells of an array -- subarrays along the first axis.

**Monadic**
: A function called with one argument (right only).

**Operator**
: A higher-order construct that takes a function (and sometimes a value) and produces a derived function. Examples: `/` (reduce), `⍤` (rank).

**Outer product**
: `∘.f` applied to two arrays. Applies f to every combination of elements.

**Pervasive**
: A scalar function that applies element-by-element, penetrating through array structure.

**Rank** (of an array)
: The number of dimensions. Scalar = 0, vector = 1, matrix = 2.

**Rank** (operator)
: The `⍤` operator. Applies a function at a specified cell rank.

**Ravel**
: Monadic `,`. Flattens an array into a vector.

**Reduce**
: The `/` operator applied to a function. Folds the function across the elements of an array.

**Replicate**
: Dyadic `/` with a non-boolean left argument. Repeats each element the specified number of times.

**Reshape**
: Dyadic `⍴`. Creates an array with the specified shape, cycling the data.

**Scalar**
: A single value (number or character). Rank 0.

**Scalar extension**
: When a scalar is paired with each element of an array in a dyadic scalar function.

**Scan**
: The `\` operator applied to a function. Running reduction producing all intermediate results.

**Shape**
: A vector of integers giving the length along each axis. Monadic `⍴` returns the shape of its argument.

**Strand**
: Numbers (or names) separated by spaces forming a vector: `1 2 3`.

**Vector**
: A one-dimensional array. Rank 1.

**Workspace**
: A saved collection of variables and functions, stored as a directory of `.apl` files.
