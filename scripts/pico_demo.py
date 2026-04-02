"""Send a script to the Pico, simulating a typist.

Each line is typed character by character with a short delay,
then Enter is pressed and we wait for the response.

Usage: python scripts/pico_demo.py script.marple [/dev/ttyACM0]
"""
import sys
import time

from marple.web.pico_bridge import PicoConnection


CHAR_DELAY = 0.05   # seconds between characters
PAUSE_AFTER = 1.0   # seconds to wait after response
PORT = "/dev/ttyACM0"


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="MARPLE Pico demo typist")
    parser.add_argument("script", help="Path to .marple script file")
    parser.add_argument("port", nargs="?", default=PORT,
                        help="Serial port (default: /dev/ttyACM0)")
    parser.add_argument("--char-delay", type=float, default=CHAR_DELAY,
                        help="Delay between characters (seconds)")
    parser.add_argument("--pause", type=float, default=PAUSE_AFTER,
                        help="Pause after each response (seconds)")
    args = parser.parse_args()

    conn = PicoConnection(args.port)

    with open(args.script) as f:
        lines = f.readlines()

    for line in lines:
        line = line.rstrip("\n")
        if not line:
            continue

        # Display the prompt and type each character with delay
        sys.stdout.write("      ")
        sys.stdout.flush()
        for ch in line:
            sys.stdout.write(ch)
            sys.stdout.flush()
            time.sleep(args.char_delay)
        sys.stdout.write("\n")
        sys.stdout.flush()

        # Skip comments — don't send to Pico
        if line.lstrip().startswith("⍝"):
            time.sleep(args.pause)
            continue

        result = conn.eval(line)
        if result:
            print(result)

        time.sleep(args.pause)

    conn.close()


if __name__ == "__main__":
    main()
