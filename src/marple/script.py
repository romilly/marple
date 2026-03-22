from __future__ import annotations

from typing import Any

from marple.errors import APLError
from marple.interpreter import interpret
from marple.repl import format_result, _is_silent


PROMPT = "      "


def run_script(path: str) -> list[str]:
    """Run an APL script file line by line.

    Echoes each input line with the REPL prompt, followed by output.
    Stops on first error with an error message including line number.
    """
    env: dict[str, Any] = {}
    output: list[str] = []
    with open(path) as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            output.append(f"{PROMPT}{line}")
            if line.startswith("⍝"):
                continue
            try:
                result = interpret(line, env)
                if not _is_silent(line):
                    output.append(format_result(result))
            except APLError as e:
                output.append(f"{e} at line {lineno}")
                output.append(f"  {line}")
                break
            except Exception as e:
                output.append(f"ERROR at line {lineno}: {e}")
                output.append(f"  {line}")
                break
    return output
