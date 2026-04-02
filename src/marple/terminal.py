"""GlyphLineEditor — platform-independent line editor with backtick→glyph translation."""

try:
    from typing import Callable
except ImportError:
    pass

from marple.glyphs import GLYPH_MAP
from marple.ports.char_source import CharSource


class GlyphLineEditor:
    """Line editor with backtick→APL glyph translation.

    Takes a CharSource (raw character input) and a write callable (output).
    Platform-independent — the CharSource handles platform-specific raw input.
    """

    def __init__(self, source: CharSource, write: 'Callable[[str], None]') -> None:
        self._source = source
        self._write = write

    def read_line(self, prompt: str) -> str | None:
        """Read a line with live backtick→glyph translation.

        Returns the line on Enter, empty string on Ctrl-C,
        or None on EOF/Ctrl-D.
        """
        buf: list[str] = []
        backtick = False
        self._source.start()
        try:
            self._write(prompt)
            while True:
                ch = self._source.read_char()
                if not ch or ch == "\x04":  # EOF or Ctrl-D
                    self._write("\r\n")
                    return None
                if ch == "\x03":  # Ctrl-C
                    self._write("\r\n")
                    return ""
                if ch == "\x1b":  # Escape sequence — discard
                    self._discard_escape()
                    continue
                if ch in ("\r", "\n"):  # Enter
                    self._write("\r\n")
                    return "".join(buf)
                if ch == "\x7f" or ch == "\x08":  # Backspace
                    if buf:
                        buf.pop()
                        line = "".join(buf)
                        self._write("\r" + prompt + line + " \r" + prompt + line)
                    continue
                if backtick:
                    backtick = False
                    if ch == "`":
                        buf.append("`")
                        self._write("`")
                    elif ch in GLYPH_MAP:
                        glyph = GLYPH_MAP[ch]
                        buf.append(glyph)
                        self._write(glyph)
                    else:
                        buf.append("`")
                        buf.append(ch)
                        self._write("`" + ch)
                    continue
                if ch == "`":
                    backtick = True
                    continue
                buf.append(ch)
                self._write(ch)
        finally:
            self._source.stop()

    def _discard_escape(self) -> None:
        """Read and discard an escape sequence."""
        ch = self._source.read_char()
        if ch == "[":
            # CSI sequence: read until final byte (0x40-0x7E)
            while True:
                seq_ch = self._source.read_char()
                if not seq_ch or (0x40 <= ord(seq_ch) <= 0x7E):
                    break
