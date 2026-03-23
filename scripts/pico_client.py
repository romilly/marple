"""Workstation-side client for Pico MARPLE.

Connects to Pico over USB serial, sends APL expressions,
displays results. Requires pyserial: pip install pyserial

Usage: python scripts/pico_client.py [/dev/ttyACM0]
"""
import sys
import serial
import time

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyACM0"
BAUD = 115200
SENTINEL = "\x00"

def main():
    print(f"Connecting to Pico on {PORT}...")
    ser = serial.Serial(PORT, BAUD, timeout=5)
    time.sleep(1)  # wait for Pico to be ready

    # Drain any startup output
    while ser.in_waiting:
        ser.read(ser.in_waiting)
        time.sleep(0.1)

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

        # Send expression as hex-encoded UTF-8 (MicroPython drops non-ASCII)
        encoded = expr.encode("utf-8").hex()
        ser.write((encoded + "\r\n").encode("ascii"))
        ser.flush()

        # Read response until sentinel
        response_lines = []
        while True:
            raw = ser.readline()
            if not raw:
                print("(timeout)")
                break
            line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
            if line == SENTINEL:
                break
            # Skip echo of our input (hex-encoded)
            if line == encoded:
                continue
            response_lines.append(line)

        if response_lines:
            print("\n".join(response_lines))

    ser.close()

if __name__ == "__main__":
    main()
