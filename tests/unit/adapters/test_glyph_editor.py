"""Tests for GlyphLineEditor — backtick translation and line editing."""

from marple.terminal import GlyphLineEditor
from tests.adapters.fake_char_source import FakeCharSource


class TestGlyphTranslation:
    def test_backtick_r_produces_rho(self) -> None:
        source = FakeCharSource("`r\r")
        output: list[str] = []
        editor = GlyphLineEditor(source, output.append)
        result = editor.read_line("      ")
        assert result == "⍴"

    def test_backtick_i_produces_iota(self) -> None:
        source = FakeCharSource("`i\r")
        output: list[str] = []
        editor = GlyphLineEditor(source, output.append)
        result = editor.read_line("      ")
        assert result == "⍳"

    def test_double_backtick_produces_literal(self) -> None:
        source = FakeCharSource("``\r")
        output: list[str] = []
        editor = GlyphLineEditor(source, output.append)
        result = editor.read_line("      ")
        assert result == "`"

    def test_backtick_unknown_passes_through(self) -> None:
        source = FakeCharSource("`3\r")
        output: list[str] = []
        editor = GlyphLineEditor(source, output.append)
        result = editor.read_line("      ")
        assert result == "`3"

    def test_plain_text(self) -> None:
        source = FakeCharSource("2+3\r")
        output: list[str] = []
        editor = GlyphLineEditor(source, output.append)
        result = editor.read_line("      ")
        assert result == "2+3"


class TestLineEditing:
    def test_backspace_removes_char(self) -> None:
        source = FakeCharSource("ab\x7fc\r")
        output: list[str] = []
        editor = GlyphLineEditor(source, output.append)
        result = editor.read_line("      ")
        assert result == "ac"

    def test_ctrl_d_returns_none(self) -> None:
        source = FakeCharSource("\x04")
        output: list[str] = []
        editor = GlyphLineEditor(source, output.append)
        result = editor.read_line("      ")
        assert result is None

    def test_ctrl_c_returns_empty(self) -> None:
        source = FakeCharSource("\x03")
        output: list[str] = []
        editor = GlyphLineEditor(source, output.append)
        result = editor.read_line("      ")
        assert result == ""

    def test_eof_returns_none(self) -> None:
        source = FakeCharSource("")
        output: list[str] = []
        editor = GlyphLineEditor(source, output.append)
        result = editor.read_line("      ")
        assert result is None
