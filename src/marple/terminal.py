
import os
import sys
import tty
import termios

from marple.glyphs import GLYPH_MAP

PROMPT = "      "


def _read_char(fd: int) -> str:
    """Read one complete UTF-8 character from the file descriptor."""
    b = os.read(fd, 1)
    if not b:
        return ""
    first = b[0]
    if first < 0x80:
        return b.decode("utf-8")
    # Multi-byte UTF-8: determine length from first byte
    if first < 0xC0:
        return b.decode("utf-8", errors="replace")
    if first < 0xE0:
        remaining = 1
    elif first < 0xF0:
        remaining = 2
    else:
        remaining = 3
    for _ in range(remaining):
        b += os.read(fd, 1)
    return b.decode("utf-8", errors="replace")


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
            ch = _read_char(fd)
            if not ch or ch == "\x04":  # Ctrl-D
                sys.stdout.write("\r\n")
                sys.stdout.flush()
                return None
            if ch == "\x03":  # Ctrl-C
                sys.stdout.write("\r\n")
                sys.stdout.flush()
                buf.clear()
                return ""
            if ch == "\x1b":  # Escape sequence — skip it
                # Read and discard the rest of the escape sequence
                next_b = os.read(fd, 1)
                if next_b == b"[":
                    # CSI sequence: read until final byte (0x40-0x7E)
                    while True:
                        seq_b = os.read(fd, 1)
                        if seq_b and 0x40 <= seq_b[0] <= 0x7E:
                            break
                continue
            if ch in ("\r", "\n"):  # Enter
                sys.stdout.write("\r\n")
                sys.stdout.flush()
                return "".join(buf)
            if ch == "\x7f" or ch == "\x08":  # Backspace
                if buf:
                    buf.pop()
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
