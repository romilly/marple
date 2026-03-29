# Using MARPLE in Jupyter

MARPLE provides a Jupyter kernel that lets you write APL in Jupyter Notebook, JupyterLab, or Jupyter Console. Arrays are displayed as HTML tables, and workspace state persists across cells.

## Installation

```bash
pip install marple-lang[jupyter]
marple-jupyter-install
jupyter notebook
```

Create a new notebook and select **MARPLE (APL)** as the kernel.

## Features

### Rich array output

Numeric vectors and matrices are displayed as HTML tables with right-justified columns. Character arrays display inline. Rank-3+ arrays show as labelled 2D slices.

```apl
2 3⍴⍳6
```

Produces a formatted 2×3 table.

### APL glyph input

Type APL characters using backtick prefixes — they are translated before execution:

| Type | Get | Type | Get | Type | Get |
|------|-----|------|-----|------|-----|
| `` `r `` | ⍴ | `` `i `` | ⍳ | `` `w `` | ⍵ |
| `` `a `` | ⍺ | `` `V `` | ∇ | `` `l `` | ← |
| `` `- `` | × | `` `= `` | ÷ | `` `J `` | ⍤ |
| `` `P `` | ⍣ | `` `x `` | ⋄ | `` `c `` | ⍝ |

In the classic Notebook (v6), a clickable language bar appears automatically. In JupyterLab, use the backtick prefixes or paste APL characters directly.

### Tab completion

Press **Tab** after typing part of a name to see matching variables and functions from the workspace:

```apl
dou<Tab>    ⍝ completes to 'double' if defined
```

### Shift+Tab introspection

Press **Shift+Tab** on a name to see its shape (for arrays) or source (for functions):

```
Name: M
Shape: 3 4
Rank: 2
Elements: 12
```

### Multi-line dfns

Multi-line direct functions work — the kernel detects unclosed braces and waits for the closing `}`:

```apl
life←{⎕IO←0
  s←{(1↑⍺)⊖(1↓⍺)⌽⍵}
  P←(⍉3 3⊤⍳9)-1
  N←(+⌿P(s⍤1 2)⍵)-⍵
  (N=3)∨⍵∧N=2}
```

### System commands

System commands work in cells:

| Command | Action |
|---------|--------|
| `)vars` | List variables |
| `)fns` | List functions |
| `)clear` | Clear workspace |
| `)wsid [name]` | Show/set workspace ID |
| `)save [name]` | Save workspace |
| `)load name` | Load workspace |
| `)lib` | List saved workspaces |

### Workspace persistence

State persists across cells within a session. Define a function in one cell, use it in the next:

```apl
⍝ Cell 1
double←{⍵×2}

⍝ Cell 2
double ⍳5
```

Load a saved workspace to get pre-defined functions:

```apl
)LOAD life
show (life⍣4) glider
```

## Configuration

### Workspace directory

By default, workspaces are saved in a `workspaces/` directory relative to where Jupyter was launched. To set an absolute path, create `~/.marple/config.ini`:

```ini
[paths]
workspaces = ~/marple-workspaces
```

## Platform notes

The Jupyter kernel works on **Linux**, **macOS**, and **Windows**. APL glyph input via backtick prefixes works on all platforms since translation happens server-side.

## Troubleshooting

### Kernel not found

If "MARPLE (APL)" doesn't appear in the kernel list, run:

```bash
marple-jupyter-install
```

Then restart Jupyter.

### Slow startup

The kernel takes a few seconds to start because it loads NumPy. This is a one-time cost per session.

### `comm_open` warnings

Messages like `[IPKernelApp] WARNING | Unknown message type: 'comm_open'` are harmless and can be ignored. They come from Jupyter's widget system, which MARPLE doesn't use.
