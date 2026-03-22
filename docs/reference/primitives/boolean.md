# Boolean Functions

Boolean functions operate on values of `0` and `1`.

## `∧` And

### Dyadic only

Returns `1` when both arguments are `1`.

```apl
      1∧1
1
      1∧0
0
      0∧0
0
      1 1 0 0∧1 0 1 0
1 0 0 0
```

## `∨` Or

### Dyadic only

Returns `1` when either argument is `1`.

```apl
      0∨1
1
      0∨0
0
      1 1 0 0∨1 0 1 0
1 1 1 0
```

## `~` Tilde

### Monadic: Not

Flips `0` to `1` and `1` to `0`.

```apl
      ~1
0
      ~0
1
      ~1 0 1 1 0
0 1 0 0 1
```

!!! note
    `⍲` (nand) and `⍱` (nor) are not yet implemented. Dyadic `~` (without / set difference) is not yet implemented.

## Boolean idioms

Boolean vectors are commonly used with compress (`/`) to filter:

```apl
      v←3 1 4 1 5 9 2 6
      (v>3)/v
4 5 9 6
```

`∧/` tests if all elements are true, `∨/` if any are true:

```apl
      ∧/1 1 1 1
1
      ∧/1 1 0 1
0
      ∨/0 0 1 0
1
```
