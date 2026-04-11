"""OsFileSystem — real FileSystem adapter using os and open()."""

import os

from marple.ports.filesystem import FileSystem


class OsFileSystem(FileSystem):
    """FileSystem adapter that uses the real OS filesystem."""

    def read_text(self, path: str) -> str:
        with open(path) as f:
            return f.read()

    def write_text(self, path: str, content: str) -> None:
        with open(path, "w") as f:
            f.write(content)

    def exists(self, path: str) -> bool:
        return os.path.exists(path)

    def is_file(self, path: str) -> bool:
        return os.path.isfile(path)

    def is_dir(self, path: str) -> bool:
        return os.path.isdir(path)

    def delete(self, path: str) -> None:
        os.remove(path)

    def makedirs(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)

    def listdir(self, path: str) -> list[str]:
        return os.listdir(path)

    def delete_dir(self, path: str) -> None:
        for entry in os.listdir(path):
            full = path + "/" + entry
            if self.is_dir(full):
                self.delete_dir(full)
            else:
                os.remove(full)
        os.rmdir(path)
