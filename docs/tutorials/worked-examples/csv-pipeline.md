# Data Processing — CSV Pipeline

This example walks through a complete data-processing workflow: reading a CSV file, splitting it into a matrix, extracting columns, and computing summaries.

<!-- TODO: build this example using actual MARPLE REPL output
     Pipeline: ⎕NREAD → $::str::v2m → column extraction via From+Rank → reduce
     Include: handling headers, numeric conversion, missing data -->

## The task

Given a CSV file of sales data, compute the total and average per product.

## Reading the file

```apl
#import $::str::v2m

raw ← ⎕NREAD '/tmp/sales.csv'
data ← ',' v2m raw
```

## Extracting columns

```apl
⍝ TODO: complete with From + Rank column selection examples
```

## Computing summaries

```apl
⍝ TODO: reduce, rank-1 operations on extracted columns
```

## Key techniques used

- File I/O with the standard library
- `v2m` for splitting delimited text into a matrix
- From + Rank for column extraction
- Reduce for aggregation
