"""Pico-side eval loop. Deploy to Pico as main.py.

Reads APL expressions from stdin (USB serial), evaluates them,
prints results. Protocol: one line in, one or more lines out,
terminated by a sentinel line "\\x00" (null byte).
"""
import sys
sys.path.insert(0, "")

from marple.interpreter import interpret, default_env
from marple.repl import format_result, _is_silent
from marple.errors import APLError

SENTINEL = "\x00"

env = default_env()

while True:
    try:
        line = input()
    except EOFError:
        break
    line = line.strip()
    if not line:
        print(SENTINEL)
        continue
    try:
        result = interpret(line, env)
        if _is_silent(line):
            print(SENTINEL)
        else:
            print(format_result(result))
            print(SENTINEL)
    except APLError as e:
        print("ERROR: " + str(e))
        print(SENTINEL)
    except Exception as e:
        print("ERROR: " + str(e))
        print(SENTINEL)
