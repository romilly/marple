"""Workstation-side client for Pico MARPLE.

Connects to Pico over USB serial, sends APL expressions,
displays results. Requires pyserial: pip install pyserial

Usage:
    python scripts/pico_client.py [/dev/ttyACM0]
    python scripts/pico_client.py --script examples/12_life.marple
"""
import sys
import time

import serial

PORT = "/dev/ttyACM0"
BAUD = 115200
SENTINEL = "\x00"


_PICO_REPLACEMENTS = {
    "\u2014": "-",   # em dash
    "\u2013": "-",   # en dash
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


def send_and_receive(ser: serial.Serial, expr: str) -> list[str]:
    """Send an expression and collect response lines until sentinel."""
    encoded = _pico_safe(expr).encode("utf-8").hex()
    ser.write((encoded + "\r\n").encode("ascii"))
    ser.flush()

    response_lines = []
    while True:
        raw = ser.readline()
        if not raw:
            response_lines.append("(timeout)")
            break
        line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
        if line == SENTINEL:
            break
        if line == encoded:
            continue
        response_lines.append(line)
    return response_lines


def run_interactive(ser: serial.Serial) -> None:
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
        response = send_and_receive(ser, expr)
        if response:
            print("\n".join(response))


def run_script(ser: serial.Serial, path: str, pause: float = 0.5) -> None:
    """Send a .marple script file line by line."""
    with open(path) as f:
        lines = [line.rstrip("\n") for line in f]
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        print(f"      {stripped}")
        response = send_and_receive(ser, stripped)
        if response:
            print("\n".join(response))
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
    ser = serial.Serial(args.port, BAUD, timeout=5)
    time.sleep(1)

    while ser.in_waiting:
        ser.read(ser.in_waiting)
        time.sleep(0.1)

    try:
        if args.script:
            run_script(ser, args.script, args.pause)
        else:
            run_interactive(ser)
    finally:
        ser.close()


if __name__ == "__main__":
    main()
