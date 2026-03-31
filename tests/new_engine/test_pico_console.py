"""Tests for PicoConsole adapter."""

import io

from marple.adapters.pico_console import PicoConsole


class TestPicoConsoleOutput:
    def test_writeln(self) -> None:
        buf = io.StringIO()
        console = PicoConsole(output=buf)
        console.writeln("hello")
        assert buf.getvalue() == "hello\n"

    def test_write(self) -> None:
        buf = io.StringIO()
        console = PicoConsole(output=buf)
        console.write("hi")
        assert buf.getvalue() == "hi"


class TestPicoConsoleInput:
    def test_read_line_returns_none(self) -> None:
        """Interactive input not available over serial."""
        console = PicoConsole()
        assert console.read_line("⎕:") is None
