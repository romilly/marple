# Conway's Game of Life in MARPLE

MARPLE can run Conway's Game of Life in a single dfn — no nested arrays needed:

```apl
life←{⎕IO←0
  s←{(1↑⍺)⊖(1↓⍺)⌽⍵}
  P←(⍉3 3⊤⍳9)-1
  N←(+⌿P(s⍤1 2)⍵)-⍵
  (N=3)∨⍵∧N=2}

G←6 6⍴0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 1 0 0 0 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0
(life⍣4) G
```

Uses the rank operator to apply 9 shift pairs, reduce-first to sum neighbours, and the power operator to iterate. Runs on CPython and the Raspberry Pi Pico 2.

## How it works

1. **Shift pairs** — `P←(⍉3 3⊤⍳9)-1` generates the 9 offset pairs (including centre)
2. **Shift function** — `s←{(1↑⍺)⊖(1↓⍺)⌽⍵}` rotates the grid by a pair of offsets
3. **Neighbour count** — `N←(+⌿P(s⍤1 2)⍵)-⍵` applies all 9 shifts via rank, sums them, subtracts the cell itself
4. **Life rule** — `(N=3)∨⍵∧N=2` — a cell lives if it has 3 neighbours, or is alive with 2 neighbours
5. **Iteration** — `(life⍣4)` applies the rule 4 times using the power operator

See the [demo videos](https://romilly.github.io/marple/demos/) for animated examples.
