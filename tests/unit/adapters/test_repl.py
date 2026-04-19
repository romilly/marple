"""REPL tests via FakeConsole — new engine."""

from marple.engine import Interpreter
from marple.repl import run_repl
from tests.adapters.fake_console import FakeConsole


class TestReplBanner:
    def test_banner_shown_on_start(self) -> None:
        console = FakeConsole([])
        run_repl(Interpreter(io=1), console)
        assert "MARPLE" in console.output
        assert "CLEAR WS" in console.output


class TestReplExpressions:
    def test_simple_addition(self) -> None:
        console = FakeConsole(["2+3"])
        run_repl(Interpreter(io=1), console)
        assert "5" in console.output_lines

    def test_vector_expression(self) -> None:
        console = FakeConsole(["⍳5"])
        run_repl(Interpreter(io=1), console)
        assert "1 2 3 4 5" in console.output_lines

    def test_silent_assignment(self) -> None:
        console = FakeConsole(["x←42"])
        run_repl(Interpreter(io=1), console)
        lines = [l for l in console.output_lines if l.strip()]
        # Only banner lines, no "42" output
        assert not any("42" in l for l in lines if "MARPLE" not in l and "CLEAR" not in l)

    def test_assignment_then_use(self) -> None:
        console = FakeConsole(["x←10", "x+5"])
        run_repl(Interpreter(io=1), console)
        assert "15" in console.output_lines


class TestReplErrors:
    def test_domain_error(self) -> None:
        console = FakeConsole(["1÷0"])
        run_repl(Interpreter(io=1), console)
        assert any("DOMAIN ERROR" in l for l in console.output_lines)

    def test_value_error(self) -> None:
        console = FakeConsole(["nope"])
        run_repl(Interpreter(io=1), console)
        assert any("ERROR" in l for l in console.output_lines)


class TestReplComments:
    def test_comment_only(self) -> None:
        console = FakeConsole(["⍝ this is a comment"])
        run_repl(Interpreter(io=1), console)
        # No result printed for comments
        lines = [l for l in console.output_lines if l.strip()]
        assert not any("0" == l.strip() for l in lines if "MARPLE" not in l and "CLEAR" not in l)


class TestReplMultiLine:
    def test_multiline_dfn(self) -> None:
        """REPL should accumulate lines until braces are balanced."""
        console = FakeConsole(["double←{", "⍵+⍵", "}", "double 7"])
        run_repl(Interpreter(io=1), console)
        assert "14" in console.output_lines


class TestReplSystemCommands:
    def test_off_exits(self) -> None:
        console = FakeConsole([")OFF"])
        run_repl(Interpreter(io=1), console)
        # Should exit cleanly — no error output

    def test_clear(self) -> None:
        console = FakeConsole(["x←42", ")CLEAR", "⎕NC 'x'"])
        run_repl(Interpreter(io=1), console)
        assert "CLEAR WS" in console.output
        # After clear, x is undefined → NC returns 0
        assert "0" in console.output_lines

    def test_wsid(self) -> None:
        console = FakeConsole([")WSID mywork", ")WSID"])
        run_repl(Interpreter(io=1), console)
        assert "mywork" in console.output

    def test_vars(self) -> None:
        console = FakeConsole(["x←1", "y←2", ")VARS"])
        run_repl(Interpreter(io=1), console)
        assert any("x" in l and "y" in l for l in console.output_lines)

    def test_fns(self) -> None:
        console = FakeConsole(["double←{⍵+⍵}", ")FNS"])
        run_repl(Interpreter(io=1), console)
        assert any("double" in l for l in console.output_lines)

    def test_fns_excludes_operators(self) -> None:
        console = FakeConsole(["double←{⍵+⍵}", "twice←{⍺⍺ ⍺⍺ ⍵}", ")FNS"])
        run_repl(Interpreter(io=1), console)
        fns_line = [l for l in console.output_lines if "double" in l][0]
        assert "twice" not in fns_line

    def test_ops(self) -> None:
        console = FakeConsole(["double←{⍵+⍵}", "twice←{⍺⍺ ⍺⍺ ⍵}", ")OPS"])
        run_repl(Interpreter(io=1), console)
        ops_line = [l for l in console.output_lines if "twice" in l]
        assert len(ops_line) > 0
        assert "double" not in ops_line[0]

    def test_unknown_command(self) -> None:
        console = FakeConsole([")NOPE"])
        run_repl(Interpreter(io=1), console)
        assert any("Unknown" in l for l in console.output_lines)
