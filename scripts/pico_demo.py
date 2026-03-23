"""Send a script to the Pico, simulating a typist.

Each line is typed character by character with a short delay,
then Enter is pressed and we wait for the response.

Usage: python scripts/pico_demo.py script.marple [/dev/ttyACM0]
"""
import sys
import time
import serial

SCRIPT = sys.argv[1]
PORT = sys.argv[2] if len(sys.argv) > 2 else "/dev/ttyACM0"
BAUD = 115200
SENTINEL = "\x00"
CHAR_DELAY = 0.05   # seconds between characters
PAUSE_AFTER = 1.0   # seconds to wait after response

def main():
    ser = serial.Serial(PORT, BAUD, timeout=5)
    time.sleep(1)

    # Drain startup output
    while ser.in_waiting:
        ser.read(ser.in_waiting)
        time.sleep(0.1)

    with open(SCRIPT) as f:
        lines = f.readlines()

    for line in lines:
        line = line.rstrip("\n")
        if not line:
            continue

        # Display the prompt
        sys.stdout.write("      ")
        sys.stdout.flush()

        # Type each character with delay
        for ch in line:
            sys.stdout.write(ch)
            sys.stdout.flush()
            time.sleep(CHAR_DELAY)

        sys.stdout.write("\n")
        sys.stdout.flush()

        # Skip comments — don't send to Pico
        if line.lstrip().startswith("⍝"):
            time.sleep(PAUSE_AFTER)
            continue

        # Send hex-encoded expression
        encoded = line.encode("utf-8").hex()
        ser.write((encoded + "\r\n").encode("ascii"))
        ser.flush()

        # Read response until sentinel
        while True:
            raw = ser.readline()
            if not raw:
                break
            text = raw.decode("utf-8", errors="replace").rstrip("\r\n")
            if text == SENTINEL:
                break
            if text == encoded:
                continue
            print(text)

        time.sleep(PAUSE_AFTER)

    ser.close()

if __name__ == "__main__":
    main()
