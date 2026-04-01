"""FakeFileSystem — in-memory test adapter for FileSystem port."""

import os.path

from marple.ports.filesystem import FileSystem


class FakeFileSystem(FileSystem):
    """FileSystem adapter backed by in-memory dicts."""

    def __init__(self, files: dict[str, str] | None = None) -> None:
        self._files: dict[str, str] = dict(files) if files else {}
        self._dirs: set[str] = set()
        # Auto-create parent dirs for any initial files
        for path in self._files:
            self._ensure_parent_dirs(path)

    def _ensure_parent_dirs(self, path: str) -> None:
        parent = os.path.dirname(path)
        while parent and parent != "/":
            self._dirs.add(parent)
            parent = os.path.dirname(parent)

    def read_text(self, path: str) -> str:
        if path not in self._files:
            raise FileNotFoundError(f"No such file: '{path}'")
        return self._files[path]

    def write_text(self, path: str, content: str) -> None:
        self._files[path] = content
        self._ensure_parent_dirs(path)

    def exists(self, path: str) -> bool:
        return path in self._files or path in self._dirs

    def is_file(self, path: str) -> bool:
        return path in self._files

    def is_dir(self, path: str) -> bool:
        return path in self._dirs

    def delete(self, path: str) -> None:
        if path not in self._files:
            raise OSError(f"File not found: '{path}'")
        del self._files[path]

    def makedirs(self, path: str) -> None:
        self._dirs.add(path)
        self._ensure_parent_dirs(path)

    def listdir(self, path: str) -> list[str]:
        prefix = path.rstrip("/") + "/"
        entries: set[str] = set()
        for p in self._files:
            if p.startswith(prefix):
                rest = p[len(prefix):]
                entries.add(rest.split("/")[0])
        for d in self._dirs:
            if d.startswith(prefix):
                rest = d[len(prefix):]
                if rest and "/" not in rest:
                    entries.add(rest)
        return sorted(entries)

    def delete_dir(self, path: str) -> None:
        prefix = path.rstrip("/") + "/"
        to_remove = [p for p in self._files if p.startswith(prefix)]
        for p in to_remove:
            del self._files[p]
        to_remove_dirs = [d for d in self._dirs if d == path or d.startswith(prefix)]
        for d in to_remove_dirs:
            self._dirs.discard(d)
