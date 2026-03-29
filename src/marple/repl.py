
try:
    from typing import Any
except ImportError:
    pass

import sys

from marple.engine import Interpreter
from marple.errors import APLError
from marple.formatting import format_result  # re-export for backward compat
from marple.ports.console import Console
from marple.system_commands import run_system_command


def run_repl(interp: Interpreter, console: Console) -> None:
    """Run the REPL loop using the given Console for I/O."""
    from marple import __version__ as ver
    console.writeln(f"MARPLE v{ver} - Mini APL in Python")
    console.writeln("CLEAR WS")
    console.writeln("")
    while True:
        line = console.read_line("      ")
        if line is None:
            break
        line = line.strip()
        if not line:
            continue
        if line.startswith(")"):
            output, should_exit = run_system_command(interp, line)
            if output:
                console.writeln(output)
            if should_exit:
                break
            continue
        try:
            r = interp.execute(line)
            if not r.silent:
                console.writeln(r.display_text)
        except APLError as e:
            console.writeln(str(e))
        except Exception as e:
            console.writeln(f"ERROR: {e}")


def main() -> None:
    if len(sys.argv) > 1:
        from marple.script import run_script
        path = sys.argv[1]
        for line in run_script(path):
            print(line)
        return

    from marple.adapters.terminal_console import TerminalConsole
    interp = Interpreter()
    console = TerminalConsole()
    run_repl(interp, console)


if __name__ == "__main__":
    main()
