from typing import Any

import sys

from marple.engine import Interpreter
from marple.errors import APLError
from marple.parser import is_balanced
from marple.ports.console import Console
from marple.system_commands import run_system_command


def process_line(
    line: str,
    accum: str,
    interp: Interpreter,
) -> tuple[str, str | None, bool]:
    """Process one input line. Returns (new_accum, output_or_None, should_exit).

    Handles system commands (when accum is empty), accumulates lines until
    braces are balanced, then executes. Raises APLError on evaluation errors
    so the caller can decide what to do.
    """
    if not accum and line.startswith(")"):
        output, should_exit = run_system_command(interp, line)
        return "", output or None, should_exit
    accum = accum + "\n" + line if accum else line
    if not is_balanced(accum):
        return accum, None, False
    r = interp.execute(accum)
    display = r.display_text if not r.silent else None
    return "", display, False


def run_repl(interp: Interpreter, console: Console, banner: bool = True) -> None:
    """Run the REPL loop using the given Console for I/O."""
    if banner:
        from marple import __version__ as ver
        console.writeln(f"MARPLE v{ver} - Mini APL in Python")
        console.writeln("CLEAR WS")
        console.writeln("")
    accum = ""
    while True:
        line = console.read_line("      ")
        if line is None:
            break
        line = line.strip()
        if not line:
            continue
        try:
            accum, output, should_exit = process_line(line, accum, interp)
            if output:
                console.writeln(output)
            if should_exit:
                break
        except APLError as e:
            console.writeln(str(e))
            accum = ""
        except Exception as e:
            console.writeln(f"ERROR: {e}")
            accum = ""


def main() -> None:
    if len(sys.argv) > 1:
        from marple.script import run_script
        path = sys.argv[1]
        for line in run_script(path):
            print(line)
        return

    from marple.adapters.desktop_config import DesktopConfig
    from marple.adapters.terminal_console import TerminalConsole
    console = TerminalConsole()
    interp = Interpreter(console=console, config=DesktopConfig())
    run_repl(interp, console)


if __name__ == "__main__":
    main()
