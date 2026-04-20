"""Unit tests for PicoConsole — serial I/O with hex decoding and sentinel framing."""

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
        hex_encoded = "322b33"  # "2+3"
        inp = FakeInput([hex_encoded])
        out = io.StringIO()
        console = PicoConsole(input=inp, output=out)
        assert console.read_line("") == "2+3"

    def test_read_line_plain_ascii_fallback(self) -> None:
        inp = FakeInput(["plain text"])
        out = io.StringIO()
        console = PicoConsole(input=inp, output=out)
        assert console.read_line("") == "plain text"

    def test_read_line_returns_none_on_eof(self) -> None:
        inp = FakeInput([])
        out = io.StringIO()
        console = PicoConsole(input=inp, output=out)
        assert console.read_line("") is None

    def test_read_line_empty_line_returns_empty(self) -> None:
        inp = FakeInput([""])
        out = io.StringIO()
        console = PicoConsole(input=inp, output=out)
        assert console.read_line("") == ""


class TestPicoConsoleSentinel:
    def test_sentinel_before_second_read(self) -> None:
        inp = FakeInput(["322b33", "332b34"])  # "2+3", "3+4"
        out = io.StringIO()
        console = PicoConsole(input=inp, output=out)
        console.read_line("")
        assert SENTINEL not in out.getvalue()
        console.read_line("")
        assert out.getvalue().count(SENTINEL) == 1

    def test_no_sentinel_on_first_read(self) -> None:
        inp = FakeInput(["322b33"])
        out = io.StringIO()
        console = PicoConsole(input=inp, output=out)
        console.read_line("")
        assert SENTINEL not in out.getvalue()

    def test_sentinel_after_empty_line(self) -> None:
        inp = FakeInput(["", "322b33"])
        out = io.StringIO()
        console = PicoConsole(input=inp, output=out)
        console.read_line("")
        console.read_line("")
        assert out.getvalue().count(SENTINEL) == 1

    def test_sentinel_after_silent_expression(self) -> None:
        hex_comment = "e28dd120636f6d6d656e74"  # "⍝ comment"
        hex_expr = "322b33"  # "2+3"
        inp = FakeInput([hex_comment, hex_expr])
        out = io.StringIO()
        console = PicoConsole(input=inp, output=out)
        console.read_line("")
        console.read_line("")
        assert SENTINEL in out.getvalue()


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
