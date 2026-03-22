from __future__ import annotations

import os
from typing import Any


class Namespace:
    """A hierarchical namespace mapping names to values or child namespaces."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.entries: dict[str, Any] = {}

    def resolve(self, parts: list[str]) -> Any:
        """Walk the namespace tree to find a value."""
        if len(parts) == 0:
            return self
        head = parts[0]
        if head not in self.entries:
            return None
        val = self.entries[head]
        if len(parts) == 1:
            return val
        if isinstance(val, Namespace):
            return val.resolve(parts[1:])
        return None

    def register(self, name: str, value: Any) -> None:
        self.entries[name] = value

    def list_names(self) -> list[str]:
        return sorted(self.entries.keys())


def load_system_workspace(stdlib_path: str) -> Namespace:
    """Load the system workspace from the stdlib directory.

    Walks subdirectories, loading each .apl file as a function definition.
    """
    from marple.interpreter import interpret

    root = Namespace("$")
    if not os.path.isdir(stdlib_path):
        return root

    for entry in sorted(os.listdir(stdlib_path)):
        subdir = os.path.join(stdlib_path, entry)
        if os.path.isdir(subdir) and not entry.startswith("_"):
            ns = Namespace(entry)
            for fname in sorted(os.listdir(subdir)):
                if fname.endswith(".apl"):
                    func_name = fname[:-4]
                    filepath = os.path.join(subdir, fname)
                    with open(filepath) as f:
                        source = f.read().strip()
                    if source:
                        env: dict[str, Any] = {}
                        result = interpret(source, env)
                        # The .apl file should define a function via assignment
                        # or be a bare dfn expression
                        if func_name in env:
                            ns.register(func_name, env[func_name])
                        else:
                            ns.register(func_name, result)
            root.register(entry, ns)
    return root
