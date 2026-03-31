"""Pico-side eval loop. Deploy to Pico as main.py.

Reads APL expressions from stdin (USB serial), evaluates them,
prints results. Protocol: one line in, one or more lines out,
terminated by a sentinel line "\\x00" (null byte).

If running on a Pimoroni Presto, also mirrors the session
to the 480x480 LCD using the APL bitmap font.
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

from marple.adapters.pico_config import PicoConfig
from marple.adapters.pico_console import PicoConsole
from marple.engine import Interpreter
from marple.errors import APLError
import marple

SENTINEL = "\x00"

try:
    from marple_config import settings as _pico_settings  # type: ignore[import-not-found]
except ImportError:
    _pico_settings = {}

interp = Interpreter(config=PicoConfig(_pico_settings), console=PicoConsole())

# Optional Presto LCD display
try:
    from presto_display import PrestoDisplay  # type: ignore[import-not-found]
    lcd = PrestoDisplay()
    lcd.show_banner("MARPLE v" + marple.__version__)
    lcd.show_banner("CLEAR WS")
except ImportError:
    lcd = None

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
    if lcd:
        lcd.show_input(line)
    if line.startswith(")"):
        from marple.system_commands import run_system_command
        output, should_exit = run_system_command(interp, line)
        if output:
            print(output)
            if lcd:
                lcd.show_output(output)
        print(SENTINEL)
        if should_exit:
            break
        continue
    try:
        r = interp.execute(line)
        if r.silent:
            print(SENTINEL)
        else:
            print(r.display_text)
            print(SENTINEL)
            if lcd:
                lcd.show_output(r.display_text)
    except APLError as e:
        print("ERROR: " + str(e))
        print(SENTINEL)
        if lcd:
            lcd.show_error(str(e))
    except Exception as e:
        print("ERROR: " + str(e))
        print(SENTINEL)
        if lcd:
            lcd.show_error(str(e))
