"""FakeCharSource — test adapter for CharSource port."""

from marple.ports.char_source import CharSource


class FakeCharSource(CharSource):
    """CharSource adapter that returns pre-loaded characters."""

    def __init__(self, chars: str) -> None:
        self._chars = list(chars)

    def read_char(self) -> str:
        if not self._chars:
            return ""
        return self._chars.pop(0)

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass
