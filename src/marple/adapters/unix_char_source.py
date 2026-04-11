"""UnixCharSource — raw character input for Unix terminals."""

import os
import sys
import termios
import tty
from typing import Any

from marple.ports.char_source import CharSource


class UnixCharSource(CharSource):
    """CharSource adapter using Unix tty raw mode."""

    def __init__(self) -> None:
        self._fd = sys.stdin.fileno()
        self._old_settings: Any = None

    def read_char(self) -> str:
        """Read one complete UTF-8 character."""
        b = os.read(self._fd, 1)
        if not b:
            return ""
        first = b[0]
        if first < 0x80:
            return b.decode("utf-8")
        if first < 0xC0:
            return b.decode("utf-8", errors="replace")
        if first < 0xE0:
            remaining = 1
        elif first < 0xF0:
            remaining = 2
        else:
            remaining = 3
        for _ in range(remaining):
            b += os.read(self._fd, 1)
        return b.decode("utf-8", errors="replace")

    def start(self) -> None:
        """Enter raw mode, saving current terminal settings."""
        self._old_settings = termios.tcgetattr(self._fd)
        tty.setraw(self._fd)

    def stop(self) -> None:
        """Restore terminal settings."""
        if self._old_settings is not None:
            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old_settings)
            self._old_settings = None
