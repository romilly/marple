from __future__ import annotations

import sys
import tty
import termios

from marple.glyphs import GLYPH_MAP

PROMPT = "      "


def read_line() -> str | None:
    """Read a line with live backtick→glyph translation.

    Returns the line on Enter, empty string on empty Enter,
    or None on Ctrl-D (EOF).
    """
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    buf: list[str] = []
    backtick = False
    try:
        tty.setraw(fd)
        sys.stdout.write(PROMPT)
        sys.stdout.flush()
        while True:
            ch = sys.stdin.read(1)
            if not ch or ch == "\x04":  # Ctrl-D
                sys.stdout.write("\r\n")
                sys.stdout.flush()
                return None
            if ch == "\x03":  # Ctrl-C
                sys.stdout.write("\r\n")
                sys.stdout.flush()
                buf.clear()
                return ""
            if ch in ("\r", "\n"):  # Enter
                sys.stdout.write("\r\n")
                sys.stdout.flush()
                return "".join(buf)
            if ch == "\x7f" or ch == "\x08":  # Backspace
                if buf:
                    buf.pop()
                    # Redraw line
                    sys.stdout.write(f"\r{PROMPT}{''.join(buf)} \r{PROMPT}{''.join(buf)}")
                    sys.stdout.flush()
                continue
            if backtick:
                backtick = False
                if ch == "`":
                    buf.append("`")
                    sys.stdout.write("`")
                elif ch in GLYPH_MAP:
                    glyph = GLYPH_MAP[ch]
                    buf.append(glyph)
                    sys.stdout.write(glyph)
                else:
                    buf.append("`")
                    buf.append(ch)
                    sys.stdout.write("`" + ch)
                sys.stdout.flush()
                continue
            if ch == "`":
                backtick = True
                continue
            buf.append(ch)
            sys.stdout.write(ch)
            sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
