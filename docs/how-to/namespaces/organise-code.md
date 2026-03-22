# How to organise code with workspaces

MARPLE uses workspaces to organise and persist your work. A workspace is a directory containing `.apl` files.

## Save your session

```apl
      )wsid myproject
myproject
      )save
myproject SAVED
```

This saves all variables and functions to the `workspaces/myproject/` directory.

## Load a workspace

```apl
      )load myproject
myproject
```

## List available workspaces

```apl
      )lib
myproject  utils
```

## Workspace directory structure

Workspaces are saved under the `workspaces/` directory (or the path set by the `MARPLE_WORKSPACES` environment variable):

```
workspaces/
  myproject/
    main.apl
  utils/
    clean.apl
    validate.apl
```

See also: [Import standard library](import-stdlib.md), [Workspaces and namespaces tutorial](../../tutorials/intermediate/workspaces-and-namespaces.md)
