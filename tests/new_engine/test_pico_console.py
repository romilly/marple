"""Tests for PicoConsole adapter."""

import io

from marple.adapters.pico_console import PicoConsole


class TestPicoConsoleOutput:
    def test_writeln(self) -> None:
        buf = io.StringIO()
        console = PicoConsole(input=io.StringIO(""), output=buf)
        console.writeln("hello")
        assert buf.getvalue() == "hello\n"

    def test_write(self) -> None:
        buf = io.StringIO()
        console = PicoConsole(input=io.StringIO(""), output=buf)
        console.write("hi")
        assert buf.getvalue() == "hi"


class TestPicoConsoleInput:
    def test_read_line_returns_none_on_eof(self) -> None:
        """read_line returns None when input is exhausted."""
        empty_input = io.StringIO("")
        console = PicoConsole(input=empty_input)
        assert console.read_line("⎕:") is None
