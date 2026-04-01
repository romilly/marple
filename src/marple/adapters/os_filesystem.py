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
        try:
            os.stat(path)
            return True
        except OSError:
            return False

    def is_file(self, path: str) -> bool:
        try:
            return (os.stat(path)[0] & 0x8000) != 0
        except OSError:
            return False

    def is_dir(self, path: str) -> bool:
        try:
            return (os.stat(path)[0] & 0x4000) != 0
        except OSError:
            return False

    def delete(self, path: str) -> None:
        os.remove(path)

    def makedirs(self, path: str) -> None:
        parts = path.replace("\\", "/").split("/")
        current = ""
        for part in parts:
            if not part:
                current = "/"
                continue
            current = current + part if current.endswith("/") else current + "/" + part
            try:
                os.mkdir(current)
            except OSError:
                pass

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
