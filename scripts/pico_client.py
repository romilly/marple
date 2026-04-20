"""Workstation-side client for Pico MARPLE.

Connects to Pico over USB serial, sends APL expressions,
displays results. Requires pyserial: pip install pyserial

Usage:
    python scripts/pico_client.py [/dev/ttyACM0]
    python scripts/pico_client.py --script examples/12_life.marple
"""
import time

from marple.adapters.pico_serial import PicoConnection


PORT = "/dev/ttyACM0"


_PICO_REPLACEMENTS = {
    "\u2014": "-",   # em dash
    "\u2013": "-",   # en dash
    "\u2500": "-",   # box drawings light horizontal
    "\u2550": "=",   # box drawings double horizontal
    "\u2018": "'",   # left single quote
    "\u2019": "'",   # right single quote
    "\u201c": '"',   # left double quote
    "\u201d": '"',   # right double quote
}


def _pico_safe(text: str) -> str:
    """Replace characters the Pico font can't render."""
    for char, replacement in _PICO_REPLACEMENTS.items():
        text = text.replace(char, replacement)
    return text


def run_interactive(conn: PicoConnection) -> None:
    """Interactive REPL over serial."""
    print("MARPLE on Pico — type APL expressions, Ctrl-C to exit\n")
    while True:
        try:
            expr = input("      ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        expr = expr.strip()
        if not expr:
            continue
        result = conn.eval(_pico_safe(expr))
        if result:
            print(result)


def run_script(conn: PicoConnection, path: str, pause: float = 0.5) -> None:
    """Send a .marple script file line by line.

    Multi-line dfns (unbalanced braces) are accumulated and
    sent as a single newline-joined expression.
    """
    with open(path) as f:
        lines = [line.rstrip("\n") for line in f]
    accum = ""
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        print(f"      {stripped}")
        if accum:
            accum += "\n" + stripped
        else:
            accum = stripped
        if accum.count("{") > accum.count("}"):
            continue
        result = conn.eval(_pico_safe(accum))
        if result:
            print(result)
        accum = ""
        time.sleep(pause)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="MARPLE Pico client")
    parser.add_argument("port", nargs="?", default=PORT,
                        help="Serial port (default: /dev/ttyACM0)")
    parser.add_argument("--script", "-s", default=None,
                        help="Run a .marple script file")
    parser.add_argument("--pause", type=float, default=0.5,
                        help="Pause between lines in script mode (seconds)")
    args = parser.parse_args()

    print(f"Connecting to Pico on {args.port}...")
    conn = PicoConnection(args.port)
    print("Connected.")

    try:
        if args.script:
            run_script(conn, args.script, args.pause)
        else:
            run_interactive(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
