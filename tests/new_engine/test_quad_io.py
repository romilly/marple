"""Tests for ⎕ (quad) and ⍞ (quote-quad) I/O system variables."""

import pytest

from hamcrest import assert_that, contains_string, equal_to, has_item, is_

from marple.adapters.buffered_console import BufferedConsole
from marple.backend_functions import chars_to_str, str_to_char_array
from marple.numpy_array import APLArray, S
from marple.engine import Interpreter
from marple.errors import DomainError
from marple.tokenizer import Token, TokenType, Tokenizer
from marple.script import run_script
from marple.web.server import WebSession
from tests.adapters.fake_console import FakeConsole


class TestConsoleWiring:
    """Console port is available to the executor via the environment."""

    def test_interpreter_receives_console(self) -> None:
        console = FakeConsole([])
        interp = Interpreter(console=console)
        assert_that(interp.env.console, is_(console))

    def test_console_defaults_to_none(self) -> None:
        interp = Interpreter()
        assert_that(interp.env.console, is_(None))

    def test_console_propagates_through_env_copy(self) -> None:
        console = FakeConsole([])
        interp = Interpreter(console=console)
        copied = interp.env.copy()
        assert_that(copied.console, is_(console))


class TestTokenizer:
    """⎕ and ⍞ are recognized as SYSVAR tokens."""

    def test_bare_quad_tokenizes_as_sysvar(self) -> None:
        tokens = Tokenizer("⎕").tokenize()
        assert_that(tokens[0], equal_to(Token(TokenType.SYSVAR, "⎕")))

    def test_quote_quad_tokenizes_as_sysvar(self) -> None:
        tokens = Tokenizer("⍞").tokenize()
        assert_that(tokens[0], equal_to(Token(TokenType.SYSVAR, "⍞")))


class TestQuadOutput:
    """⎕← outputs value with newline (tee behavior)."""

    def test_quad_assign_outputs_with_newline(self) -> None:
        console = FakeConsole([])
        interp = Interpreter(console=console)
        interp.run("⎕←42")
        assert_that(console.output, equal_to("42\n"))

    def test_quad_assign_returns_value(self) -> None:
        console = FakeConsole([])
        interp = Interpreter(console=console)
        result = interp.run("⎕←42")
        assert_that(result, equal_to(S(42)))

    def test_quad_assign_string(self) -> None:
        console = FakeConsole([])
        interp = Interpreter(console=console)
        interp.run("⎕←'hello'")
        assert_that(console.output, equal_to("hello\n"))

    def test_quad_assign_vector(self) -> None:
        console = FakeConsole([])
        interp = Interpreter(console=console)
        interp.run("⎕←1 2 3")
        assert_that(console.output, equal_to("1 2 3\n"))


class TestQuoteQuadOutput:
    """⍞← displays prompt, reads input, returns prompt+response."""

    def test_quote_quad_assign_displays_prompt_and_reads(self) -> None:
        console = FakeConsole(["Romilly"])
        interp = Interpreter(console=console)
        result = interp.run("⍞←'Name: '")
        assert_that(chars_to_str(result.data), equal_to("Romilly"))

    def test_quote_quad_assign_chain(self) -> None:
        """a ← ⍞ ← 'prompt' sets a to response only (Dyalog style)."""
        console = FakeConsole(["Romilly"])
        interp = Interpreter(console=console)
        interp.run("a ← ⍞ ← 'Name: '")
        result = interp.run("a")
        assert_that(chars_to_str(result.data), equal_to("Romilly"))

    def test_quote_quad_assign_raises_when_no_input(self) -> None:
        console = FakeConsole([])  # no inputs
        interp = Interpreter(console=console)
        with pytest.raises(DomainError, match="⍞ input not available"):
            interp.run("⍞←'Name: '")


class TestQuoteQuadInput:
    """⍞ reads a line of raw character input."""

    def test_quote_quad_reads_character_vector(self) -> None:
        console = FakeConsole(["hello"])
        interp = Interpreter(console=console)
        interp.run("x←⍞")
        result = interp.run("x")
        assert_that(chars_to_str(result.data), equal_to("hello"))

    def test_quote_quad_numeric_input_stays_as_characters(self) -> None:
        console = FakeConsole(["42"])
        interp = Interpreter(console=console)
        interp.run("x←⍞")
        result = interp.run("x")
        assert_that(chars_to_str(result.data), equal_to("42"))

    def test_quote_quad_empty_input(self) -> None:
        console = FakeConsole([""])
        interp = Interpreter(console=console)
        interp.run("x←⍞")
        result = interp.run("x")
        assert result.shape == [0]
        assert chars_to_str(result.data) == ""

    def test_quote_quad_raises_when_no_input_available(self) -> None:
        console = FakeConsole([])  # no inputs
        interp = Interpreter(console=console)
        with pytest.raises(DomainError, match="⍞ input not available"):
            interp.run("x←⍞")


class TestQuadInput:
    """⎕ prompts, reads, parses, and evaluates input as APL."""

    def test_quad_evaluates_expression(self) -> None:
        console = FakeConsole(["2+3"])
        interp = Interpreter(console=console)
        interp.run("x←⎕")
        result = interp.run("x")
        assert_that(result, equal_to(S(5)))

    def test_quad_passes_prompt_to_read_line(self) -> None:
        """⎕ passes '⎕:' as the prompt argument to read_line."""
        from unittest.mock import MagicMock
        console = FakeConsole(["42"])
        original_read = console.read_line
        console.read_line = MagicMock(side_effect=original_read)  # type: ignore[method-assign]
        interp = Interpreter(console=console)
        interp.run("x←⎕")
        console.read_line.assert_called_once_with("⎕:")

    def test_quad_reads_vector(self) -> None:
        console = FakeConsole(["1 2 3"])
        interp = Interpreter(console=console)
        interp.run("x←⎕")
        result = interp.run("x")
        assert_that(result, equal_to(APLArray.array([3], [1, 2, 3])))

    def test_quad_in_expression(self) -> None:
        console = FakeConsole(["5"])
        interp = Interpreter(console=console)
        result = interp.run("3+⎕")
        assert_that(result, equal_to(S(8)))

    def test_quad_raises_when_no_input_available(self) -> None:
        console = FakeConsole([])  # no inputs
        interp = Interpreter(console=console)
        with pytest.raises(DomainError, match="⎕ input not available"):
            interp.run("x←⎕")


class TestBufferedConsole:
    """BufferedConsole captures output and can be cleared between evaluations."""

    def test_captures_writeln(self) -> None:
        bc = BufferedConsole()
        bc.writeln("hello")
        assert_that(bc.output, equal_to("hello\n"))

    def test_captures_write(self) -> None:
        bc = BufferedConsole()
        bc.write("hi")
        assert_that(bc.output, equal_to("hi"))

    def test_clear_resets_output(self) -> None:
        bc = BufferedConsole()
        bc.writeln("old")
        bc.clear()
        bc.writeln("new")
        assert_that(bc.output, equal_to("new\n"))

    def test_read_line_returns_none(self) -> None:
        bc = BufferedConsole()
        assert_that(bc.read_line("prompt"), is_(None))

    def test_quad_assign_via_buffered_console(self) -> None:
        bc = BufferedConsole()
        interp = Interpreter(console=bc)
        interp.run("⎕←42")
        assert_that(bc.output, equal_to("42\n"))

    def test_output_lines(self) -> None:
        bc = BufferedConsole()
        bc.writeln("line1")
        bc.writeln("line2")
        assert_that(bc.output_lines, equal_to(["line1", "line2"]))


@pytest.mark.slow
class TestPrideQuadOutput:
    """PRIDE WebSession includes ⎕← output in HTML response."""

    def test_quad_assign_appears_in_pride_output(self) -> None:
        session = WebSession()
        result_html = session.evaluate("⎕←42")
        assert_that(result_html, contains_string('class="output"'))
        assert_that(result_html, contains_string("42"))

    def test_quote_quad_assign_with_input(self) -> None:
        import threading
        session = WebSession()

        def provide_input() -> None:
            session._console.wait_for_prompt(timeout=2.0)
            session._console.provide_input("world")

        t = threading.Thread(target=provide_input)
        t.start()
        result_html = session.evaluate("a ← ⍞ ← 'hello '")
        t.join(timeout=2.0)
        # Assignment is silent, but the value was captured
        result = session.interp.run("a")
        assert_that(chars_to_str(result.data), equal_to("world"))


class TestScriptQuadOutput:
    """Script runner includes ⎕← output."""

    def test_quad_assign_in_script(self, tmp_path: object) -> None:
        from pathlib import Path
        p = Path(str(tmp_path)) / "test.marple"
        p.write_text("⎕←42\n")
        lines = run_script(str(p))
        # Should not error, and should have "42" as output
        assert not any("ERROR" in line for line in lines)
        assert_that(lines, has_item("42"))
