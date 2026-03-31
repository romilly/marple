"""Tests for PicoConsole adapter."""

import io

from marple.adapters.pico_console import INPUT_REQUEST, PicoConsole


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
    def test_read_line_sends_input_request_marker(self) -> None:
        hex_input = "Romilly".encode("utf-8").hex() + "\n"
        inp = io.StringIO(hex_input)
        out = io.StringIO()
        console = PicoConsole(input=inp, output=out)
        result = console.read_line("Name: ")
        assert out.getvalue() == INPUT_REQUEST + "Name: \n"
        assert result == "Romilly"

    def test_read_line_decodes_hex(self) -> None:
        hex_input = "2+3".encode("utf-8").hex() + "\n"
        inp = io.StringIO(hex_input)
        out = io.StringIO()
        console = PicoConsole(input=inp, output=out)
        result = console.read_line("⎕:")
        assert result == "2+3"

    def test_read_line_empty_prompt(self) -> None:
        hex_input = "hello".encode("utf-8").hex() + "\n"
        inp = io.StringIO(hex_input)
        out = io.StringIO()
        console = PicoConsole(input=inp, output=out)
        result = console.read_line("")
        assert out.getvalue() == INPUT_REQUEST + "\n"
        assert result == "hello"
