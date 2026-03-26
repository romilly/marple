# System Commands

System commands begin with `)` and are entered at the REPL prompt. They are not APL expressions.

## Workspace management

| Command | Description |
|---------|-------------|
| `)wsid` | Show the current workspace ID |
| `)wsid name` | Set the workspace ID to `name` |
| `)save` | Save the workspace to `workspaces/{wsid}/`. Requires WSID to be set. |
| `)save name` | Set WSID to `name` and save |
| `)load name` | Load workspace `name` from `workspaces/` |
| `)clear` | Clear the workspace and reset WSID to `CLEAR WS` |
| `)lib` | List available workspaces |

A fresh session starts with workspace ID `CLEAR WS`. You must set a WSID before saving:

```
      )wsid
CLEAR WS
      )save
ERROR: No workspace ID set. Use )WSID name first.
      )wsid mywork
mywork
      )save
mywork SAVED
```

## Inspection

| Command | Description |
|---------|-------------|
| `)fns` | List user-defined functions in the workspace |
| `)fns $::str` | List functions in a namespace |
| `)vars` | List user-defined variables |

## Session control

| Command | Description |
|---------|-------------|
| `)off` | Exit the REPL |

## Directives

Directives begin with `#` and work in both the REPL and script files:

| Directive | Description |
|-----------|-------------|
| `#import $::str::upper` | Import a function by its qualified name |
| `#import $::str::upper as up` | Import with an alias |
| `#import $::str` | Import a namespace |
