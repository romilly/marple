# The REPL

MARPLE's interactive environment is a read-eval-print loop (REPL) with live glyph input. You type ASCII shortcuts and they're converted to APL characters as you type.

## Launching and exiting

```bash
marple          # launch the REPL
```

```apl
      )off      ⍝ exit the REPL
```

You can also exit with ++ctrl+d++ (Unix/macOS) or ++ctrl+z++ then ++enter++ (Windows).

## Typing APL glyphs

APL uses special characters like `⍴`, `⍳`, `⌽`, and `⍤`. In MARPLE, you type these using **backtick sequences**: press the backtick key (`` ` ``) followed by a letter or symbol.

For example:

| You type | You get | Name |
|----------|---------|------|
| `` `r `` | `⍴` | Rho (shape/reshape) |
| `` `i `` | `⍳` | Iota (index generator) |
| `` `+ `` | `⌽` | Circle-stile (reverse) |
| `` `R `` | `⍤` | Jot-diaeresis (rank) |
| `` `# `` | `⌷` | Squad (from) |

The translation happens live — you'll see the APL character appear immediately after you type the second key.

!!! tip
    A complete glyph reference card is available at [Glyph Input](../reference/glyph-input.md).

## The prompt

The MARPLE prompt is six spaces, following APL tradition:

```
      _
```

Expressions are typed at the prompt. Results appear left-aligned on the next line:

```apl
      2 + 3
5
      ⍳5
1 2 3 4 5
```

## Comments

Everything after `⍝` (lamp, typed `` `; ``) on a line is a comment:

```apl
      2 + 3  ⍝ this is a comment
5
```

## System commands

System commands start with `)` and are entered at the REPL prompt. They manage the workspace and session.

| Command | Description |
|---------|-------------|
| `)off` | Exit the REPL |
| `)clear` | Clear the workspace (remove all names) |
| `)fns` | List defined functions |
| `)vars` | List defined variables |
| `)save` | Save the current workspace |
| `)load name` | Load a saved workspace |
| `)lib` | List available workspaces |
| `)wsid` | Show the current workspace name |
| `)wsid name` | Set the workspace name |

See [System Commands](../reference/system/system-commands.md) for full details.

## Multi-line input

Dfns (direct functions) that span multiple lines are entered by opening a brace `{` and continuing on subsequent lines until the closing `}`:

<!-- TODO: confirm multi-line REPL behaviour — does MARPLE use a continuation prompt? -->

```apl
      avg ← {
          (+/⍵) ÷ ⍴⍵
      }
      avg 3 5 7 9
6
```

## Terminal compatibility

MARPLE's glyph input uses raw terminal mode. It works in most modern terminals on macOS, Linux, and Windows (Windows Terminal, WSL). If glyph input isn't working, see [REPL Issues](../troubleshooting/repl-issues.md).

<!-- TODO: Romilly — confirm which terminals are tested/supported -->
