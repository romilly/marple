
from __future__ import annotations

import os
from typing import Any


def _isdir(path):
    """Check if path is a directory (works on MicroPython)."""
    try:
        return (os.stat(path)[0] & 0x4000) != 0
    except OSError:
        return False


def _join(base, name):
    """Join path components (works on MicroPython)."""
    if base.endswith("/"):
        return base + name
    return base + "/" + name


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
    from marple.engine import Interpreter

    root = Namespace("$")
    if not _isdir(stdlib_path):
        return root

    for entry in sorted(os.listdir(stdlib_path)):
        subdir = _join(stdlib_path, entry)
        if _isdir(subdir) and not entry.startswith("_"):
            ns = Namespace(entry)
            for fname in sorted(os.listdir(subdir)):
                if fname.endswith(".apl"):
                    func_name = fname[:-4]
                    filepath = _join(subdir, fname)
                    with open(filepath) as f:
                        source = f.read().strip()
                    if source:
                        interp = Interpreter(io=1)
                        interp.run(source)
                        val = interp.env.get(func_name)
                        if val is not None:
                            ns.register(func_name, val)
            root.register(entry, ns)
    return root
