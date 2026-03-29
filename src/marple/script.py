
try:
    from typing import Any
except ImportError:
    pass

from marple.engine import Interpreter
from marple.errors import APLError
from marple.ports.filesystem import FileSystem
from marple.repl import format_result, _is_silent


PROMPT = "      "


def run_script(path: str, fs: FileSystem | None = None) -> list[str]:
    """Run an APL script file line by line.

    Echoes each input line with the REPL prompt, followed by output.
    Stops on first error with an error message including line number.
    """
    if fs is None:
        from marple.adapters.os_filesystem import OsFileSystem
        fs = OsFileSystem()
    interp = Interpreter(fs=fs)
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
        if accum:
            accum += "\n" + line
        else:
            accum = line
            start_lineno = lineno
        # Check if braces are balanced
        if accum.count("{") > accum.count("}"):
            continue
        try:
            result = interp.run(accum)
            if not _is_silent(accum):
                output.append(format_result(result, interp.env))
        except APLError as e:
            output.append(f"{e} at line {start_lineno}")
            output.append(f"  {accum}")
            break
        except Exception as e:
            output.append(f"ERROR at line {start_lineno}: {e}")
            output.append(f"  {accum}")
            break
        accum = ""
    return output
