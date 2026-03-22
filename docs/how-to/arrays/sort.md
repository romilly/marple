# How to sort a vector

Use grade up (`⍋`) to get the indices that would sort a vector, then index with those:

```apl
      V ← 3 1 4 1 5 9
      V[⍋V]
1 1 3 4 5 9
```

For descending order, use grade down (`⍒`):

```apl
      V[⍒V]
9 5 4 3 1 1
```

## Sort each row of a matrix

Define a sort dfn and apply it at rank 1:

```apl
      sort ← {⍵[⍋⍵]}
      (sort⍤1) 3 4⍴12 3 7 1 8 2 11 5 9 4 10 6
1  3  7 12
2  5  8 11
4  6  9 10
```

See also: [Rank operator -- apply to rows](../rank-operator/apply-to-rows.md)
