"""Pico-side eval loop. Deploy to Pico as main.py.

Reads APL expressions from stdin (USB serial), evaluates them,
prints results. Protocol: one line in, one or more lines out,
terminated by a sentinel line "\\x00" (null byte).
"""
import sys
import time
sys.path.insert(0, "")

# Sync RTC via NTP if WiFi config is available (Pico W only)
try:
    import network  # type: ignore[import-not-found]
    import ntptime  # type: ignore[import-not-found]
    import WIFI_CONFIG  # type: ignore[import-not-found]
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_CONFIG.SSID, WIFI_CONFIG.PASSWORD)
    for _ in range(20):
        if wlan.isconnected():
            break
        time.sleep(1)
    if wlan.isconnected():
        ntptime.settime()
except (ImportError, OSError):
    pass  # No WiFi — RTC will be unset

from marple.interpreter import interpret, default_env
from marple.repl import format_result, _is_silent
from marple.errors import APLError

SENTINEL = "\x00"

env = default_env()

while True:
    try:
        raw = input()
    except EOFError:
        break
    raw = raw.strip()
    if not raw:
        print(SENTINEL)
        continue
    # Decode hex-encoded UTF-8 from workstation
    try:
        line = bytes.fromhex(raw).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        line = raw  # fallback: treat as plain ASCII
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
