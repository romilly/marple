
try:
    from typing import Any
except ImportError:
    pass

from marple.adapters.buffered_console import BufferedConsole
from marple.engine import Interpreter
from marple.errors import APLError
from marple.ports.filesystem import FileSystem
from marple.repl import process_line


PROMPT = "      "


def run_script(path: str, fs: FileSystem | None = None) -> list[str]:
    """Run an APL script file line by line.

    Echoes each input line with the REPL prompt, followed by output.
    Stops on first error with an error message including line number.
    """
    if fs is None:
        from marple.adapters.os_filesystem import OsFileSystem
        fs = OsFileSystem()
    console = BufferedConsole()
    interp = Interpreter(fs=fs, console=console)
    output: list[str] = []
    text = fs.read_text(path)
    accum = ""
    start_lineno = 1
    for lineno, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        output.append(f"{PROMPT}{line}")
        if line.startswith("⍝") and not accum:
            continue
        if not accum:
            start_lineno = lineno
        try:
            console.clear()
            accum, result, should_exit = process_line(line, accum, interp)
            console_output = console.output
            if console_output:
                output.append(console_output.rstrip("\n"))
            if result:
                output.append(result)
            if should_exit:
                break
        except APLError as e:
            output.append(f"{e} at line {start_lineno}")
            output.append(f"  {accum or line}")
            break
        except Exception as e:
            output.append(f"ERROR at line {start_lineno}: {e}")
            output.append(f"  {accum or line}")
            break
    return output
