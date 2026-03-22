# Fill Elements

When MARPLE needs to pad arrays to uniform shape (for example during rank-operator reassembly), it uses fill elements:

| Array type | Fill element |
|-----------|-------------|
| Numeric | `0` |
| Character | `' '` (space) |
| Boolean | `0` |

## Where fill elements are used

- **Rank operator reassembly**: when result cells from `f⍤k` differ in shape, shorter cells are padded with fill elements to match the largest cell shape.

## See also

- [Rank Operator](../operators/rank.md)
