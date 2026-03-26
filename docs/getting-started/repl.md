# The REPL

MARPLE provides two interactive environments: a **terminal REPL** and a **web REPL**.

## Terminal REPL

```bash
marple          # launch the terminal REPL
```

```apl
      )off      ⍝ exit the REPL
```

You can also exit with ++ctrl+d++ (Unix/macOS) or ++ctrl+z++ then ++enter++ (Windows).

### Typing APL glyphs in the terminal

In the terminal REPL, type APL characters using **backtick sequences**: press `` ` `` followed by a letter or symbol.

| You type | You get | Name |
|----------|---------|------|
| `` `r `` | `⍴` | Rho (shape/reshape) |
| `` `i `` | `⍳` | Iota (index generator) |
| `` `l `` | `←` | Assignment |
| `` `J `` | `⍤` | Rank operator |
| `` `I `` | `⌷` | From (squad) |

The translation happens live — the APL character appears immediately.

!!! tip
    A complete glyph reference card is available at [Glyph Input](../reference/glyph-input.md).

Alternatively, if you have a Dyalog APL keyboard layout installed (e.g. via `setxkbmap` with `grp:win_switch`), you can use the Win key to type APL glyphs directly.

## PRIDE Web IDE

```bash
python -m marple.web.server          # start on port 8888
python -m marple.web.server --port 9000  # custom port
```

Open `http://localhost:8888/` in your browser. PRIDE (the MARPLE web IDE) communicates over WebSocket and provides:

- **Language bar** — clickable APL glyphs above the input area. Click a glyph to insert it. Hover for name and description.
- **Click to re-edit** — click any previous input line in the session to copy it back to the input for editing and re-submission.
- **Session save/load** — use the Session menu to save the transcript as markdown or load a previous session.
- **Workspace panel** — sidebar showing defined variables (with shapes) and functions. Click a name to insert it into the input.
- **Session history** — up/down arrow keys cycle through previously entered expressions.
- **Multi-line input** — Shift+Enter adds a newline; Enter submits. Newlines are converted to `⋄` (diamond) for execution.

### Pico bridge

To evaluate APL on a connected Raspberry Pi Pico 2:

```bash
python -m marple.web.server --pico-port /dev/ttyACM0
```

A Local/Pico toggle appears in the header bar. Switch to Pico mode to send expressions to the Pico over USB serial.

### Explorer LCD mirror

On the Pimoroni Explorer, the REPL session automatically mirrors to the 320x240 LCD. Input is shown in white, output in green, and errors in red, using a custom APL bitmap font that renders all APL glyphs. No configuration needed — if `picographics` is available, the display activates automatically.

PRIDE is accessible from other machines on the same network — useful for running MARPLE on a Raspberry Pi and programming it from your workstation.

## The prompt

The MARPLE prompt is six spaces, following APL tradition:

```apl
      2 + 3
5
      ⍳5
1 2 3 4 5
```

## Comments

Everything after `⍝` (lamp) on a line is a comment:

```apl
      2 + 3  ⍝ this is a comment
5
```

## System commands

System commands start with `)` and work in both the terminal and web REPLs.

| Command | Description |
|---------|-------------|
| `)off` | Exit the REPL (terminal only) |
| `)clear` | Clear the workspace |
| `)fns` | List defined functions |
| `)vars` | List defined variables |
| `)save` | Save the current workspace |
| `)load name` | Load a saved workspace |
| `)lib` | List available workspaces |
| `)wsid` | Show the current workspace name |
| `)wsid name` | Set the workspace name |

See [System Commands](../reference/system/system-commands.md) for full details.
