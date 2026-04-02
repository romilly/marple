"""Tests for PicoConsole — serial I/O with hex decoding and sentinel framing."""

import io

from marple.adapters.pico_console import PicoConsole


SENTINEL = "\x00"


class FakeInput:
    """Simulates stdin with pre-loaded lines."""

    def __init__(self, lines: list[str]) -> None:
        self._lines = list(lines)

    def readline(self) -> str:
        if not self._lines:
            return ""
        return self._lines.pop(0) + "\n"


class TestPicoConsoleReadLine:
    def test_read_line_hex_decodes(self) -> None:
        """read_line should hex-decode UTF-8 input."""
        # "2+3" hex-encoded
        hex_encoded = "322b33"
        inp = FakeInput([hex_encoded])
        out = io.StringIO()
        console = PicoConsole(input=inp, output=out)
        line = console.read_line("")
        assert line == "2+3"

    def test_read_line_plain_ascii_fallback(self) -> None:
        """Non-hex input should be returned as-is."""
        inp = FakeInput(["plain text"])
        out = io.StringIO()
        console = PicoConsole(input=inp, output=out)
        line = console.read_line("")
        assert line == "plain text"

    def test_read_line_returns_none_on_eof(self) -> None:
        """True EOF (no more data) should return None."""
        inp = FakeInput([])
        out = io.StringIO()
        console = PicoConsole(input=inp, output=out)
        assert console.read_line("") is None

    def test_read_line_empty_line_returns_empty(self) -> None:
        """An empty line (just newline) should return empty string, not None."""
        inp = FakeInput([""])
        out = io.StringIO()
        console = PicoConsole(input=inp, output=out)
        assert console.read_line("") == ""


class TestPicoConsoleSentinel:
    def test_sentinel_after_writeln_then_read(self) -> None:
        """Sentinel sent before next read when writeln was called."""
        hex_first = "322b33"  # "2+3"
        hex_second = "332b34"  # "3+4"
        inp = FakeInput([hex_first, hex_second])
        out = io.StringIO()
        console = PicoConsole(input=inp, output=out)
        console.read_line("")  # reads "2+3"
        console.writeln("5")  # output — sets needs_sentinel
        console.read_line("")  # sends sentinel before reading "3+4"
        output = out.getvalue()
        assert output.count(SENTINEL) == 1

    def test_no_sentinel_without_output(self) -> None:
        """No sentinel if nothing was written between reads."""
        hex_first = "322b33"
        hex_second = "332b34"
        inp = FakeInput([hex_first, hex_second])
        out = io.StringIO()
        console = PicoConsole(input=inp, output=out)
        console.read_line("")  # reads "2+3"
        console.read_line("")  # no writeln between — no sentinel
        assert SENTINEL not in out.getvalue()

    def test_sentinel_after_empty_line(self) -> None:
        """Empty line (probe) triggers sentinel on next read."""
        hex_expr = "322b33"
        inp = FakeInput(["", hex_expr])
        out = io.StringIO()
        console = PicoConsole(input=inp, output=out)
        console.read_line("")  # reads empty line — sets needs_sentinel
        console.read_line("")  # sends sentinel, reads "2+3"
        assert out.getvalue().count(SENTINEL) == 1


class TestPicoConsoleWrite:
    def test_writeln_writes_text(self) -> None:
        inp = FakeInput([])
        out = io.StringIO()
        console = PicoConsole(input=inp, output=out)
        console.writeln("hello")
        assert out.getvalue() == "hello\n"

    def test_write_no_newline(self) -> None:
        inp = FakeInput([])
        out = io.StringIO()
        console = PicoConsole(input=inp, output=out)
        console.write("hello")
        assert out.getvalue() == "hello"
