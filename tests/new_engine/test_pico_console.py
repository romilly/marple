"""Tests for PicoConsole adapter."""

from marple.adapters.pico_console import PicoConsole


class TestPicoConsoleOutput:
    def test_writeln(self, capsys: object) -> None:
        import io, sys
        buf = io.StringIO()
        console = PicoConsole(output=buf)
        console.writeln("hello")
        assert buf.getvalue() == "hello\n"

    def test_write(self, capsys: object) -> None:
        import io
        buf = io.StringIO()
        console = PicoConsole(output=buf)
        console.write("hi")
        assert buf.getvalue() == "hi"


class TestPicoConsoleInput:
    def test_read_line(self) -> None:
        import io
        inp = io.StringIO("test input\n")
        out = io.StringIO()
        console = PicoConsole(input=inp, output=out)
        result = console.read_line("")
        assert result == "test input"

    def test_read_line_with_prompt(self) -> None:
        import io
        inp = io.StringIO("Romilly\n")
        out = io.StringIO()
        console = PicoConsole(input=inp, output=out)
        result = console.read_line("Name: ")
        assert out.getvalue() == "Name: "
        assert result == "Romilly"
