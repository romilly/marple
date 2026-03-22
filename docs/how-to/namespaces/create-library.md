# How to create your own library

Create a workspace subdirectory with one `.apl` file per function. Each file should define a single function:

```
workspaces/
  mylib/
    double.apl
    greet.apl
```

Each `.apl` file contains a function definition:

```apl
double←{⍵+⍵}
```

After saving, you can load the workspace and use the functions:

```apl
      )load mylib
mylib
      double 5
10
```

!!! note
    User namespaces currently work through workspaces. Namespace-qualified access to user libraries (e.g. `mylib::double`) is not yet available -- use `#import` or `)load` instead.

See also: [Organise code](organise-code.md), [Import standard library](import-stdlib.md)
